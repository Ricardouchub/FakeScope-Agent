from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)


def load_csv_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_csv(path)


def fever_samples() -> pd.DataFrame:
    # Placeholder loader - expects pre-downloaded FEVER csv in eval/data
    path = DATA_DIR / "fever.csv"
    return load_csv_dataset(path)


__all__ = ["fever_samples", "load_csv_dataset", "DATA_DIR"]
