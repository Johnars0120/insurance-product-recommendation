from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
RUNTIME_DATA_DIR = DATA_DIR / "runtime"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DATA_DIR = DATA_DIR / "output"
SAVED_MODEL_DIR = BASE_DIR / "saved_models"

DEFAULT_TRAIN_DATA_FILE = RAW_DATA_DIR / "data.xlsx"
DEFAULT_EVAL_DATA_FILE = RAW_DATA_DIR / "eval.xlsx"
TRAIN_DATA_FILE = RUNTIME_DATA_DIR / "data.xlsx"
EVAL_DATA_FILE = RUNTIME_DATA_DIR / "eval.xlsx"
TARGET_COLUMN = "移动房车险数量"
