"""
cc_plugin_og/tests/test_basicchecks.py
"""

import pytest
from compliance_checker.base import Result
from compliance_checker.suite import CheckSuite
from netCDF4 import Dataset

from cc_plugin_og.checker import OGChecker
from cc_plugin_og.tests.resources import STATIC_FILES


@pytest.fixture
def check():
    return OGChecker()


@pytest.fixture
def dataset():
    """
    Return a pairwise object for the dataset
    """
    fname = STATIC_FILES["good_dataset"]
    dataset = Dataset(
        fname,
        mode="r",
        diskless=True,
        persist=False,
    )
    yield dataset
    dataset.close()


def test_og_is_loaded():
    cs = CheckSuite()
    cs.load_all_available_checkers()
    assert "og" in cs.checkers


def test_good_dataset(check, dataset):
    """
    Checks that a file with the proper lat and lon do work
    """
    result = check.check_mandatory_variables(dataset)
    assert isinstance(result, Result)
    assert result.value == (3, 14)
