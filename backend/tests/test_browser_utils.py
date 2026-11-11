import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from backend.publishing.browser_utils import (
    find_brave_executable,
    get_detected_browsers,
    get_primary_browser,
    clean_stale_profile_locks,
    get_browser_args,
    attach_dialog_handler,
    sweep_page_traps
)

def test_find_brave_executable():
    path = find_brave_executable()
    # If a browser is installed, it should return a valid path string
    if path:
        assert Path(path).is_file()

def test_get_detected_browsers():
    browsers = get_detected_browsers()
    assert isinstance(browsers, list)
    for b in browsers:
        assert "name" in b
        assert "path" in b
        assert Path(b["path"]).is_file()

def test_get_primary_browser():
    name, path = get_primary_browser()
    assert isinstance(name, str)
    if path:
        assert Path(path).is_file()
    else:
        assert name == "Playwright Browser Engine"

def test_custom_browser_override(tmp_path, monkeypatch):
    dummy_exe = tmp_path / "my_custom_browser.exe"
    dummy_exe.write_text("dummy binary")
    monkeypatch.setenv("BROWSER_PATH", str(dummy_exe))

    detected = get_detected_browsers()
    assert len(detected) >= 1
    assert detected[0]["name"] == "Custom Browser"
    assert detected[0]["path"] == str(dummy_exe.resolve())

    name, path = get_primary_browser()
    assert name == "Custom Browser"
    assert path == str(dummy_exe.resolve())

def test_browser_fallback_when_none_found(monkeypatch):
    monkeypatch.delenv("BROWSER_PATH", raising=False)
    monkeypatch.delenv("BRAVE_PATH", raising=False)
    
    with patch("pathlib.Path.is_file", return_value=False), \
         patch("shutil.which", return_value=None):
        detected = get_detected_browsers()
        assert detected == []
        name, path = get_primary_browser()
        assert name == "Playwright Browser Engine"
        assert path is None

def test_clean_stale_profile_locks(tmp_path):
    lock1 = tmp_path / "SingletonLock"
    lock1.write_text("test lock")
    lock2 = tmp_path / "subdir" / "LOCK"
    lock2.parent.mkdir(parents=True, exist_ok=True)
    lock2.write_text("db lock")
    
    assert lock1.exists()
    assert lock2.exists()
    
    clean_stale_profile_locks(tmp_path)
    
    assert not lock1.exists()
    assert not lock2.exists()

def test_get_browser_args():
    args = get_browser_args(headless=True)
    assert "--disable-blink-features=AutomationControlled" in args
    assert "--no-sandbox" in args

@pytest.mark.asyncio
async def test_attach_dialog_handler():
    mock_page = MagicMock()
    await attach_dialog_handler(mock_page)
    mock_page.on.assert_called_once()
    assert mock_page.on.call_args[0][0] == "dialog"

@pytest.mark.asyncio
async def test_sweep_page_traps():
    mock_page = MagicMock()
    mock_page.evaluate = AsyncMock()
    mock_locator = MagicMock()
    mock_locator.count = AsyncMock(return_value=1)
    mock_button = MagicMock()
    mock_button.inner_text = AsyncMock(return_value="Got it")
    mock_button.is_visible = AsyncMock(return_value=True)
    mock_button.click = AsyncMock()
    mock_locator.nth = MagicMock(return_value=mock_button)
    mock_locator.first = mock_button
    mock_page.locator = MagicMock(return_value=mock_locator)

    await sweep_page_traps(mock_page)

    mock_page.evaluate.assert_called_once()
