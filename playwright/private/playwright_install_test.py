"""Tests for the playwright_install module."""

# pylint: disable=redefined-outer-name

from pathlib import Path

import pytest

from playwright.private.playwright_install import copy_browser


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Temporary output directory for browser installs."""
    return tmp_path / "output"


@pytest.fixture
def tmp_browser(tmp_path: Path) -> Path:
    """Temporary directory simulating an extracted browser archive."""
    return tmp_path / "browser"


class TestCopyBrowserCftPreserved:
    """Verify copy_browser preserves CfT directory names as-is.

    Playwright >= 1.57.0 expects CfT naming conventions (chrome-linux64,
    chrome-mac-arm64, Google Chrome for Testing.app, etc.) natively.
    Older versions use Playwright CDN archives with legacy names.
    """

    def test_cft_linux_chromium(self, tmp_browser: Path, tmp_output: Path) -> None:
        """CfT archive with chrome-linux64 should preserve the directory name."""
        browser_dir = tmp_browser / "chrome-linux64"
        browser_dir.mkdir(parents=True)
        (browser_dir / "chrome").write_text("fake")
        (browser_dir / "libEGL.so").write_text("fake")

        copy_browser(
            browser_type="chromium",
            revision="1200",
            file_paths=[
                str(browser_dir / "chrome"),
                str(browser_dir / "libEGL.so"),
            ],
            output_dir=tmp_output,
        )

        dest = tmp_output / "chromium-1200" / "chrome-linux64"
        assert dest.exists(), f"Expected {dest} to exist"
        assert (dest / "chrome").exists()
        assert (dest / "libEGL.so").exists()

    def test_legacy_linux_chromium(self, tmp_browser: Path, tmp_output: Path) -> None:
        """Legacy Playwright CDN archive with chrome-linux stays chrome-linux."""
        browser_dir = tmp_browser / "chrome-linux"
        browser_dir.mkdir(parents=True)
        (browser_dir / "chrome").write_text("fake")
        (browser_dir / "libEGL.so").write_text("fake")

        copy_browser(
            browser_type="chromium",
            revision="1000",
            file_paths=[
                str(browser_dir / "chrome"),
                str(browser_dir / "libEGL.so"),
            ],
            output_dir=tmp_output,
        )

        dest = tmp_output / "chromium-1000" / "chrome-linux"
        assert dest.exists(), f"Expected {dest} to exist"
        assert (dest / "chrome").exists()

    def test_cft_headless_shell_linux(
        self, tmp_browser: Path, tmp_output: Path
    ) -> None:
        """CfT headless-shell linux64 should preserve the directory name."""
        browser_dir = tmp_browser / "chrome-headless-shell-linux64"
        browser_dir.mkdir(parents=True)
        (browser_dir / "chrome-headless-shell").write_text("fake")
        (browser_dir / "libEGL.so").write_text("fake")

        copy_browser(
            browser_type="chromium-headless-shell",
            revision="1200",
            file_paths=[
                str(browser_dir / "chrome-headless-shell"),
                str(browser_dir / "libEGL.so"),
            ],
            output_dir=tmp_output,
        )

        dest = (
            tmp_output
            / "chromium_headless_shell-1200"
            / "chrome-headless-shell-linux64"
        )
        assert dest.exists(), f"Expected {dest} to exist"
        assert (dest / "chrome-headless-shell").exists()

    def test_cft_mac_arm64_chromium(self, tmp_browser: Path, tmp_output: Path) -> None:
        """CfT archive with chrome-mac-arm64 should preserve the directory name."""
        browser_dir = tmp_browser / "chrome-mac-arm64"
        browser_dir.mkdir(parents=True)
        app_dir = browser_dir / "Google Chrome for Testing.app" / "Contents" / "MacOS"
        app_dir.mkdir(parents=True)
        (app_dir / "Google Chrome for Testing").write_text("fake")

        copy_browser(
            browser_type="chromium",
            revision="1200",
            file_paths=[
                str(app_dir / "Google Chrome for Testing"),
            ],
            output_dir=tmp_output,
        )

        dest = tmp_output / "chromium-1200" / "chrome-mac-arm64"
        assert dest.exists(), f"Expected {dest} to exist"
