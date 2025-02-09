import sys
import json
import geopy.distance
import gpsd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QDialog, QLineEdit, QVBoxLayout,
    QPushButton, QLabel, QGridLayout, QSpinBox, QComboBox
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

data_file = "courses.json"
club_data_file = "club_data.json"

class OnScreenKeyboard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard")
        self.setFixedSize(800, 600)  # Increased keyboard size
        
        layout = QVBoxLayout()
        self.input_field = QLineEdit(self)
        self.input_field.setFont(QFont("Arial", 24))  # Increase font size for input field
        layout.addWidget(self.input_field)
        
        key_layout = QGridLayout()
        keys = [
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P',
            'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L',
            'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Space', 'Backspace'
        ]
        row, col = 0, 0
        for key in keys:
            button = QPushButton(' ' if key == 'Space' else key)
            button.setFont(QFont("Arial", 18))  # Increase font size for buttons
            button.setFixedSize(80, 80)  # Increase button size
            if key == 'Space':
                button.clicked.connect(lambda checked: self.input_field.insert(' '))
            elif key == 'Backspace':
                button.clicked.connect(lambda checked: self.input_field.backspace())
            else:
                button.clicked.connect(lambda checked, k=key: self.input_field.insert(k))
            key_layout.addWidget(button, row, col)
            col += 1
            if col > 9:
                col = 0
                row += 1
        
        layout.addLayout(key_layout)
        
        action_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.setFont(QFont("Arial", 18))  # Increase font size for OK button
        self.ok_button.setFixedSize(120, 80)  # Increase OK button size
        self.ok_button.clicked.connect(self.accept)
        action_layout.addWidget(self.ok_button)
        
        layout.addLayout(action_layout)
        self.setLayout(layout)
    
    def get_text(self):
        return self.input_field.text()

# The rest of your code remains unchanged


class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⛳ Golf Range Finder & Scorekeeper ⛳")
        self.setFixedSize(1024, 600)

        self.scores = [[0] * 18 for _ in range(4)]  # Scores for 4 golfers
        self.drive_start = None
        self.drive_end = None
        self.pin_location = None
        self.course_name = ""
        self.player_names = ["Player 1", "Player 2", "Player 3", "Player 4"]
        self.course_data = {}  # To store tee and pin locations for courses
        self.club_distances = {}  # To store distances for each club
        self.selected_club = None

        gpsd.connect()  # Connect to GPS daemon
        
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#4CAF50"))  # Green background
        self.setPalette(palette)

        layout = QVBoxLayout()

        # Title Label
        self.title_label = QLabel("🏌️‍♂️ Golf Scorecard & GPS Tracker 🏌️‍♀️", self)
        self.title_label.setFont(QFont("Comic Sans MS", 24, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white; text-align: center;")
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Course Name Input
        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("Enter Course Name")
        self.course_name_input.setFont(QFont("Comic Sans MS", 16))
        self.course_name_input.setStyleSheet("color: black; padding: 5px;")
        self.course_name_input.mousePressEvent = self.show_keyboard
        layout.addWidget(self.course_name_input, alignment=Qt.AlignmentFlag.AlignCenter)

        # Course Load Dropdown
        self.load_course_dropdown = QComboBox(self)
        self.load_course_dropdown.addItem("Select Course to Load")
        self.load_course_dropdown.currentIndexChanged.connect(self.load_course_data)
        layout.addWidget(self.load_course_dropdown, alignment=Qt.AlignmentFlag.AlignCenter)
        self.load_courses()

        # Score Grid
        self.score_grid = QGridLayout()
        self.score_labels = []
        self.score_spinboxes = [[None] * 18 for _ in range(4)]

        # Hole Labels
        for i in range(18):
            hole_label = QLabel(f"Hole {i + 1}")
            hole_label.setFont(QFont("Comic Sans MS", 12))
            hole_label.setStyleSheet("color: white;")
            self.score_grid.addWidget(hole_label, 0, i + 1)
        
        # Player Labels and Score SpinBoxes
        for player in range(4):
            player_label = QLabel(self.player_names[player])
            player_label.setFont(QFont("Comic Sans MS", 16, QFont.Weight.Bold))
            player_label.setStyleSheet("color: white; padding: 5px;")
            player_label.mousePressEvent = lambda event, p=player: self.show_keyboard_for_player(p)
            self.score_grid.addWidget(player_label, player + 1, 0)

            for i in range(18):
                score_spinbox = QSpinBox()
                score_spinbox.setRange(0, 10)
                score_spinbox.setValue(self.scores[player][i])
                score_spinbox.setFixedSize(50, 50)  # Make spinboxes easier to tap
                score_spinbox.valueChanged.connect(lambda value, p=player, h=i: self.update_score(p, h, value))
                
                self.score_spinboxes[player][i] = score_spinbox

                self.score_grid.addWidget(score_spinbox, player + 1, i + 1)

        layout.addLayout(self.score_grid)

        # Total Score Display
        self.total_score_label = QLabel("Total Scores: P1: 0 | P2: 0 | P3: 0 | P4: 0")
        self.total_score_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(self.total_score_label)

        # GPS Functionality
        self.drive_label = QLabel("🚗 Drive Distance: N/A")
        self.range_label = QLabel("📍 Range to Pin: N/A")
        for label in [self.drive_label, self.range_label]:
            label.setFont(QFont("Comic Sans MS", 18))
            label.setStyleSheet("color: white; padding: 5px;")
            layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        button_style = """
            QPushButton {
                background-color: #FFEB3B;
                font-size: 18px;
                padding: 10px;
                border-radius: 10px;
                border: 2px solid black;
            }
            QPushButton:hover {
                background-color: #FBC02D;
            }
            QPushButton:pressed {
                background-color: #F57F17;
            }
        """

        # GPS Buttons
        self.set_drive_start_btn = QPushButton("🚗 Set Drive Start")
        self.set_drive_start_btn.setStyleSheet(button_style)
        self.set_drive_start_btn.clicked.connect(self.set_drive_start)
        layout.addWidget(self.set_drive_start_btn)

        self.set_drive_end_btn = QPushButton("🏁 Set Drive End")
        self.set_drive_end_btn.setStyleSheet(button_style)
        self.set_drive_end_btn.clicked.connect(self.set_drive_end)
        layout.addWidget(self.set_drive_end_btn)

        self.set_pin_btn = QPushButton("📌 Set Pin Location")
        self.set_pin_btn.setStyleSheet(button_style)
        self.set_pin_btn.clicked.connect(self.set_pin_location)
        layout.addWidget(self.set_pin_btn)

        # Club Selection
        self.club_selection = QComboBox(self)
        clubs = ["Driver", "3 Wood", "5 Wood", "Hybrid", "3 Iron", "4 Iron", "5 Iron", "6 Iron", "7 Iron", "8 Iron", "9 Iron", "Pitching Wedge", "Sand Wedge", "Lob Wedge", "Putter"]
        self.club_selection.addItems(clubs)
        self.club_selection.currentIndexChanged.connect(self.set_selected_club)
        layout.addWidget(self.club_selection)

        # Reset Button
        reset_button = QPushButton("🔄 Reset Scores")
        reset_button.setStyleSheet(button_style)
        reset_button.clicked.connect(self.reset_scores)
        layout.addWidget(reset_button)

        # Save Button
        save_button = QPushButton("💾 Save Course Data")
        save_button.setStyleSheet(button_style)
        save_button.clicked.connect(self.save_course_data)
        layout.addWidget(save_button)

        # Save Club Data Button
        save_club_button = QPushButton("💾 Save Club Data")
        save_club_button.setStyleSheet(button_style)
        save_club_button.clicked.connect(self.save_club_data)
        layout.addWidget(save_club_button)

        self.setLayout(layout)

    def show_keyboard(self, event):
        keyboard = OnScreenKeyboard(self)
        if keyboard.exec() == QDialog.DialogCode.Accepted:
            self.course_name_input.setText(keyboard.get_text())

    def show_keyboard_for_player(self, player):
        keyboard = OnScreenKeyboard(self)
        if keyboard.exec() == QDialog.DialogCode.Accepted:
            name = keyboard.get_text()
            self.player_names[player] = name
            player_label = self.score_grid.itemAtPosition(player + 1, 0).widget()
            player_label.setText(name)

    def update_score(self, player, hole, value):
        self.scores[player][hole] = value
        total_scores = [sum(self.scores[p]) for p in range(4)]
        self.total_score_label.setText(
            f"Total Scores: {self.player_names[0]}: {total_scores[0]} | "
            f"{self.player_names[1]}: {total_scores[1]} | "
            f"{self.player_names[2]}: {total_scores[2]} | "
            f"{self.player_names[3]}: {total_scores[3]}"
        )

    def reset_scores(self):
        for player in range(4):
            for i in range(18):
                self.scores[player][i] = 0
                self.score_spinboxes[player][i].setValue(0)
        self.total_score_label.setText(
            f"Total Scores: {self.player_names[0]}: 0 | "
            f"{self.player_names[1]}: 0 | "
            f"{self.player_names[2]}: 0 | "
            f"{self.player_names[3]}: 0"
        )

    def get_gps_location(self):
        try:
            packet = gpsd.get_current()
            if packet.mode >= 2:
                return (packet.lat, packet.lon)
            else:
                return None
        except Exception:
            return None

    def set_drive_start(self):
        self.drive_start = self.get_gps_location()
        if self.drive_start:
            self.drive_label.setText("🚗 Drive Start Recorded")
        else:
            self.drive_label.setText("🚗 GPS Unavailable")

    def set_drive_end(self):
        self.drive_end = self.get_gps_location()
        if self.drive_end and self.drive_start:
            distance = geopy.distance.distance(self.drive_start, self.drive_end).meters
            self.drive_label.setText(f"🚗 Drive Distance: {distance:.2f} m")
            self.record_club_distance(distance)
        else:
            self.drive_label.setText("🚗 Set Drive Start First or GPS Unavailable")

    def set_pin_location(self):
        self.pin_location = self.get_gps_location()
        if self.pin_location:
            self.range_label.setText("📍 Pin Location Set")
            if self.drive_end:
                distance = geopy.distance.distance(self.drive_end, self.pin_location).meters
                self.range_label.setText(f"📍 Range to Pin: {distance:.2f} m")
            else:
                self.range_label.setText("📍 Pin Set. Drive End Not Set.")
        else:
            self.range_label.setText("📍 GPS Unavailable")

    def load_courses(self):
        try:
            with open(data_file, 'r') as f:
                courses = json.load(f)
                for course in courses:
                    self.load_course_dropdown.addItem(course['course_name'])
        except FileNotFoundError:
            pass

    def load_course_data(self, index):
        if index == 0:
            return
        course_name = self.load_course_dropdown.currentText()
        try:
            with open(data_file, 'r') as f:
                courses = json.load(f)
                for course in courses:
                    if course['course_name'] == course_name:
                        self.course_name_input.setText(course['course_name'])
                        self.drive_start = course.get('tee_location', None)
                        self.pin_location = course.get('pin_location', None)
                        if self.drive_start:
                            self.drive_label.setText("🚗 Drive Start Recorded")
                        if self.pin_location:
                            self.range_label.setText("📍 Pin Location Set")
                        break
        except FileNotFoundError:
            pass

    def save_course_data(self):
        self.course_name = self.course_name_input.text()
        if not self.course_name:
            self.course_name_input.setPlaceholderText("Please enter a course name")
            return

        # Save tee and pin locations
        course_info = {
            'course_name': self.course_name,
            'tee_location': self.drive_start,
            'pin_location': self.pin_location
        }

        try:
            with open(data_file, 'r') as f:
                courses = json.load(f)
        except FileNotFoundError:
            courses = []

        courses.append(course_info)

        with open(data_file, 'w') as f:
            json.dump(courses, f, indent=4)

        self.course_name_input.setText("")
        self.drive_label.setText("🚗 Drive Distance: N/A")
        self.range_label.setText("📍 Range to Pin: N/A")
        self.drive_start = self.drive_end = self.pin_location = None

        self.title_label.setText(f"Course '{self.course_name}' Saved Successfully!")
        self.load_course_dropdown.addItem(self.course_name)

    def set_selected_club(self, index):
        self.selected_club = self.club_selection.currentText()

    def record_club_distance(self, distance):
        if not self.selected_club:
            return
        if self.selected_club not in self.club_distances:
            self.club_distances[self.selected_club] = []
        self.club_distances[self.selected_club].append(distance)

    def save_club_data(self):
        with open(club_data_file, 'w') as f:
            json.dump(self.club_distances, f, indent=4)

    def recommend_club(self, distance):
        club_recommendation = "No Data"
        closest_diff = float('inf')

        for club, distances in self.club_distances.items():
            avg_distance = sum(distances) / len(distances)
            diff = abs(distance - avg_distance)
            if diff < closest_diff:
                closest_diff = diff
                club_recommendation = club

        return club_recommendation

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.show()
    sys.exit(app.exec())
 