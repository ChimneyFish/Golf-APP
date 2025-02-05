import sys
import json
import geopy.distance
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QSpinBox, QDialog, QLineEdit, QHBoxLayout,
)
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt
import gpsd


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
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
            "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
            "A", "S", "D", "F", "G", "H", "J", "K", "L",
            "Z", "X", "C", "V", "B", "N", "M"
        ]
        row, col = 0, 0
        for key in keys:
            button = QPushButton(key)
            button.clicked.connect(lambda _, k=key: self.input_field.insert(k))
            key_layout.addWidget(button, row, col)
            col += 1
            if col > 9:
                col = 0
                row += 1

        layout.addLayout(key_layout)

        action_layout = QHBoxLayout()
        self.backspace_button = QPushButton("Backspace")
        self.backspace_button.clicked.connect(self.input_field.backspace)
        action_layout.addWidget(self.backspace_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        action_layout.addWidget(self.ok_button)

        layout.addLayout(action_layout)
        self.setLayout(layout)

    def get_text(self):
        return self.input_field.text()


def jls_extract_def(jls_extract_var):
    return jls_extract_var


class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setFixedSize(800, 480)

        self.scores = [[0] * 18 for _ in range(4)]
        self.current_page = 0  # 0 for Front 9, 1 for Back
        self.players = ["Player 1", "Player 2", "Player 3", "Player 4"]
        self.pin_locations = {}
        self.tee_location = None
        self.load_course_data()

        gpsd.connect()
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#4CAF50"))
        self.setPalette(palette)

        layout = QVBoxLayout()
        self.title_label = QLabel("🏌 Golf Scorecard & GPS Tracker", self)
        self.title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("Enter Course Name")
        self.course_name_input.mousePressEvent = self.show_keyboard  # Attach keyboard
        layout.addWidget(self.course_name_input)

        self.score_grid = QGridLayout()
        self.score_spinboxes = [[None] * 18 for _ in range(4)]

        for player in range(4):
            player_label = QLabel(f"P{player + 1}")
            player_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            player_label.setStyleSheet("color: white;")
            self.score_grid.addWidget(player_label, player, 0)

            for i in range(9):
                score_spinbox = QSpinBox()
                score_spinbox.setRange(0, 10)
                score_spinbox.setFixedSize(40, 40)
                score_spinbox.setStyleSheet("background-color: white; font-size: 14px;")
                score_spinbox.valueChanged.connect(lambda value, p=player, h=i: self.update_score(p, h, value))

                self.score_spinboxes[player][i] = score_spinbox
                self.score_grid.addWidget(score_spinbox, player, i + 1)

        layout.addLayout(self.score_grid)

        self.total_score_label = QLabel("Total Scores: P1: 0 | P2: 0 | P3: 0 | P4: 0")
        self.total_score_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.total_score_label.setStyleSheet("color: yellow;")
        layout.addWidget(self.total_score_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.next_button = QPushButton("Next 9 Holes")
        self.next_button.clicked.connect(self.switch_page)
        layout.addWidget(self.next_button)

        self.save_button = QPushButton("💾 Save Course Data")
        self.save_button.clicked.connect(self.save_course_data)
        layout.addWidget(self.save_button)

        self.drive_distance_btn = QPushButton("Mark Tee Shot", self)
        self.drive_distance_btn.clicked.connect(self.mark_tee_shot)
        layout.addWidget(self.drive_distance_btn)

        self.calculate_distance_btn = QPushButton("Calculate Drive Distance", self)
        self.calculate_distance_btn.clicked.connect(self.calculate_drive_distance)
        layout.addWidget(self.calculate_distance_btn)

        self.setLayout(layout)
        self.update_ui()

    def show_keyboard(self, event):
        keyboard = OnScreenKeyboard(self)
        if keyboard.exec():
            self.course_name_input.setText(keyboard.get_text())
        else:
            super().mousePressEvent(event)  # Ensure original behavior occurs

    def update_score(self, player, hole, value):
        self.scores[player][hole] = value
        total_scores = [sum(self.scores[p]) for p in range(4)]
        self.total_score_label.setText(
            f"Total: P1: {total_scores[0]} | P2: {total_scores[1]} | P3: {total_scores[2]} | P4: {total_scores[3]}"
        )

    def switch_page(self):
        self.current_page = 1 - self.current_page  # Toggle between 0 and 1
        self.update_ui()

    def update_ui(self):
        start_hole = 9 * self.current_page
        for player in range(4):
            for i in range(9):
                self.score_spinboxes[player][i].setValue(self.scores[player][start_hole + i])
        self.next_button.setText("Previous 9 Holes" if self.current_page else "Next 9 Holes")

    def mark_tee_shot(self):
        try:
            packet = gpsd.get_current()
            self.tee_location = (packet.lat, packet.lon)
        except Exception as e:
            print(f"Error getting GPS data: {e}")

    def calculate_drive_distance(self):
        if not self.tee_location:
            print("Tee location not marked.")
            return

        try:
            packet = gpsd.get_current()
            current_location = (packet.lat, packet.lon)
            distance = geopy.distance.geodesic(self.tee_location, current_location).yards
            print(f"Drive Distance: {distance:.2f} yards")
        except Exception as e:
            print(f"Error calculating distance: {e}")

    def course_data(self):
         return {
         "course_name": self.course_name_input.text().strip(),
         "tee_location": self.tee_location,
         "pin_locations": self.pin_locations,
    }

    def save_course_data(self):
        try:
            with open("courses.json", "w") as f:
                json.dump(self.course_data(), f, indent=4)  # Call the method using parentheses
            print("Course data saved successfully.")
        except Exception as e:
            print(f"Error saving course data: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.showFullScreen()
    sys.exit(app.exec())
