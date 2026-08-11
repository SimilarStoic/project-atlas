"""Foundation-level package checks."""

import project_atlas


def test_package_is_importable() -> None:
    """Verify the installed src-layout package can be imported."""
    assert project_atlas.__doc__
