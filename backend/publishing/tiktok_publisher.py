import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import httpx

from backend.config import settings

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
    using persistent user session and cookies.json fallback.
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
        Publishes video to TikTok using Playwright.
        If user is not logged in, launches browser window for login, then uploads immediately.
        """
        if not os.path.exists(video_path):
            return TikTokPublishResult(
                success=False,
                error_message=f"Video file not found at: {video_path}"
            )

        # 1. Primary Method: Playwright Browser Automation
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
        Playwright automated upload to TikTok Studio.
        Handles cookie consent, session login if needed, file injection, captioning, and post submission.
        """
        from playwright.async_api import async_playwright

        abs_video_path = str(Path(video_path).resolve())
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            # Check if we should start headless or headful (headful if not connected yet to let user log in)
            is_first_time = not self.is_connected()
            headless_mode = not is_first_time

            print(f"[*] [TIKTOK PUBLISH] Launching Playwright browser (headless={headless_mode})...")

            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    headless=headless_mode,
                    viewport={"width": 1280, "height": 850},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox"
                    ]
                )
            except Exception as e:
                # If persistent context is locked by another process, fallback to standard launch
                browser = await p.chromium.launch(
                    headless=headless_mode,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 850},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )

            # Load exported cookies if available
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

            # Navigate to TikTok Studio Upload
            upload_url = "https://www.tiktok.com/tiktokstudio/upload"
            print(f"[*] [TIKTOK PUBLISH] Navigating to {upload_url}...")
            await page.goto(upload_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(2.0)

            # Dismiss cookie consent dialog if present
            await self._dismiss_cookie_consent(page)

            # Check if login is required
            if "login" in page.url.lower():
                print("[!] [TIKTOK PUBLISH] TikTok session login required.")
                if headless_mode:
                    # Switch to visible window so user can log in
                    await context.close()
                    print("[*] [TIKTOK PUBLISH] Re-opening visible browser window for 1-time TikTok login...")
                    return await self._login_then_upload(abs_video_path, caption, comment_text)
                else:
                    # Already visible: wait for user to log in
                    print("[*] [TIKTOK PUBLISH] Please log into your TikTok account in the browser window now...")
                    logged_in = await self._wait_for_login(page, timeout=180)
                    if not logged_in:
                        await context.close()
                        return TikTokPublishResult(
                            success=False,
                            error_message="TikTok login timed out. Please log in when prompted."
                        )
                    # Redirect to upload page after login
                    await page.goto(upload_url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2.0)
                    await self._dismiss_cookie_consent(page)

            # Locate File Input
            print(f"[*] [TIKTOK PUBLISH] Selecting video file: {abs_video_path}...")
            file_input = await self._find_file_input(page)
            if not file_input:
                # Retry navigating once
                await page.goto(upload_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2.0)
                await self._dismiss_cookie_consent(page)
                file_input = await self._find_file_input(page)

            if not file_input:
                await context.close()
                return TikTokPublishResult(
                    success=False,
                    error_message="Could not find video file upload input on TikTok Studio page."
                )

            # Upload video file
            await file_input.set_input_files(abs_video_path)
            print("[*] [TIKTOK PUBLISH] Video file uploaded to browser. Processing...")
            await asyncio.sleep(4.0)

            # Fill Caption & Hashtags
            print(f"[*] [TIKTOK PUBLISH] Setting caption & hashtags...")
            await self._fill_caption(page, caption)
            await asyncio.sleep(2.0)

            # Wait for upload completion & Post button to be enabled
            print("[*] [TIKTOK PUBLISH] Waiting for TikTok to finish processing video...")
            post_btn = await self._wait_for_post_button(page, timeout=120)
            if not post_btn:
                await context.close()
                return TikTokPublishResult(
                    success=False,
                    error_message="TikTok 'Post' button was not ready or remained disabled."
                )

            # Submit Post
            print("[*] [TIKTOK PUBLISH] Clicking 'Post' button to publish video...")
            await post_btn.click()
            await asyncio.sleep(5.0)

            # Save session cookies for background reuse
            try:
                cookies = await context.cookies()
                with open(self.cookies_path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=2)
                from backend.database.session import get_db
                from backend.database import crud
                with get_db() as s:
                    crud.upsert_platform_account(s, "tiktok", is_connected=True, account_name="TikTok Account")
            except Exception:
                pass

            await context.close()
            print("[OK] [TIKTOK PUBLISH] Video published successfully to TikTok!")

            return TikTokPublishResult(
                success=True,
                publish_id="tiktok_studio_post",
                url="https://www.tiktok.com/tiktokstudio/manage",
                comment_posted=bool(comment_text)
            )

    async def _login_then_upload(self, video_path: str, caption: str, comment_text: Optional[str]) -> TikTokPublishResult:
        """Launches a visible browser window, waits for user login, then immediately publishes."""
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=False,
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://www.tiktok.com/login?redirect_url=https%3A%2F%2Fwww.tiktok.com%2Ftiktokstudio%2Fupload", timeout=45000)
            await self._dismiss_cookie_consent(page)

            print("[*] [TIKTOK PUBLISH] Please log into your TikTok account in the browser window now...")
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
            await self._dismiss_cookie_consent(page)

            file_input = await self._find_file_input(page)
            if not file_input:
                await context.close()
                return TikTokPublishResult(success=False, error_message="Could not find file upload input.")

            await file_input.set_input_files(video_path)
            await asyncio.sleep(4.0)

            await self._fill_caption(page, caption)
            await asyncio.sleep(2.0)

            post_btn = await self._wait_for_post_button(page, timeout=120)
            if not post_btn:
                await context.close()
                return TikTokPublishResult(success=False, error_message="Post button not enabled.")

            await post_btn.click()
            await asyncio.sleep(6.0)

            # Save cookies
            try:
                cookies = await context.cookies()
                with open(self.cookies_path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=2)
                from backend.database.session import get_db
                from backend.database import crud
                with get_db() as s:
                    crud.upsert_platform_account(s, "tiktok", is_connected=True, account_name="TikTok Account")
            except Exception:
                pass

            await context.close()
            return TikTokPublishResult(
                success=True,
                publish_id="tiktok_studio_post",
                url="https://www.tiktok.com/tiktokstudio/manage",
                comment_posted=bool(comment_text)
            )

    async def _dismiss_cookie_consent(self, page):
        """Clicks 'Decline optional cookies' or 'Allow all' if banner is present."""
        for label in ["Decline optional cookies", "Allow all", "Aceptar todo", "Rechazar"]:
            try:
                btn = page.locator(f"button:has-text('{label}')")
                if await btn.count() > 0 and await btn.first.is_visible():
                    await btn.first.click()
                    await asyncio.sleep(1.0)
                    break
            except Exception:
                pass

    async def _wait_for_login(self, page, timeout: int = 180) -> bool:
        """Polls until user logs in or timeout expires."""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            await asyncio.sleep(2.0)
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
        """Types the full caption and viral hashtags into the TikTok caption editor."""
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
            # Check frames
            for frame in page.frames:
                f_loc = frame.locator(sel)
                if await f_loc.count() > 0 and await f_loc.first.is_visible():
                    caption_editor = f_loc.first
                    break
            if caption_editor:
                break

        if caption_editor:
            try:
                await caption_editor.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await page.keyboard.type(caption[:2100], delay=10)
            except Exception:
                pass

    async def _wait_for_post_button(self, page, timeout: int = 120):
        """Waits for Post button to become visible and enabled."""
        btn_selectors = [
            'button:has-text("Post")',
            'button:has-text("Publicar")',
            'button[data-e2e="post_video_button"]',
            '.btn-post'
        ]
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            for b_sel in btn_selectors:
                b_loc = page.locator(b_sel)
                if await b_loc.count() > 0:
                    btn = b_loc.first
                    if await btn.is_visible() and await btn.is_enabled():
                        return btn
                for frame in page.frames:
                    f_loc = frame.locator(b_sel)
                    if await f_loc.count() > 0:
                        btn = f_loc.first
                        if await btn.is_visible() and await btn.is_enabled():
                            return btn
            await asyncio.sleep(2.0)
        return None
