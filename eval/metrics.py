from __future__ import annotations

from typing import Iterable

from sklearn.metrics import accuracy_score, f1_score


def macro_f1(y_true: Iterable[str], y_pred: Iterable[str]) -> float:
    return float(f1_score(list(y_true), list(y_pred), average="macro"))


def accuracy(y_true: Iterable[str], y_pred: Iterable[str]) -> float:
    return float(accuracy_score(list(y_true), list(y_pred)))


def fever_score(y_true: Iterable[str], y_pred: Iterable[str]) -> float:
    y_true_list = list(y_true)
    y_pred_list = list(y_pred)
    correct = 0
    for truth, pred in zip(y_true_list, y_pred_list):
        if truth == pred and truth != "unknown":
            correct += 1
    return correct / len(y_true_list) if y_true_list else 0.0


__all__ = ["macro_f1", "accuracy", "fever_score"]
