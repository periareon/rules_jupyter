"""Parser for extracting Playwright version from requirements.txt files."""

def parse_playwright_version_from_requirements(content):
    """Parse playwright version from a requirements.txt file content.

    Args:
        content: String content of the requirements.txt file

    Returns:
        Version string (e.g., "1.57.0") or None if not found
    """
    for line in content.split("\n"):
        line = line.strip()

        # Look for lines like: playwright==1.57.0 \
        # or: playwright==1.57.0
        # Handle continuation lines (lines ending with \)
        if line.startswith("playwright=="):
            # Extract version after ==, handle backslash continuation
            version_part = line.split("==")[1]

            # Remove backslash and any trailing whitespace
            # Split on space to get the first token (the version)
            parts = version_part.split(" ")
            if len(parts) > 0:
                version = parts[0].rstrip("\\").strip()
                if version:
                    return version
    return None
