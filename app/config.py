from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DATA_DIR = DATA_DIR / "output"
SAVED_MODEL_DIR = BASE_DIR / "saved_models"

TRAIN_DATA_FILE = RAW_DATA_DIR / "data.xlsx"
EVAL_DATA_FILE = RAW_DATA_DIR / "eval.xlsx"
TARGET_COLUMN = "移动房车险数量"
