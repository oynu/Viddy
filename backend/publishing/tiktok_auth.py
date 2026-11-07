import os
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright
from backend.config import settings

TIKTOK_COOKIES_PATH = settings.base_dir / "data" / "tiktok_cookies.json"

async def launch_interactive_tiktok_login(headless: bool = False, timeout_seconds: int = 300) -> Dict[str, Any]:
    """
    Opens a Chromium browser window for the user to log in to TikTok once.
    Automatically captures and saves the session cookies to data/tiktok_cookies.json.
    Once saved, all subsequent uploads run headlessly and automatically in the background.
    """
    print("Launching TikTok Login Window...")
    TIKTOK_COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        # Load existing cookies if present
        if TIKTOK_COOKIES_PATH.exists():
            try:
                with open(TIKTOK_COOKIES_PATH, "r", encoding="utf-8") as f:
                    old_cookies = json.load(f)
                    if isinstance(old_cookies, list):
                        await context.add_cookies(old_cookies)
            except Exception:
                pass
                
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded")
        
        start_time = asyncio.get_event_loop().time()
        logged_in = False
        cookies = []
        account_name = None
        
        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            await asyncio.sleep(2.0)
            cookies = await context.cookies()
            cookie_names = {c.get("name") for c in cookies}
            
            # Key TikTok session indicators
            if "sessionid" in cookie_names or "sid_guard" in cookie_names or "sessionid_ss" in cookie_names:
                logged_in = True
                # Try getting account username from current page or cookies
                for c in cookies:
                    if c.get("name") == "passport_auth_status":
                        pass
                break
                
            # Check URL redirection away from login
            cur_url = page.url
            if "tiktok.com" in cur_url and "/login" not in cur_url and len(cookie_names) > 5:
                logged_in = True
                break
                
        if logged_in:
            with open(TIKTOK_COOKIES_PATH, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
                
            await browser.close()
            return {
                "success": True,
                "cookies_count": len(cookies),
                "path": str(TIKTOK_COOKIES_PATH),
                "message": "TikTok session saved successfully! Background autonomous publishing is now active."
            }
        else:
            await browser.close()
            return {
                "success": False,
                "error": "Login timed out before session cookies were detected."
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
    """Checks if valid TikTok cookies file exists and is not empty."""
    if not TIKTOK_COOKIES_PATH.exists():
        return False
    try:
        with open(TIKTOK_COOKIES_PATH, "r", encoding="utf-8") as f:
            cookies = json.load(f)
            return isinstance(cookies, list) and len(cookies) > 0
    except Exception:
        return False

if __name__ == "__main__":
    print("Starting interactive TikTok login helper...")
    res = asyncio.run(launch_interactive_tiktok_login(headless=False))
    print(res)
