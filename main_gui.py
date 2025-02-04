import sys
import geopy.distance
import gpsd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QSpinBox
)
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt

class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setFixedSize(800, 480)  # Set fixed window size for 800x480 display

        self.scores = [[0] * 18 for _ in range(4)]
        self.drive_start = None
        self.drive_end = None
        self.pin_location = None

        gpsd.connect()  # Connect to GPS

        self.initUI()

    def initUI(self):
        # Set color theme
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#4CAF50"))  # Green background
        self.setPalette(palette)

        layout = QVBoxLayout()

        # Title Label
        self.title_label = QLabel("🏌 Golf Scorecard & GPS Tracker", self)
        self.title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white; text-align: center;")
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Score Grid
        self.score_grid = QGridLayout()
        self.score_spinboxes = [[None] * 18 for _ in range(4)]

        for player in range(4):
            player_label = QLabel(f"P{player + 1}")
            player_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            player_label.setStyleSheet("color: white; padding: 2px;")
            self.score_grid.addWidget(player_label, player, 0)

            for i in range(9):  # Only 9 holes displayed at a time
                score_spinbox = QSpinBox()
                score_spinbox.setRange(0, 10)
                score_spinbox.setValue(self.scores[player][i])
                score_spinbox.setFixedSize(40, 40)
                score_spinbox.setStyleSheet("background-color: white; font-size: 14px;")
                score_spinbox.valueChanged.connect(lambda value, p=player, h=i: self.update_score(p, h, value))

                self.score_spinboxes[player][i] = score_spinbox
                self.score_grid.addWidget(score_spinbox, player, i + 1)

        layout.addLayout(self.score_grid)

        # Total Score Display
        self.total_score_label = QLabel("Total Scores: P1: 0 | P2: 0 | P3: 0 | P4: 0")
        self.total_score_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.total_score_label.setStyleSheet("color: yellow; padding: 5px;")
        layout.addWidget(self.total_score_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # GPS Labels
        self.drive_label = QLabel("Drive Distance: N/A")
        self.range_label = QLabel("Range to Pin: N/A")
        for label in [self.drive_label, self.range_label]:
            label.setFont(QFont("Arial", 12))
            label.setStyleSheet("color: white; padding: 2px;")
            layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Button Styles
        button_style = """
            QPushButton {
                background-color: #FFEB3B;
                font-size: 14px;
                padding: 5px;
                border-radius: 8px;
                border: 1px solid black;
            }
            QPushButton:hover {
                background-color: #FBC02D;
            }
            QPushButton:pressed {
                background-color: #F57F17;
            }
        """

        # GPS Buttons
        self.set_drive_start_btn = QPushButton("📍 Set Drive Start")
        self.set_drive_start_btn.setStyleSheet(button_style)
        self.set_drive_start_btn.clicked.connect(self.set_drive_start)
        layout.addWidget(self.set_drive_start_btn)

        self.set_drive_end_btn = QPushButton("🚗 Set Drive End")
        self.set_drive_end_btn.setStyleSheet(button_style)
        self.set_drive_end_btn.clicked.connect(self.set_drive_end)
        layout.addWidget(self.set_drive_end_btn)

        self.set_pin_btn = QPushButton("🏁 Set Pin Location")
        self.set_pin_btn.setStyleSheet(button_style)
        self.set_pin_btn.clicked.connect(self.set_pin_location)
        layout.addWidget(self.set_pin_btn)

        # Reset Button
        reset_button = QPushButton("🔄 Reset Scores")
        reset_button.setStyleSheet(button_style)
        reset_button.clicked.connect(self.reset_scores)
        layout.addWidget(reset_button)

        self.setLayout(layout)

    def update_score(self, player, hole, value):
        self.scores[player][hole] = value
        total_scores = [sum(self.scores[p]) for p in range(4)]
        self.total_score_label.setText(
            f"Total: P1: {total_scores[0]} | P2: {total_scores[1]} | P3: {total_scores[2]} | P4: {total_scores[3]}"
        )

    def reset_scores(self):
        for player in range(4):
            for i in range(18):
                self.scores[player][i] = 0
                self.score_spinboxes[player][i].setValue(0)
        self.total_score_label.setText("Total Scores: P1: 0 | P2: 0 | P3: 0 | P4: 0")

    def get_gps_location(self):
        try:
            packet = gpsd.get_current()
            return (packet.lat, packet.lon)
        except Exception:
            return None

    def set_drive_start(self):
        self.drive_start = self.get_gps_location()
        if self.drive_start:
            self.drive_label.setText("Drive Start Recorded")

    def set_drive_end(self):
        self.drive_end = self.get_gps_location()
        if self.drive_end and self.drive_start:
            distance = geopy.distance.distance(self.drive_start, self.drive_end).meters
            self.drive_label.setText(f"Drive Distance: {distance:.2f} m")

    def set_pin_location(self):
        self.pin_location = self.get_gps_location()
        if self.pin_location:
            self.range_label.setText("Pin Location Set")
            if self.drive_end:
                distance = geopy.distance.distance(self.drive_end, self.pin_location).meters
                self.range_label.setText(f"Range to Pin: {distance:.2f} m")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.show()
    sys.exit(app.exec())
