import os
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright

from backend.config import settings
from backend.publishing.browser_utils import (
    get_primary_browser,
    find_brave_executable,
    clean_stale_profile_locks,
    get_browser_args,
    attach_dialog_handler,
    sweep_page_traps
)
from backend.database.session import get_db
from backend.database import crud

TIKTOK_COOKIES_PATH = settings.base_dir / "data" / "tiktok_cookies.json"
USER_DATA_DIR = settings.base_dir / "data" / "tiktok_user_data"

async def launch_interactive_tiktok_login(headless: bool = False, timeout_seconds: int = 300) -> Dict[str, Any]:
    """
    Opens a Brave browser window for the user to log in to TikTok.
    Automatically captures and saves the persistent session and cookies.json.
    Once saved, all subsequent uploads run autonomously in the background.
    """
    browser_name, browser_path = get_primary_browser()
    if browser_path:
        print(f"[*] [TIKTOK AUTH] Using {browser_name}: {browser_path}")
    else:
        print("[*] [TIKTOK AUTH] Local browser not detected, falling back to Playwright engine.")

    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TIKTOK_COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_stale_profile_locks(USER_DATA_DIR)

    async with async_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(USER_DATA_DIR),
            "headless": headless,
            "viewport": {"width": 1280, "height": 850},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "args": get_browser_args(headless=headless)
        }
        if browser_path:
            launch_kwargs["executable_path"] = browser_path

        try:
            context = await p.chromium.launch_persistent_context(**launch_kwargs)
        except Exception as e:
            print(f"[!] Persistent launch issue ({e}). Cleaning stale locks and retrying...")
            clean_stale_profile_locks(USER_DATA_DIR)
            context = await p.chromium.launch_persistent_context(**launch_kwargs)

        # Pre-load existing cookies if available
        if TIKTOK_COOKIES_PATH.exists():
            try:
                with open(TIKTOK_COOKIES_PATH, "r", encoding="utf-8") as f:
                    old_cookies = json.load(f)
                    if isinstance(old_cookies, list):
                        formatted = []
                        for c in old_cookies:
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
        target_url = "https://www.tiktok.com/tiktokstudio/upload"
        print(f"[*] [TIKTOK AUTH] Navigating to {target_url}...")
        await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(2.0)
        await sweep_page_traps(page)

        # Check if already authenticated
        cookies = await context.cookies()
        c_names = {c.get("name") for c in cookies}
        has_session = ("sessionid" in c_names or "sessionid_ss" in c_names or "sid_guard" in c_names)
        
        if "tiktokstudio" in page.url.lower() and "/login" not in page.url.lower() and has_session:
            print("[OK] [TIKTOK AUTH] Active TikTok Studio session already authenticated!")
            # Export and persist cookies
            with open(TIKTOK_COOKIES_PATH, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            try:
                with get_db() as s:
                    crud.upsert_platform_account(s, "tiktok", is_connected=True, account_name=f"TikTok ({browser_name} Session Active)")
            except Exception:
                pass
            await context.close()
            return {
                "success": True,
                "message": "TikTok session active and verified in Brave!",
                "cookies_count": len(cookies)
            }

        # Otherwise guide user to login
        if "/login" in page.url.lower() or not has_session:
            print("[*] [TIKTOK AUTH] Please log into your TikTok account in the Brave window...")
            await sweep_page_traps(page)

        start_time = asyncio.get_event_loop().time()
        logged_in = False

        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            await asyncio.sleep(2.0)
            await sweep_page_traps(page)

            cookies = await context.cookies()
            cookie_names = {c.get("name") for c in cookies}
            has_valid_session = bool("sessionid" in cookie_names or "sessionid_ss" in cookie_names or "sid_guard" in cookie_names)

            cur_url = page.url.lower()
            if has_valid_session and ("/login" not in cur_url or "tiktokstudio" in cur_url):
                print("[*] [TIKTOK AUTH] Session detected. Verifying TikTok Studio access...")
                if "tiktokstudio" not in cur_url:
                    try:
                        await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=30000)
                        await asyncio.sleep(3.0)
                        await sweep_page_traps(page)
                    except Exception:
                        pass
                logged_in = True
                break

        if logged_in:
            print("[OK] [TIKTOK AUTH] TikTok login confirmed! Saving session...")
            cookies = await context.cookies()
            with open(TIKTOK_COOKIES_PATH, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            try:
                with get_db() as s:
                    crud.upsert_platform_account(s, "tiktok", is_connected=True, account_name=f"TikTok ({browser_name} Session Active)")
            except Exception:
                pass

            await asyncio.sleep(1.0)
            await context.close()
            return {
                "success": True,
                "cookies_count": len(cookies),
                "path": str(TIKTOK_COOKIES_PATH),
                "message": "TikTok session saved in Brave! Autonomous publishing is active."
            }
        else:
            await context.close()
            return {
                "success": False,
                "error": "Login timed out before session credentials were confirmed."
            }

def save_pasted_cookies(cookies_json_text: str) -> Dict[str, Any]:
    """
    Saves manually exported/pasted cookies JSON (from EditThisCookie or Cookie-Editor).
    """
    try:
        data = json.loads(cookies_json_text.strip())
        if not isinstance(data, list):
            return {"success": False, "error": "Cookies must be a JSON array of cookie objects."}
            
        TIKTOK_COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TIKTOK_COOKIES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        return {
            "success": True,
            "cookies_count": len(data),
            "path": str(TIKTOK_COOKIES_PATH),
            "message": "TikTok cookies.json saved successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Invalid JSON format: {str(e)}"}

def has_saved_tiktok_cookies() -> bool:
    """Checks if valid TikTok cookies file exists and has authentication cookies."""
    if not TIKTOK_COOKIES_PATH.exists():
        return False
    try:
        with open(TIKTOK_COOKIES_PATH, "r", encoding="utf-8") as f:
            cookies = json.load(f)
            if not isinstance(cookies, list) or len(cookies) == 0:
                return False
            names = {c.get("name") for c in cookies if isinstance(c, dict)}
            return bool("sessionid" in names or "sessionid_ss" in names or "sid_guard" in names or len(cookies) > 5)
    except Exception:
        return False

if __name__ == "__main__":
    print("Starting interactive TikTok login helper with Brave...")
    res = asyncio.run(launch_interactive_tiktok_login(headless=False))
    print(res)
