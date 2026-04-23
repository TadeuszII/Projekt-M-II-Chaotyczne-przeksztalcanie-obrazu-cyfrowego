# ---- Moduł / dokumentacja ----
"""Etap 1: naiwny, odwracalny scrambling obrazu."""  # Krótki opis pliku.

# ---- Importy ----
from __future__ import annotations  # Pozwala na opóźnione obliczanie typów.

import hashlib  # Wbudowana biblioteka do skrótu klucza.

import numpy as np  # NumPy do operacji na obrazach.


# ---- Funkcje pomocnicze ----
def key_to_seed(key_text: str) -> int:  # Zamiana tekstu klucza na deterministyczny seed.
    """Convert any non-empty key text into a deterministic integer seed."""  # Opis funkcji.
    normalized_key: str = key_text.strip()  # Usunięcie spacji z klucza.
    if not normalized_key:  # Sprawdzenie, czy klucz nie jest pusty.
        raise ValueError("Klucz nie może być pusty.")  # Komunikat błędu dla pustego klucza.
    digest: bytes = hashlib.sha256(normalized_key.encode("utf-8")).digest()  # Skrót SHA-256 klucza.
    return int.from_bytes(digest[:8], byteorder="big", signed=False)  # Konwersja na liczbę całkowitą.


# ---- Funkcje przesunięć (Etap 1) ----
def _row_shifts(height: int, seed: int) -> np.ndarray:  # Wyliczenie przesunięć dla wierszy.
    """Build deterministic row shifts for the naive Stage 1 algorithm."""  # Opis funkcji.
    if height <= 0:  # Ochrona przed pustym obrazem.
        return np.zeros(0, dtype=np.int64)  # Zwrócenie pustej tablicy przesunięć.
    row_indices: np.ndarray = np.arange(height, dtype=np.int64)  # Indeksy wszystkich wierszy.
    base_shift: int = seed % height  # Bazowe przesunięcie zależne od klucza.
    return (base_shift + row_indices * 3) % height  # Deterministyczne przesunięcia wierszy.


def _column_shifts(width: int, seed: int) -> np.ndarray:  # Wyliczenie przesunięć dla kolumn.
    """Build deterministic column shifts for the naive Stage 1 algorithm."""  # Opis funkcji.
    if width <= 0:  # Ochrona przed pustym obrazem.
        return np.zeros(0, dtype=np.int64)  # Zwrócenie pustej tablicy przesunięć.
    column_indices: np.ndarray = np.arange(width, dtype=np.int64)  # Indeksy wszystkich kolumn.
    base_shift: int = (seed // 7) % width  # Bazowe przesunięcie zależne od klucza.
    return (base_shift + column_indices * 5) % width  # Deterministyczne przesunięcia kolumn.


# ---- Etap 1: scrambling ----
def scramble_image(image: np.ndarray, key_text: str) -> np.ndarray:  # Scrambling Etapu 1.
    """Scramble an image by cyclically shifting rows and then columns."""  # Opis funkcji.
    if image.ndim != 3:  # Sprawdzenie liczby wymiarów obrazu.
        raise ValueError("Obraz musi mieć trzy kanały kolorów.")  # Błąd, gdy obraz nie ma 3 kanałów.

    seed: int = key_to_seed(key_text)  # Wyliczenie seeda z klucza.
    scrambled: np.ndarray = image.copy()  # Kopia obrazu do modyfikacji.
    height: int = scrambled.shape[0]  # Wysokość obrazu.
    width: int = scrambled.shape[1]  # Szerokość obrazu.

    for row_index, shift in enumerate(_row_shifts(height, seed)):  # Iteracja po wierszach i ich przesunięciach.
        scrambled[row_index] = np.roll(scrambled[row_index], int(shift), axis=0)  # Przesunięcie wiersza.

    for column_index, shift in enumerate(_column_shifts(width, seed)):  # Iteracja po kolumnach i ich przesunięciach.
        scrambled[:, column_index] = np.roll(scrambled[:, column_index], int(shift), axis=0)  # Przesunięcie kolumny.

    return scrambled  # Zwrócenie obrazu po scramblingu.


# ---- Etap 1: unscrambling ----
def unscramble_image(image: np.ndarray, key_text: str) -> np.ndarray:  # Odwracanie Etapu 1.
    """Reverse the Stage 1 row/column cyclic shifts."""  # Opis funkcji.
    if image.ndim != 3:  # Sprawdzenie liczby wymiarów obrazu.
        raise ValueError("Obraz musi mieć trzy kanały kolorów.")  # Błąd, gdy obraz nie ma 3 kanałów.

    seed: int = key_to_seed(key_text)  # Wyliczenie seeda z klucza.
    restored: np.ndarray = image.copy()  # Kopia obrazu do odtwarzania.
    height: int = restored.shape[0]  # Wysokość obrazu.
    width: int = restored.shape[1]  # Szerokość obrazu.

    for column_index, shift in enumerate(_column_shifts(width, seed)):  # Iteracja po kolumnach i ich przesunięciach.
        restored[:, column_index] = np.roll(restored[:, column_index], -int(shift), axis=0)  # Odwrócenie przesunięcia kolumny.

    for row_index, shift in enumerate(_row_shifts(height, seed)):  # Iteracja po wierszach i ich przesunięciach.
        restored[row_index] = np.roll(restored[row_index], -int(shift), axis=0)  # Odwrócenie przesunięcia wiersza.

    return restored  # Zwrócenie odtworzonego obrazu.


# ---- Opis Etapu 1 ----
def stage1_description() -> str:  # Tekst opisu Etapu 1.
    """Return a short explanation of Stage 1 and its expected weakness."""  # Opis funkcji.
    return (  # Zwrócenie gotowego opisu.
        "Etap 1 wykonuje jedynie cykliczne przesunięcia wierszy i kolumn zależne od klucza.\n"  # Krótki opis operacji.
        "Metoda jest odwracalna, ale słaba: nie zmienia wartości pikseli, więc wiele struktur obrazu nadal pozostaje częściowo widocznych.\n"  # Wyjaśnienie słabości.
        "Szczególnie dobrze widać to dla obrazów o silnej regularności, np. szachownicy, gradientu albo tekstu."  # Przykłady struktur.
    )  # Koniec zwracanego opisu.
