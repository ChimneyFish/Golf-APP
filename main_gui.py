import sys
import json
import geopy.distance
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QGridLayout, QSpinBox, QComboBox, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt
import gpsd

COURSES_FILE = "courses.json"

def load_courses():
    try:
        with open(COURSES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_courses(courses):
    with open(COURSES_FILE, "w") as f:
        json.dump(courses, f, indent=4)

class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setGeometry(100, 100, 500, 600)
        
        self.scores = [0] * 18
        self.drive_start = None
        self.drive_end = None
        self.current_course = None
        self.pin_locations = {}  # Dictionary to store pin locations by hole
        self.courses = load_courses()
        
        gpsd.connect()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        self.title_label = QLabel("Golf Scorecard", self)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # Course Selection
        self.course_dropdown = QComboBox()
        self.course_dropdown.addItems(["Select Course"] + list(self.courses.keys()))
        self.course_dropdown.currentTextChanged.connect(self.load_course)
        layout.addWidget(self.course_dropdown)
        
        self.new_course_input = QLineEdit()
        self.new_course_input.setPlaceholderText("Enter New Course Name")
        layout.addWidget(self.new_course_input)
        
        self.save_course_btn = QPushButton("Save Course")
        self.save_course_btn.clicked.connect(self.save_course)
        layout.addWidget(self.save_course_btn)
        
        # Score Grid
        self.score_grid = QGridLayout()
        self.score_spinboxes = []
        
        for i in range(18):
            hole_label = QLabel(f"Hole {i + 1}")
            score_spinbox = QSpinBox()
            score_spinbox.setRange(0, 10)
            score_spinbox.setValue(self.scores[i])
            score_spinbox.valueChanged.connect(lambda value, idx=i: self.update_score(idx, value))
            
            self.score_spinboxes.append(score_spinbox)
            self.score_grid.addWidget(hole_label, i // 9, (i % 9) * 2)
            self.score_grid.addWidget(score_spinbox, i // 9, (i % 9) * 2 + 1)
        
        layout.addLayout(self.score_grid)
        
        self.total_score_label = QLabel("Total Score: 0")
        self.total_score_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.total_score_label)
        
        # GPS Functionality
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
        
        reset_button = QPushButton("Reset Scores")
        reset_button.clicked.connect(self.reset_scores)
        layout.addWidget(reset_button)
        
        self.setLayout(layout)
    
    def update_score(self, hole, value):
        self.scores[hole] = value
        self.total_score_label.setText(f"Total Score: {sum(self.scores)}")
    
    def reset_scores(self):
        for i in range(18):
            self.scores[i] = 0
            self.score_spinboxes[i].setValue(0)
        self.total_score_label.setText("Total Score: 0")
    
    def get_gps_location(self):
        try:
            packet = gpsd.get_current()
            return (packet.lat, packet.lon)
        except Exception as e:
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
        if not self.current_course:
            QMessageBox.warning(self, "Error", "Please select or save a course first.")
            return
        
        hole_number = sum(1 for _ in self.pin_locations) + 1
        if hole_number > 18:
            QMessageBox.warning(self, "Error", "All 18 holes are already recorded!")
            return
        
        location = self.get_gps_location()
        if location:
            self.pin_locations[hole_number] = location
            QMessageBox.information(self, "Success", f"Pin location set for Hole {hole_number}.")
    
    def save_course(self):
        course_name = self.new_course_input.text().strip()
        if not course_name:
            QMessageBox.warning(self, "Error", "Please enter a valid course name.")
            return
        
        self.courses[course_name] = self.pin_locations
        save_courses(self.courses)
        self.course_dropdown.addItem(course_name)
        self.new_course_input.clear()
        QMessageBox.information(self, "Success", f"Course '{course_name}' saved!")
    
    def load_course(self, course_name):
        if course_name == "Select Course":
            return
        
        self.current_course = course_name
        self.pin_locations = self.courses.get(course_name, {})
        QMessageBox.information(self, "Course Loaded", f"Loaded course: {course_name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.show()
    sys.exit(app.exec())
