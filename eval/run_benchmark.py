from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List

import click
import pandas as pd

from agents.pipeline import FakeScopePipeline
from agents.types import VerificationTask
from eval.datasets import load_csv_dataset
from eval.metrics import accuracy, macro_f1


@click.command()
@click.option("--dataset", default="fever", help="Nombre base del dataset CSV en eval/data (sin extension).")
@click.option("--text-column", default="claim", help="Columna con el texto o claim a verificar.")
@click.option("--label-column", default="label", help="Columna con la etiqueta real del dataset.")
@click.option("--limit", default=50, type=int, help="Cantidad de ejemplos a evaluar.")
def main(dataset: str, text_column: str, label_column: str, limit: int) -> None:
    data_path = Path(__file__).resolve().parent / "data" / f"{dataset}.csv"
    df = load_csv_dataset(data_path).head(limit)
    pipeline = FakeScopePipeline()
    records: List[dict] = []
    for _, row in df.iterrows():
        text = row[text_column]
        task = VerificationTask(input_text=text, language="en")
        result = asyncio.run(pipeline.ainvoke(task))
        verdict = result.get("verdict")
        records.append(
            {
                "text": text,
                "true_label": row[label_column],
                "predicted": verdict.label.value if verdict else "unknown",
            }
        )
    out = pd.DataFrame(records)
    print(out.head())
    print("Accuracy:", accuracy(out["true_label"], out["predicted"]))
    print("Macro F1:", macro_f1(out["true_label"], out["predicted"]))


if __name__ == "__main__":
    main()
