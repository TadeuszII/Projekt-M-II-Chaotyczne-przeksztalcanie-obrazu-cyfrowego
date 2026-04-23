# ---- Moduł / dokumentacja ----
"""Etap 2: czysta permutacja pikseli sterowana kluczem."""  # Krótki opis pliku.

# ---- Importy ----
from __future__ import annotations  # Pozwala na opóźnione obliczanie typów.

import hashlib  # Biblioteka do deterministycznego przekształcenia klucza w seed.

import numpy as np  # NumPy do operacji na tablicach obrazu.


# ---- Funkcje pomocnicze: klucz i seed ----
def key_to_seed(key_text: str) -> int:  # Zamiana tekstu klucza na deterministyczny seed.
    """Convert any non-empty key text into a deterministic integer seed."""  # Opis funkcji.
    normalized_key: str = key_text.strip()  # Usunięcie nadmiarowych spacji z klucza.
    if not normalized_key:  # Sprawdzenie, czy klucz nie jest pusty.
        raise ValueError("Klucz nie może być pusty.")  # Błąd dla pustego klucza.
    digest: bytes = hashlib.sha256(normalized_key.encode("utf-8")).digest()  # Obliczenie skrótu SHA-256 dla klucza.
    return int.from_bytes(digest[:8], byteorder="big", signed=False)  # Konwersja części skrótu na liczbę całkowitą.


# ---- Funkcje pomocnicze: permutacja ----
def generate_permutation(pixel_count: int, key_text: str) -> np.ndarray:  # Generowanie deterministycznej permutacji indeksów.
    """Generate a key-driven permutation of flattened pixel indices."""  # Opis funkcji.
    if pixel_count < 0:  # Ochrona przed niepoprawną liczbą pikseli.
        raise ValueError("Liczba pikseli nie może być ujemna.")  # Błąd dla niepoprawnego rozmiaru.
    seed: int = key_to_seed(key_text)  # Wyliczenie seeda z klucza.
    rng: np.random.Generator = np.random.default_rng(seed)  # Utworzenie generatora losowego sterowanego seedem.
    permutation: np.ndarray = np.arange(pixel_count, dtype=np.int64)  # Utworzenie tablicy indeksów początkowych.
    rng.shuffle(permutation)  # Przemieszanie indeksów w sposób deterministyczny.
    return permutation  # Zwrócenie gotowej permutacji.


def inverse_permutation(permutation: np.ndarray) -> np.ndarray:  # Generowanie permutacji odwrotnej.
    """Build the inverse permutation for a given permutation array."""  # Opis funkcji.
    inverse: np.ndarray = np.empty_like(permutation)  # Utworzenie pustej tablicy na permutację odwrotną.
    inverse[permutation] = np.arange(permutation.size, dtype=permutation.dtype)  # Wpisanie pozycji odwrotnych dla każdego indeksu.
    return inverse  # Zwrócenie permutacji odwrotnej.


# ---- Etap 2: scrambling ----
def scramble_image(image: np.ndarray, key_text: str) -> np.ndarray:  # Scrambling Etapu 2.
    """Scramble an image using a pure permutation of pixel positions."""  # Opis funkcji.
    if image.ndim != 3:  # Sprawdzenie liczby wymiarów obrazu.
        raise ValueError("Obraz musi mieć trzy kanały kolorów.")  # Błąd, gdy obraz nie ma oczekiwanego formatu.

    height: int = image.shape[0]  # Wysokość obrazu.
    width: int = image.shape[1]  # Szerokość obrazu.
    channels: int = image.shape[2]  # Liczba kanałów obrazu.
    flat_image: np.ndarray = image.reshape(height * width, channels)  # Spłaszczenie obrazu do listy pikseli.
    permutation: np.ndarray = generate_permutation(flat_image.shape[0], key_text)  # Wygenerowanie permutacji zależnej od klucza.
    scrambled_flat: np.ndarray = flat_image[permutation]  # Przestawienie pikseli według permutacji.
    return scrambled_flat.reshape(height, width, channels)  # Odtworzenie oryginalnego kształtu obrazu.


# ---- Etap 2: unscrambling ----
def unscramble_image(image: np.ndarray, key_text: str) -> np.ndarray:  # Odwracanie Etapu 2.
    """Reverse the pure key-driven pixel permutation used in Stage 2."""  # Opis funkcji.
    if image.ndim != 3:  # Sprawdzenie liczby wymiarów obrazu.
        raise ValueError("Obraz musi mieć trzy kanały kolorów.")  # Błąd, gdy obraz nie ma oczekiwanego formatu.

    height: int = image.shape[0]  # Wysokość obrazu.
    width: int = image.shape[1]  # Szerokość obrazu.
    channels: int = image.shape[2]  # Liczba kanałów obrazu.
    flat_image: np.ndarray = image.reshape(height * width, channels)  # Spłaszczenie obrazu do listy pikseli.
    permutation: np.ndarray = generate_permutation(flat_image.shape[0], key_text)  # Wygenerowanie tej samej permutacji zależnej od klucza.
    inverse: np.ndarray = inverse_permutation(permutation)  # Wyliczenie permutacji odwrotnej.
    restored_flat: np.ndarray = flat_image[inverse]  # Odtworzenie właściwej kolejności pikseli.
    return restored_flat.reshape(height, width, channels)  # Odtworzenie oryginalnego kształtu obrazu.


# ---- Opis Etapu 2 ----
def stage2_description() -> str:  # Tekst opisu Etapu 2.
    """Return a short explanation of Stage 2."""  # Opis funkcji.
    return (  # Zwrócenie gotowego opisu.
        "Etap 2 wykonuje czystą permutację pozycji pikseli sterowaną kluczem.\n"  # Krótki opis operacji.
        "Wartości pikseli nie są zmieniane, zmienia się tylko ich kolejność.\n"  # Wyjaśnienie natury transformacji.
        "Algorytm jest odwracalny dzięki zastosowaniu permutacji i jej odwrotności."  # Wyjaśnienie odwracalności.
    )  # Koniec zwracanego opisu.
