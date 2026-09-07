""" Tests for the package version attribute
"""

import re
from importlib.metadata import PackageNotFoundError, version

import pytest

import coreforge


def test_version_attribute_exists():
    """ CoreForge exposes __version__ so a consumer can record which build produced a model
    """
    assert hasattr(coreforge, "__version__")
    assert isinstance(coreforge.__version__, str)
    assert coreforge.__version__


def test_version_is_pep440_shaped():
    """ The value is a version, not a placeholder string
    """
    assert re.match(r"^\d+\.\d+", coreforge.__version__), coreforge.__version__


def test_version_matches_installed_distribution():
    """ __version__ tracks packaging metadata rather than a hand-maintained copy
    """
    try:
        expected = version("coreforge")
    except PackageNotFoundError:
        pytest.skip("coreforge is not installed in this environment")

    assert coreforge.__version__ == expected
