# ---- Moduł / dokumentacja ----
"""Analiza eksperymentalna i metryki dla Etapu 3."""  # Krótki opis pliku.

# ---- Importy ----
from __future__ import annotations  # Pozwala na opóźnione obliczanie typów.

import numpy as np  # NumPy do obliczeń numerycznych.

from stage2_analysis import adjacent_pixel_correlation  # Import funkcji korelacji sąsiednich pikseli.
from stage2_analysis import image_difference_metrics  # Import funkcji liczącej różnicę pomiędzy obrazami.
from stage2_analysis import _format_metric  # Import funkcji formatującej liczby do raportu.
from stage2_analysis import _formal_permutation_lines  # Import funkcji budującej formalny opis permutacji.
from stage3 import scramble_image  # Import funkcji scramblingu Etapu 3.
from stage3 import substitution_mask  # Import funkcji budującej maskę substytucji Etapu 3.
from stage3 import substitution_seed  # Import funkcji wyznaczającej seed substytucji Etapu 3.
from stage3 import unscramble_image  # Import funkcji unscramblingu Etapu 3.


# ---- Funkcje pomocnicze: formalny opis substytucji ----
def _formal_substitution_lines(image_shape: tuple[int, ...], key_text: str) -> list[str]:  # Budowa linii raportu formalnie opisujących warstwę substytucji.
    """Return report lines describing the additive substitution used in Stage 3."""  # Opis funkcji.
    mask: np.ndarray = substitution_mask(image_shape, key_text)  # Wygenerowanie maski substytucji dla podanego rozmiaru danych.
    sample_values: list[int] = mask.reshape(-1)[: min(12, mask.size)].astype(int).tolist()  # Przygotowanie kilku przykładowych wartości maski do raportu.
    report_lines: list[str] = [  # Lista linii formalnego opisu substytucji.
        "Formalny opis substytucji:",  # Nagłówek sekcji formalnej.
        "- Po wykonaniu permutacji generowana jest deterministyczna maska M zależna od klucza.",  # Opis źródła maski.
        "- Dla każdego kanału piksela stosowane jest równanie: y = (x + M) mod 256.",  # Formalny zapis działania substytucji.
        "- Algorytm odwrotny stosuje równanie: x = (y - M) mod 256.",  # Formalny zapis odwrotności substytucji.
        f"- Seed warstwy substytucji: {substitution_seed(key_text)}",  # Pokazanie deterministycznego seeda warstwy substytucji.
        f"- Rozmiar maski substytucji: {image_shape}",  # Informacja o rozmiarze wygenerowanej maski.
        f"- Przykładowe pierwsze wartości maski: {sample_values}",  # Kilka pierwszych wartości maski dla opisu algorytmu.
    ]  # Koniec listy linii formalnego opisu.
    return report_lines  # Zwrócenie gotowych linii raportu.


# ---- Raport: scrambling ----
def build_scramble_analysis_text(
    original_image: np.ndarray,
    scrambled_image: np.ndarray,
    correct_key_text: str,
    wrong_key_text: str,
    used_key_label: str,
) -> str:  # Budowa tekstu analizy po wykonaniu scramblingu Etapu 3.
    pixel_count: int = original_image.shape[0] * original_image.shape[1]  # Liczba pikseli po spłaszczeniu obrazu.
    original_correlation: dict[str, float] = adjacent_pixel_correlation(original_image)  # Korelacja sąsiednich pikseli przed scramblingiem.
    scrambled_correlation: dict[str, float] = adjacent_pixel_correlation(scrambled_image)  # Korelacja sąsiednich pikseli po scramblingu.
    report_lines: list[str] = [  # Lista linii raportu końcowego.
        "Wykonano scrambling dla Etapu 3.",  # Nagłówek raportu.
        f"Użyty klucz operacyjny: {used_key_label}.",  # Informacja o kluczu użytym w bieżącej operacji.
        "",  # Pusta linia dla czytelności.
        "Analiza eksperymentalna:",  # Sekcja analizy eksperymentalnej.
        "- Etap 3 łączy dwa mechanizmy: permutację pozycji pikseli oraz substytucję ich wartości.",  # Charakterystyka algorytmu.
        "- Utrata struktury obrazu jest większa niż w Etapie 2, ponieważ po permutacji zmieniane są także wartości pikseli.",  # Wniosek o strukturze obrazu.
        "- Odwracalność jest pełna dla poprawnego klucza, bo algorytm odwrotny najpierw cofa substytucję, a potem stosuje permutację odwrotną.",  # Wniosek o odwracalności.
        "- Wrażliwość na parametry jest większa niż w Etapie 2, ponieważ zmiana klucza wpływa jednocześnie na permutację i maskę substytucji.",  # Wniosek o parametrach.
        "",  # Pusta linia dla czytelności.
        "Obowiązkowe metryki, korelacja sąsiednich pikseli:",  # Sekcja obowiązkowych metryk.
        f"- Przed scramblingiem, pozioma: {_format_metric(original_correlation['horizontal'])}",  # Korelacja pozioma przed scramblingiem.
        f"- Przed scramblingiem, pionowa: {_format_metric(original_correlation['vertical'])}",  # Korelacja pionowa przed scramblingiem.
        f"- Po scramblingu, pozioma: {_format_metric(scrambled_correlation['horizontal'])}",  # Korelacja pozioma po scramblingu.
        f"- Po scramblingu, pionowa: {_format_metric(scrambled_correlation['vertical'])}",  # Korelacja pionowa po scramblingu.
    ]  # Koniec podstawowych linii raportu.

    report_lines.extend(["", *_formal_permutation_lines(pixel_count, correct_key_text)])  # Dopisanie formalnego opisu permutacji P oraz P^-1.
    report_lines.extend(["", *_formal_substitution_lines(scrambled_image.reshape(-1, scrambled_image.shape[2]).shape, correct_key_text)])  # Dopisanie formalnego opisu warstwy substytucji.

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
                "- Wniosek o efekcie lawinowym: Etap 3 jest bardziej wrażliwy na zmianę klucza niż Etap 2, bo klucz wpływa zarówno na pozycje, jak i na wartości pikseli.",  # Odpowiedź o efekcie lawinowym.
                "- Powód: zmiana klucza modyfikuje jednocześnie permutację indeksów i pseudolosową maskę dodawaną modulo 256.",  # Uzasadnienie odpowiedzi o efekcie lawinowym.
            ]
        )  # Koniec dopisywania sekcji wpływu klucza.
    else:  # Obsługa sytuacji, gdy nie podano obu kluczy.
        report_lines.extend(
            [
                "",  # Pusta linia dla czytelności.
                "Wpływ zmiany klucza na wynik:",  # Nagłówek sekcji wpływu klucza.
                "- Aby policzyć tę analizę, wpisz zarówno klucz poprawny, jak i klucz błędny.",  # Instrukcja dla użytkownika.
                "- Przykładowy test minimalnej zmiany klucza: klucz123 vs klucz124 albo zmiana jednego znaku.",  # Podpowiedź, jak wykonać test minimalnej zmiany klucza.
                "- Odpowiedź o efekcie lawinowym: Etap 3 daje silniejszy efekt wizualny niż Etap 2, bo zmienia zarówno pozycję, jak i wartości pikseli.",  # Odpowiedź o efekcie lawinowym bez pełnych danych liczbowych.
            ]
        )  # Koniec dopisywania informacji pomocniczej.

    report_lines.extend(
        [
            "",  # Pusta linia dla czytelności.
            "Porównanie Etapu 1, 2 i 3:",  # Nagłówek wymaganej sekcji porównawczej.
            "- Etap 1: mała utrata struktury obrazu, pełna odwracalność przy poprawnym kluczu, ograniczona wrażliwość na parametry.",  # Charakterystyka Etapu 1.
            "- Etap 2: większa utrata struktury obrazu niż w Etapie 1, pełna odwracalność przy poprawnym kluczu, wyższa wrażliwość na parametry.",  # Charakterystyka Etapu 2.
            "- Etap 3: największa utrata struktury obrazu spośród trzech etapów, pełna odwracalność przy poprawnym kluczu, najwyższa wrażliwość na parametry w tej implementacji.",  # Charakterystyka Etapu 3.
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
) -> str:  # Budowa tekstu analizy po wykonaniu unscramblingu Etapu 3.
    pixel_count: int = scrambled_image.shape[0] * scrambled_image.shape[1]  # Liczba pikseli po spłaszczeniu obrazu.
    report_lines: list[str] = [  # Lista linii raportu końcowego.
        "Wykonano unscrambling dla Etapu 3.",  # Nagłówek raportu.
        f"Użyty klucz operacyjny: {used_key_label}.",  # Informacja o kluczu użytym w bieżącej operacji.
        "",  # Pusta linia dla czytelności.
        "Zachowanie algorytmu przy błędnym kluczu:",  # Nagłówek sekcji związanej z błędnym kluczem.
        "- Dla poprawnego klucza obraz jest odtwarzany przez cofnięcie substytucji oraz zastosowanie permutacji odwrotnej.",  # Wniosek dla poprawnego klucza.
        "- Dla błędnego klucza używana jest inna maska substytucji i inna permutacja odwrotna, więc wynik pozostaje silnie zniekształcony.",  # Wniosek dla błędnego klucza.
    ]  # Koniec podstawowych linii raportu.

    if correct_key_text.strip():  # Sprawdzenie, czy dostępny jest poprawny klucz do formalnego opisu algorytmu.
        report_lines.extend(["", *_formal_permutation_lines(pixel_count, correct_key_text)])  # Dopisanie formalnego opisu P oraz P^-1.
        report_lines.extend(["", *_formal_substitution_lines(scrambled_image.reshape(-1, scrambled_image.shape[2]).shape, correct_key_text)])  # Dopisanie formalnego opisu warstwy substytucji.

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
