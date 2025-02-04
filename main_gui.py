import sys
import json
import os
import geopy.distance
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QSpinBox, QStackedWidget,
    QLineEdit, QDialog
)
from PyQt6.QtCore import Qt  # noqa: F401
import gpsd

data_file = "courses.json"

class OnScreenKeyboard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard")
        self.setGeometry(100, 100, 400, 200)
        self.input_field = QLineEdit(self)
        self.input_field.setGeometry(50, 20, 300, 40)
        self.ok_button = QPushButton("OK", self)
        self.ok_button.setGeometry(150, 150, 100, 40)
        self.ok_button.clicked.connect(self.accept)
    
    def get_text(self):
        return self.input_field.text()

class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setGeometry(0, 0, 800, 480)
        
        self.scores = [[0] * 18 for _ in range(4)]  # 4 players, 18 holes
        self.current_page = 0
        self.players = ["Player 1", "Player 2", "Player 3", "Player 4"]
        self.pin_locations = {}
        self.tee_location = None
        self.load_course_data()
        
        gpsd.connect()
        self.initUI()
    
    def initUI(self):
        self.layout = QVBoxLayout()
        
        self.title_label = QLabel("Golf Scorecard", self)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: green;")
        self.layout.addWidget(self.title_label)
        
        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("Enter Course Name")
        self.course_name_input.mousePressEvent = self.show_keyboard
        self.layout.addWidget(self.course_name_input)
        
        self.stack = QStackedWidget()
        self.pages = [self.create_score_page(i) for i in range(2)]
        for page in self.pages:
            self.stack.addWidget(page)
        
        self.layout.addWidget(self.stack)
        
        self.total_score_label = QLabel("Total Scores: 0", self)
        self.layout.addWidget(self.total_score_label)
        
        self.page_switch_btn = QPushButton("Switch to Back 9", self)
        self.page_switch_btn.clicked.connect(self.switch_page)
        self.layout.addWidget(self.page_switch_btn)
        
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
    
    def create_score_page(self, page_idx):
        widget = QWidget()
        layout = QVBoxLayout()
        
        grid = QGridLayout()
        self.score_inputs = [[None] * 9 for _ in range(4)]
        
        for i in range(4):
            player_input = QLineEdit(self.players[i])
            player_input.mousePressEvent = lambda event, idx=i: self.show_keyboard_for_player(idx)
            grid.addWidget(player_input, i, 0)
            
            for j in range(9):
                spinbox = QSpinBox()
                spinbox.setRange(0, 10)
                spinbox.setValue(self.scores[i][j + (page_idx * 9)])
                spinbox.valueChanged.connect(lambda value, row=i, col=j + (page_idx * 9): self.update_score(row, col, value))
                self.score_inputs[i][j] = spinbox
                grid.addWidget(spinbox, i, j + 1)
        
        layout.addLayout(grid)
        widget.setLayout(layout)
        return widget
    
    def update_score(self, player, hole, value):
        self.scores[player][hole] = value
        total = sum(sum(player_scores) for player_scores in self.scores)
        self.total_score_label.setText(f"Total Scores: {total}")
    
    def switch_page(self):
        self.current_page = 1 - self.current_page
        self.stack.setCurrentIndex(self.current_page)
        self.page_switch_btn.setText("Switch to Front 9" if self.current_page else "Switch to Back 9")
    
    def load_course_data(self):
        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                self.pin_locations = json.load(f)
    
    def save_course_data(self):
        course_name = self.course_name_input.text()
        if course_name:
            self.pin_locations[course_name] = self.get_gps_location()
            with open(data_file, "w") as f:
                json.dump(self.pin_locations, f)
    
    def get_gps_location(self):
        try:
            packet = gpsd.get_current()
            return (packet.lat, packet.lon)
        except:  # noqa: E722
            return None
    
    def mark_tee_shot(self):
        self.tee_location = self.get_gps_location()
        if self.tee_location:
            print(f"Tee shot marked at: {self.tee_location}")
    
    def calculate_drive_distance(self):
        if self.tee_location:
            current_location = self.get_gps_location()
            if current_location:
                distance = geopy.distance.distance(self.tee_location, current_location).yards
                print(f"Drive distance: {distance:.2f} yards")
            else:
                print("Could not get current location")
        else:
            print("Tee shot location not set")
    
    def show_keyboard(self, event):
        keyboard = OnScreenKeyboard(self)
        if keyboard.exec():
            self.course_name_input.setText(keyboard.get_text())
    
    def show_keyboard_for_player(self, player_idx):
        keyboard = OnScreenKeyboard(self)
        if keyboard.exec():
            self.players[player_idx] = keyboard.get_text()
            self.initUI()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.showFullScreen()
    sys.exit(app.exec())
