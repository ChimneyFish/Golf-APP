import sys
import json
import os
import geopy.distance
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QGridLayout,
    QLineEdit,
    QDialog,
    QHBoxLayout,
)
import gpsd

data_file = "courses.json"


class OnScreenKeyboard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        self.input_field = QLineEdit(self)
        layout.addWidget(self.input_field)

        key_layout = QGridLayout()
        keys = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "0",
            "Q",
            "W",
            "E",
            "R",
            "T",
            "Y",
            "U",
            "I",
            "O",
            "P",
            "A",
            "S",
            "D",
            "F",
            "G",
            "H",
            "J",
            "K",
            "L",
            "Z",
            "X",
            "C",
            "V",
            "B",
            "N",
            "M",
        ]
        row, col = 0, 0
        for key in keys:
            button = QPushButton(key)
            button.clicked.connect(lambda checked, k=key: self.input_field.insert(k))
            key_layout.addWidget(button, row, col)
            col += 1
            if col > 9:
                col = 0
                row += 1

        layout.addLayout(key_layout)

        action_layout = QHBoxLayout()
        self.backspace_button = QPushButton("Backspace")
        self.backspace_button.clicked.connect(lambda: self.input_field.backspace())
        action_layout.addWidget(self.backspace_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        action_layout.addWidget(self.ok_button)

        layout.addLayout(action_layout)
        self.setLayout(layout)

    def get_text(self):
        return self.input_field.text()


class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setGeometry(0, 0, 800, 480)

        self.players = ["Player 1", "Player 2", "Player 3", "Player 4"]
        self.pin_locations = {}
        self.tee_location = None
        self.load_course_data()

        gpsd.connect()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        self.title_label = QLabel("Golf Scorecard", self)
        self.title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: green;"
        )
        self.layout.addWidget(self.title_label)

        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("Enter Course Name")
        self.course_name_input.mousePressEvent = self.show_keyboard
        self.layout.addWidget(self.course_name_input)

        self.total_score_label = QLabel("Total Scores: 0", self)
        self.layout.addWidget(self.total_score_label)

        self.save_course_btn = QPushButton("Save Course", self)
        self.save_course_btn.clicked.connect(self.save_course_data)
        self.layout.addWidget(self.save_course_btn)

        self.drive_distance_btn = QPushButton("Mark Tee Shot", self)
        self.drive_distance_btn.clicked.connect(self.mark_tee_shot)
        self.layout.addWidget(self.drive_distance_btn)

        self.calculate_distance_btn = QPushButton("Calculate Drive Distance", self)
        self.calculate_distance_btn.clicked.connect(self.calculate_drive_distance)
        self.layout.addWidget(self.calculate_distance_btn)

        self.setLayout(self.layout)

    def show_keyboard(self, event):
        keyboard = OnScreenKeyboard(self)
        if keyboard.exec():
            self.course_name_input.setText(keyboard.get_text())

    def mark_tee_shot(self):
        try:
            packet = gpsd.get_current()
            self.tee_location = (packet.lat, packet.lon)
            print(f"Tee-off marked at: {self.tee_location}")
        except Exception as e:
            print(f"Error getting GPS data: {e}")

    def mark_pin_location(self, hole_number):
        try:
            packet = gpsd.get_current()
            self.pin_locations[hole_number] = (packet.lat, packet.lon)
            print(
                f"Pin location for hole {hole_number} marked at: {self.pin_locations[hole_number]}"
            )
        except Exception as e:
            print(f"Error getting GPS data: {e}")

    def calculate_drive_distance(self):
        if not self.tee_location:
            print("Tee location not marked.")
            return

        try:
            packet = gpsd.get_current()
            current_location = (packet.lat, packet.lon)
            distance = geopy.distance.geodesic(
                self.tee_location, current_location
            ).yards
            print(f"Drive Distance: {distance:.2f} yards")
        except Exception as e:
            print(f"Error calculating distance: {e}")

    def save_course_data(self):
        course_name = self.course_name_input.text().strip()
        if not course_name:
            print("Course name is empty, not saving.")
            return

        course_data = {
            "course_name": course_name,
            "players": self.players,
            "tee_location": self.tee_location,
            "pin_locations": self.pin_locations,
        }

        with open(data_file, "w") as f:
            json.dump(course_data, f, indent=4)

        print("Course data saved successfully.")

    def load_course_data(self):
        if not os.path.exists(data_file):
            print("No saved course data found.")
            return

        with open(data_file, "r") as f:
            course_data = json.load(f)

        self.course_name_input.setText(course_data.get("course_name", ""))
        self.players = course_data.get(
            "players", ["Player 1", "Player 2", "Player 3", "Player 4"]
        )
        self.tee_location = course_data.get("tee_location", None)
        self.pin_locations = course_data.get("pin_locations", {})

        print("Course data loaded successfully.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.showFullScreen()
    sys.exit(app.exec())
