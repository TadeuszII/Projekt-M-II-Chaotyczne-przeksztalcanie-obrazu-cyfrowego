# ---- Moduł / dokumentacja ----
"""Etap 3: hybryda permutacji i substytucji sterowana kluczem."""  # Krótki opis pliku.

# ---- Importy ----
from __future__ import annotations  # Pozwala na opóźnione obliczanie typów.

import numpy as np  # NumPy do operacji na tablicach obrazu.

from stage2 import generate_permutation  # Import generatora permutacji z Etapu 2.
from stage2 import key_to_seed  # Import funkcji zamiany klucza na seed.
from stage2 import inverse_permutation  # Import funkcji budującej permutację odwrotną.


# ---- Funkcje pomocnicze: maska substytucji ----
def substitution_seed(key_text: str) -> int:  # Wyliczenie osobnego seeda dla warstwy substytucji.
    """Return a deterministic seed dedicated to Stage 3 substitution."""  # Opis funkcji.
    base_seed: int = key_to_seed(key_text)  # Pobranie bazowego seeda z klucza.
    return (base_seed + 1) % (2 ** 63)  # Zwrócenie drugiego seeda dla niezależnej maski.


def substitution_mask(shape: tuple[int, ...], key_text: str) -> np.ndarray:  # Budowa maski pseudolosowej dla substytucji.
    """Build a deterministic uint8 mask for additive substitution."""  # Opis funkcji.
    rng: np.random.Generator = np.random.default_rng(substitution_seed(key_text))  # Utworzenie generatora dla warstwy substytucji.
    return rng.integers(0, 256, size=shape, dtype=np.uint8)  # Zwrócenie maski wartości z zakresu 0..255.


# ---- Etap 3: scrambling ----
def scramble_image(image: np.ndarray, key_text: str) -> np.ndarray:  # Scrambling Etapu 3.
    """Scramble an image using Stage 2 permutation followed by additive substitution."""  # Opis funkcji.
    if image.ndim != 3:  # Sprawdzenie liczby wymiarów obrazu.
        raise ValueError("Obraz musi mieć trzy kanały kolorów.")  # Błąd dla niepoprawnego formatu obrazu.

    height: int = image.shape[0]  # Wysokość obrazu.
    width: int = image.shape[1]  # Szerokość obrazu.
    channels: int = image.shape[2]  # Liczba kanałów obrazu.
    flat_image: np.ndarray = image.reshape(height * width, channels)  # Spłaszczenie obrazu do listy pikseli.
    permutation: np.ndarray = generate_permutation(flat_image.shape[0], key_text)  # Wygenerowanie permutacji zależnej od klucza.
    permuted_flat: np.ndarray = flat_image[permutation]  # Zastosowanie permutacji pozycji pikseli.
    mask: np.ndarray = substitution_mask(permuted_flat.shape, key_text)  # Wygenerowanie maski substytucji dla wszystkich pikseli.
    permuted_int: np.ndarray = permuted_flat.astype(np.uint16)  # Konwersja danych do typu bezpiecznego dla dodawania.
    mask_int: np.ndarray = mask.astype(np.uint16)  # Konwersja maski do typu bezpiecznego dla dodawania.
    substituted_flat: np.ndarray = ((permuted_int + mask_int) % 256).astype(np.uint8)  # Dodanie maski modulo 256 i powrót do uint8.
    return substituted_flat.reshape(height, width, channels)  # Odtworzenie oryginalnego kształtu obrazu.


# ---- Etap 3: unscrambling ----
def unscramble_image(image: np.ndarray, key_text: str) -> np.ndarray:  # Odwracanie Etapu 3.
    """Reverse Stage 3 by undoing substitution and then applying inverse permutation."""  # Opis funkcji.
    if image.ndim != 3:  # Sprawdzenie liczby wymiarów obrazu.
        raise ValueError("Obraz musi mieć trzy kanały kolorów.")  # Błąd dla niepoprawnego formatu obrazu.

    height: int = image.shape[0]  # Wysokość obrazu.
    width: int = image.shape[1]  # Szerokość obrazu.
    channels: int = image.shape[2]  # Liczba kanałów obrazu.
    flat_image: np.ndarray = image.reshape(height * width, channels)  # Spłaszczenie obrazu do listy pikseli.
    mask: np.ndarray = substitution_mask(flat_image.shape, key_text)  # Wygenerowanie tej samej maski substytucji co podczas scramblingu.
    image_int: np.ndarray = flat_image.astype(np.int16)  # Konwersja obrazu do typu bezpiecznego dla odejmowania.
    mask_int: np.ndarray = mask.astype(np.int16)  # Konwersja maski do typu bezpiecznego dla odejmowania.
    unsubstituted_flat: np.ndarray = ((image_int - mask_int) % 256).astype(np.uint8)  # Cofnięcie substytucji modulo 256.
    permutation: np.ndarray = generate_permutation(unsubstituted_flat.shape[0], key_text)  # Odtworzenie tej samej permutacji co podczas scramblingu.
    inverse: np.ndarray = inverse_permutation(permutation)  # Wyliczenie permutacji odwrotnej.
    restored_flat: np.ndarray = unsubstituted_flat[inverse]  # Odtworzenie właściwej kolejności pikseli.
    return restored_flat.reshape(height, width, channels)  # Odtworzenie oryginalnego kształtu obrazu.


# ---- Opis Etapu 3 ----
def stage3_description() -> str:  # Tekst opisu Etapu 3.
    """Return a short explanation of Stage 3 and its hybrid structure."""  # Opis funkcji.
    return (  # Zwrócenie gotowego opisu.
        "Etap 3 rozszerza Etap 2 o mechanizm wzmacniający w postaci hybrydy: najpierw wykonywana jest permutacja pikseli, a potem substytucja ich wartości.\n"  # Opis kolejności operacji.
        "Substytucja polega na dodaniu pseudolosowej maski modulo 256 zależnej od klucza, dzięki czemu zmienia się nie tylko pozycja, ale także wartość pikseli.\n"  # Wyjaśnienie mechanizmu wzmacniającego.
        "Algorytm pozostaje w pełni odwracalny: podczas unscramblingu najpierw cofana jest substytucja, a następnie stosowana jest permutacja odwrotna."  # Wyjaśnienie algorytmu odwrotnego.
    )  # Koniec zwracanego opisu.
