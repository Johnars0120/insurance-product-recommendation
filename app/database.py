from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "insurance_recommendation.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE.as_posix()}"
