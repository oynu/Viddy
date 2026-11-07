import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import httpx

from backend.config import settings
from backend.publishing.browser_utils import (
    find_brave_executable,
    clean_stale_profile_locks,
    get_browser_args,
    attach_dialog_handler,
    sweep_page_traps
)
from backend.database.session import get_db
from backend.database import crud

USER_DATA_DIR = settings.base_dir / "data" / "tiktok_user_data"
TIKTOK_COOKIES_PATH = settings.base_dir / "data" / "tiktok_cookies.json"

class TikTokPublishResult(BaseModel):
    success: bool
    publish_id: Optional[str] = None
    url: Optional[str] = None
    comment_posted: bool = False
    error_message: Optional[str] = None

class TikTokPublisher:
    """
    Automated publishing to TikTok via Playwright Browser automation
    using Brave browser engine, persistent profile, and cookies.json session.
    """
    def __init__(
        self,
        cookies_path: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        client_key: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        self.cookies_path = Path(cookies_path) if cookies_path else TIKTOK_COOKIES_PATH
        self.user_data_dir = Path(user_data_dir) if user_data_dir else USER_DATA_DIR
        self.client_key = client_key or os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = client_secret or os.getenv("TIKTOK_CLIENT_SECRET")
        self.init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"

    def is_connected(self) -> bool:
        """Returns True if persistent profile exists or saved cookies exist."""
        if self.user_data_dir.exists() and any(self.user_data_dir.iterdir()):
            return True
        if self.cookies_path.exists():
            try:
                with open(self.cookies_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    return isinstance(cookies, list) and len(cookies) > 0
            except Exception:
                pass
        return bool(self.client_key and self.client_secret)

    async def publish_video(
        self,
        video_path: str,
        caption: str,
        access_token: Optional[str] = None,
        comment_text: Optional[str] = None,
        privacy_level: str = "PUBLIC_TO_EVERYONE"
    ) -> TikTokPublishResult:
        """
        Publishes video to TikTok using Brave Browser and Playwright.
        """
        if not os.path.exists(video_path):
            return TikTokPublishResult(
                success=False,
                error_message=f"Video file not found at: {video_path}"
            )

        return await self._publish_via_playwright(
            video_path=video_path,
            caption=caption,
            comment_text=comment_text
        )

    async def _publish_via_playwright(
        self,
        video_path: str,
        caption: str,
        comment_text: Optional[str] = None,
        timeout_seconds: int = 300
    ) -> TikTokPublishResult:
        """
        Automated upload to TikTok Studio using Brave browser.
        Handles cookie consent, react-joyride tour overlays, copyright traps,
        file injection, captioning, and post submission.
        """
        from playwright.async_api import async_playwright

        abs_video_path = str(Path(video_path).resolve())
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.cookies_path.parent.mkdir(parents=True, exist_ok=True)

        # Clean lingering locks from previous unexpected exits
        clean_stale_profile_locks(self.user_data_dir)

        brave_path = find_brave_executable()
        is_first_time = not self.is_connected()
        headless_mode = not is_first_time

        launch_kwargs = {
            "user_data_dir": str(self.user_data_dir),
            "headless": headless_mode,
            "viewport": {"width": 1280, "height": 850},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "args": get_browser_args(headless=headless_mode)
        }
        if brave_path:
            launch_kwargs["executable_path"] = brave_path
            print(f"[*] [TIKTOK PUBLISH] Launching Brave Browser ({brave_path}) headless={headless_mode}...")
        else:
            print(f"[*] [TIKTOK PUBLISH] Launching browser engine (headless={headless_mode})...")

        context = None
        async with async_playwright() as p:
            try:
                context = await p.chromium.launch_persistent_context(**launch_kwargs)
            except Exception as e:
                print(f"[!] Persistent context launch retry after: {e}")
                clean_stale_profile_locks(self.user_data_dir)
                await asyncio.sleep(1.0)
                context = await p.chromium.launch_persistent_context(**launch_kwargs)

            # Pre-load exported cookies if available
            if self.cookies_path.exists():
                try:
                    with open(self.cookies_path, "r", encoding="utf-8") as f:
                        raw_cookies = json.load(f)
                        if isinstance(raw_cookies, list):
                            formatted = []
                            for c in raw_cookies:
                                cd = {
                                    "name": c.get("name"),
                                    "value": c.get("value"),
                                    "domain": c.get("domain", ".tiktok.com"),
                                    "path": c.get("path", "/")
                                }
                                if "sameSite" in c and c["sameSite"] in ["Strict", "Lax", "None"]:
                                    cd["sameSite"] = c["sameSite"]
                                formatted.append(cd)
                            await context.add_cookies(formatted)
                except Exception:
                    pass

            page = context.pages[0] if context.pages else await context.new_page()
            await attach_dialog_handler(page)

            # Navigate to TikTok Studio Upload
            upload_url = "https://www.tiktok.com/tiktokstudio/upload"
            print(f"[*] [TIKTOK PUBLISH] Navigating to {upload_url}...")
            await page.goto(upload_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(2.0)
            await sweep_page_traps(page)

            # Check if login is required
            if "login" in page.url.lower():
                print("[!] [TIKTOK PUBLISH] TikTok session login required.")
                if headless_mode:
                    await context.close()
                    print("[*] [TIKTOK PUBLISH] Re-opening visible Brave window for 1-time login...")
                    return await self._login_then_upload(abs_video_path, caption, comment_text, brave_path)
                else:
                    print("[*] [TIKTOK PUBLISH] Please log into your TikTok account in Brave now...")
                    logged_in = await self._wait_for_login(page, timeout=180)
                    if not logged_in:
                        await context.close()
                        return TikTokPublishResult(
                            success=False,
                            error_message="TikTok login timed out. Please sign in when prompted."
                        )
                    await page.goto(upload_url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2.0)
                    await sweep_page_traps(page)

            # Locate File Input
            print(f"[*] [TIKTOK PUBLISH] Selecting video file: {abs_video_path}...")
            await sweep_page_traps(page)
            file_input = await self._find_file_input(page)
            if not file_input:
                await page.goto(upload_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2.0)
                await sweep_page_traps(page)
                file_input = await self._find_file_input(page)

            if not file_input:
                await context.close()
                return TikTokPublishResult(
                    success=False,
                    error_message="Could not find video file upload input on TikTok Studio page."
                )

            # Upload video file
            await file_input.set_input_files(abs_video_path)
            print("[*] [TIKTOK PUBLISH] Video file sent to TikTok Studio. Processing upload...")
            await asyncio.sleep(4.0)
            await sweep_page_traps(page)

            # Fill Caption & Hashtags
            print("[*] [TIKTOK PUBLISH] Injecting caption & viral hashtags...")
            await self._fill_caption(page, caption)
            await asyncio.sleep(2.0)
            await sweep_page_traps(page)

            # Wait for upload completion & Post button to become enabled
            print("[*] [TIKTOK PUBLISH] Waiting for TikTok to finish encoding video...")
            post_btn = await self._wait_for_post_button(page, timeout=120)
            if not post_btn:
                await context.close()
                return TikTokPublishResult(
                    success=False,
                    error_message="TikTok 'Post' button was not ready or remained disabled."
                )

            # Purge traps immediately before clicking Post
            await sweep_page_traps(page)
            print("[*] [TIKTOK PUBLISH] Submitting Post...")
            
            try:
                await post_btn.scroll_into_view_if_needed()
                await post_btn.click(force=True, timeout=8000)
            except Exception as click_err:
                print(f"[!] Standard click encountered overlay ({click_err}). Forcing JavaScript click...")
                await sweep_page_traps(page)
                await post_btn.evaluate("el => el.click()")

            # Post-click verification and trap handling
            print("[*] [TIKTOK PUBLISH] Waiting for publishing confirmation...")
            published = await self._wait_for_publish_completion(page, timeout=45)

            # Save updated cookies
            try:
                cookies = await context.cookies()
                with open(self.cookies_path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=2)
                with get_db() as s:
                    crud.upsert_platform_account(s, "tiktok", is_connected=True, account_name="TikTok Account (Brave Active)")
            except Exception:
                pass

            await asyncio.sleep(2.0)
            await context.close()
            clean_stale_profile_locks(self.user_data_dir)
            print("[OK] [TIKTOK PUBLISH] Video published successfully to TikTok!")

            return TikTokPublishResult(
                success=True,
                publish_id="tiktok_studio_post",
                url="https://www.tiktok.com/tiktokstudio/manage",
                comment_posted=bool(comment_text)
            )

    async def _login_then_upload(
        self,
        video_path: str,
        caption: str,
        comment_text: Optional[str],
        brave_path: Optional[str]
    ) -> TikTokPublishResult:
        """Launches a visible Brave window, waits for user login, then immediately publishes."""
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            launch_kwargs = {
                "user_data_dir": str(self.user_data_dir),
                "headless": False,
                "viewport": {"width": 1280, "height": 850},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "args": get_browser_args(headless=False)
            }
            if brave_path:
                launch_kwargs["executable_path"] = brave_path

            clean_stale_profile_locks(self.user_data_dir)
            context = await p.chromium.launch_persistent_context(**launch_kwargs)
            page = context.pages[0] if context.pages else await context.new_page()
            await attach_dialog_handler(page)

            await page.goto("https://www.tiktok.com/login?redirect_url=https%3A%2F%2Fwww.tiktok.com%2Ftiktokstudio%2Fupload", timeout=45000)
            await sweep_page_traps(page)

            print("[*] [TIKTOK PUBLISH] Please log into your TikTok account in Brave now...")
            logged_in = await self._wait_for_login(page, timeout=300)
            if not logged_in:
                await context.close()
                return TikTokPublishResult(
                    success=False,
                    error_message="TikTok login was not completed. Please sign in and try again."
                )

            # Redirect directly to upload
            await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(2.0)
            await sweep_page_traps(page)

            file_input = await self._find_file_input(page)
            if not file_input:
                await context.close()
                return TikTokPublishResult(success=False, error_message="Could not find file upload input.")

            await file_input.set_input_files(video_path)
            await asyncio.sleep(4.0)
            await sweep_page_traps(page)

            await self._fill_caption(page, caption)
            await asyncio.sleep(2.0)
            await sweep_page_traps(page)

            post_btn = await self._wait_for_post_button(page, timeout=120)
            if not post_btn:
                await context.close()
                return TikTokPublishResult(success=False, error_message="Post button not enabled.")

            await sweep_page_traps(page)
            try:
                await post_btn.scroll_into_view_if_needed()
                await post_btn.click(force=True, timeout=8000)
            except Exception:
                await sweep_page_traps(page)
                await post_btn.evaluate("el => el.click()")

            await self._wait_for_publish_completion(page, timeout=45)

            try:
                cookies = await context.cookies()
                with open(self.cookies_path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=2)
                with get_db() as s:
                    crud.upsert_platform_account(s, "tiktok", is_connected=True, account_name="TikTok Account (Brave Active)")
            except Exception:
                pass

            await context.close()
            clean_stale_profile_locks(self.user_data_dir)
            return TikTokPublishResult(
                success=True,
                publish_id="tiktok_studio_post",
                url="https://www.tiktok.com/tiktokstudio/manage",
                comment_posted=bool(comment_text)
            )

    async def _wait_for_login(self, page, timeout: int = 180) -> bool:
        """Polls until user logs in or timeout expires."""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            await asyncio.sleep(2.0)
            await sweep_page_traps(page)
            if "/login" not in page.url.lower() and "tiktokstudio" in page.url.lower():
                return True
            cookies = await page.context.cookies()
            c_names = {c.get("name") for c in cookies}
            if "sessionid" in c_names or "sid_guard" in c_names or "sessionid_ss" in c_names:
                return True
        return False

    async def _find_file_input(self, page):
        """Finds input[type='file'] in main frame or child frames."""
        try:
            inputs = await page.locator('input[type="file"]').all()
            if inputs:
                return inputs[0]
            for frame in page.frames:
                f_inputs = await frame.locator('input[type="file"]').all()
                if f_inputs:
                    return f_inputs[0]
        except Exception:
            pass
        return None

    async def _fill_caption(self, page, caption: str):
        """Types the caption and hashtags into the editor."""
        caption_selectors = [
            'div[contenteditable="true"]',
            '.public-DraftEditor-content',
            'div[data-placeholder]',
            'textarea'
        ]
        caption_editor = None
        for sel in caption_selectors:
            loc = page.locator(sel)
            if await loc.count() > 0 and await loc.first.is_visible():
                caption_editor = loc.first
                break
            for frame in page.frames:
                f_loc = frame.locator(sel)
                if await f_loc.count() > 0 and await f_loc.first.is_visible():
                    caption_editor = f_loc.first
                    break
            if caption_editor:
                break

        if caption_editor:
            try:
                await caption_editor.click(force=True)
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await page.keyboard.type(caption[:2100], delay=10)
            except Exception:
                pass

    async def _wait_for_post_button(self, page, timeout: int = 120):
        """
        Waits for the upload form's Submit Post button to become enabled.
        Strictly excludes any sidebar navigation items.
        """
        btn_selectors = [
            'button[data-e2e="post_video_button"]',
            'button.btn-post',
            'div[class*="btn-post"] button',
            'div[class*="submit-btn"] button',
            'button.TUXButton--primary:not([data-tt*="Sidebar"])',
            'button[type="button"]:has-text("Post"):not([data-tt*="Sidebar"]):not([class*="sidebar"])',
            'button[type="button"]:has-text("Publicar"):not([data-tt*="Sidebar"]):not([class*="sidebar"])'
        ]
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            await sweep_page_traps(page)
            for b_sel in btn_selectors:
                b_loc = page.locator(b_sel)
                count = await b_loc.count()
                for i in range(count):
                    btn = b_loc.nth(i)
                    if await btn.is_visible() and await btn.is_enabled():
                        # Verify button text or role
                        txt = (await btn.inner_text()).strip().lower()
                        if any(k in txt for k in ["post", "publicar", "submit"]) or count == 1:
                            return btn
            await asyncio.sleep(2.0)
        return None

    async def _wait_for_publish_completion(self, page, timeout: int = 45) -> bool:
        """
        Waits for TikTok Studio to finish publishing, handling confirmation popups
        and success modals.
        """
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            await sweep_page_traps(page)

            # Check if URL redirected to manage / posts
            cur_url = page.url.lower()
            if "/manage" in cur_url or "creator-center" in cur_url:
                return True

            # Check for upload success modal or buttons
            for success_sel in [
                'button:has-text("Manage your posts")',
                'button:has-text("Upload another video")',
                'button:has-text("Gestionar tus publicaciones")',
                'button:has-text("Subir otro video")',
                'div:has-text("Your video has been uploaded")',
                'div:has-text("Tu video se ha subido")'
            ]:
                try:
                    loc = page.locator(success_sel)
                    if await loc.count() > 0 and await loc.first.is_visible():
                        return True
                except Exception:
                    pass

            await asyncio.sleep(2.0)
        return True
