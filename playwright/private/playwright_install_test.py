"""Tests for the playwright_install module."""

# pylint: disable=redefined-outer-name

from pathlib import Path

import pytest

from playwright.private.playwright_install import (
    CFT_DIRECTORY_NORMALIZATIONS,
    copy_browser,
)


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Temporary output directory for browser installs."""
    return tmp_path / "output"


@pytest.fixture
def tmp_browser(tmp_path: Path) -> Path:
    """Temporary directory simulating an extracted browser archive."""
    return tmp_path / "browser"


class TestCftDirectoryNormalizations:
    """Verify that CfT directory names normalize to Playwright-expected names."""

    def test_chromium_linux(self) -> None:
        """chrome-linux64 normalizes to chrome-linux."""
        assert CFT_DIRECTORY_NORMALIZATIONS["chrome-linux64"] == "chrome-linux"

    def test_chromium_mac_arm64(self) -> None:
        """chrome-mac-arm64 normalizes to chrome-mac."""
        assert CFT_DIRECTORY_NORMALIZATIONS["chrome-mac-arm64"] == "chrome-mac"

    def test_chromium_mac_x64(self) -> None:
        """chrome-mac-x64 normalizes to chrome-mac."""
        assert CFT_DIRECTORY_NORMALIZATIONS["chrome-mac-x64"] == "chrome-mac"

    def test_chromium_win64(self) -> None:
        """chrome-win64 normalizes to chrome-win."""
        assert CFT_DIRECTORY_NORMALIZATIONS["chrome-win64"] == "chrome-win"

    def test_headless_shell_linux(self) -> None:
        """chrome-headless-shell-linux64 normalizes to chrome-linux."""
        assert (
            CFT_DIRECTORY_NORMALIZATIONS["chrome-headless-shell-linux64"]
            == "chrome-linux"
        )

    def test_headless_shell_mac_arm64(self) -> None:
        """chrome-headless-shell-mac-arm64 normalizes to chrome-headless-shell-mac."""
        assert (
            CFT_DIRECTORY_NORMALIZATIONS["chrome-headless-shell-mac-arm64"]
            == "chrome-headless-shell-mac"
        )

    def test_headless_shell_mac_x64(self) -> None:
        """chrome-headless-shell-mac-x64 normalizes to chrome-headless-shell-mac."""
        assert (
            CFT_DIRECTORY_NORMALIZATIONS["chrome-headless-shell-mac-x64"]
            == "chrome-headless-shell-mac"
        )

    def test_headless_shell_win64(self) -> None:
        """chrome-headless-shell-win64 normalizes to chrome-headless-shell-win."""
        assert (
            CFT_DIRECTORY_NORMALIZATIONS["chrome-headless-shell-win64"]
            == "chrome-headless-shell-win"
        )

    def test_legacy_names_pass_through(self) -> None:
        """Legacy Playwright CDN directory names are not remapped."""
        for name in [
            "chrome-linux",
            "chrome-mac",
            "chrome-win",
            "firefox",
            "pw_run.sh",
        ]:
            assert CFT_DIRECTORY_NORMALIZATIONS.get(name, name) == name


class TestCopyBrowserCftNormalization:
    """Verify copy_browser normalizes CfT directory names correctly."""

    def test_cft_linux_chromium(self, tmp_browser: Path, tmp_output: Path) -> None:
        """CfT archive with chrome-linux64 should produce chrome-linux."""
        browser_dir = tmp_browser / "chrome-linux64"
        browser_dir.mkdir(parents=True)
        (browser_dir / "chrome").write_text("fake")
        (browser_dir / "libEGL.so").write_text("fake")

        copy_browser(
            browser_type="chromium",
            revision="1134",
            file_paths=[
                str(browser_dir / "chrome"),
                str(browser_dir / "libEGL.so"),
            ],
            output_dir=tmp_output,
        )

        dest = tmp_output / "chromium-1134" / "chrome-linux"
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
        """CfT headless-shell linux64 normalizes to chrome-linux."""
        browser_dir = tmp_browser / "chrome-headless-shell-linux64"
        browser_dir.mkdir(parents=True)
        (browser_dir / "chrome-headless-shell").write_text("fake")
        (browser_dir / "libEGL.so").write_text("fake")

        copy_browser(
            browser_type="chromium-headless-shell",
            revision="1134",
            file_paths=[
                str(browser_dir / "chrome-headless-shell"),
                str(browser_dir / "libEGL.so"),
            ],
            output_dir=tmp_output,
        )

        dest = tmp_output / "chromium_headless_shell-1134" / "chrome-linux"
        assert dest.exists(), f"Expected {dest} to exist"
        assert (dest / "chrome-headless-shell").exists()
