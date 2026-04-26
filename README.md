# Projekt-M---II-Chaotyczne-przekszta-canie-obrazu-cyfrowego

Cześć! To mój projekt na zaliczenie, w którym zrobiłem aplikację do **chaotycznego przekształcania obrazu cyfrowego**.

Projekt ma charakter **dydaktyczny**, a nie kryptograficzny. Chodziło o pokazanie w praktyce:
- różnicy między **permutacją** i **substytucją**,
- wpływu **klucza** na wynik,
- pełnej **odwracalności** algorytmów,
- oraz tego, że **wizualny chaos nie oznacza bezpieczeństwa**.

Aplikację napisałem w **Pythonie** z użyciem bibliotek **NumPy**, **OpenCV** oraz **PyQt**.

---

## Co robi ten projekt?

Program pozwala wczytać obraz i przekształcić go jednym z trzech etapów scramblingu:

### Etap 1 - Naiwny scrambling
Najprostsza wersja, oparta na **cyklicznych przesunięciach wierszy i kolumn** zależnych od klucza.

To etap celowo słaby, bo:
- nie zmienia wartości pikseli,
- zostawia część struktury obrazu,
- dobrze pokazuje ograniczenia prostych metod.

### Etap 2 - Czysta permutacja sterowana kluczem
W tej wersji obraz jest spłaszczany do listy pikseli, a potem przestawiany przez **deterministyczną permutację** zależną od klucza.

Permutacja jest budowana jawnym algorytmem **Fishera-Yatesa**, a odwracanie działa przez permutację odwrotną **P^-1**.

### Etap 3 - Mechanizm wzmacniający
Najmocniejszy etap w projekcie.

Tutaj połączyłem:
- **permutację pozycji pikseli**,
- oraz **substytucję wartości pikseli**.

Po permutacji do pikseli dodawana jest pseudolosowa maska **modulo 256**, zależna od klucza. Przy odwracaniu najpierw cofana jest substytucja, a potem permutacja odwrotna.

---

## Funkcje programu

Interfejs graficzny pozwala na:
- wczytanie obrazu **PNG / JPEG / BMP**,
- wybór **Etapu 1 / 2 / 3**,
- wpisanie **klucza poprawnego** i **klucza błędnego**,
- wykonanie operacji **Scramble**,
- wykonanie operacji **Unscramble**,
- jednoczesne wyświetlenie:
  - obrazu oryginalnego,
  - obrazu przekształconego,
  - obrazu odtworzonego,
- szybkie przełączanie między poprawnym i błędnym kluczem,
- zapis wyniku jako:
  - obraz,
  - metryki,
- eksport metryk do **JSON** lub **CSV**,
- reset całego interfejsu.

Dodatkowo cięższe operacje działają w tle, żeby GUI nie zawieszało się przy większych obrazach.

---

## Analiza i metryki

Program nie tylko przekształca obraz, ale też liczy wymagane metryki.

W projekcie uwzględniłem:
- **korelację sąsiednich pikseli** przed i po scramblingu,
- **różnicę obrazu przy unscramblingu błędnym kluczem**,
- wpływ zmiany klucza na wynik,
- porównanie Etapu 1, 2 i 3 pod kątem:
  - utraty struktury obrazu,
  - odwracalności,
  - wrażliwości na parametry.

---

## Technologie

- **Python** - główny język projektu,
- **NumPy** - operacje na tablicach i pikselach,
- **OpenCV** - wczytywanie, zapis i konwersja obrazów,
- **PyQt** - interfejs graficzny użytkownika.

---

## Jak uruchomić?

1. Pobierz pliki projektu.
2. Upewnij się, że masz zainstalowanego Pythona 3.
3. Zainstaluj wymagane biblioteki:
   - `numpy`
   - `opencv-python`
   - `PyQt6`
4. Uruchom plik `gui.py`.

Przykładowo:

```bash
python gui.py
```

---

## Najważniejszy wniosek

Ten projekt pokazuje, że obraz może wyglądać na bardzo „chaotyczny”, ale to jeszcze nie znaczy, że metoda jest bezpiecznym szyfrem.

Etap 1, 2 i 3 dobrze pokazują rosnącą siłę ukrywania obrazu, ale cały projekt należy traktować jako **eksperyment dydaktyczny**, a nie gotowy system kryptograficzny.
