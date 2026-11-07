import os
import shutil
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

def find_brave_executable() -> Optional[str]:
    """
    Locates the Brave Browser executable on Windows or other OS.
    Checks environment overrides, standard install paths, and PATH.
    """
    candidates = [
        os.environ.get("BRAVE_PATH"),
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        shutil.which("brave"),
        shutil.which("brave.exe")
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return str(Path(c).resolve())
    return None

def clean_stale_profile_locks(profile_dir: Path):
    """
    Removes lingering lock files (SingletonLock, SingletonCookie, SingletonSocket)
    left behind after unexpected browser crashes.
    """
    if not profile_dir.exists():
        return
    lock_names = ["SingletonLock", "SingletonCookie", "SingletonSocket", "LOCK"]
    for lock_name in lock_names:
        for p in profile_dir.glob(f"**/{lock_name}"):
            try:
                if p.is_file():
                    p.unlink(missing_ok=True)
            except Exception:
                pass

def get_browser_args(headless: bool = True) -> List[str]:
    """Standard hardened anti-detection arguments for Playwright browser launch."""
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        "--no-default-browser-check",
        "--no-first-run",
        "--password-store=basic",
        "--use-mock-keychain"
    ]

async def attach_dialog_handler(page):
    """Auto-accepts browser alerts, confirms, prompts, and beforeunload dialogs."""
    try:
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
    except Exception:
        pass

async def sweep_page_traps(page):
    """
    Comprehensive sweeper that neutralizes TikTok Studio walkthrough traps,
    react-joyride overlays, cookie banners, copyright check prompts, and tooltips.
    """
    # 1. Purge DOM overlays and react-joyride tour portals via JavaScript
    js_purge = """
    () => {
        // Remove joyride walkthrough portals and overlays
        const joyridePortal = document.getElementById('react-joyride-portal');
        if (joyridePortal) joyridePortal.remove();

        const joyrideOverlays = document.querySelectorAll('.react-joyride__overlay, .react-joyride__tooltip, [class*="joyride"]');
        joyrideOverlays.forEach(el => el.remove());

        const testOverlays = document.querySelectorAll('div[data-test-id="overlay"]');
        testOverlays.forEach(el => el.remove());

        // Remove modal backdrops that intercept pointer events
        const backdrops = document.querySelectorAll('.modal-mask, .backdrop, [class*="mask-"]');
        backdrops.forEach(el => {
            if (!el.innerText || el.innerText.trim() === '') {
                el.remove();
            }
        });
    }
    """
    try:
        await page.evaluate(js_purge)
    except Exception:
        pass

    # 2. Dismiss cookie consent banners
    cookie_labels = [
        "Decline optional cookies",
        "Allow all",
        "Accept all",
        "Rechazar opcionales",
        "Aceptar todas",
        "Aceptar todo",
        "Rechazar todo"
    ]
    for label in cookie_labels:
        try:
            btn = page.locator(f"button:has-text('{label}')")
            if await btn.count() > 0 and await btn.first.is_visible():
                await btn.first.click(force=True)
                await asyncio.sleep(0.5)
                break
        except Exception:
            pass

    # 3. Dismiss Walkthrough / Tour / Update Popups ("Got it", "Dismiss", "Skip", etc.)
    tour_labels = [
        "Got it",
        "Entendido",
        "Dismiss",
        "Skip",
        "Next",
        "Close",
        "Aceptar",
        "Omitir"
    ]
    for label in tour_labels:
        try:
            loc = page.locator(f"button:has-text('{label}')")
            count = await loc.count()
            for i in range(count):
                btn = loc.nth(i)
                # Don't click the primary Post button if label matches
                txt = (await btn.inner_text()).strip().lower()
                if txt in ["post", "publicar"]:
                    continue
                if await btn.is_visible():
                    await btn.click(force=True)
                    await asyncio.sleep(0.3)
                    break
        except Exception:
            pass

    # 4. Handle Sound / Copyright warning confirmations ("Post anyway", "Confirm", "Continue")
    confirm_labels = [
        "Post anyway",
        "Publicar de todos modos",
        "Confirm",
        "Confirmar",
        "Continue",
        "Continuar"
    ]
    for label in confirm_labels:
        try:
            btn = page.locator(f"button:has-text('{label}')")
            if await btn.count() > 0 and await btn.first.is_visible():
                await btn.first.click(force=True)
                await asyncio.sleep(0.5)
        except Exception:
            pass
