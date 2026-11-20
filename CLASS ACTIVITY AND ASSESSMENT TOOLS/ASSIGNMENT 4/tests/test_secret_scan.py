"""The secret-scan gate itself must be tested: a gate that never fires is not a gate."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import secret_scan  # noqa: E402

pytestmark = pytest.mark.unit


def test_U11_scanner_flags_hard_coded_secret():
    assert secret_scan.find('DB_PASSWORD = "hunter2hunter2"')
    assert secret_scan.find("api_key: 'abcdef123456'")


def test_U11b_scanner_accepts_environment_and_ci_secret_references():
    assert not secret_scan.find('SECRET_KEY = os.environ.get("SECRET_KEY")')
    assert not secret_scan.find("env: { POSTGRES_PASSWORD: ${{ secrets.TEST_DB_PASSWORD }} }")
