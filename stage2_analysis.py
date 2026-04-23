# ---- Moduł / dokumentacja ----
"""Analiza eksperymentalna i metryki dla Etapu 2."""  # Krótki opis pliku.

# ---- Importy ----
from __future__ import annotations  # Pozwala na opóźnione obliczanie typów.

import cv2  # OpenCV do konwersji obrazu na skalę szarości.
import numpy as np  # NumPy do obliczeń numerycznych.

from stage2 import scramble_image  # Import funkcji scramblingu Etapu 2.
from stage2 import permutation_mapping  # Import funkcji zwracającej formalne odwzorowania P i P^-1.
from stage2 import verify_inverse_relation  # Import funkcji przygotowującej przykłady P^-1(P(i)) = i.
from stage2 import unscramble_image  # Import funkcji unscramblingu Etapu 2.


# ---- Funkcje pomocnicze: przygotowanie danych ----
def _to_grayscale_float(image: np.ndarray) -> np.ndarray:  # Konwersja obrazu do skali szarości typu float.
    gray_image: np.ndarray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Zamiana obrazu kolorowego na skalę szarości.
    return gray_image.astype(np.float64)  # Konwersja na float dla stabilniejszych obliczeń.


# ---- Funkcje pomocnicze: korelacja ----
def _safe_correlation(first_values: np.ndarray, second_values: np.ndarray) -> float:  # Bezpieczne liczenie korelacji Pearsona.
    if first_values.size == 0 or second_values.size == 0:  # Ochrona przed pustymi danymi wejściowymi.
        return 0.0  # Zwrócenie neutralnej wartości.
    if np.all(first_values == first_values[0]) or np.all(second_values == second_values[0]):  # Sprawdzenie braku zmienności danych.
        return 0.0  # Brak sensownej korelacji przy stałych danych.
    correlation_matrix: np.ndarray = np.corrcoef(first_values, second_values)  # Wyliczenie macierzy korelacji.
    return float(correlation_matrix[0, 1])  # Zwrócenie współczynnika korelacji.


def adjacent_pixel_correlation(image: np.ndarray) -> dict[str, float]:  # Korelacja sąsiednich pikseli w poziomie i pionie.
    gray_image: np.ndarray = _to_grayscale_float(image)  # Konwersja obrazu do skali szarości.
    horizontal_left: np.ndarray = gray_image[:, :-1].ravel()  # Piksele z lewej strony par poziomych.
    horizontal_right: np.ndarray = gray_image[:, 1:].ravel()  # Piksele z prawej strony par poziomych.
    vertical_top: np.ndarray = gray_image[:-1, :].ravel()  # Piksele z góry par pionowych.
    vertical_bottom: np.ndarray = gray_image[1:, :].ravel()  # Piksele z dołu par pionowych.
    return {  # Zwrócenie obu obowiązkowych korelacji.
        "horizontal": _safe_correlation(horizontal_left, horizontal_right),  # Korelacja pozioma.
        "vertical": _safe_correlation(vertical_top, vertical_bottom),  # Korelacja pionowa.
    }  # Koniec słownika wyników.


# ---- Funkcje pomocnicze: różnica obrazu ----
def image_difference_metrics(reference_image: np.ndarray, test_image: np.ndarray) -> dict[str, float]:  # Podstawowe metryki różnicy dwóch obrazów.
    reference_int: np.ndarray = reference_image.astype(np.int16)  # Konwersja obrazu odniesienia do typu bezpiecznego dla odejmowania.
    test_int: np.ndarray = test_image.astype(np.int16)  # Konwersja obrazu testowego do typu bezpiecznego dla odejmowania.
    absolute_difference: np.ndarray = np.abs(reference_int - test_int)  # Różnica bezwzględna pomiędzy obrazami.
    changed_mask: np.ndarray = np.any(absolute_difference > 0, axis=2)  # Mapa pikseli, które zmieniły się w co najmniej jednym kanale.
    return {  # Zwrócenie zbioru prostych metryk różnicy.
        "mean_abs_diff": float(np.mean(absolute_difference)),  # Średnia bezwzględna różnica pikseli.
        "max_abs_diff": float(np.max(absolute_difference)),  # Maksymalna bezwzględna różnica pikseli.
        "changed_percent": float(np.mean(changed_mask) * 100.0),  # Procent zmienionych pikseli.
    }  # Koniec słownika wyników.


# ---- Funkcje pomocnicze: formatowanie ----
def _format_metric(value: float) -> str:  # Formatowanie liczb do czytelnej postaci tekstowej.
    return f"{value:.6f}"  # Zwrócenie liczby z sześcioma miejscami po przecinku.


# ---- Funkcje pomocnicze: formalny opis permutacji ----
def _formal_permutation_lines(pixel_count: int, key_text: str) -> list[str]:  # Budowa linii raportu formalnie opisujących P oraz P^-1.
    permutation: np.ndarray
    inverse: np.ndarray
    permutation, inverse = permutation_mapping(pixel_count, key_text)  # Pobranie permutacji P i permutacji odwrotnej P^-1.
    verification_rows: list[tuple[int, int, int]] = verify_inverse_relation(pixel_count, key_text)  # Pobranie przykładowych weryfikacji relacji odwrotności.
    report_lines: list[str] = [  # Lista linii formalnego opisu permutacji.
        "Formalny opis permutacji:",  # Nagłówek sekcji formalnej.
        f"- Domena i przeciwdziedzina: P: {{0...{pixel_count - 1}}} -> {{0...{pixel_count - 1}}}",  # Formalny zapis funkcji P.
        "- P(i) oznacza indeks wyjściowy przypisany i-temu pikselowi po spłaszczeniu obrazu.",  # Wyjaśnienie znaczenia funkcji P.
        "- P^-1(j) oznacza indeks wejściowy odzyskany z pozycji j po zastosowaniu permutacji odwrotnej.",  # Wyjaśnienie znaczenia funkcji P^-1.
        f"- P jest generowana jawnym algorytmem Fishera-Yatesa sterowanym seedem z klucza.",  # Informacja o sposobie generowania P.
        f"- Liczba wszystkich indeksów N: {pixel_count}",  # Rozmiar dziedziny permutacji.
        f"- Przykład pierwszych wartości P(i): {permutation[:min(8, pixel_count)].tolist()}",  # Kilka pierwszych wartości permutacji.
        f"- Przykład pierwszych wartości P^-1(i): {inverse[:min(8, pixel_count)].tolist()}",  # Kilka pierwszych wartości permutacji odwrotnej.
        "- Weryfikacja relacji P^-1(P(i)) = i dla wybranych indeksów:",  # Nagłówek sekcji weryfikacyjnej.
    ]  # Koniec podstawowych linii formalnego opisu.
    for source_index, mapped_index, restored_index in verification_rows:  # Iteracja po wybranych przykładach indeksów.
        report_lines.append(  # Dopisanie pojedynczego przykładu formalnej weryfikacji.
            f"  - i = {source_index}, P(i) = {mapped_index}, P^-1(P(i)) = {restored_index}"  # Konkretna trójka pokazująca odwracalność.
        )  # Koniec dopisania pojedynczego przykładu.
    return report_lines  # Zwrócenie pełnej listy linii formalnego opisu.


# ---- Raport: scrambling ----
def build_scramble_analysis_text(
    original_image: np.ndarray,
    scrambled_image: np.ndarray,
    correct_key_text: str,
    wrong_key_text: str,
    used_key_label: str,
) -> str:  # Budowa tekstu analizy po wykonaniu scramblingu.
    pixel_count: int = original_image.shape[0] * original_image.shape[1]  # Liczba pikseli po spłaszczeniu obrazu.
    original_correlation: dict[str, float] = adjacent_pixel_correlation(original_image)  # Korelacja sąsiednich pikseli przed scramblingiem.
    scrambled_correlation: dict[str, float] = adjacent_pixel_correlation(scrambled_image)  # Korelacja sąsiednich pikseli po scramblingu.
    report_lines: list[str] = [  # Lista linii raportu końcowego.
        "Wykonano scrambling dla Etapu 2.",  # Nagłówek raportu.
        f"Użyty klucz operacyjny: {used_key_label}.",  # Informacja o kluczu użytym w bieżącej operacji.
        "",  # Pusta linia dla czytelności.
        "Analiza eksperymentalna:",  # Sekcja analizy eksperymentalnej.
        "- Etap 2 wykonuje czystą permutację pikseli, więc wartości pikseli pozostają bez zmian.",  # Charakterystyka algorytmu.
        "- Utrata struktury obrazu jest większa niż w Etapie 1, bo mieszane są wszystkie pozycje pikseli, nie tylko całe wiersze i kolumny.",  # Wniosek o strukturze obrazu.
        "- Odwracalność jest pełna dla poprawnego klucza, ponieważ istnieje jawna permutacja odwrotna.",  # Wniosek o odwracalności.
        "- Wrażliwość na parametry jest większa niż w Etapie 1, bo zmiana klucza zmienia cały układ permutacji indeksów.",  # Wniosek o parametrach.
        "",  # Pusta linia dla czytelności.
        "Obowiązkowe metryki, korelacja sąsiednich pikseli:",  # Sekcja obowiązkowych metryk.
        f"- Przed scramblingiem, pozioma: {_format_metric(original_correlation['horizontal'])}",  # Korelacja pozioma przed scramblingiem.
        f"- Przed scramblingiem, pionowa: {_format_metric(original_correlation['vertical'])}",  # Korelacja pionowa przed scramblingiem.
        f"- Po scramblingu, pozioma: {_format_metric(scrambled_correlation['horizontal'])}",  # Korelacja pozioma po scramblingu.
        f"- Po scramblingu, pionowa: {_format_metric(scrambled_correlation['vertical'])}",  # Korelacja pionowa po scramblingu.
    ]  # Koniec podstawowych linii raportu.

    report_lines.extend(["", *_formal_permutation_lines(pixel_count, correct_key_text)])  # Dopisanie formalnego opisu P oraz P^-1.

    if correct_key_text.strip() and wrong_key_text.strip():  # Sprawdzenie, czy użytkownik podał oba klucze do porównania.
        scrambled_with_wrong_key: np.ndarray = scramble_image(original_image, wrong_key_text)  # Scrambling tego samego obrazu z błędnym kluczem.
        key_change_difference: dict[str, float] = image_difference_metrics(scrambled_image, scrambled_with_wrong_key)  # Różnica między wynikami dla dwóch kluczy.
        report_lines.extend(
            [
                "",  # Pusta linia dla czytelności.
                "Wpływ zmiany klucza na wynik:",  # Nagłówek sekcji wpływu klucza.
                f"- Test minimalnej zmiany klucza można wykonać np. dla pary: {correct_key_text} vs {wrong_key_text}",  # Wskazanie pary kluczy użytej do testu.
                f"- Średnia różnica między dwoma obrazami scrambled: {_format_metric(key_change_difference['mean_abs_diff'])}",  # Średnia różnica po zmianie klucza.
                f"- Maksymalna różnica między dwoma obrazami scrambled: {_format_metric(key_change_difference['max_abs_diff'])}",  # Maksymalna różnica po zmianie klucza.
                f"- Procent zmienionych pikseli po zmianie klucza: {_format_metric(key_change_difference['changed_percent'])}%",  # Odsetek pikseli zmienionych po zmianie klucza.
                "- Wniosek o efekcie lawinowym: Etap 2 pokazuje większą wrażliwość na zmianę klucza niż Etap 1, ale nie daje pełnego efektu lawinowego w sensie kryptograficznym.",  # Odpowiedź o efekcie lawinowym.
                "- Powód: zmienia się permutacja pozycji pikseli, ale same wartości pikseli nie są modyfikowane.",  # Uzasadnienie odpowiedzi o efekcie lawinowym.
            ]
        )  # Koniec dopisywania sekcji wpływu klucza.
    else:  # Obsługa sytuacji, gdy nie podano obu kluczy.
        report_lines.extend(
            [
                "",  # Pusta linia dla czytelności.
                "Wpływ zmiany klucza na wynik:",  # Nagłówek sekcji wpływu klucza.
                "- Aby policzyć tę analizę, wpisz zarówno klucz poprawny, jak i klucz błędny.",  # Instrukcja dla użytkownika.
                "- Przykładowy test minimalnej zmiany klucza: klucz123 vs klucz124 albo zmiana jednego znaku.",  # Podpowiedź, jak wykonać test minimalnej zmiany klucza.
                "- Odpowiedź o efekcie lawinowym: sam wzrost chaosu permutacji nie oznacza pełnego efektu lawinowego, bo wartości pikseli pozostają bez zmian.",  # Odpowiedź o efekcie lawinowym bez pełnych danych liczbowych.
            ]
        )  # Koniec dopisywania informacji pomocniczej.

    report_lines.extend(
        [
            "",  # Pusta linia dla czytelności.
            "Porównanie Etapu 1, 2 i 3:",  # Nagłówek wymaganej sekcji porównawczej.
            "- Etap 1: mała utrata struktury obrazu, pełna odwracalność przy poprawnym kluczu, ograniczona wrażliwość na parametry.",  # Charakterystyka Etapu 1.
            "- Etap 2: większa utrata struktury obrazu niż w Etapie 1, pełna odwracalność przy poprawnym kluczu, wyższa wrażliwość na parametry.",  # Charakterystyka Etapu 2.
            "- Etap 3: porównanie zostanie uzupełnione po jego implementacji.",  # Informacja o stanie projektu.
        ]
    )  # Koniec dopisywania sekcji porównawczej.

    return "\n".join(report_lines)  # Zwrócenie gotowego raportu tekstowego.


# ---- Raport: unscrambling ----
def build_unscramble_analysis_text(
    original_image: np.ndarray | None,
    scrambled_image: np.ndarray,
    restored_image: np.ndarray,
    correct_key_text: str,
    wrong_key_text: str,
    used_key_label: str,
) -> str:  # Budowa tekstu analizy po wykonaniu unscramblingu.
    pixel_count: int = scrambled_image.shape[0] * scrambled_image.shape[1]  # Liczba pikseli po spłaszczeniu obrazu.
    report_lines: list[str] = [  # Lista linii raportu końcowego.
        "Wykonano unscrambling dla Etapu 2.",  # Nagłówek raportu.
        f"Użyty klucz operacyjny: {used_key_label}.",  # Informacja o kluczu użytym w bieżącej operacji.
        "",  # Pusta linia dla czytelności.
        "Zachowanie algorytmu przy błędnym kluczu:",  # Nagłówek sekcji związanej z błędnym kluczem.
        "- Dla poprawnego klucza obraz jest odtwarzany przez zastosowanie permutacji odwrotnej do tej użytej w scramblingu.",  # Wniosek dla poprawnego klucza.
        "- Dla błędnego klucza używana jest inna permutacja odwrotna, więc piksele trafiają na niewłaściwe pozycje.",  # Wniosek dla błędnego klucza.
    ]  # Koniec podstawowych linii raportu.

    if correct_key_text.strip():  # Sprawdzenie, czy dostępny jest poprawny klucz do formalnego opisu permutacji.
        report_lines.extend(["", *_formal_permutation_lines(pixel_count, correct_key_text)])  # Dopisanie formalnego opisu P oraz P^-1.

    if original_image is not None:  # Sprawdzenie, czy dostępny jest obraz referencyjny do porównania.
        restored_difference: dict[str, float] = image_difference_metrics(original_image, restored_image)  # Różnica między oryginałem a obrazem odtworzonym.
        exact_recovery: bool = np.array_equal(original_image, restored_image)  # Sprawdzenie idealnej odwracalności.
        report_lines.extend(
            [
                "",  # Pusta linia dla czytelności.
                "Porównanie obrazu odtworzonego z oryginałem:",  # Nagłówek sekcji porównawczej.
                f"- Idealne odtworzenie: {'tak' if exact_recovery else 'nie'}",  # Informacja o pełnej odwracalności.
                f"- Średnia bezwzględna różnica: {_format_metric(restored_difference['mean_abs_diff'])}",  # Średnia różnica względem oryginału.
                f"- Maksymalna różnica: {_format_metric(restored_difference['max_abs_diff'])}",  # Maksymalna różnica względem oryginału.
                f"- Procent zmienionych pikseli: {_format_metric(restored_difference['changed_percent'])}%",  # Procent pikseli różniących się od oryginału.
            ]
        )  # Koniec dopisywania sekcji porównawczej.
    else:  # Obsługa sytuacji bez obrazu oryginalnego.
        report_lines.extend(
            [
                "",  # Pusta linia dla czytelności.
                "Porównanie obrazu odtworzonego z oryginałem:",  # Nagłówek sekcji porównawczej.
                "- Brak obrazu oryginalnego, więc nie można policzyć różnicy względem źródła.",  # Informacja o braku danych wejściowych.
            ]
        )  # Koniec dopisywania informacji pomocniczej.

    if original_image is not None and correct_key_text.strip() and wrong_key_text.strip():  # Sprawdzenie, czy można policzyć metrykę dla błędnego klucza.
        wrong_key_restored: np.ndarray = unscramble_image(scrambled_image, wrong_key_text)  # Odtworzenie obrazu z użyciem błędnego klucza.
        wrong_key_difference: dict[str, float] = image_difference_metrics(original_image, wrong_key_restored)  # Różnica względem oryginału przy błędnym kluczu.
        report_lines.extend(
            [
                "",  # Pusta linia dla czytelności.
                "Obowiązkowa metryka, różnica obrazu przy unscramblingu błędnym kluczem:",  # Nagłówek obowiązkowej metryki.
                f"- Średnia bezwzględna różnica: {_format_metric(wrong_key_difference['mean_abs_diff'])}",  # Średnia różnica dla błędnego klucza.
                f"- Maksymalna różnica: {_format_metric(wrong_key_difference['max_abs_diff'])}",  # Maksymalna różnica dla błędnego klucza.
                f"- Procent zmienionych pikseli: {_format_metric(wrong_key_difference['changed_percent'])}%",  # Procent zmienionych pikseli dla błędnego klucza.
            ]
        )  # Koniec dopisywania obowiązkowej metryki.
    else:  # Obsługa sytuacji bez pełnego zestawu danych.
        report_lines.extend(
            [
                "",  # Pusta linia dla czytelności.
                "Obowiązkowa metryka, różnica obrazu przy unscramblingu błędnym kluczem:",  # Nagłówek obowiązkowej metryki.
                "- Aby policzyć tę metrykę, potrzebny jest obraz oryginalny oraz oba klucze: poprawny i błędny.",  # Instrukcja dla użytkownika.
            ]
        )  # Koniec dopisywania informacji pomocniczej.

    return "\n".join(report_lines)  # Zwrócenie gotowego raportu tekstowego.
