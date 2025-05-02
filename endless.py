import sys, json, random, os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QSpinBox,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QDialog
)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ClickableLabel(QLabel):
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

class MapBox(QWidget):
    def __init__(self):
        super().__init__()
        with open(resource_path("style.qss"), "r") as f:
            self.setStyleSheet(f.read())
        self.current_image_path = ""  # store path for double-click usage

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)

        # Top row: clickable title and BAD MAP button (for reloading the current map)
        self.top_layout = QHBoxLayout()
        self.title_label = QLabel("Map Title")
        self.title_label.setOpenExternalLinks(True)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setWordWrap(True)
        self.top_layout.addWidget(self.title_label)
        self.top_layout.addStretch()
        self.bad_map_button = QPushButton("BAD MAP")
        self.bad_map_button.setFlat(True)
        self.top_layout.addWidget(self.bad_map_button)
        self.main_layout.addLayout(self.top_layout)

        # Creator label (gray, 50% opacity)
        self.creator_label = QLabel("Creator")
        self.creator_label.setWordWrap(True)
        self.creator_label.setStyleSheet("color: #888;")
        self.creator_label.setWordWrap(True)
        self.main_layout.addWidget(self.creator_label)

        # Image preview using ClickableLabel
        self.image_label = ClickableLabel()
        self.image_label.setFixedSize(320, 180)
        self.image_label.setStyleSheet("border: 1px solid #555;")
        self.image_label.setScaledContents(True)
        self.main_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        # Connect double-click signal to open image in new window
        self.image_label.doubleClicked.connect(self.open_image_window)

        # Bottom row: Control buttons for CLEAR, FC, SKIP/GIVE UP.
        # These will be hidden after a selection is made.
        self.bottom_layout = QHBoxLayout()
        self.clear_button = QPushButton("CLEAR")
        self.fc_button = QPushButton("FC")
        self.skip_button = QPushButton("SKIP")
        self.bottom_layout.addWidget(self.clear_button)
        self.bottom_layout.addWidget(self.fc_button)
        self.bottom_layout.addWidget(self.skip_button)
        self.main_layout.addLayout(self.bottom_layout)

        # Label to display the result (e.g. "Cleared", "Skipped", etc)
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.hide()  # hidden until a choice is made
        self.main_layout.addWidget(self.result_label)

    def update_map_data(self, title, creator, image_path, link):
        # Title becomes a clickable link (dummy URL)
        link_html = f'<a href="{link}" style="text-decoration:none; color:#fff;">{title}</a>'
        self.title_label.setText(link_html)
        self.creator_label.setText(creator)
        self.current_image_path = image_path

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("No Image Found")

    def set_skip_button_text(self, text):
        self.skip_button.setText(text)

    def display_selected_option(self, option_text):
        self.clear_button.hide()
        self.fc_button.hide()
        self.skip_button.hide()
        self.result_label.setText(option_text)
        self.result_label.show()

    def open_image_window(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Map Image")
        layout = QVBoxLayout(dialog)
        image_display = QLabel(dialog)
        pixmap = QPixmap(self.current_image_path)
        if not pixmap.isNull():
            image_display.setPixmap(pixmap)
            image_display.setScaledContents(True)
            dialog.resize(min(pixmap.width(), 800), min(pixmap.height(), 600))
        else:
            image_display.setText("No Image Found")
        layout.addWidget(image_display)
        dialog.exec_()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local Celeste Endless Map Randomizer")
        self.resize(600, 800)
        self.setWindowIcon(QIcon(resource_path("image.png")))
        # Counters and run state
        self.clears = 0
        self.skips = 0
        self.run_active = False

        # Load maps from JSON
        self.map_data_list = self.load_maps_json("Maps.json")

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Header: Title, subtitle, and start settings
        header_layout = QVBoxLayout()
        self.title_icon = QLabel()
        self.title_icon.setPixmap(QPixmap(resource_path("image.svg")))
        header_layout.addWidget(self.title_icon)
        self.title_label = QLabel("Local Celeste Endless Map Randomizer")
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("by Ottomated, ripped from Maddie's random map API")
        self.subtitle_label.setStyleSheet("color: #aaa;")
        header_layout.addWidget(self.subtitle_label)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start with skips:"))
        self.skips_spinbox = QSpinBox()
        self.skips_spinbox.setRange(0, 20)
        self.skips_spinbox.setValue(1)
        start_layout.addWidget(self.skips_spinbox)
        self.begin_button = QPushButton("Begin")
        start_layout.addWidget(self.begin_button)
        header_layout.addLayout(start_layout)
        self.main_layout.addLayout(header_layout)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        self.main_layout.addWidget(sep)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.status_label.setStyleSheet("color: #ccc;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_label)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        self.main_layout.addWidget(sep2)

        # Scroll area to hold the chain of map boxes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.maps_container = QWidget()
        self.maps_layout = QVBoxLayout(self.maps_container)
        self.maps_layout.setContentsMargins(10, 10, 10, 10)
        self.maps_layout.setSpacing(10)
        self.scroll_area.setWidget(self.maps_container)
        self.main_layout.addWidget(self.scroll_area)

        # Connect the Begin button signal
        self.begin_button.clicked.connect(self.start_game)

        self.apply_dark_stylesheet()

    def load_maps_json(self, filename):
        try:
            with open(filename, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            maps_raw = data.get("Maps", {})
            return [map_info for key, map_info in maps_raw.items()]
        except Exception as e:
            print("Failed to load or parse JSON:", e)
            return []

    def start_game(self):
        self.clears = 0
        self.skips = self.skips_spinbox.value()
        self.run_active = True
        self.status_label.setText(f"START, {self.skips} SKIP{'S' if self.skips != 1 else ''}")

        # Clear any existing map boxes.
        for i in reversed(range(self.maps_layout.count())):
            widget = self.maps_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Add the first map box.
        self.add_new_map_box()

    def add_new_map_box(self):
        if not self.run_active:
            return

        map_box = MapBox()

        # Connect the button signals.
        map_box.clear_button.clicked.connect(lambda: self.handle_result("clear", map_box))
        map_box.fc_button.clicked.connect(lambda: self.handle_result("fc", map_box))
        map_box.skip_button.clicked.connect(lambda: self.handle_result("skip", map_box))
        map_box.bad_map_button.clicked.connect(lambda: self.handle_bad_map(map_box))

        self.show_new_random_map(map_box)
        self.maps_layout.addWidget(map_box)

        # Update skip button text as needed.
        if self.skips == 0:
            map_box.set_skip_button_text("GIVE UP")
        else:
            map_box.set_skip_button_text("SKIP")

    def show_new_random_map(self, map_box):
        if not self.map_data_list:
            map_box.update_map_data("No Maps Found", "", "")
            return

        map_info = random.choice(self.map_data_list)
        title = map_info.get("title", "Untitled")
        creator = map_info.get("creator", "Unknown")
        image_path = map_info.get("image", "")
        link = map_info.get("link", "")
        map_box.update_map_data(title, creator, image_path, link)

    def add_between_maps_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        self.maps_layout.addWidget(sep)

        counters_label = QLabel(f"|\n|\n\n{self.clears} CLEARS, {self.skips} SKIP{'S' if self.skips != 1 else ''}\n\n|\n|")
        counters_label.setAlignment(Qt.AlignCenter)
        counters_label.setStyleSheet("color: #aaa; font-weight: bold;")
        self.maps_layout.addWidget(counters_label)

    def handle_result(self, action, map_box):
        if not self.run_active:
            return

        if action == "clear":
            self.clears += 1
            result_text = "Cleared"
        elif action == "fc":
            self.clears += 1
            self.skips += 1
            result_text = "Full Cleared"
        elif action == "skip":
            if self.skips > 0:
                self.skips -= 1
                result_text = "Skipped"
            else:
                self.end_run()
                return

        # Hide the buttons on this MapBox and show the result text.
        map_box.display_selected_option(result_text)

        # Add a separator and then a new map box.
        self.add_between_maps_separator()
        self.add_new_map_box()
        self.status_label.setText(f"RUN: {self.clears} CLEARS, {self.skips} SKIP{'S' if self.skips != 1 else ''}")

    def handle_bad_map(self, map_box):
        self.show_new_random_map(map_box)

    def end_run(self):
        self.run_active = False
        self.status_label.setText(f"RUN ENDED: {self.clears} CLEARS, {self.skips} SKIP{'S' if self.skips != 1 else ''}")

        if self.maps_layout.count() > 0:
            last_item = self.maps_layout.itemAt(self.maps_layout.count() - 1)
            last_widget = last_item.widget()
            if isinstance(last_widget, MapBox):
                last_widget.clear_button.setEnabled(False)
                last_widget.fc_button.setEnabled(False)
                last_widget.skip_button.setEnabled(False)
                last_widget.bad_map_button.setEnabled(False)

    def apply_dark_stylesheet(self):
        dark_stylesheet = """
        QMainWindow { background-color: #2b2b2b; }
        QWidget { color: #ffffff; background-color: #2b2b2b; }
        QPushButton {
            background-color: #444;
            border: 1px solid #555;
            padding: 6px;
            border-radius: 4px;
        }
        QPushButton:hover { background-color: #555; }
        QPushButton:pressed { background-color: #666; }
        QSpinBox {
            background-color: #333;
            color: #fff;
            border: 1px solid #555;
        }
        QFrame { background-color: #2b2b2b; }
        """
        self.setStyleSheet(dark_stylesheet)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())



if __name__ == "__main__":
    main()
