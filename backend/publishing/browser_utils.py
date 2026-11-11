import os
import shutil
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

def get_detected_browsers() -> List[Dict[str, str]]:
    """
    Discovers installed modern Chromium-based browsers across Windows, macOS, and Linux.
    Returns list of detected browsers sorted by preference:
    1. Brave Browser (recommended for ad/tracker shield & anti-detection)
    2. Google Chrome
    3. Microsoft Edge
    4. Chromium
    """
    browsers: List[Dict[str, str]] = []

    # 1. Custom Override
    custom_path = os.environ.get("BROWSER_PATH") or os.environ.get("BRAVE_PATH")
    if custom_path and Path(custom_path).is_file():
        browsers.append({
            "name": "Custom Browser",
            "path": str(Path(custom_path).resolve())
        })

    # 2. Brave Browser
    brave_candidates = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/usr/bin/brave-browser",
        "/usr/bin/brave",
        shutil.which("brave"),
        shutil.which("brave.exe"),
        shutil.which("brave-browser")
    ]
    for c in brave_candidates:
        if c and Path(c).is_file():
            browsers.append({
                "name": "Brave",
                "path": str(Path(c).resolve())
            })
            break

    # 3. Google Chrome
    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chrome",
        shutil.which("google-chrome"),
        shutil.which("chrome"),
        shutil.which("chrome.exe")
    ]
    for c in chrome_candidates:
        if c and Path(c).is_file():
            browsers.append({
                "name": "Google Chrome",
                "path": str(Path(c).resolve())
            })
            break

    # 4. Microsoft Edge
    edge_candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/usr/bin/microsoft-edge",
        "/usr/bin/microsoft-edge-stable",
        shutil.which("msedge"),
        shutil.which("msedge.exe"),
        shutil.which("microsoft-edge")
    ]
    for c in edge_candidates:
        if c and Path(c).is_file():
            browsers.append({
                "name": "Microsoft Edge",
                "path": str(Path(c).resolve())
            })
            break

    # 5. Generic Chromium
    chromium_candidates = [
        r"C:\Program Files\Chromium\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Chromium\Application\chrome.exe"),
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        shutil.which("chromium"),
        shutil.which("chromium-browser")
    ]
    for c in chromium_candidates:
        if c and Path(c).is_file():
            browsers.append({
                "name": "Chromium",
                "path": str(Path(c).resolve())
            })
            break

    return browsers

def get_primary_browser() -> Tuple[str, Optional[str]]:
    """
    Returns the best available browser as (name, executable_path).
    Falls back to ('Playwright Browser Engine', None) if no local browser is installed.
    """
    detected = get_detected_browsers()
    if detected:
        return detected[0]["name"], detected[0]["path"]
    return "Playwright Browser Engine", None

def find_brave_executable() -> Optional[str]:
    """Backward compatibility alias: returns executable path of the best detected browser."""
    _, path = get_primary_browser()
    return path

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
