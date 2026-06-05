import os
import tempfile
from pathlib import Path

from app.database import configure_database


_TEST_DATABASE_DIR = Path(tempfile.mkdtemp(prefix="insurance-recommendation-tests-"))
_TEST_DATABASE_URL = f"sqlite:///{(_TEST_DATABASE_DIR / 'pytest.db').as_posix()}"


def pytest_configure(config):
    os.environ["INSURANCE_RECOMMENDATION_DATABASE_URL"] = _TEST_DATABASE_URL
    configure_database(_TEST_DATABASE_URL)
