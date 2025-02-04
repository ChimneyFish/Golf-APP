import sys
import json
import os
import geopy.distance
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QSpinBox, QLineEdit, QStackedWidget, QDialog)
from PyQt6.QtCore import Qt
import gpsd

gpsd.connect()

COURSE_DATA_FILE = "course_data.json"

def save_course_data(course_name, pin_locations):
    data = {}  
    if os.path.exists(COURSE_DATA_FILE):
        with open(COURSE_DATA_FILE, "r") as file:
            data = json.load(file)
    data[course_name] = pin_locations
    with open(COURSE_DATA_FILE, "w") as file:
        json.dump(data, file)

def load_course_data(course_name):
    if os.path.exists(COURSE_DATA_FILE):
        with open(COURSE_DATA_FILE, "r") as file:
            data = json.load(file)
        return data.get(course_name, [None] * 18)
    return [None] * 18

class OnScreenKeyboard(QDialog):
    def __init__(self, target_input):
        super().__init__()
        self.setWindowTitle("Keyboard")
        self.target_input = target_input
        layout = QVBoxLayout()
        self.input_field = QLineEdit(self)
        layout.addWidget(self.input_field)
        keys = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM", "SPACE"]
        for row in keys:
            row_layout = QVBoxLayout()
            for key in row:
                btn = QPushButton(" " if key == "SPACE" else key)
                btn.clicked.connect(lambda checked, k=key: self.add_key(k))
                row_layout.addWidget(btn)
            layout.addLayout(row_layout)
        self.setLayout(layout)
    
    def add_key(self, key):
        if key == "SPACE":
            self.input_field.setText(self.input_field.text() + " ")
        else:
            self.input_field.setText(self.input_field.text() + key)
    
    def accept(self):
        self.target_input.setText(self.input_field.text())
        super().accept()

class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setGeometry(0, 0, 800, 480)
        self.setStyleSheet("background-color: #2E7D32; color: white; font-size: 18px;")
        
        self.scores = [[0] * 9, [0] * 9]  # 18 holes split into two pages
        self.current_page = 0  # 0 for Front 9, 1 for Back 9
        self.pin_locations = [None] * 18
        self.players = ["Player 1", "Player 2", "Player 3", "Player 4"]
        
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("Enter Course Name")
        self.course_name_input.mousePressEvent = self.show_keyboard
        layout.addWidget(self.course_name_input)
        
        self.score_grid = QGridLayout()
        self.score_spinboxes = [[None] * 9 for _ in range(4)]
        
        for i in range(9):
            hole_label = QLabel(f"Hole {i + 1}")
            self.score_grid.addWidget(hole_label, 0, i)
            for p in range(4):
                self.score_spinboxes[p][i] = QSpinBox()
                self.score_spinboxes[p][i].setRange(0, 10)
                self.score_grid.addWidget(self.score_spinboxes[p][i], p + 1, i)
        
        layout.addLayout(self.score_grid)
        
        self.total_score_label = QLabel("Total Score: 0")
        layout.addWidget(self.total_score_label)
        
        self.drive_label = QLabel("Drive Distance: N/A")
        layout.addWidget(self.drive_label)
        
        self.range_label = QLabel("Range to Pin: N/A")
        layout.addWidget(self.range_label)
        
        self.set_drive_start_btn = QPushButton("Set Drive Start")
        self.set_drive_start_btn.clicked.connect(self.set_drive_start)
        layout.addWidget(self.set_drive_start_btn)
        
        self.set_drive_end_btn = QPushButton("Set Drive End")
        self.set_drive_end_btn.clicked.connect(self.set_drive_end)
        layout.addWidget(self.set_drive_end_btn)
        
        self.set_pin_btn = QPushButton("Set Pin Location")
        self.set_pin_btn.clicked.connect(self.set_pin_location)
        layout.addWidget(self.set_pin_btn)
        
        self.toggle_page_btn = QPushButton("Next 9 Holes")
        self.toggle_page_btn.clicked.connect(self.toggle_page)
        layout.addWidget(self.toggle_page_btn)
        
        self.save_course_btn = QPushButton("Save Course Data")
        self.save_course_btn.clicked.connect(self.save_course)
        layout.addWidget(self.save_course_btn)
        
        self.setLayout(layout)
    
    def show_keyboard(self, event):
        keyboard = OnScreenKeyboard(self.course_name_input)
        keyboard.exec()
    
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
        location = self.get_gps_location()
        if location:
            hole = self.current_page * 9 + len([p for p in self.pin_locations if p is not None])
            if hole < 18:
                self.pin_locations[hole] = location
                self.range_label.setText(f"Pin for Hole {hole + 1} Set")
    
    def get_gps_location(self):
        try:
            packet = gpsd.get_current()
            return (packet.lat, packet.lon)
        except:
            return None
    
    def toggle_page(self):
        self.current_page = 1 - self.current_page
        self.toggle_page_btn.setText("Back to Front 9" if self.current_page == 1 else "Next 9 Holes")
    
    def save_course(self):
        course_name = self.course_name_input.text().strip()
        if course_name:
            save_course_data(course_name, self.pin_locations)
            self.range_label.setText("Course Saved")
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.show()
    sys.exit(app.exec())
