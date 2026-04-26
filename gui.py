# ---- Moduł / dokumentacja ----
"""PyQt GUI skeleton for the M-II project."""  # Module docstring describing this file.

# ---- Importy ----
from __future__ import annotations  # Allow postponed evaluation of type hints.

import csv  # Import csv for exporting metrics in table form.
import json  # Import json for exporting metrics in structured form.
import sys  # Import sys to access command-line arguments and app exit handling.
import threading  # Import threading to run heavy non-GUI work in background threads.
from pathlib import Path  # Import Path for safe filesystem paths.

import cv2  # Import OpenCV as the image-processing library required by the project.
import numpy as np  # Import NumPy as the array-processing library required by the project.
from stage1 import scramble_image as stage1_scramble  # Import Stage 1 scrambling algorithm.
from stage1 import stage1_description  # Import Stage 1 description for the metrics panel.
from stage1 import unscramble_image as stage1_unscramble  # Import Stage 1 unscrambling algorithm.
from stage1_analysis import build_scramble_analysis_text  # Import Stage 1 experimental analysis for scrambling.
from stage1_analysis import build_unscramble_analysis_text  # Import Stage 1 experimental analysis for unscrambling.
from stage2 import scramble_image as stage2_scramble  # Import Stage 2 scrambling algorithm.
from stage2 import stage2_description  # Import Stage 2 description for the metrics panel.
from stage2 import unscramble_image as stage2_unscramble  # Import Stage 2 unscrambling algorithm.
from stage3 import scramble_image as stage3_scramble  # Import Stage 3 scrambling algorithm.
from stage3 import stage3_description  # Import Stage 3 description for the metrics panel.
from stage3 import unscramble_image as stage3_unscramble  # Import Stage 3 unscrambling algorithm.
from stage3_analysis import build_scramble_analysis_text as build_stage3_scramble_analysis_text  # Import raportu analizy po scramblingu Etapu 3.
from stage3_analysis import build_unscramble_analysis_text as build_stage3_unscramble_analysis_text  # Import raportu analizy po unscramblingu Etapu 3.
from stage2_analysis import build_scramble_analysis_text as build_stage2_scramble_analysis_text  # Import raportu analizy po scramblingu Etapu 2.
from stage2_analysis import build_unscramble_analysis_text as build_stage2_unscramble_analysis_text  # Import raportu analizy po unscramblingu Etapu 2.
from stage1_analysis import build_scramble_analysis_text  # Import raportu analizy po scramblingu Etapu 1.
from stage1_analysis import build_unscramble_analysis_text  # Import raportu analizy po unscramblingu Etapu 1.

from PyQt6.QtCore import QObject  # Import QObject for defining a bridge object with Qt signals.
from PyQt6.QtCore import Qt  # Import Qt alignment and scaling flags.
from PyQt6.QtCore import pyqtSignal  # Import pyqtSignal for safely returning worker results to the GUI thread.
from PyQt6.QtGui import QImage  # Import QImage for converting arrays to Qt images.
from PyQt6.QtGui import QPixmap  # Import QPixmap for displaying images in labels.
from PyQt6.QtWidgets import QApplication  # Import the main Qt application object.
from PyQt6.QtWidgets import QButtonGroup  # Import a helper for grouping radio buttons.
from PyQt6.QtWidgets import QCheckBox  # Import checkbox widget.
from PyQt6.QtWidgets import QFrame  # Import frame widget for bordered areas.
from PyQt6.QtWidgets import QGroupBox  # Import group box widget for logical sections.
from PyQt6.QtWidgets import QHBoxLayout  # Import horizontal layout manager.
from PyQt6.QtWidgets import QFileDialog  # Import file-save dialog widget.
from PyQt6.QtWidgets import QInputDialog  # Import simple selection dialog widget.
from PyQt6.QtWidgets import QLabel  # Import label widget.
from PyQt6.QtWidgets import QLineEdit  # Import single-line text input widget.
from PyQt6.QtWidgets import QMainWindow  # Import the main window base class.
from PyQt6.QtWidgets import QMessageBox  # Import message boxes for user feedback.
from PyQt6.QtWidgets import QPushButton  # Import push button widget.
from PyQt6.QtWidgets import QPlainTextEdit  # Import plain text area widget.
from PyQt6.QtWidgets import QRadioButton  # Import radio button widget.
from PyQt6.QtWidgets import QSizePolicy  # Import size policy helper.
from PyQt6.QtWidgets import QVBoxLayout  # Import vertical layout manager.
from PyQt6.QtWidgets import QWidget  # Import generic Qt widget base class.

# ---- Klasa pomocnicza: podgląd obrazu ----
class ImagePreviewLabel(QLabel):  # Define a reusable preview label for image panels.
    """Simple preview widget with placeholder text and optional image support."""  # Class docstring.

    def __init__(self, title_text: str) -> None:  # Initialize the preview widget.
        super().__init__()  # Call the QLabel constructor.
        self.title_text: str = title_text  # Store the title or placeholder meaning for this preview.
        self.current_pixmap: QPixmap | None = None  # Store the currently displayed pixmap.
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center image and text inside the label.
        self.setMinimumSize(320, 240)  # Set a minimum preview size.
        self.setFrameShape(QFrame.Shape.Box)  # Draw a visible box around the preview.
        self.setStyleSheet("background-color: #f0f0f0; color: #555555; font-size: 14px;")  # Apply simple placeholder styling.
        self.setText("Brak obrazu")  # Show initial placeholder text.

    def set_placeholder(self, placeholder_text: str = "Brak obrazu") -> None:  # Show placeholder text instead of an image.
        self.current_pixmap = None  # Clear any stored pixmap.
        self.setPixmap(QPixmap())  # Remove any image from the label.
        self.setText(placeholder_text)  # Display placeholder text.

    def set_numpy_image(self, image_array: np.ndarray) -> None:  # Convert a NumPy/OpenCV image into a visible Qt pixmap.
        if image_array.ndim != 3:  # Ensure the image has height, width, and channels.
            self.set_placeholder("Nieprawidłowy obraz")  # Show fallback text when shape is invalid.
            return  # Stop processing invalid data.
        if image_array.shape[2] != 3:  # Ensure the image has exactly three color channels.
            self.set_placeholder("Nieobsługiwany format")  # Show fallback text when channel count is unsupported.
            return  # Stop processing invalid data.
        rgb_image: np.ndarray = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)  # Convert the OpenCV BGR image to RGB for Qt.
        image_height: int = rgb_image.shape[0]  # Read image height from the array.
        image_width: int = rgb_image.shape[1]  # Read image width from the array.
        bytes_per_line: int = image_width * 3  # Compute the number of bytes used by one image row.
        qt_image: QImage = QImage(  # Create a Qt image that wraps the NumPy array data.
            rgb_image.data,  # Provide the raw image buffer.
            image_width,  # Provide the width.
            image_height,  # Provide the height.
            bytes_per_line,  # Provide the row stride.
            QImage.Format.Format_RGB888,  # Tell Qt that the data is 8-bit RGB.
        ).copy()  # Copy the image so Qt owns its own memory safely.
        pixmap: QPixmap = QPixmap.fromImage(qt_image)  # Convert the Qt image into a pixmap for display.
        self.current_pixmap = pixmap  # Store the pixmap for future rescaling.
        self._apply_scaled_pixmap()  # Scale and display the pixmap inside the label.

    def resizeEvent(self, event) -> None:  # React whenever the preview widget changes size.
        super().resizeEvent(event)  # Let QLabel handle its own resize logic first.
        self._apply_scaled_pixmap()  # Re-apply scaling so the image fits the new size.

    def _apply_scaled_pixmap(self) -> None:  # Scale the current pixmap to fit the preview area.
        if self.current_pixmap is None:  # Check whether there is an image to display.
            return  # Stop if there is no pixmap yet.
        scaled_pixmap: QPixmap = self.current_pixmap.scaled(  # Create a scaled copy of the pixmap.
            self.size(),  # Use the current label size as the target area.
            Qt.AspectRatioMode.KeepAspectRatio,  # Preserve the image aspect ratio.
            Qt.TransformationMode.SmoothTransformation,  # Use smoother scaling quality.
        )  # Finish creating the scaled pixmap.
        self.setText("")  # Remove placeholder text while an image is visible.
        self.setPixmap(scaled_pixmap)  # Display the scaled pixmap.


# ---- Klasa pomocnicza: most dla wyników z wątków ----
class BackgroundTaskBridge(QObject):  # Define a Qt bridge for thread-safe communication back to the GUI.
    success_signal = pyqtSignal(object, object)  # Signal carrying the success callback and the computed result.
    error_signal = pyqtSignal(str, object)  # Signal carrying the task name and the raised exception.


# ---- Główna klasa GUI ----
class ProjectGui(QMainWindow):  # Define the main application window.
    """Main PyQt GUI skeleton for the project."""  # Class docstring.

    def __init__(self) -> None:  # Initialize the main window and all widgets.
        super().__init__()  # Call the QMainWindow constructor.
        self.base_dir: Path = Path(__file__).resolve().parent  # Store the folder containing this file.
        self.logo_path: Path = self.base_dir / "filia_uwb_logo.png"  # Build the path to the university logo.
        self.original_image: np.ndarray | None = None  # Reserve storage for the future original image.
        self.scrambled_image: np.ndarray | None = None  # Reserve storage for the future transformed image.
        self.restored_image: np.ndarray | None = None  # Reserve storage for the future restored image.
        self.is_busy: bool = False  # Store whether a background task is currently running.
        self.current_task_name: str = ""  # Store the human-readable name of the current background task.
        self.background_bridge: BackgroundTaskBridge = BackgroundTaskBridge()  # Create the Qt bridge used for background-thread results.
        self.setWindowTitle("M-II Projekt - GUI Skeleton")  # Set the main window title.
        self.resize(1350, 850)  # Set a comfortable default window size.
        self._build_ui()  # Build the whole user interface.
        self._connect_signals()  # Connect button actions to their handlers.

    def _build_ui(self) -> None:  # Create and arrange all interface sections.
        central_widget: QWidget = QWidget()  # Create the central widget used by QMainWindow.
        self.setCentralWidget(central_widget)  # Attach the central widget to the main window.
        root_layout: QVBoxLayout = QVBoxLayout(central_widget)  # Create the top-level vertical layout.
        root_layout.setContentsMargins(12, 12, 12, 12)  # Set outer margins around the interface.
        root_layout.setSpacing(12)  # Set spacing between major sections.

        header_layout: QHBoxLayout = QHBoxLayout()  # Create the top header layout.
        header_layout.setSpacing(14)  # Set spacing between header elements.
        root_layout.addLayout(header_layout)  # Add the header layout to the window.

        logo_label: QLabel = QLabel()  # Create a label for the university logo.
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Keep the logo aligned to the upper-left area.
        logo_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)  # Prevent the logo from stretching unnecessarily.
        self._load_logo_into_label(logo_label)  # Load the logo into the header label.
        header_layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Put the logo in the left upper corner.

        title_layout: QVBoxLayout = QVBoxLayout()  # Create a vertical layout for title texts.
        header_layout.addLayout(title_layout, 1)  # Add the title layout next to the logo.

        title_label: QLabel = QLabel("Projekt M-II: Chaotyczne przekształcanie obrazu cyfrowego")  # Create the main title label.
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")  # Make the title visually prominent.
        title_layout.addWidget(title_label)  # Add the title label to the title layout.

        subtitle_label: QLabel = QLabel("Szkielet GUI przygotowany w technologii NumPy + OpenCV + PyQt.")  # Create the subtitle label.
        subtitle_label.setStyleSheet("font-size: 12px; color: #444444;")  # Apply smaller subtitle styling.
        title_layout.addWidget(subtitle_label)  # Add the subtitle label below the title.
        title_layout.addStretch(1)  # Push title content upward when space grows.

        content_layout: QHBoxLayout = QHBoxLayout()  # Create the main content layout.
        content_layout.setSpacing(12)  # Set spacing between left and right panels.
        root_layout.addLayout(content_layout, 1)  # Add the content layout and let it expand.

        controls_group: QGroupBox = QGroupBox("Sterowanie")  # Create the left control panel group.
        controls_group.setMinimumWidth(320)  # Keep enough width for form controls.
        controls_layout: QVBoxLayout = QVBoxLayout(controls_group)  # Create a vertical layout inside the control panel.
        controls_layout.setSpacing(10)  # Set spacing between controls.
        content_layout.addWidget(controls_group, 0)  # Add the control panel on the left.

        self.load_button: QPushButton = QPushButton("Wczytaj obraz")  # Create the future load-image button.
        controls_layout.addWidget(self.load_button)  # Add the load button to the control panel.

        stage_group: QGroupBox = QGroupBox("Wybór etapu")  # Create the stage selection group box.
        stage_layout: QVBoxLayout = QVBoxLayout(stage_group)  # Create a vertical layout for stage radio buttons.
        self.stage_button_group: QButtonGroup = QButtonGroup(self)  # Create a button group to keep radio buttons exclusive.
        self.stage1_radio: QRadioButton = QRadioButton("Etap 1")  # Create the Stage 1 radio button.
        self.stage2_radio: QRadioButton = QRadioButton("Etap 2")  # Create the Stage 2 radio button.
        self.stage3_radio: QRadioButton = QRadioButton("Etap 3")  # Create the Stage 3 radio button.
        self.stage1_radio.setChecked(True)  # Select Stage 1 by default.
        self.stage_button_group.addButton(self.stage1_radio, 1)  # Register the Stage 1 radio button in the group.
        self.stage_button_group.addButton(self.stage2_radio, 2)  # Register the Stage 2 radio button in the group.
        self.stage_button_group.addButton(self.stage3_radio, 3)  # Register the Stage 3 radio button in the group.
        stage_layout.addWidget(self.stage1_radio)  # Add the Stage 1 option to the layout.
        stage_layout.addWidget(self.stage2_radio)  # Add the Stage 2 option to the layout.
        stage_layout.addWidget(self.stage3_radio)  # Add the Stage 3 option to the layout.
        controls_layout.addWidget(stage_group)  # Add the stage selection group to the control panel.

        correct_key_label: QLabel = QLabel("Klucz poprawny:")  # Create the label for the correct key field.
        controls_layout.addWidget(correct_key_label)  # Add the correct-key label.

        self.correct_key_input: QLineEdit = QLineEdit()  # Create the correct-key input field.
        self.correct_key_input.setPlaceholderText("Wpisz poprawny klucz")  # Add placeholder help text.
        controls_layout.addWidget(self.correct_key_input)  # Add the correct-key input field.

        wrong_key_label: QLabel = QLabel("Klucz błędny:")  # Create the label for the wrong key field.
        controls_layout.addWidget(wrong_key_label)  # Add the wrong-key label.

        self.wrong_key_input: QLineEdit = QLineEdit()  # Create the wrong-key input field.
        self.wrong_key_input.setPlaceholderText("Wpisz błędny klucz")  # Add placeholder help text.
        controls_layout.addWidget(self.wrong_key_input)  # Add the wrong-key input field.

        self.use_wrong_key_checkbox: QCheckBox = QCheckBox("Użyj błędnego klucza")  # Create the wrong-key toggle checkbox.
        controls_layout.addWidget(self.use_wrong_key_checkbox)  # Add the checkbox to the control panel.

        self.scramble_button: QPushButton = QPushButton("Scramble")  # Create the future scramble button.
        controls_layout.addWidget(self.scramble_button)  # Add the scramble button.

        self.unscramble_button: QPushButton = QPushButton("Unscramble")  # Create the future unscramble button.
        controls_layout.addWidget(self.unscramble_button)  # Add the unscramble button.

        self.reset_button: QPushButton = QPushButton("Reset")  # Create the reset button clearing the current experiment state.
        controls_layout.addWidget(self.reset_button)  # Add the reset button to the control panel.

        self.save_button: QPushButton = QPushButton("Zapisz wynik")  # Create the future save-results button.
        controls_layout.addWidget(self.save_button)  # Add the save-results button.
        controls_layout.addStretch(1)  # Push the controls upward and leave free space below.

        right_panel_layout: QVBoxLayout = QVBoxLayout()  # Create the right-side layout for previews and metrics.
        content_layout.addLayout(right_panel_layout, 1)  # Add the right panel and let it expand.

        previews_group: QGroupBox = QGroupBox("Podgląd")  # Create the preview section group box.
        previews_layout: QHBoxLayout = QHBoxLayout(previews_group)  # Create a horizontal layout for three preview columns.
        previews_layout.setSpacing(12)  # Set spacing between preview columns.
        right_panel_layout.addWidget(previews_group, 1)  # Add the preview group to the right panel.

        original_column: QVBoxLayout = QVBoxLayout()  # Create the layout for the original-image column.
        scrambled_column: QVBoxLayout = QVBoxLayout()  # Create the layout for the transformed-image column.
        restored_column: QVBoxLayout = QVBoxLayout()  # Create the layout for the restored-image column.
        previews_layout.addLayout(original_column, 1)  # Add the original-image column.
        previews_layout.addLayout(scrambled_column, 1)  # Add the transformed-image column.
        previews_layout.addLayout(restored_column, 1)  # Add the restored-image column.

        original_title: QLabel = QLabel("Obraz oryginalny")  # Create the original preview title label.
        original_title.setStyleSheet("font-weight: bold;")  # Make the title bold.
        original_column.addWidget(original_title)  # Add the title to the original column.

        self.original_preview: ImagePreviewLabel = ImagePreviewLabel("Obraz oryginalny")  # Create the original preview widget.
        original_column.addWidget(self.original_preview, 1)  # Add the original preview widget.

        scrambled_title: QLabel = QLabel("Obraz przekształcony")  # Create the transformed preview title label.
        scrambled_title.setStyleSheet("font-weight: bold;")  # Make the title bold.
        scrambled_column.addWidget(scrambled_title)  # Add the title to the transformed column.

        self.scrambled_preview: ImagePreviewLabel = ImagePreviewLabel("Obraz przekształcony")  # Create the transformed preview widget.
        scrambled_column.addWidget(self.scrambled_preview, 1)  # Add the transformed preview widget.

        restored_title: QLabel = QLabel("Obraz odtworzony")  # Create the restored preview title label.
        restored_title.setStyleSheet("font-weight: bold;")  # Make the title bold.
        restored_column.addWidget(restored_title)  # Add the title to the restored column.

        self.restored_preview: ImagePreviewLabel = ImagePreviewLabel("Obraz odtworzony")  # Create the restored preview widget.
        restored_column.addWidget(self.restored_preview, 1)  # Add the restored preview widget.

        metrics_group: QGroupBox = QGroupBox("Metryki i analiza")  # Create the metrics section group box.
        metrics_layout: QVBoxLayout = QVBoxLayout(metrics_group)  # Create a vertical layout for the metrics area.
        right_panel_layout.addWidget(metrics_group, 0)  # Add the metrics group below the previews.

        self.metrics_box: QPlainTextEdit = QPlainTextEdit()  # Create the metrics text area.
        self.metrics_box.setReadOnly(True)  # Make the metrics area read-only for now.
        self.metrics_box.setPlainText(self._default_metrics_text())  # Insert the default placeholder text for the analysis area.
        metrics_layout.addWidget(self.metrics_box)  # Add the metrics text area to the metrics section.

    def _connect_signals(self) -> None:  # Connect widget signals to their action handlers.
        self.load_button.clicked.connect(self._load_image)  # Load an image from disk.
        self.scramble_button.clicked.connect(self._run_scramble)  # Run the selected scrambling stage.
        self.unscramble_button.clicked.connect(self._run_unscramble)  # Run the selected unscrambling stage.
        self.reset_button.clicked.connect(self._reset_interface)  # Reset the experiment state in the GUI.
        self.save_button.clicked.connect(self._save_selected_image)  # Handle saving one of the available images.
        self.background_bridge.success_signal.connect(self._handle_background_success)  # Connect worker success results back to the GUI thread.
        self.background_bridge.error_signal.connect(self._handle_background_error)  # Connect worker errors back to the GUI thread.

    def _set_busy_state(self, is_busy: bool, task_name: str = "") -> None:  # Aktualizacja stanu zajętości interfejsu podczas pracy w tle.
        self.is_busy = is_busy  # Zapisanie nowego stanu zajętości aplikacji.
        self.current_task_name = task_name if is_busy else ""  # Zapisanie nazwy zadania tylko wtedy, gdy aplikacja jest zajęta.
        self.load_button.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie przycisku wczytywania obrazu.
        self.scramble_button.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie przycisku scramblingu.
        self.unscramble_button.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie przycisku unscramblingu.
        self.reset_button.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie przycisku resetu.
        self.save_button.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie przycisku zapisu wyniku.
        self.stage1_radio.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie wyboru Etapu 1.
        self.stage2_radio.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie wyboru Etapu 2.
        self.stage3_radio.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie wyboru Etapu 3.
        self.correct_key_input.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie pola poprawnego klucza.
        self.wrong_key_input.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie pola błędnego klucza.
        self.use_wrong_key_checkbox.setEnabled(not is_busy)  # Zablokowanie lub odblokowanie checkboxa błędnego klucza.
        if is_busy:  # Sprawdzenie, czy przechodzimy do stanu zajętości.
            self.metrics_box.setPlainText(f"Trwa operacja: {task_name}.\nProszę czekać...")  # Wyświetlenie komunikatu o pracy w tle.

    def _run_in_background(self, task_name: str, worker, on_success) -> None:  # Uruchomienie ciężkiej operacji poza wątkiem GUI.
        if self.is_busy:  # Sprawdzenie, czy inna operacja jest już uruchomiona.
            QMessageBox.information(self, "Operacja w toku", f"Najpierw zaczekaj na zakończenie: {self.current_task_name}.")  # Komunikat o już trwającym zadaniu.
            return  # Zakończenie funkcji bez uruchamiania kolejnego zadania.
        self._set_busy_state(True, task_name)  # Ustawienie GUI w tryb zajętości.

        def background_runner() -> None:  # Funkcja wykonywana w osobnym wątku roboczym.
            try:  # Rozpoczęcie obsługi potencjalnych wyjątków w wątku roboczym.
                result = worker()  # Wykonanie ciężkiej operacji poza wątkiem GUI.
            except Exception as error:  # Przechwycenie błędu zgłoszonego przez wątek roboczy.
                self.background_bridge.error_signal.emit(task_name, error)  # Przekazanie błędu z powrotem do wątku GUI przez sygnał Qt.
                return  # Zakończenie pracy wątku po błędzie.
            self.background_bridge.success_signal.emit(on_success, result)  # Przekazanie wyniku z powrotem do wątku GUI przez sygnał Qt.

        worker_thread: threading.Thread = threading.Thread(target=background_runner, daemon=True)  # Utworzenie wątku roboczego działającego w tle.
        worker_thread.start()  # Uruchomienie pracy wątku roboczego.

    def _handle_background_success(self, on_success, result) -> None:  # Obsługa poprawnego zakończenia zadania w tle.
        self._set_busy_state(False)  # Przywrócenie aktywności interfejsu po zakończeniu zadania.
        on_success(result)  # Wywołanie funkcji aktualizującej GUI gotowym wynikiem.

    def _handle_background_error(self, task_name: str, error: Exception) -> None:  # Obsługa błędu zgłoszonego przez zadanie w tle.
        self._set_busy_state(False)  # Przywrócenie aktywności interfejsu po błędzie zadania.
        QMessageBox.critical(self, "Błąd operacji", f"Operacja '{task_name}' zakończyła się błędem:\n{error}")  # Wyświetlenie komunikatu o błędzie zadania.

    # ---- Wczytywanie obrazów ----
    def _load_image(self) -> None:  # Wczytanie obrazu i przypisanie go do wybranego pola podglądu.
        if self.is_busy:  # Sprawdzenie, czy aplikacja nie wykonuje już innej operacji w tle.
            QMessageBox.information(self, "Operacja w toku", f"Najpierw zaczekaj na zakończenie: {self.current_task_name}.")  # Komunikat o zajętości aplikacji.
            return  # Zakończenie funkcji bez rozpoczynania nowego zadania.
        target_options: list[str] = [  # Lista typów obrazów, które użytkownik może wczytać.
            "Obraz oryginalny",  # Opcja wczytania obrazu źródłowego.
            "Obraz przekształcony",  # Opcja wczytania obrazu po scramblingu.
            "Obraz odtworzony",  # Opcja wczytania obrazu już odtworzonego.
        ]  # Koniec listy opcji.
        selected_target, accepted = QInputDialog.getItem(  # Okno wyboru typu obrazu do wczytania.
            self,  # Rodzic okna dialogowego.
            "Wczytaj obraz",  # Tytuł okna dialogowego.
            "Wybierz typ obrazu do wczytania:",  # Treść pytania dla użytkownika.
            target_options,  # Dostępne opcje wyboru.
            0,  # Domyślnie zaznaczona pierwsza opcja.
            False,  # Brak możliwości wpisania własnej wartości.
        )  # Koniec wywołania okna wyboru.
        if not accepted:  # Sprawdzenie, czy użytkownik zatwierdził wybór.
            return  # Zakończenie funkcji po anulowaniu.

        file_path, _ = QFileDialog.getOpenFileName(  # Okno wyboru pliku obrazu.
            self,  # Rodzic okna dialogowego.
            "Wczytaj obraz",  # Tytuł okna wyboru pliku.
            str(self.base_dir),  # Domyślny katalog startowy.
            "Pliki obrazów (*.png *.jpg *.jpeg *.bmp);;Wszystkie pliki (*)",  # Obsługiwane formaty obrazów.
        )  # Koniec wywołania okna wyboru pliku.
        if not file_path:  # Sprawdzenie, czy użytkownik wybrał plik.
            return  # Zakończenie funkcji po anulowaniu.
        selected_path: Path = Path(file_path)  # Zamiana ścieżki pliku na obiekt Path dla wygodniejszej pracy.
        self._run_in_background(  # Uruchomienie wczytywania obrazu poza wątkiem GUI.
            "wczytywanie obrazu",  # Nazwa zadania pokazywana użytkownikowi.
            lambda: self._load_image_worker(selected_path),  # Funkcja robocza wykonująca odczyt pliku obrazu.
            lambda loaded_image, selected_target=selected_target, selected_path=selected_path: self._finish_load_image(selected_target, selected_path, loaded_image),  # Funkcja kończąca aktualizację GUI po wczytaniu obrazu.
        )  # Koniec uruchamiania zadania w tle.

    def _load_image_worker(self, image_path: Path) -> np.ndarray:  # Wczytanie obrazu z dysku w wątku roboczym.
        loaded_image: np.ndarray | None = cv2.imread(str(image_path), cv2.IMREAD_COLOR)  # Wczytanie obrazu z dysku w trybie kolorowym.
        if loaded_image is None:  # Sprawdzenie, czy plik został poprawnie odczytany jako obraz.
            raise ValueError("Nie udało się wczytać wybranego obrazu.")  # Zgłoszenie błędu do obsługi w wątku GUI.
        return loaded_image  # Zwrócenie poprawnie wczytanego obrazu.

    def _finish_load_image(self, target_label: str, image_path: Path, loaded_image: np.ndarray) -> None:  # Zakończenie obsługi wczytania obrazu w wątku GUI.
        self._assign_loaded_image(target_label, loaded_image)  # Przypisanie wczytanego obrazu do wybranego miejsca w aplikacji.
        self.metrics_box.setPlainText(  # Aktualizacja pola analizy po wczytaniu obrazu.
            f"Wczytano plik: {image_path.name}\n"  # Nazwa wczytanego pliku.
            f"Typ obrazu: {target_label}\n"  # Informacja, do którego pola przypisano obraz.
            f"Rozdzielczość: {loaded_image.shape[1]} x {loaded_image.shape[0]} px\n\n"  # Rozdzielczość obrazu.
            f"{self._current_stage_description()}"  # Opis działania aktualnie wybranego etapu.
        )  # Koniec ustawiania tekstu analizy.

    def _assign_loaded_image(self, target_label: str, loaded_image: np.ndarray) -> None:  # Przypisanie wczytanego obrazu do odpowiedniego slotu w GUI.
        if target_label == "Obraz oryginalny":  # Sprawdzenie, czy użytkownik wybrał obraz oryginalny.
            self.original_image = loaded_image  # Zapisanie obrazu jako obrazu wejściowego.
            self.scrambled_image = None  # Wyczyszczenie starego obrazu przekształconego.
            self.restored_image = None  # Wyczyszczenie starego obrazu odtworzonego.
            self.original_preview.set_numpy_image(self.original_image)  # Aktualizacja podglądu obrazu oryginalnego.
            self.scrambled_preview.set_placeholder("Brak obrazu przekształconego")  # Wyzerowanie podglądu obrazu przekształconego.
            self.restored_preview.set_placeholder("Brak obrazu odtworzonego")  # Wyzerowanie podglądu obrazu odtworzonego.
            return  # Zakończenie obsługi dla obrazu oryginalnego.

        if target_label == "Obraz przekształcony":  # Sprawdzenie, czy użytkownik wybrał obraz przekształcony.
            self.scrambled_image = loaded_image  # Zapisanie obrazu jako wejścia do późniejszego unscramble.
            self.restored_image = None  # Wyczyszczenie poprzedniego obrazu odtworzonego.
            self.scrambled_preview.set_numpy_image(self.scrambled_image)  # Aktualizacja podglądu obrazu przekształconego.
            self.restored_preview.set_placeholder("Brak obrazu odtworzonego")  # Wyzerowanie podglądu obrazu odtworzonego.
            return  # Zakończenie obsługi dla obrazu przekształconego.

        self.restored_image = loaded_image  # Zapisanie obrazu jako obrazu odtworzonego.
        self.restored_preview.set_numpy_image(self.restored_image)  # Aktualizacja podglądu obrazu odtworzonego.

    # ---- Operacje Etapu 1 ----
    def _run_scramble(self) -> None:  # Wykonanie scramblingu dla aktualnie wybranego etapu.
        if self.original_image is None:  # Sprawdzenie, czy istnieje obraz wejściowy.
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz wejściowy.")  # Komunikat o braku obrazu wejściowego.
            return  # Zakończenie funkcji bez scramblingu.

        selected_stage: int = self._selected_stage()  # Pobranie numeru aktualnie wybranego etapu.
        if selected_stage not in (1, 2, 3):  # Sprawdzenie, czy użytkownik wybrał obsługiwany etap.
            QMessageBox.information(self, "Etap niedostępny", "Obecnie zaimplementowane są Etap 1, Etap 2 i Etap 3.")  # Informacja o braku innych etapów.
            return  # Zakończenie funkcji dla nieobsługiwanego etapu.
        original_image: np.ndarray = self.original_image.copy()  # Utworzenie kopii obrazu wejściowego do pracy w tle.
        correct_key_text: str = self.correct_key_input.text()  # Pobranie tekstu poprawnego klucza w wątku GUI.
        wrong_key_text: str = self.wrong_key_input.text()  # Pobranie tekstu błędnego klucza w wątku GUI.
        used_key_label: str = self._active_key_label()  # Pobranie etykiety aktywnego klucza w wątku GUI.
        key_text: str = self._active_key_text()  # Pobranie aktywnego klucza w wątku GUI.
        self._run_in_background(  # Uruchomienie scramblingu poza wątkiem GUI.
            "scrambling",  # Nazwa zadania pokazywana użytkownikowi.
            lambda: self._scramble_worker(selected_stage, original_image, key_text, correct_key_text, wrong_key_text, used_key_label),  # Funkcja robocza wykonująca scrambling i analizę.
            self._finish_scramble,  # Funkcja kończąca aktualizację GUI po scramblingu.
        )  # Koniec uruchamiania zadania w tle.

    def _scramble_worker(self, selected_stage: int, original_image: np.ndarray, key_text: str, correct_key_text: str, wrong_key_text: str, used_key_label: str) -> dict[str, object]:  # Wykonanie scramblingu i analizy w wątku roboczym.
        if selected_stage == 1:  # Sprawdzenie, czy aktywny jest Etap 1.
            scrambled_image: np.ndarray = stage1_scramble(original_image, key_text)  # Wykonanie scramblingu Etapu 1.
            analysis_text: str = build_scramble_analysis_text(original_image, scrambled_image, correct_key_text, wrong_key_text, used_key_label)  # Zbudowanie raportu analitycznego dla Etapu 1.
        elif selected_stage == 2:  # Sprawdzenie, czy aktywny jest Etap 2.
            scrambled_image = stage2_scramble(original_image, key_text)  # Wykonanie scramblingu Etapu 2.
            analysis_text = build_stage2_scramble_analysis_text(original_image, scrambled_image, correct_key_text, wrong_key_text, used_key_label)  # Zbudowanie raportu analitycznego dla Etapu 2.
        else:  # Obsługa Etapu 3.
            scrambled_image = stage3_scramble(original_image, key_text)  # Wykonanie scramblingu Etapu 3.
            analysis_text = build_stage3_scramble_analysis_text(original_image, scrambled_image, correct_key_text, wrong_key_text, used_key_label)  # Zbudowanie raportu analitycznego dla Etapu 3.
        return {"scrambled_image": scrambled_image, "analysis_text": analysis_text}  # Zwrócenie wyniku obliczeń do wątku GUI.

    def _finish_scramble(self, result: dict[str, object]) -> None:  # Aktualizacja GUI po zakończeniu scramblingu w tle.
        scrambled_image: np.ndarray = result["scrambled_image"]  # Pobranie obrazu po scramblingu z wyniku zadania.
        analysis_text: str = result["analysis_text"]  # Pobranie raportu analitycznego z wyniku zadania.
        self.scrambled_image = scrambled_image  # Zapisanie obrazu przekształconego w stanie aplikacji.
        self.scrambled_preview.set_numpy_image(self.scrambled_image)  # Aktualizacja podglądu obrazu przekształconego.
        self.restored_image = None  # Wyczyszczenie starego obrazu odtworzonego.
        self.restored_preview.set_placeholder("Brak obrazu odtworzonego")  # Wyzerowanie podglądu obrazu odtworzonego.
        self.metrics_box.setPlainText(analysis_text)  # Wyświetlenie raportu analitycznego po scramblingu.

    def _run_unscramble(self) -> None:  # Wykonanie odwrotnej transformacji dla aktualnie wybranego etapu.
        if self.scrambled_image is None:  # Sprawdzenie, czy istnieje obraz przekształcony do odtworzenia.
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wykonaj scrambling obrazu albo wczytaj obraz przekształcony.")  # Komunikat o braku obrazu wejściowego do unscramblingu.
            return  # Zakończenie funkcji bez odtwarzania.

        selected_stage: int = self._selected_stage()  # Pobranie numeru aktualnie wybranego etapu.
        if selected_stage not in (1, 2, 3):  # Sprawdzenie, czy użytkownik wybrał obsługiwany etap.
            QMessageBox.information(self, "Etap niedostępny", "Obecnie zaimplementowane są Etap 1, Etap 2 i Etap 3.")  # Informacja o braku innych etapów.
            return  # Zakończenie funkcji dla nieobsługiwanego etapu.
        scrambled_image: np.ndarray = self.scrambled_image.copy()  # Utworzenie kopii obrazu przekształconego do pracy w tle.
        original_image: np.ndarray | None = self.original_image.copy() if self.original_image is not None else None  # Utworzenie kopii obrazu oryginalnego, jeśli jest dostępny.
        correct_key_text: str = self.correct_key_input.text()  # Pobranie tekstu poprawnego klucza w wątku GUI.
        wrong_key_text: str = self.wrong_key_input.text()  # Pobranie tekstu błędnego klucza w wątku GUI.
        used_key_label: str = self._active_key_label()  # Pobranie etykiety aktywnego klucza w wątku GUI.
        key_text: str = self._active_key_text()  # Pobranie aktywnego klucza w wątku GUI.
        self._run_in_background(  # Uruchomienie unscramblingu poza wątkiem GUI.
            "unscrambling",  # Nazwa zadania pokazywana użytkownikowi.
            lambda: self._unscramble_worker(selected_stage, scrambled_image, original_image, key_text, correct_key_text, wrong_key_text, used_key_label),  # Funkcja robocza wykonująca unscrambling i analizę.
            self._finish_unscramble,  # Funkcja kończąca aktualizację GUI po unscramblingu.
        )  # Koniec uruchamiania zadania w tle.

    def _unscramble_worker(self, selected_stage: int, scrambled_image: np.ndarray, original_image: np.ndarray | None, key_text: str, correct_key_text: str, wrong_key_text: str, used_key_label: str) -> dict[str, object]:  # Wykonanie unscramblingu i analizy w wątku roboczym.
        if selected_stage == 1:  # Sprawdzenie, czy aktywny jest Etap 1.
            restored_image: np.ndarray = stage1_unscramble(scrambled_image, key_text)  # Wykonanie odwrotnej transformacji Etapu 1.
            analysis_text: str = build_unscramble_analysis_text(original_image, scrambled_image, restored_image, correct_key_text, wrong_key_text, used_key_label)  # Zbudowanie raportu analitycznego dla Etapu 1.
        elif selected_stage == 2:  # Sprawdzenie, czy aktywny jest Etap 2.
            restored_image = stage2_unscramble(scrambled_image, key_text)  # Wykonanie odwrotnej transformacji Etapu 2.
            analysis_text = build_stage2_unscramble_analysis_text(original_image, scrambled_image, restored_image, correct_key_text, wrong_key_text, used_key_label)  # Zbudowanie raportu analitycznego dla Etapu 2.
        else:  # Obsługa Etapu 3.
            restored_image = stage3_unscramble(scrambled_image, key_text)  # Wykonanie odwrotnej transformacji Etapu 3.
            analysis_text = build_stage3_unscramble_analysis_text(original_image, scrambled_image, restored_image, correct_key_text, wrong_key_text, used_key_label)  # Zbudowanie raportu analitycznego dla Etapu 3.
        return {"restored_image": restored_image, "analysis_text": analysis_text}  # Zwrócenie wyniku obliczeń do wątku GUI.

    def _finish_unscramble(self, result: dict[str, object]) -> None:  # Aktualizacja GUI po zakończeniu unscramblingu w tle.
        restored_image: np.ndarray = result["restored_image"]  # Pobranie obrazu odtworzonego z wyniku zadania.
        analysis_text: str = result["analysis_text"]  # Pobranie raportu analitycznego z wyniku zadania.
        self.restored_image = restored_image  # Zapisanie obrazu odtworzonego w stanie aplikacji.
        self.restored_preview.set_numpy_image(self.restored_image)  # Aktualizacja podglądu obrazu odtworzonego.
        self.metrics_box.setPlainText(analysis_text)  # Wyświetlenie raportu analitycznego po unscramblingu.

    def _selected_stage(self) -> int:  # Return the selected stage number.
        checked_button: QRadioButton | None = self.stage_button_group.checkedButton()  # Pobranie aktualnie zaznaczonego przycisku etapu.
        if checked_button is None:  # Sprawdzenie, czy jakikolwiek etap jest zaznaczony.
            return 1  # Domyślny wybór Etapu 1 przy braku zaznaczenia.
        return self.stage_button_group.id(checked_button)  # Zwrócenie identyfikatora wybranego etapu.

    def _active_key_text(self) -> str:  # Return the currently active key text based on the checkbox state.
        if self.use_wrong_key_checkbox.isChecked():  # Sprawdzenie, czy użytkownik chce użyć błędnego klucza.
            return self.wrong_key_input.text()  # Zwrócenie tekstu błędnego klucza.
        return self.correct_key_input.text()  # Zwrócenie tekstu poprawnego klucza.

    def _active_key_label(self) -> str:  # Return a human-readable label for the key currently in use.
        return "klucz błędny" if self.use_wrong_key_checkbox.isChecked() else "klucz poprawny"  # Zwrócenie etykiety aktywnego klucza.

    def _current_stage_description(self) -> str:  # Zwrócenie opisu aktualnie wybranego etapu.
        if self._selected_stage() == 1:  # Sprawdzenie, czy aktywny jest Etap 1.
            return stage1_description()  # Zwrócenie opisu Etapu 1.
        if self._selected_stage() == 2:  # Sprawdzenie, czy aktywny jest Etap 2.
            return stage2_description()  # Zwrócenie opisu Etapu 2.
        return stage3_description()  # Zwrócenie opisu Etapu 3.

    def _default_metrics_text(self) -> str:  # Zwrócenie domyślnego tekstu dla pola metryk i analizy.
        return (  # Zwrócenie gotowego tekstu zastępczego.
            "Tutaj pojawią się metryki, komentarze i wyniki eksperymentów.\n"  # Pierwsza linia tekstu zastępczego.
            "Wczytaj obraz i uruchom wybrany etap, aby zobaczyć analizę."
        )  # Koniec zwracanego tekstu.

    def _reset_interface(self) -> None:  # Wyczyszczenie aktualnego stanu eksperymentu w GUI.
        if self.is_busy:  # Sprawdzenie, czy aplikacja nie wykonuje aktualnie zadania w tle.
            QMessageBox.information(self, "Operacja w toku", f"Najpierw zaczekaj na zakończenie: {self.current_task_name}.")  # Komunikat o niemożności resetu podczas pracy w tle.
            return  # Zakończenie funkcji bez resetowania stanu aplikacji.
        self.original_image = None  # Wyzerowanie obrazu oryginalnego.
        self.scrambled_image = None  # Wyzerowanie obrazu przekształconego.
        self.restored_image = None  # Wyzerowanie obrazu odtworzonego.
        self.original_preview.set_placeholder("Brak obrazu oryginalnego")  # Przywrócenie pustego stanu podglądu obrazu oryginalnego.
        self.scrambled_preview.set_placeholder("Brak obrazu przekształconego")  # Przywrócenie pustego stanu podglądu obrazu przekształconego.
        self.restored_preview.set_placeholder("Brak obrazu odtworzonego")  # Przywrócenie pustego stanu podglądu obrazu odtworzonego.
        self.correct_key_input.clear()  # Wyczyszczenie pola poprawnego klucza.
        self.wrong_key_input.clear()  # Wyczyszczenie pola błędnego klucza.
        self.use_wrong_key_checkbox.setChecked(False)  # Wyłączenie użycia błędnego klucza.
        self.metrics_box.setPlainText(self._default_metrics_text())  # Przywrócenie domyślnego tekstu pola analizy.

    def _save_selected_image(self) -> None:  # Zapis wyniku po wyborze typu danych do zapisania.
        if self.is_busy:  # Sprawdzenie, czy aplikacja nie wykonuje aktualnie zadania w tle.
            QMessageBox.information(self, "Operacja w toku", f"Najpierw zaczekaj na zakończenie: {self.current_task_name}.")  # Komunikat o niemożności uruchomienia zapisu podczas pracy w tle.
            return  # Zakończenie funkcji bez rozpoczynania zapisu.
        save_options: list[str] = ["Obraz", "Metryki"]  # Lista dostępnych typów danych do zapisania.
        selected_option, accepted = QInputDialog.getItem(  # Zapytanie użytkownika, co chce zapisać.
            self,  # Rodzic okna dialogowego.
            "Zapisz wynik",  # Tytuł okna dialogowego.
            "Co chcesz zapisać:",  # Treść pytania dla użytkownika.
            save_options,  # Dostępne opcje wyboru.
            0,  # Domyślnie zaznaczona pierwsza opcja.
            False,  # Brak możliwości wpisania własnej wartości.
        )  # Koniec wywołania okna wyboru.
        if not accepted:  # Sprawdzenie, czy użytkownik zatwierdził wybór.
            return  # Zakończenie funkcji po anulowaniu.
        if selected_option == "Obraz":  # Sprawdzenie, czy użytkownik chce zapisać obraz.
            self._save_image_result()  # Uruchomienie zapisu obrazu.
            return  # Zakończenie funkcji po obsłudze zapisu obrazu.
        self._save_metrics_result()  # Uruchomienie zapisu metryk.

    def _save_image_result(self) -> None:  # Zapis wybranego obrazu do pliku.
        image_options: list[tuple[str, np.ndarray | None]] = [  # Define saveable image choices.
            ("Obraz oryginalny", self.original_image),  # Opcja zapisu obrazu oryginalnego.
            ("Obraz przekształcony", self.scrambled_image),  # Opcja zapisu obrazu po scramblingu.
            ("Obraz odtworzony", self.restored_image),  # Opcja zapisu obrazu po unscramblingu.
        ]  # Koniec listy opcji.
        option_labels: list[str] = [label for label, _ in image_options]  # Extract labels for the selection dialog.
        selected_label, accepted = QInputDialog.getItem(  # Ask the user which image should be saved.
            self,  # Rodzic okna dialogowego.
            "Zapisz obraz",  # Tytuł okna dialogowego.
            "Wybierz obraz do zapisania:",  # Treść pytania dla użytkownika.
            option_labels,  # Dostępne opcje wyboru.
            0,  # Domyślnie zaznaczona pierwsza opcja.
            False,  # Brak możliwości wpisania własnej wartości.
        )  # Koniec wywołania okna wyboru.
        if not accepted:  # Stop if the user canceled the image-type selection.
            return  # Zakończenie funkcji po anulowaniu.

        selected_image: np.ndarray | None = next(  # Find the image that matches the chosen label.
            image for label, image in image_options if label == selected_label  # Wyszukanie obrazu odpowiadającego wybranej etykiecie.
        )  # Koniec wyszukiwania obrazu.
        if selected_image is None:  # Warn when the chosen image is not available yet.
            QMessageBox.warning(  # Wyświetlenie ostrzeżenia o braku wybranego obrazu.
                self,  # Rodzic okna komunikatu.
                "Brak obrazu",  # Tytuł ostrzeżenia.
                f"{selected_label} nie jest jeszcze dostępny do zapisania.",  # Treść ostrzeżenia.
            )  # Koniec wyświetlania ostrzeżenia.
            return  # Zakończenie funkcji po błędzie.

        default_filename: str = self._default_save_filename(selected_label)  # Suggest a filename matching the selected image type.
        file_path, _ = QFileDialog.getSaveFileName(  # Let the user choose the target path and format.
            self,  # Rodzic okna dialogowego.
            "Zapisz obraz",  # Tytuł okna zapisu.
            str(self.base_dir / default_filename),  # Domyślna ścieżka docelowa.
            "Pliki obrazów (*.png *.jpg *.jpeg *.bmp);;Wszystkie pliki (*)",  # Obsługiwane formaty zapisu obrazu.
        )  # Koniec wywołania okna zapisu.
        if not file_path:  # Stop if the user canceled the save dialog.
            return  # Zakończenie funkcji po anulowaniu.
        image_copy: np.ndarray = selected_image.copy()  # Utworzenie kopii obrazu do bezpiecznego zapisu w wątku roboczym.
        target_path: Path = Path(file_path)  # Zamiana ścieżki zapisu na obiekt Path.
        self._run_in_background(  # Uruchomienie zapisu obrazu poza wątkiem GUI.
            "zapis obrazu",  # Nazwa zadania pokazywana użytkownikowi.
            lambda: self._save_image_worker(target_path, image_copy),  # Funkcja robocza zapisująca obraz na dysk.
            self._finish_save_result,  # Funkcja kończąca aktualizację GUI po zapisie obrazu.
        )  # Koniec uruchamiania zadania w tle.

    def _save_image_worker(self, file_path: Path, image: np.ndarray) -> Path:  # Zapis obrazu do pliku w wątku roboczym.
        if not cv2.imwrite(str(file_path), image):  # Sprawdzenie, czy obraz został poprawnie zapisany przez OpenCV.
            raise ValueError(f"Nie udało się zapisać pliku:\n{file_path}")  # Zgłoszenie błędu do obsługi w wątku GUI.
        return file_path  # Zwrócenie ścieżki poprawnie zapisanego pliku.

    def _save_metrics_result(self) -> None:  # Zapis metryk i analizy do pliku JSON lub CSV.
        metrics_text: str = self.metrics_box.toPlainText().strip()  # Pobranie aktualnego tekstu metryk z pola analizy.
        if not metrics_text:  # Sprawdzenie, czy istnieje tekst do zapisania.
            QMessageBox.warning(self, "Brak metryk", "Nie ma metryk ani analizy do zapisania.")  # Ostrzeżenie o braku danych do zapisu.
            return  # Zakończenie funkcji po błędzie.

        format_options: list[str] = ["JSON", "CSV"]  # Lista dostępnych formatów zapisu metryk.
        selected_format, accepted = QInputDialog.getItem(  # Zapytanie użytkownika o format zapisu metryk.
            self,  # Rodzic okna dialogowego.
            "Zapisz metryki",  # Tytuł okna dialogowego.
            "Wybierz format zapisu metryk:",  # Treść pytania dla użytkownika.
            format_options,  # Dostępne formaty zapisu.
            0,  # Domyślnie zaznaczony pierwszy format.
            False,  # Brak możliwości wpisania własnej wartości.
        )  # Koniec wywołania okna wyboru.
        if not accepted:  # Sprawdzenie, czy użytkownik zatwierdził wybór.
            return  # Zakończenie funkcji po anulowaniu.

        parsed_metrics: dict[str, object] = self._parse_metrics_text(metrics_text)  # Zamiana tekstu raportu na prostą strukturę danych.
        if selected_format == "JSON":  # Sprawdzenie, czy użytkownik wybrał zapis JSON.
            default_path: Path = self.base_dir / "metryki.json"  # Domyślna ścieżka pliku JSON.
            file_path, _ = QFileDialog.getSaveFileName(  # Okno wyboru ścieżki zapisu pliku JSON.
                self,  # Rodzic okna dialogowego.
                "Zapisz metryki",  # Tytuł okna zapisu.
                str(default_path),  # Domyślna ścieżka docelowa.
                "Pliki JSON (*.json);;Wszystkie pliki (*)",  # Filtr formatów dla pliku JSON.
            )  # Koniec wywołania okna zapisu.
            if not file_path:  # Sprawdzenie, czy użytkownik wybrał plik docelowy.
                return  # Zakończenie funkcji po anulowaniu.
            payload: dict[str, object] = {  # Budowa pełnego obiektu danych do zapisu JSON.
                "selected_stage": self._selected_stage(),  # Numer aktualnie wybranego etapu.
                "active_key_label": self._active_key_label(),  # Informacja o aktywnym trybie klucza.
                "correct_key": self.correct_key_input.text(),  # Tekst poprawnego klucza.
                "wrong_key": self.wrong_key_input.text(),  # Tekst błędnego klucza.
                "metrics_text": metrics_text,  # Surowy tekst raportu metryk.
                "parsed_metrics": parsed_metrics,  # Ustrukturyzowana wersja raportu metryk.
            }  # Koniec budowy obiektu JSON.
            target_path: Path = Path(file_path)  # Zamiana ścieżki zapisu JSON na obiekt Path.
            self._run_in_background(  # Uruchomienie zapisu JSON poza wątkiem GUI.
                "zapis metryk JSON",  # Nazwa zadania pokazywana użytkownikowi.
                lambda payload=payload, target_path=target_path: self._save_metrics_json_worker(target_path, payload),  # Funkcja robocza zapisująca metryki JSON.
                self._finish_save_result,  # Funkcja kończąca aktualizację GUI po zapisie metryk JSON.
            )  # Koniec uruchamiania zadania w tle.
            return  # Zakończenie funkcji po zapisie JSON.

        default_path: Path = self.base_dir / "metryki.csv"  # Domyślna ścieżka pliku CSV.
        file_path, _ = QFileDialog.getSaveFileName(  # Okno wyboru ścieżki zapisu pliku CSV.
            self,  # Rodzic okna dialogowego.
            "Zapisz metryki",  # Tytuł okna zapisu.
            str(default_path),  # Domyślna ścieżka docelowa.
            "Pliki CSV (*.csv);;Wszystkie pliki (*)",  # Filtr formatów dla pliku CSV.
        )  # Koniec wywołania okna zapisu.
        if not file_path:  # Sprawdzenie, czy użytkownik wybrał plik docelowy.
            return  # Zakończenie funkcji po anulowaniu.
        csv_rows: list[tuple[str, str, str]] = self._metrics_to_csv_rows(parsed_metrics)  # Przygotowanie wierszy do zapisu CSV.
        target_path = Path(file_path)  # Zamiana ścieżki zapisu CSV na obiekt Path.
        self._run_in_background(  # Uruchomienie zapisu CSV poza wątkiem GUI.
            "zapis metryk CSV",  # Nazwa zadania pokazywana użytkownikowi.
            lambda csv_rows=csv_rows, target_path=target_path: self._save_metrics_csv_worker(target_path, csv_rows),  # Funkcja robocza zapisująca metryki CSV.
            self._finish_save_result,  # Funkcja kończąca aktualizację GUI po zapisie metryk CSV.
        )  # Koniec uruchamiania zadania w tle.

    def _save_metrics_json_worker(self, file_path: Path, payload: dict[str, object]) -> Path:  # Zapis metryk do pliku JSON w wątku roboczym.
        with open(file_path, "w", encoding="utf-8") as output_file:  # Otwarcie pliku wyjściowego w trybie zapisu tekstowego.
            json.dump(payload, output_file, ensure_ascii=False, indent=2)  # Zapis danych JSON z zachowaniem polskich znaków.
        return file_path  # Zwrócenie ścieżki poprawnie zapisanego pliku JSON.

    def _save_metrics_csv_worker(self, file_path: Path, csv_rows: list[tuple[str, str, str]]) -> Path:  # Zapis metryk do pliku CSV w wątku roboczym.
        with open(file_path, "w", encoding="utf-8", newline="") as output_file:  # Otwarcie pliku CSV w trybie zapisu.
            writer: csv.writer = csv.writer(output_file)  # Utworzenie obiektu zapisującego CSV.
            writer.writerow(["sekcja", "klucz", "wartość"])  # Zapis nagłówka tabeli CSV.
            for section_name, metric_key, metric_value in csv_rows:  # Iteracja po przygotowanych wierszach danych.
                writer.writerow([section_name, metric_key, metric_value])  # Zapis pojedynczego wiersza do pliku CSV.
        return file_path  # Zwrócenie ścieżki poprawnie zapisanego pliku CSV.

    def _finish_save_result(self, saved_path: Path) -> None:  # Wyświetlenie potwierdzenia po zakończeniu zapisu w tle.
        QMessageBox.information(self, "Zapis zakończony", f"Zapisano plik:\n{saved_path}")  # Potwierdzenie poprawnego zapisu pliku.

    def _parse_metrics_text(self, metrics_text: str) -> dict[str, object]:  # Konwersja raportu tekstowego na prostą strukturę słownikową.
        parsed_data: dict[str, object] = {}  # Utworzenie pustego słownika wynikowego.
        current_section: str = "główne"  # Ustawienie domyślnej sekcji raportu.
        parsed_data[current_section] = []  # Utworzenie listy dla treści ogólnych w sekcji domyślnej.
        for raw_line in metrics_text.splitlines():  # Iteracja po wszystkich liniach raportu.
            line: str = raw_line.strip()  # Usunięcie nadmiarowych spacji z aktualnej linii.
            if not line:  # Sprawdzenie, czy linia jest pusta.
                continue  # Pominięcie pustej linii.
            if line.endswith(":") and not line.startswith("-"):  # Sprawdzenie, czy linia wygląda jak nagłówek sekcji.
                current_section = line[:-1]  # Ustawienie nowej nazwy sekcji bez końcowego dwukropka.
                parsed_data.setdefault(current_section, [])  # Utworzenie wpisu sekcji, jeśli jeszcze nie istnieje.
                continue  # Przejście do kolejnej linii raportu.
            if line.startswith("-") and ":" in line:  # Sprawdzenie, czy linia zawiera wpis klucz-wartość.
                item_text: str = line[1:].strip()  # Usunięcie myślnika z początku linii.
                metric_key: str  # Deklaracja nazwy klucza metryki.
                metric_value: str  # Deklaracja wartości metryki.
                metric_key, metric_value = item_text.split(":", 1)  # Rozdzielenie wpisu na klucz i wartość.
                section_items: object = parsed_data.setdefault(current_section, [])  # Pobranie listy wpisów dla bieżącej sekcji.
                if isinstance(section_items, list):  # Sprawdzenie, czy sekcja ma postać listy.
                    section_items.append({metric_key.strip(): metric_value.strip()})  # Dodanie wpisu klucz-wartość do sekcji.
                continue  # Przejście do kolejnej linii raportu.
            section_items = parsed_data.setdefault(current_section, [])  # Pobranie listy wpisów dla bieżącej sekcji.
            if isinstance(section_items, list):  # Sprawdzenie, czy sekcja ma postać listy.
                section_items.append(line)  # Dodanie zwykłej linii tekstu do bieżącej sekcji.
        return parsed_data  # Zwrócenie gotowej struktury danych.

    def _metrics_to_csv_rows(self, parsed_metrics: dict[str, object]) -> list[tuple[str, str, str]]:  # Zamiana słownika metryk na listę wierszy CSV.
        csv_rows: list[tuple[str, str, str]] = []  # Utworzenie pustej listy wynikowych wierszy CSV.
        for section_name, section_value in parsed_metrics.items():  # Iteracja po wszystkich sekcjach raportu.
            if isinstance(section_value, list):  # Sprawdzenie, czy sekcja jest listą wpisów.
                for entry in section_value:  # Iteracja po elementach bieżącej sekcji.
                    if isinstance(entry, dict):  # Sprawdzenie, czy element sekcji jest parą klucz-wartość.
                        for metric_key, metric_value in entry.items():  # Iteracja po wszystkich parach klucz-wartość w elemencie.
                            csv_rows.append((section_name, str(metric_key), str(metric_value)))  # Dodanie sformatowanego wiersza do listy CSV.
                        continue  # Przejście do kolejnego elementu sekcji.
                    csv_rows.append((section_name, "opis", str(entry)))  # Dodanie zwykłej linii tekstowej jako wiersza opisowego.
                continue  # Przejście do kolejnej sekcji raportu.
            csv_rows.append((section_name, "wartość", str(section_value)))  # Dodanie uproszczonego wiersza dla nieoczekiwanej struktury danych.
        return csv_rows  # Zwrócenie gotowej listy wierszy CSV.

    def _default_save_filename(self, selected_label: str) -> str:  # Build a simple suggested filename for the chosen image type.
        filename_map: dict[str, str] = {
            "Obraz oryginalny": "obraz_oryginalny.png",
            "Obraz przekształcony": "obraz_przeksztalcony.png",
            "Obraz odtworzony": "obraz_odtworzony.png",
        }
        return filename_map.get(selected_label, "obraz.png")

    def _load_logo_into_label(self, target_label: QLabel) -> None:  # Load the university logo into a label.
        if not self.logo_path.exists():  # Check whether the logo file exists.
            target_label.setText("Brak logo")  # Show fallback text when the file is missing.
            return  # Stop when the logo cannot be loaded.
        logo_pixmap: QPixmap = QPixmap(str(self.logo_path))  # Load the image file directly into a QPixmap.
        scaled_logo: QPixmap = logo_pixmap.scaled(  # Scale the logo so it fits nicely in the header.
            180,  # Set the target width limit.
            180,  # Set the target height limit.
            Qt.AspectRatioMode.KeepAspectRatio,  # Preserve the original aspect ratio.
            Qt.TransformationMode.SmoothTransformation,  # Use smooth scaling quality.
        )  # Finish creating the scaled logo.
        target_label.setPixmap(scaled_logo)  # Display the logo inside the label.


# ---- Uruchomienie aplikacji ----
def main() -> int:  # Define the application entry point.
    app: QApplication = QApplication(sys.argv)  # Create the Qt application object.
    window: ProjectGui = ProjectGui()  # Create the main project window.
    window.show()  # Show the window on screen.
    return app.exec()  # Start the Qt event loop and return its exit code.


if __name__ == "__main__":  # Run the application only when this file is executed directly.
    raise SystemExit(main())  # Start the program and exit cleanly with Qt's return code.
