"""PyQt GUI skeleton for the M-II project."""  # Module docstring describing this file.

from __future__ import annotations  # Allow postponed evaluation of type hints.

import sys  # Import sys to access command-line arguments and app exit handling.
from pathlib import Path  # Import Path for safe filesystem paths.

import cv2  # Import OpenCV as the image-processing library required by the project.
import numpy as np  # Import NumPy as the array-processing library required by the project.
from stage1 import scramble_image as stage1_scramble  # Import Stage 1 scrambling algorithm.
from stage1 import stage1_description  # Import Stage 1 description for the metrics panel.
from stage1 import unscramble_image as stage1_unscramble  # Import Stage 1 unscrambling algorithm.

from PyQt6.QtCore import Qt  # Import Qt alignment and scaling flags.
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


class ProjectGui(QMainWindow):  # Define the main application window.
    """Main PyQt GUI skeleton for the project."""  # Class docstring.

    def __init__(self) -> None:  # Initialize the main window and all widgets.
        super().__init__()  # Call the QMainWindow constructor.
        self.base_dir: Path = Path(__file__).resolve().parent  # Store the folder containing this file.
        self.logo_path: Path = self.base_dir / "filia_uwb_logo.png"  # Build the path to the university logo.
        self.original_image: np.ndarray | None = None  # Reserve storage for the future original image.
        self.scrambled_image: np.ndarray | None = None  # Reserve storage for the future transformed image.
        self.restored_image: np.ndarray | None = None  # Reserve storage for the future restored image.
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
        self.metrics_box.setPlainText(  # Insert placeholder text describing future use.
            "Tutaj pojawią się przyszłe metryki, komentarze i wyniki eksperymentów.\n"
            "Na tym etapie to tylko szkielet interfejsu."
        )  # Finish setting the placeholder text.
        metrics_layout.addWidget(self.metrics_box)  # Add the metrics text area to the metrics section.

    def _connect_signals(self) -> None:  # Connect widget signals to their action handlers.
        self.load_button.clicked.connect(self._load_image)  # Load an image from disk.
        self.scramble_button.clicked.connect(self._run_scramble)  # Run the selected scrambling stage.
        self.unscramble_button.clicked.connect(self._run_unscramble)  # Run the selected unscrambling stage.
        self.save_button.clicked.connect(self._save_selected_image)  # Handle saving one of the available images.

    def _load_image(self) -> None:  # Load an input image and show it in the original preview.
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wczytaj obraz",
            str(self.base_dir),
            "Pliki obrazów (*.png *.jpg *.jpeg *.bmp);;Wszystkie pliki (*)",
        )
        if not file_path:
            return

        loaded_image: np.ndarray | None = cv2.imread(file_path, cv2.IMREAD_COLOR)
        if loaded_image is None:
            QMessageBox.critical(self, "Błąd wczytywania", "Nie udało się wczytać wybranego obrazu.")
            return

        self.original_image = loaded_image
        self.scrambled_image = None
        self.restored_image = None
        self.original_preview.set_numpy_image(self.original_image)
        self.scrambled_preview.set_placeholder("Brak obrazu przekształconego")
        self.restored_preview.set_placeholder("Brak obrazu odtworzonego")
        self.metrics_box.setPlainText(
            f"Wczytano obraz: {Path(file_path).name}\n"
            f"Rozdzielczość: {self.original_image.shape[1]} x {self.original_image.shape[0]} px\n\n"
            f"{stage1_description()}"
        )

    def _run_scramble(self) -> None:  # Run scrambling for the currently selected stage.
        if self.original_image is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz wejściowy.")
            return

        if self._selected_stage() != 1:
            QMessageBox.information(self, "Etap niedostępny", "Obecnie zaimplementowany jest tylko Etap 1.")
            return

        try:
            key_text: str = self._active_key_text()
            self.scrambled_image = stage1_scramble(self.original_image, key_text)
        except ValueError as error:
            QMessageBox.warning(self, "Błędny klucz", str(error))
            return

        self.scrambled_preview.set_numpy_image(self.scrambled_image)
        self.restored_image = None
        self.restored_preview.set_placeholder("Brak obrazu odtworzonego")
        self.metrics_box.setPlainText(
            "Wykonano scrambling dla Etapu 1.\n"
            f"Użyty klucz: {self._active_key_label()}\n\n"
            f"{stage1_description()}\n\n"
            "Słabość metody: widoczne mogą pozostać kontury, pasy, regularne przejścia i inne duże struktury obrazu,\n"
            "ponieważ algorytm tylko przestawia piksele przez przesunięcia cykliczne, ale nie zmienia ich wartości."
        )

    def _run_unscramble(self) -> None:  # Run inverse transformation for the currently selected stage.
        if self.scrambled_image is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wykonaj scrambling obrazu.")
            return

        if self._selected_stage() != 1:
            QMessageBox.information(self, "Etap niedostępny", "Obecnie zaimplementowany jest tylko Etap 1.")
            return

        try:
            key_text = self._active_key_text()
            self.restored_image = stage1_unscramble(self.scrambled_image, key_text)
        except ValueError as error:
            QMessageBox.warning(self, "Błędny klucz", str(error))
            return

        self.restored_preview.set_numpy_image(self.restored_image)
        self.metrics_box.setPlainText(
            "Wykonano unscrambling dla Etapu 1.\n"
            f"Użyty klucz: {self._active_key_label()}\n\n"
            "Dla poprawnego klucza obraz powinien zostać odtworzony idealnie.\n"
            "Dla błędnego klucza wynik zwykle pozostaje zniekształcony, ale metoda nadal nie jest bezpieczna,\n"
            "bo opiera się tylko na prostych przesunięciach wierszy i kolumn."
        )

    def _selected_stage(self) -> int:  # Return the selected stage number.
        checked_button = self.stage_button_group.checkedButton()
        if checked_button is None:
            return 1
        return self.stage_button_group.id(checked_button)

    def _active_key_text(self) -> str:  # Return the currently active key text based on the checkbox state.
        if self.use_wrong_key_checkbox.isChecked():
            return self.wrong_key_input.text()
        return self.correct_key_input.text()

    def _active_key_label(self) -> str:  # Return a human-readable label for the key currently in use.
        return "klucz błędny" if self.use_wrong_key_checkbox.isChecked() else "klucz poprawny"

    def _save_selected_image(self) -> None:  # Let the user choose which image should be saved.
        image_options: list[tuple[str, np.ndarray | None]] = [  # Define saveable image choices.
            ("Obraz oryginalny", self.original_image),
            ("Obraz przekształcony", self.scrambled_image),
            ("Obraz odtworzony", self.restored_image),
        ]
        option_labels: list[str] = [label for label, _ in image_options]  # Extract labels for the selection dialog.
        selected_label, accepted = QInputDialog.getItem(  # Ask the user which image should be saved.
            self,
            "Zapisz obraz",
            "Wybierz obraz do zapisania:",
            option_labels,
            0,
            False,
        )
        if not accepted:  # Stop if the user canceled the image-type selection.
            return

        selected_image: np.ndarray | None = next(  # Find the image that matches the chosen label.
            image for label, image in image_options if label == selected_label
        )
        if selected_image is None:  # Warn when the chosen image is not available yet.
            QMessageBox.warning(
                self,
                "Brak obrazu",
                f"{selected_label} nie jest jeszcze dostępny do zapisania.",
            )
            return

        default_filename: str = self._default_save_filename(selected_label)  # Suggest a filename matching the selected image type.
        file_path, _ = QFileDialog.getSaveFileName(  # Let the user choose the target path and format.
            self,
            "Zapisz obraz",
            str(self.base_dir / default_filename),
            "Pliki obrazów (*.png *.jpg *.jpeg *.bmp);;Wszystkie pliki (*)",
        )
        if not file_path:  # Stop if the user canceled the save dialog.
            return
        if cv2.imwrite(file_path, selected_image):  # Save the chosen image with OpenCV.
            QMessageBox.information(self, "Zapis zakończony", f"Zapisano plik:\n{file_path}")
            return
        QMessageBox.critical(self, "Błąd zapisu", f"Nie udało się zapisać pliku:\n{file_path}")

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


def main() -> int:  # Define the application entry point.
    app: QApplication = QApplication(sys.argv)  # Create the Qt application object.
    window: ProjectGui = ProjectGui()  # Create the main project window.
    window.show()  # Show the window on screen.
    return app.exec()  # Start the Qt event loop and return its exit code.


if __name__ == "__main__":  # Run the application only when this file is executed directly.
    raise SystemExit(main())  # Start the program and exit cleanly with Qt's return code.
