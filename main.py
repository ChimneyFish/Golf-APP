import sys
import json
import geopy.distance
import gpsd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QDialog, QLineEdit, QVBoxLayout,
    QPushButton, QLabel, QGridLayout, QSpinBox, QComboBox, QStackedWidget
)
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt

data_file = "courses.json"
club_data_file = "club_data.json"

class OnScreenKeyboard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard")
        self.setFixedSize(800, 500)  # Adjusted size to fit 1024x600 screen

        layout = QVBoxLayout()
        self.input_field = QLineEdit(self)
        self.input_field.setFont(QFont("Arial", 24))  # Increase font size for input field
        layout.addWidget(self.input_field)

        key_layout = QGridLayout()
        keys = [
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P',
            'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L',
            'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Space', 'Backspace', 'Enter'
        ]
        row, col = 0, 0
        for key in keys:
            button = QPushButton(' ' if key == 'Space' else key)
            button.setFont(QFont("Arial", 18))  # Increase font size for buttons
            button.setFixedSize(70, 70)  # Adjust button size
            if key == 'Space':
                button.clicked.connect(lambda checked: self.input_field.insert(' '))
            elif key == 'Backspace':
                button.clicked.connect(lambda checked: self.input_field.backspace())
            elif key == 'Enter':
                button.clicked.connect(self.accept)
            else:
                button.clicked.connect(lambda checked, k=key: self.input_field.insert(k))
            button.setStyleSheet("border-radius: 35px;")  # Make buttons round
            key_layout.addWidget(button, row, col)
            col += 1
            if col > 9:
                col = 0
                row += 1

        layout.addLayout(key_layout)

        self.setLayout(layout)

    def get_text(self):
        return self.input_field.text()

class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⛳ Golf Range Finder & Scorekeeper ⛳")
        self.setFixedSize(1024, 600)

        self.scores = [[0] * 18 for _ in range(4)]  # Scores for 4 golfers
        self.current_holes = list(range(9))  # Start with Front 9
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
        palette.setColor(QPalette.Window, QColor("#4CAF50"))  # Green background
        self.setPalette(palette)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Title Label
        self.title_label = QLabel("🏌️‍♂️ Golf Scorecard & GPS Tracker 🏌️‍♀️", self)
        self.title_label.setFont(QFont("Comic Sans MS", 24, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white; text-align: center;")
        main_layout.addWidget(self.title_label, alignment=Qt.AlignCenter)

        # Course Name Input and Load Dropdown
        course_layout = QHBoxLayout()

        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("Enter Course Name")
        self.course_name_input.setFont(QFont("Comic Sans MS", 16))
        self.course_name_input.setStyleSheet("color: black; padding: 5px;")
        self.course_name_input.mousePressEvent = self.show_keyboard
        course_layout.addWidget(self.course_name_input)

        self.load_course_dropdown = QComboBox(self)
        self.load_course_dropdown.addItem("Select Course to Load")
        self.load_course_dropdown.currentIndexChanged.connect(self.load_course_data)
        course_layout.addWidget(self.load_course_dropdown)
        self.load_courses()

        main_layout.addLayout(course_layout)

        # Stack Widget for Front 9 and Back 9
        self.score_stack = QStackedWidget(self)
        main_layout.addWidget(self.score_stack)

        # Create Front 9 and Back 9 score grids
        self.create_score_grids()

        # Toggle Buttons for Front 9 and Back 9
        toggle_layout = QHBoxLayout()
        self.front9_button = QPushButton("Front 9")
        self.front9_button.setFont(QFont("Arial", 14))
        self.front9_button.setFixedSize(100, 100)
        self.front9_button.setStyleSheet("border-radius:50px; background-color:#FBC02D;")
        self.front9_button.clicked.connect(lambda: self.score_stack.setCurrentIndex(0))

        self.back9_button = QPushButton("Back 9")
        self.back9_button.setFont(QFont("Arial", 14))
        self.back9_button.setFixedSize(100, 100)
        self.back9_button.setStyleSheet("border-radius:50px; background-color:#FBC02D;")
        self.back9_button.clicked.connect(lambda: self.score_stack.setCurrentIndex(1))

        toggle_layout.addWidget(self.front9_button, alignment=Qt.AlignCenter)
        toggle_layout.addWidget(self.back9_button, alignment=Qt.AlignCenter)
        main_layout.addLayout(toggle_layout)

        # Total Score Display
        self.total_score_label = QLabel("Total Scores:")
        self.total_score_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.total_score_label.setStyleSheet("color: white;")
        main_layout.addWidget(self.total_score_label)

        # GPS Functionality Labels
        gps_layout = QHBoxLayout()
        self.drive_label = QLabel("🚗 Drive Distance: N/A")
        self.range_label = QLabel("📍 Range to Pin: N/A")
        for label in [self.drive_label, self.range_label]:
            label.setFont(QFont("Comic Sans MS", 18))
            label.setStyleSheet("color: white; padding: 5px;")
            gps_layout.addWidget(label, alignment=Qt.AlignCenter)
        main_layout.addLayout(gps_layout)

        # Buttons Layout
        buttons_layout = QHBoxLayout()

        self.set_drive_start_btn = QPushButton()
        self.set_drive_start_btn.setIcon(QIcon("drive_start_icon.png"))  # Add appropriate icons
        self.set_drive_start_btn.setIconSize(Qt.QSize(50,50))
        self.set_drive_start_btn.setFixedSize(80, 80)
        self.set_drive_start_btn.setStyleSheet("border-radius:40px; background-color:#FFEB3B;")
        self.set_drive_start_btn.clicked.connect(self.set_drive_start)
        self.set_drive_start_btn.setToolTip("Set Drive Start")
        buttons_layout.addWidget(self.set_drive_start_btn)

        self.set_drive_end_btn = QPushButton()
        self.set_drive_end_btn.setIcon(QIcon("drive_end_icon.png"))
        self.set_drive_end_btn.setIconSize(Qt.QSize(50,50))
        self.set_drive_end_btn.setFixedSize(80, 80)
        self.set_drive_end_btn.setStyleSheet("border-radius:40px; background-color:#FFEB3B;")
        self.set_drive_end_btn.clicked.connect(self.set_drive_end)
        self.set_drive_end_btn.setToolTip("Set Drive End")
        buttons_layout.addWidget(self.set_drive_end_btn)

        self.set_pin_btn = QPushButton()
        self.set_pin_btn.setIcon(QIcon("pin_icon.png"))
        self.set_pin_btn.setIconSize(Qt.QSize(50,50))
        self.set_pin_btn.setFixedSize(80, 80)
        self.set_pin_btn.setStyleSheet("border-radius:40px; background-color:#FFEB3B;")
        self.set_pin_btn.clicked.connect(self.set_pin_location)
        self.set_pin_btn.setToolTip("Set Pin Location")
        buttons_layout.addWidget(self.set_pin_btn)

        # Club Selection
        self.club_selection = QComboBox(self)
        clubs = ["Select Club", "Driver", "3 Wood", "5 Wood", "Hybrid", "3 Iron", "4 Iron", "5 Iron",
                 "6 Iron", "7 Iron", "8 Iron", "9 Iron", "Pitching Wedge", "Sand Wedge", "Lob Wedge", "Putter"]
        self.club_selection.addItems(clubs)
        self.club_selection.setFont(QFont("Arial", 14))
        self.club_selection.setStyleSheet("background-color: white;")
        self.club_selection.currentIndexChanged.connect(self.set_selected_club)
        buttons_layout.addWidget(self.club_selection)

        # Reset Button
        reset_button = QPushButton("Reset")
        reset_button.setFont(QFont("Arial", 14))
        reset_button.setFixedSize(80, 80)
        reset_button.setStyleSheet("border-radius:40px; background-color:#EF5350; color: white;")
        reset_button.clicked.connect(self.reset_scores)
        buttons_layout.addWidget(reset_button)

        # Save Button
        save_button = QPushButton("Save")
        save_button.setFont(QFont("Arial", 14))
        save_button.setFixedSize(80, 80)
        save_button.setStyleSheet("border-radius:40px; background-color:#66BB6A; color: white;")
        save_button.clicked.connect(self.save_course_data)
        buttons_layout.addWidget(save_button)

        main_layout.addLayout(buttons_layout)

    def create_score_grids(self):
        # Front 9
        self.front9_widget = QWidget()
        front9_layout = QGridLayout()
        self.front9_widget.setLayout(front9_layout)

        # Back 9
        self.back9_widget = QWidget()
        back9_layout = QGridLayout()
        self.back9_widget.setLayout(back9_layout)

        self.score_stack.addWidget(self.front9_widget)
        self.score_stack.addWidget(self.back9_widget)

        for player in range(4):
            # Player Labels
            player_label_front = QLabel(self.player_names[player])
            player_label_front.setFont(QFont("Comic Sans MS", 14, QFont.Weight.Bold))
            player_label_front.setStyleSheet("color: white; padding: 5px;")
            player_label_front.mousePressEvent = lambda event, p=player: self.show_keyboard_for_player(p)

            player_label_back = QLabel(self.player_names[player])
            player_label_back.setFont(QFont("Comic Sans MS", 14, QFont.Weight.Bold))
            player_label_back.setStyleSheet("color: white; padding: 5px;")
            player_label_back.mousePressEvent = lambda event, p=player: self.show_keyboard_for_player(p)

            front9_layout.addWidget(player_label_front, player + 1, 0)
            back9_layout.addWidget(player_label_back, player + 1, 0)

            for i in range(9):
                # Front 9 Holes
                if player == 0:
                    hole_label = QLabel(f"Hole {i + 1}")
                    hole_label.setFont(QFont("Comic Sans MS", 12))
                    hole_label.setStyleSheet("color: white;")
                    front9_layout.addWidget(hole_label, 0, i + 1)

                score_spinbox_front = QSpinBox()
                score_spinbox_front.setRange(0, 10)
                score_spinbox_front.setValue(self.scores[player][i])
                score_spinbox_front.setFixedSize(50, 50)
                score_spinbox_front.valueChanged.connect(lambda value, p=player, h=i: self.update_score(p, h, value))
                front9_layout.addWidget(score_spinbox_front, player + 1, i + 1)

                # Back 9 Holes
                if player == 0:
                    hole_label = QLabel(f"Hole {i + 10}")
                    hole_label.setFont(QFont("Comic Sans MS", 12))
                    hole_label.setStyleSheet("color: white;")
                    back9_layout.addWidget(hole_label, 0, i + 1)

                score_spinbox_back = QSpinBox()
                score_spinbox_back.setRange(0, 10)
                score_spinbox_back.setValue(self.scores[player][i + 9])
                score_spinbox_back.setFixedSize(50, 50)
                score_spinbox_back.valueChanged.connect(lambda value, p=player, h=i + 9: self.update_score(p, h, value))
                back9_layout.addWidget(score_spinbox_back, player + 1, i + 1)

    def show_keyboard(self, event):
        keyboard = OnScreenKeyboard(self)
        if keyboard.exec_() == QDialog.Accepted:
            self.course_name_input.setText(keyboard.get_text())

    def show_keyboard_for_player(self, player):
        keyboard = OnScreenKeyboard(self)
        if keyboard.exec_() == QDialog.Accepted:
            name = keyboard.get_text()
            self.player_names[player] = name
            self.update_player_labels()

    def update_player_labels(self):
        # Update player labels on both Front 9 and Back 9
        for index, widget in enumerate([self.front9_widget, self.back9_widget]):
            layout = widget.layout()
            for player in range(4):
                player_label = layout.itemAtPosition(player + 1, 0).widget()
                player_label.setText(self.player_names[player])

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
        self.update_spinboxes()
        self.update_score(0, 0, 0)  # Update total scores

    def update_spinboxes(self):
        # Update spinboxes on both Front 9 and Back 9
        for index, widget in enumerate([self.front9_widget, self.back9_widget]):
            layout = widget.layout()
            for player in range(4):
                for i in range(9):
                    spinbox = layout.itemAtPosition(player + 1, i + 1).widget()
                    hole_index = i + (0 if index == 0 else 9)
                    spinbox.setValue(self.scores[player][hole_index])

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
        if index == 0:
            self.selected_club = None
        else:
            self.selected_club = self.club_selection.currentText()

    def record_club_distance(self, distance):
        if not self.selected_club or self.selected_club == "Select Club":
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
    sys.exit(app.exec_())
