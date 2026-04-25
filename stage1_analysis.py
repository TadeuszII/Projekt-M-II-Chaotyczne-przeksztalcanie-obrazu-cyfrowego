# ---- Moduł / dokumentacja ----
"""Analiza eksperymentalna i metryki dla Etapu 1."""  # Krótki opis pliku.

# ---- Importy ----
from __future__ import annotations  # Pozwala na opóźnione obliczanie typów.

import cv2  # OpenCV do konwersji obrazu na skalę szarości.
import numpy as np  # NumPy do obliczeń numerycznych.

from stage1 import scramble_image  # Import funkcji scramblingu Etapu 1.
from stage1 import unscramble_image  # Import funkcji unscramblingu Etapu 1.


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


# ---- Raport: scrambling ----
def build_scramble_analysis_text(
    original_image: np.ndarray,
    scrambled_image: np.ndarray,
    correct_key_text: str,
    wrong_key_text: str,
    used_key_label: str,
) -> str:  # Budowa tekstu analizy po wykonaniu scramblingu.
    original_correlation: dict[str, float] = adjacent_pixel_correlation(original_image)  # Korelacja sąsiednich pikseli przed scramblingiem.
    scrambled_correlation: dict[str, float] = adjacent_pixel_correlation(scrambled_image)  # Korelacja sąsiednich pikseli po scramblingu.
    report_lines: list[str] = [  # Lista linii raportu końcowego.
        "Wykonano scrambling dla Etapu 1.",  # Nagłówek raportu.
        f"Użyty klucz operacyjny: {used_key_label}.",  # Informacja o kluczu użytym w bieżącej operacji.
        "",  # Pusta linia dla czytelności.
        "Analiza eksperymentalna:",  # Sekcja analizy eksperymentalnej.
        "- Etap 1 tylko przesuwa wiersze i kolumny, więc zachowuje wartości pikseli.",  # Krótkie przypomnienie charakteru algorytmu.
        "- Utrata struktury obrazu jest ograniczona, bo część dużych konturów i regularności nadal pozostaje widoczna.",  # Wniosek o strukturze obrazu.
        "- Odwracalność jest pełna dla poprawnego klucza, ponieważ wszystkie przesunięcia są cykliczne i deterministyczne.",  # Wniosek o odwracalności.
        "- Wrażliwość na parametry istnieje, ale jest ograniczona, bo algorytm nadal wykonuje tylko prostą permutację pozycji.",  # Wniosek o parametrach.
        "",  # Pusta linia dla czytelności.
        "Obowiązkowe metryki, korelacja sąsiednich pikseli:",  # Sekcja obowiązkowych metryk.
        f"- Przed scramblingiem, pozioma: {_format_metric(original_correlation['horizontal'])}",  # Korelacja pozioma przed scramblingiem.
        f"- Przed scramblingiem, pionowa: {_format_metric(original_correlation['vertical'])}",  # Korelacja pionowa przed scramblingiem.
        f"- Po scramblingu, pozioma: {_format_metric(scrambled_correlation['horizontal'])}",  # Korelacja pozioma po scramblingu.
        f"- Po scramblingu, pionowa: {_format_metric(scrambled_correlation['vertical'])}",  # Korelacja pionowa po scramblingu.
    ]  # Koniec podstawowych linii raportu.

    if correct_key_text.strip() and wrong_key_text.strip():  # Sprawdzenie, czy użytkownik podał oba klucze do porównania.
        scrambled_with_wrong_key: np.ndarray = scramble_image(original_image, wrong_key_text)  # Scrambling tego samego obrazu z błędnym kluczem.
        key_change_difference: dict[str, float] = image_difference_metrics(scrambled_image, scrambled_with_wrong_key)  # Różnica między wynikami dla dwóch kluczy.
        report_lines.extend(  # Dopisanie analizy wpływu zmiany klucza.
            [
                "",  # Pusta linia dla czytelności.
                "Wpływ zmiany klucza na wynik:",  # Nagłówek sekcji wpływu klucza.
                f"- Średnia różnica między dwoma obrazami scrambled: {_format_metric(key_change_difference['mean_abs_diff'])}",  # Średnia różnica po zmianie klucza.
                f"- Maksymalna różnica między dwoma obrazami scrambled: {_format_metric(key_change_difference['max_abs_diff'])}",  # Maksymalna różnica po zmianie klucza.
                f"- Procent zmienionych pikseli po zmianie klucza: {_format_metric(key_change_difference['changed_percent'])}%",  # Odsetek pikseli zmienionych po zmianie klucza.
            ]
        )  # Koniec dopisywania sekcji wpływu klucza.
    else:  # Obsługa sytuacji, gdy nie podano obu kluczy.
        report_lines.extend(  # Dopisanie informacji o braku pełnej analizy klucza.
            [
                "",  # Pusta linia dla czytelności.
                "Wpływ zmiany klucza na wynik:",  # Nagłówek sekcji wpływu klucza.
                "- Aby policzyć tę analizę, wpisz zarówno klucz poprawny, jak i klucz błędny.",  # Instrukcja dla użytkownika.
            ]
        )  # Koniec dopisywania informacji pomocniczej.

    report_lines.extend(  # Dopisanie notatki o porównaniu etapów.
        [
            "",  # Pusta linia dla czytelności.
            "Porównanie Etapu 1, 2 i 3:",  # Nagłówek wymaganej sekcji porównawczej.
            "- Etap 1: mała utrata struktury obrazu, pełna odwracalność przy poprawnym kluczu, ograniczona wrażliwość na parametry.",  # Aktualna charakterystyka Etapu 1.
            "- Etap 2: większa utrata struktury obrazu niż w Etapie 1, pełna odwracalność przy poprawnym kluczu, wyższa wrażliwość na parametry.",  # Aktualna charakterystyka Etapu 2.
            "- Etap 3: największa utrata struktury obrazu spośród trzech etapów, pełna odwracalność przy poprawnym kluczu, najwyższa wrażliwość na parametry w tej implementacji.",  # Aktualna charakterystyka Etapu 3.
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
    report_lines: list[str] = [  # Lista linii raportu końcowego.
        "Wykonano unscrambling dla Etapu 1.",  # Nagłówek raportu.
        f"Użyty klucz operacyjny: {used_key_label}.",  # Informacja o kluczu użytym w bieżącej operacji.
        "",  # Pusta linia dla czytelności.
        "Zachowanie algorytmu przy błędnym kluczu:",  # Nagłówek sekcji związanej z błędnym kluczem.
        "- Dla poprawnego klucza wszystkie przesunięcia są odwracane dokładnie w odwrotnej kolejności.",  # Wniosek dla poprawnego klucza.
        "- Dla błędnego klucza obraz zwykle pozostaje zniekształcony, bo odwracane są nie te przesunięcia, które zostały użyte w scramblingu.",  # Wniosek dla błędnego klucza.
    ]  # Koniec podstawowych linii raportu.

    if original_image is not None:  # Sprawdzenie, czy dostępny jest obraz referencyjny do porównania.
        restored_difference: dict[str, float] = image_difference_metrics(original_image, restored_image)  # Różnica między oryginałem a obrazem odtworzonym.
        exact_recovery: bool = np.array_equal(original_image, restored_image)  # Sprawdzenie idealnej odwracalności.
        report_lines.extend(  # Dopisanie wyników porównania z oryginałem.
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
        report_lines.extend(  # Dopisanie informacji pomocniczej.
            [
                "",  # Pusta linia dla czytelności.
                "Porównanie obrazu odtworzonego z oryginałem:",  # Nagłówek sekcji porównawczej.
                "- Brak obrazu oryginalnego, więc nie można policzyć różnicy względem źródła.",  # Informacja o braku danych wejściowych.
            ]
        )  # Koniec dopisywania informacji pomocniczej.

    if original_image is not None and correct_key_text.strip() and wrong_key_text.strip():  # Sprawdzenie, czy można policzyć metrykę dla błędnego klucza.
        wrong_key_restored: np.ndarray = unscramble_image(scrambled_image, wrong_key_text)  # Odtworzenie obrazu z użyciem błędnego klucza.
        wrong_key_difference: dict[str, float] = image_difference_metrics(original_image, wrong_key_restored)  # Różnica względem oryginału przy błędnym kluczu.
        report_lines.extend(  # Dopisanie obowiązkowej metryki dla błędnego klucza.
            [
                "",  # Pusta linia dla czytelności.
                "Obowiązkowa metryka, różnica obrazu przy unscramblingu błędnym kluczem:",  # Nagłówek obowiązkowej metryki.
                f"- Średnia bezwzględna różnica: {_format_metric(wrong_key_difference['mean_abs_diff'])}",  # Średnia różnica dla błędnego klucza.
                f"- Maksymalna różnica: {_format_metric(wrong_key_difference['max_abs_diff'])}",  # Maksymalna różnica dla błędnego klucza.
                f"- Procent zmienionych pikseli: {_format_metric(wrong_key_difference['changed_percent'])}%",  # Procent zmienionych pikseli dla błędnego klucza.
            ]
        )  # Koniec dopisywania obowiązkowej metryki.
    else:  # Obsługa sytuacji bez pełnego zestawu danych.
        report_lines.extend(  # Dopisanie informacji pomocniczej.
            [
                "",  # Pusta linia dla czytelności.
                "Obowiązkowa metryka, różnica obrazu przy unscramblingu błędnym kluczem:",  # Nagłówek obowiązkowej metryki.
                "- Aby policzyć tę metrykę, potrzebny jest obraz oryginalny oraz oba klucze: poprawny i błędny.",  # Instrukcja dla użytkownika.
            ]
        )  # Koniec dopisywania informacji pomocniczej.

    return "\n".join(report_lines)  # Zwrócenie gotowego raportu tekstowego.
