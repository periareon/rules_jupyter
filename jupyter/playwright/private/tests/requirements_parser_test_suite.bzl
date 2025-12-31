"""Unit tests for the requirements.txt parser"""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load("//jupyter/playwright/private:requirements_parser.bzl", "parse_playwright_version_from_requirements")

def _parse_simple_requirements_test_impl(ctx):
    env = unittest.begin(ctx)

    requirements_content = """\
pytest==7.4.0
playwright==1.57.0
requests==2.31.0
"""

    version = parse_playwright_version_from_requirements(requirements_content)

    asserts.equals(env, "1.57.0", version, "Should parse playwright version")

    return unittest.end(env)

parse_simple_requirements_test = unittest.make(_parse_simple_requirements_test_impl)

def _parse_requirements_with_comments_test_impl(ctx):
    env = unittest.begin(ctx)

    requirements_content = """\
# This is a comment
pytest==7.4.0
playwright==1.57.0  # Inline comment
requests==2.31.0
"""

    version = parse_playwright_version_from_requirements(requirements_content)

    asserts.equals(env, "1.57.0", version, "Should parse playwright version with inline comment")

    return unittest.end(env)

parse_requirements_with_comments_test = unittest.make(_parse_requirements_with_comments_test_impl)

def _parse_requirements_with_continuation_test_impl(ctx):
    env = unittest.begin(ctx)

    requirements_content = """\
pytest==7.4.0
playwright==1.57.0 \\
    --extra-index-url https://example.com
requests==2.31.0
"""

    version = parse_playwright_version_from_requirements(requirements_content)

    asserts.equals(env, "1.57.0", version, "Should parse playwright version with line continuation")

    return unittest.end(env)

parse_requirements_with_continuation_test = unittest.make(_parse_requirements_with_continuation_test_impl)

def _parse_requirements_no_playwright_test_impl(ctx):
    env = unittest.begin(ctx)

    requirements_content = """\
pytest==7.4.0
requests==2.31.0
"""

    version = parse_playwright_version_from_requirements(requirements_content)

    asserts.equals(env, None, version, "Should return None when playwright is not found")

    return unittest.end(env)

parse_requirements_no_playwright_test = unittest.make(_parse_requirements_no_playwright_test_impl)

def _parse_empty_requirements_test_impl(ctx):
    env = unittest.begin(ctx)

    requirements_content = ""

    version = parse_playwright_version_from_requirements(requirements_content)

    asserts.equals(env, None, version, "Should return None for empty file")

    return unittest.end(env)

parse_empty_requirements_test = unittest.make(_parse_empty_requirements_test_impl)

def _parse_requirements_multiple_playwright_test_impl(ctx):
    env = unittest.begin(ctx)

    requirements_content = """\
pytest==7.4.0
playwright==1.57.0
requests==2.31.0
playwright==1.58.0
"""

    version = parse_playwright_version_from_requirements(requirements_content)

    asserts.equals(env, "1.57.0", version, "Should return first playwright version found")

    return unittest.end(env)

parse_requirements_multiple_playwright_test = unittest.make(_parse_requirements_multiple_playwright_test_impl)

def _parse_requirements_with_whitespace_test_impl(ctx):
    env = unittest.begin(ctx)

    requirements_content = """\
pytest==7.4.0
  playwright==1.57.0  
requests==2.31.0
"""

    version = parse_playwright_version_from_requirements(requirements_content)

    asserts.equals(env, "1.57.0", version, "Should handle whitespace around playwright line")

    return unittest.end(env)

parse_requirements_with_whitespace_test = unittest.make(_parse_requirements_with_whitespace_test_impl)

def _parse_requirements_different_version_formats_test_impl(ctx):
    env = unittest.begin(ctx)

    requirements_content = """\
pytest==7.4.0
playwright==1.57.0
playwright-browser==1.57.0
"""

    version = parse_playwright_version_from_requirements(requirements_content)

    asserts.equals(env, "1.57.0", version, "Should only match playwright==, not playwright-browser==")

    return unittest.end(env)

parse_requirements_different_version_formats_test = unittest.make(_parse_requirements_different_version_formats_test_impl)

def _parse_requirements_complex_format_test_impl(ctx):
    env = unittest.begin(ctx)

    requirements_content = """\
# Python requirements

--extra-index-urls https://python.org

platformdirs==4.5.1 \\
    --hash=sha256:d03afa3963c806a9bed9d5125c8f4cb2fdaf74a55ab60e5d59b3fde758104d31
    # via
    #   black (>=2)
    #   jupyter_core (>=2.5)
    #   pylint (>=2.2)
    # https://files.pythonhosted.org/packages/cb/28/3bfe2fa5a7b9c46fe7e13c97bda14c895fb10fa2ebf1d0abb90e0cea7ee1/platformdirs-4.5.1-py3-none-any.whl#sha256=d03afa3963c806a9bed9d5125c8f4cb2fdaf74a55ab60e5d59b3fde758104d31
playwright==1.57.0 \\
    --hash=sha256:284ed5a706b7c389a06caa431b2f0ba9ac4130113c3a779767dda758c2497bb1
    # via nbconvert[webpdf]
    # https://files.pythonhosted.org/packages/56/61/3a803cb5ae0321715bfd5247ea871d25b32c8f372aeb70550a90c5f586df/playwright-1.57.0-py3-none-manylinux1_x86_64.whl#sha256=284ed5a706b7c389a06caa431b2f0ba9ac4130113c3a779767dda758c2497bb1
pluggy==1.6.0 \\
    --hash=sha256:e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746
    # via
    #   pytest (<2,>=1.5)
    #   pytest-cov (>=1.2)
    # https://files.pythonhosted.org/packages/54/20/4d324d65cc6d9205fabedc306948156824eb9f0ee1633355a8f7ec5c66bf/pluggy-1.6.0-py3-none-any.whl#sha256=e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746
"""

    version = parse_playwright_version_from_requirements(requirements_content)

    asserts.equals(env, "1.57.0", version, "Should parse playwright version from complex requirements format with hashes and multi-line entries")

    return unittest.end(env)

parse_requirements_complex_format_test = unittest.make(_parse_requirements_complex_format_test_impl)

def requirements_parser_test_suite(name):
    """Create the test suite for requirements parser tests.

    Args:
        name: The name of the test suite
    """
    parse_simple_requirements_test(
        name = "parse_simple_requirements_test",
    )
    parse_requirements_with_comments_test(
        name = "parse_requirements_with_comments_test",
    )
    parse_requirements_with_continuation_test(
        name = "parse_requirements_with_continuation_test",
    )
    parse_requirements_no_playwright_test(
        name = "parse_requirements_no_playwright_test",
    )
    parse_empty_requirements_test(
        name = "parse_empty_requirements_test",
    )
    parse_requirements_multiple_playwright_test(
        name = "parse_requirements_multiple_playwright_test",
    )
    parse_requirements_with_whitespace_test(
        name = "parse_requirements_with_whitespace_test",
    )
    parse_requirements_different_version_formats_test(
        name = "parse_requirements_different_version_formats_test",
    )
    parse_requirements_complex_format_test(
        name = "parse_requirements_complex_format_test",
    )

    native.test_suite(
        name = name,
        tests = [
            "parse_simple_requirements_test",
            "parse_requirements_with_comments_test",
            "parse_requirements_with_continuation_test",
            "parse_requirements_no_playwright_test",
            "parse_empty_requirements_test",
            "parse_requirements_multiple_playwright_test",
            "parse_requirements_with_whitespace_test",
            "parse_requirements_different_version_formats_test",
            "parse_requirements_complex_format_test",
        ],
    )
