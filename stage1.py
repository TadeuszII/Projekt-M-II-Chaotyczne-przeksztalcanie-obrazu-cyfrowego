"""Etap 1: naiwny, odwracalny scrambling obrazu."""

from __future__ import annotations

import hashlib

import numpy as np


def key_to_seed(key_text: str) -> int:
    """Convert any non-empty key text into a deterministic integer seed."""
    normalized_key: str = key_text.strip()
    if not normalized_key:
        raise ValueError("Klucz nie może być pusty.")
    digest: bytes = hashlib.sha256(normalized_key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def _row_shifts(height: int, seed: int) -> np.ndarray:
    """Build deterministic row shifts for the naive Stage 1 algorithm."""
    row_indices: np.ndarray = np.arange(height, dtype=np.int64)
    return (seed + row_indices * 3) % max(height, 1)


def _column_shifts(width: int, seed: int) -> np.ndarray:
    """Build deterministic column shifts for the naive Stage 1 algorithm."""
    column_indices: np.ndarray = np.arange(width, dtype=np.int64)
    return ((seed // 7) + column_indices * 5) % max(width, 1)


def scramble_image(image: np.ndarray, key_text: str) -> np.ndarray:
    """Scramble an image by cyclically shifting rows and then columns."""
    if image.ndim != 3:
        raise ValueError("Obraz musi mieć trzy kanały kolorów.")

    seed: int = key_to_seed(key_text)
    scrambled: np.ndarray = image.copy()
    height: int = scrambled.shape[0]
    width: int = scrambled.shape[1]

    for row_index, shift in enumerate(_row_shifts(height, seed)):
        scrambled[row_index] = np.roll(scrambled[row_index], int(shift), axis=0)

    for column_index, shift in enumerate(_column_shifts(width, seed)):
        scrambled[:, column_index] = np.roll(scrambled[:, column_index], int(shift), axis=0)

    return scrambled


def unscramble_image(image: np.ndarray, key_text: str) -> np.ndarray:
    """Reverse the Stage 1 row/column cyclic shifts."""
    if image.ndim != 3:
        raise ValueError("Obraz musi mieć trzy kanały kolorów.")

    seed: int = key_to_seed(key_text)
    restored: np.ndarray = image.copy()
    height: int = restored.shape[0]
    width: int = restored.shape[1]

    for column_index, shift in enumerate(_column_shifts(width, seed)):
        restored[:, column_index] = np.roll(restored[:, column_index], -int(shift), axis=0)

    for row_index, shift in enumerate(_row_shifts(height, seed)):
        restored[row_index] = np.roll(restored[row_index], -int(shift), axis=0)

    return restored


def stage1_description() -> str:
    """Return a short explanation of Stage 1 and its expected weakness."""
    return (
        "Etap 1 wykonuje jedynie cykliczne przesunięcia wierszy i kolumn zależne od klucza.\n"
        "Metoda jest odwracalna, ale słaba: nie zmienia wartości pikseli, więc wiele struktur obrazu nadal pozostaje częściowo widocznych.\n"
        "Szczególnie dobrze widać to dla obrazów o silnej regularności, np. szachownicy, gradientu albo tekstu."
    )
