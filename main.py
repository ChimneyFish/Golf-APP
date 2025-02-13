import sys
import json
import serial
import pynmea2
import geopy.distance
import time
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QDialog, QLineEdit, QVBoxLayout,
    QPushButton, QLabel, QGridLayout, QSpinBox, QComboBox, QStackedWidget, QScrollArea
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt, pyqtSignal

data_file = "courses.json"
club_data_file = "club_data.json"

class OnScreenKeyboard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard")
        self.setFixedSize(600, 300)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        self.input_field = QLineEdit(self)
        self.input_field.setFont(QFont("Arial", 14))
        layout.addWidget(self.input_field)

        key_layout = QGridLayout()
        key_layout.setSpacing(2)

        keys = [
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P',
            'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L',
            'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Space', 'Back', 'Enter'
        ]
        row, col = 0, 0
        for key in keys:
            button = QPushButton(' ' if key == 'Space' else key)
            button.setFont(QFont("Arial", 14))
            button.setFixedSize(50, 50)
            button.setStyleSheet("border-radius: 10px; background-color: #f2f2f2;")
            if key == 'Space':
                button.clicked.connect(lambda checked: self.input_field.insert(' '))
            elif key == 'Back':
                button.clicked.connect(lambda checked: self.input_field.backspace())
            elif key == 'Enter':
                button.clicked.connect(self.accept)
            else:
                button.clicked.connect(lambda checked, k=key: self.input_field.insert(k))
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
    location_updated = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setFixedSize(1024, 550)

        self.scores = [[0] * 18 for _ in range(4)]
        self.drive_start = None
        self.drive_end = None
        self.pin_locations = {}
        self.current_location = None
        self.course_name = ""
        self.player_names = ["Player 1", "Player 2", "Player 3", "Player 4"]
        self.course_data = {}
        self.club_distances = {}
        self.selected_club = None

        self.initUI()

    def fetch_external_gps_coordinates(self):
        port="/dev/ttyAMA0"

        while True:
            try:
                with serial.Serial(port, baudrate=9600, timeout=0.5) as ser:
                    newdata = ser.readline().decode("utf-8", errors="ignore").strip()
                    if newdata.startswith("$GPRMC"):  # Removed unnecessary backslash
                        try:
                            newmsg = pynmea2.parse(newdata)
                            lat = newmsg.latitude
                            lng = newmsg.longitude
                            if lat is not None and lng is not None:
                                self.location_updated.emit(lat, lng)
                                print(f"GPS Coordinates Updated: {lat}, {lng}")  # Debugging
                        except pynmea2.ParseError:
                            print("Error parsing GPS data")
            except serial.SerialException as e:
                print(f"Serial error: {e}")
        
            time.sleep(2)

        
    def initUI(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#2E8B57"))
        self.setPalette(palette)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(7, 7, 7, 7)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        self.title_label = QLabel("Golf Scorecard & GPS Tracker", self)
        self.title_label.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #FFFFFF; text-align: center;")
        main_layout.addWidget(self.title_label, alignment=Qt.AlignCenter)

        course_layout = QHBoxLayout()
        course_layout.setSpacing(4)

        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("Course Name")
        self.course_name_input.setFont(QFont("Helvetica", 14))
        self.course_name_input.setFixedHeight(30)
        self.course_name_input.mousePressEvent = self.show_keyboard
        self.course_name_input.setStyleSheet("background-color: #f2f2f2; padding: 5px;")
        course_layout.addWidget(self.course_name_input)

        self.load_course_dropdown = QComboBox(self)
        self.load_course_dropdown.addItem("Select Course")
        self.load_course_dropdown.currentIndexChanged.connect(self.load_course_data)
        self.load_courses()
        self.load_course_dropdown.setFixedHeight(30)
        self.load_course_dropdown.setStyleSheet("background-color: #f2f2f2;")
        course_layout.addWidget(self.load_course_dropdown)

        main_layout.addLayout(course_layout)

        self.score_stack = QStackedWidget(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.score_stack)
        main_layout.addWidget(scroll_area)

        self.create_score_grids()

        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(7)

        self.front9_button = QPushButton("Front 9")
        self.front9_button.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
        self.front9_button.setFixedSize(60, 60)
        self.front9_button.setStyleSheet("border-radius: 40px; background-color: #FFA500; color: #FFFFFF;")
        self.front9_button.clicked.connect(lambda: self.score_stack.setCurrentIndex(0))

        self.back9_button = QPushButton("Back 9")
        self.back9_button.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
        self.back9_button.setFixedSize(60, 60)
        self.back9_button.setStyleSheet("border-radius: 40px; background-color: #FFA500; color: #FFFFFF;")
        self.back9_button.clicked.connect(lambda: self.score_stack.setCurrentIndex(1))

        toggle_layout.addWidget(self.front9_button)
        toggle_layout.addWidget(self.back9_button)
        main_layout.addLayout(toggle_layout)

        self.total_score_label = QLabel("Total Scores:")
        self.total_score_label.setFont(QFont("Helvetica", 16, QFont.Weight.Bold))
        self.total_score_label.setStyleSheet("color: #FFFFFF;")
        main_layout.addWidget(self.total_score_label, alignment=Qt.AlignCenter)

        gps_layout = QHBoxLayout()
        gps_layout.setSpacing(10)

        self.drive_label = QLabel("Drive Distance: N/A")
        self.drive_label.setFont(QFont("Helvetica", 14))
        self.drive_label.setStyleSheet("color: #FFFFFF;")
        gps_layout.addWidget(self.drive_label)

        self.range_label = QLabel("Range to Pin: N/A")
        self.range_label.setFont(QFont("Helvetica", 14))
        self.range_label.setStyleSheet("color: #FFFFFF;")
        gps_layout.addWidget(self.range_label)

        main_layout.addLayout(gps_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.set_drive_start_btn = QPushButton("Start")
        self.set_drive_start_btn.setFont(QFont("Helvetica", 12))
        self.set_drive_start_btn.setFixedSize(60, 60)
        self.set_drive_start_btn.setStyleSheet("border-radius: 30px; background-color: #FF4500; color: #FFFFFF;")
        self.set_drive_start_btn.clicked.connect(self.set_drive_start)
        self.set_drive_start_btn.setToolTip("Set Drive Start")
        buttons_layout.addWidget(self.set_drive_start_btn)

        self.set_drive_end_btn = QPushButton("End")
        self.set_drive_end_btn.setFont(QFont("Helvetica", 12))
        self.set_drive_end_btn.setFixedSize(60, 60)
        self.set_drive_end_btn.setStyleSheet("border-radius: 30px; background-color: #FF4500; color: #FFFFFF;")
        self.set_drive_end_btn.clicked.connect(self.set_drive_end)
        self.set_drive_end_btn.setToolTip("Set Drive End")
        buttons_layout.addWidget(self.set_drive_end_btn)

        self.set_pin_btn = QPushButton("Pin")
        self.set_pin_btn.setFont(QFont("Helvetica", 12))
        self.set_pin_btn.setFixedSize(60, 60)
        self.set_pin_btn.setStyleSheet("border-radius: 30px; background-color: #FF4500; color: #FFFFFF;")
        self.set_pin_btn.setToolTip("Set Pin Location")
        buttons_layout.addWidget(self.set_pin_btn)

        self.club_selection = QComboBox(self)
        clubs = [
            "Select Club", "Driver", "3 Wood", "5 Wood", "Hybrid", "3 Iron", "4 Iron", "5 Iron",
            "6 Iron", "7 Iron", "8 Iron", "9 Iron", "Pitching Wedge", "Sand Wedge", "Lob Wedge", "Putter"
        ]
        self.club_selection.addItems(clubs)
        self.club_selection.setFont(QFont("Helvetica", 12))
        self.club_selection.setFixedHeight(30)
        self.club_selection.setFixedWidth(150)
        self.club_selection.setStyleSheet("background-color: #f2f2f2; padding: 5px;")
        self.club_selection.currentIndexChanged.connect(self.set_selected_club)
        buttons_layout.addWidget(self.club_selection)

        reset_button = QPushButton("Reset")
        reset_button.setFont(QFont("Helvetica", 12))
        reset_button.setFixedSize(60, 60)
        reset_button.setStyleSheet("border-radius: 30px; background-color: #FF0000; color: #FFFFFF;")
        reset_button.clicked.connect(self.reset_scores)
        buttons_layout.addWidget(reset_button)

        save_button = QPushButton("Save")
        save_button.setFont(QFont("Helvetica", 12))
        save_button.setFixedSize(60, 60)
        save_button.setStyleSheet("border-radius: 30px; background-color: #32CD32; color: #FFFFFF;")
        save_button.clicked.connect(self.save_course_data)
        buttons_layout.addWidget(save_button)

        main_layout.addLayout(buttons_layout)
    
    def start_gps_thread(self):
        self.gps_thread = threading.Thread(target=self.fetch_external_gps_coordinates, daemon=True)
        self.gps_thread.start()

    def update_current_location(self, lat, lng):
        print(f"Updating location on UI: {lat}, {lng}")  # Debugging
        self.current_location = (lat, lng)
        self.gps_info_label.setText(f"Current Location: {lat:.6f}, {lng:.6f}")
  
        
        if self.last_location:
            distance = geopy.distance.geodesic(self.last_location, self.current_location).meters
            self.distance_label.setText(f"Distance Traveled: {distance:.2f} m")
        
    def start_tracking(self):
        self.last_location = self.current_location
        self.distance_label.setText("Distance Traveled: 0.00 m")
    
    def stop_tracking(self):
        self.last_location = None
        self.distance_label.setText("Distance Traveled: N/A")

    def create_score_grids(self):
        # Front 9
        self.front9_widget = QWidget()
        front9_layout = QGridLayout()
        front9_layout.setSpacing(2)
        front9_layout.setContentsMargins(0, 0, 0, 0)
        self.front9_widget.setLayout(front9_layout)

        # Back 9
        self.back9_widget = QWidget()
        back9_layout = QGridLayout()
        back9_layout.setSpacing(2)
        back9_layout.setContentsMargins(0, 0, 0, 0)
        self.back9_widget.setLayout(back9_layout)

        self.score_stack.addWidget(self.front9_widget)
        self.score_stack.addWidget(self.back9_widget)

        for player in range(4):
            # Player Labels
            player_label_front = QLabel(self.player_names[player])
            player_label_front.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
            player_label_front.setStyleSheet("color: white;")
            player_label_front.mousePressEvent = lambda event, p=player: self.show_keyboard_for_player(p)
            player_label_back = QLabel(self.player_names[player])
            player_label_back.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
            player_label_back.setStyleSheet("color: white;")
            player_label_back.mousePressEvent = lambda event, p=player: self.show_keyboard_for_player(p)
            front9_layout.addWidget(player_label_front, player + 1, 0)
            back9_layout.addWidget(player_label_back, player + 1, 0)

            for i in range(9):
                # Front 9 Holes
                if player == 0:
                    hole_label = QPushButton(f"{i + 1}")
                    hole_label.setFont(QFont("Helvetica", 16))
                    hole_label.setStyleSheet("background-color: #FFA500; color: #FFFFFF;")
                    hole_label.clicked.connect(lambda _, h=i: self.set_pin_location(h))
                    front9_layout.addWidget(hole_label, 0, i + 1)

                score_spinbox_front = QSpinBox()
                score_spinbox_front.setRange(0, 10)
                score_spinbox_front.setValue(self.scores[player][i])
                score_spinbox_front.setFixedSize(50, 50)
                score_spinbox_front.valueChanged.connect(lambda value, p=player, h=i: self.update_score(p, h, value))
                front9_layout.addWidget(score_spinbox_front, player + 1, i + 1)

                # Back 9 Holes
                if player == 0:
                    hole_label = QPushButton(f"{i + 10}")
                    hole_label.setFont(QFont("Helvetica", 16))
                    hole_label.setStyleSheet("background-color: #FFA500; color: #FFFFFF;")
                    hole_label.clicked.connect(lambda _, h=i + 9: self.set_pin_location(h))
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
        for widget in [self.front9_widget, self.back9_widget]:
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
        if self.current_location:
            return self.current_location
        else:
            return None

    def set_drive_start(self):
        self.drive_start = self.get_gps_location()
        if self.drive_start:
            self.drive_label.setText("Drive Start Recorded")
        else:
            self.drive_label.setText("GPS Unavailable")

    def set_drive_end(self):
        self.drive_end = self.get_gps_location()
        if self.drive_end and self.drive_start:
            distance = geopy.distance.distance(self.drive_start, self.drive_end).meters
            self.drive_label.setText(f"Drive Distance: {distance:.2f} m")
            self.record_club_distance(distance)
        else:
            self.drive_label.setText("Set Drive Start First or GPS Unavailable")

    def set_pin_location(self, hole):
        pin_location = self.get_gps_location()
        if pin_location:
            self.pin_locations[hole] = pin_location
            self.range_label.setText(f"Pin for Hole {hole + 1} Set")
        else:
            self.range_label.setText("GPS Unavailable")

    def load_courses(self):
        try:
            with open(data_file, 'r') as f:
                courses = json.load(f)
                self.load_course_dropdown.clear()
                self.load_course_dropdown.addItem("Select Course")
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
                        self.course_name_input.setText(course_name)
                        self.drive_start = course.get('tee_location', None)
                        self.pin_locations = course.get('pin_locations', {})
                        if self.drive_start:
                            self.drive_label.setText("Drive Start Recorded")
                        else:
                            self.drive_label.setText("Drive Start: N/A")
                        self.range_label.setText("Pin Locations Loaded")
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
            'pin_locations': self.pin_locations
        }

        try:
            with open(data_file, 'r') as f:
                courses = json.load(f)
        except FileNotFoundError:
            courses = []

    # Remove any existing course with the same name
        courses = [c for c in courses if c['course_name'] != self.course_name]
        courses.append(course_info)

        with open(data_file, 'w') as f:
            json.dump(courses, f, indent=4)

        self.course_name_input.setText("")
        self.drive_label.setText("Drive Distance: N/A")
        self.range_label.setText("Range to Pin: N/A")
        self.drive_start = self.drive_end = None

        self.title_label.setText(f"Course '{self.course_name}' Saved Successfully!")
        self.load_courses()

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

    def closeEvent(self, event):
    # Stop the external GPS fetching thread when the application is closed
        self.external_gps_thread.join(0)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.show()
    sys.exit(app.exec_())
