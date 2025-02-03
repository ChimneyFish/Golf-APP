import sys
import json
import geopy.distance
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QSpinBox, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt
import gpsd

class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setGeometry(100, 100, 600, 600)
        
        self.golfers = ["Golfer 1", "Golfer 2", "Golfer 3", "Golfer 4"]
        self.scores = {golfer: [0] * 18 for golfer in self.golfers}  # Scores for 4 golfers
        self.drive_start = None
        self.drive_end = None
        self.pin_location = None
        self.courses = self.load_courses()
        self.current_course = ""
        
        gpsd.connect()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Course Selection
        self.course_label = QLabel("Select Course:")
        self.course_dropdown = QComboBox()
        self.course_dropdown.addItems(["New Course"] + list(self.courses.keys()))
        self.course_dropdown.currentIndexChanged.connect(self.load_course)
        layout.addWidget(self.course_label)
        layout.addWidget(self.course_dropdown)
        
        # New Course Input
        self.new_course_input = QLineEdit()
        self.new_course_input.setPlaceholderText("Enter new course name")
        layout.addWidget(self.new_course_input)
        
        # Golfer Selection
        self.golfer_label = QLabel("Select Golfer:")
        self.golfer_dropdown = QComboBox()
        self.golfer_dropdown.addItems(self.golfers)
        self.golfer_dropdown.currentIndexChanged.connect(self.update_score_display)
        layout.addWidget(self.golfer_label)
        layout.addWidget(self.golfer_dropdown)
        
        # Score Grid
        self.score_grid = QGridLayout()
        self.score_labels = []
        self.score_spinboxes = []
        
        for i in range(18):
            hole_label = QLabel(f"Hole {i + 1}")
            score_spinbox = QSpinBox()
            score_spinbox.setRange(0, 10)
            score_spinbox.valueChanged.connect(lambda value, idx=i: self.update_score(idx, value))
            
            self.score_labels.append(hole_label)
            self.score_spinboxes.append(score_spinbox)
            self.score_grid.addWidget(hole_label, i // 9, (i % 9) * 2)
            self.score_grid.addWidget(score_spinbox, i // 9, (i % 9) * 2 + 1)
        
        layout.addLayout(self.score_grid)
        
        # Total Score Display
        self.total_score_label = QLabel("Total Score: 0")
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
        
        # Save and Load Buttons
        self.save_course_btn = QPushButton("Save Course")
        self.save_course_btn.clicked.connect(self.save_course)
        layout.addWidget(self.save_course_btn)
        
        self.setLayout(layout)
        self.update_score_display()
    
    def update_score(self, hole, value):
        golfer = self.golfer_dropdown.currentText()
        self.scores[golfer][hole] = value
        self.total_score_label.setText(f"Total Score: {sum(self.scores[golfer])}")
    
    def update_score_display(self):
        golfer = self.golfer_dropdown.currentText()
        for i in range(18):
            self.score_spinboxes[i].setValue(self.scores[golfer][i])
        self.total_score_label.setText(f"Total Score: {sum(self.scores[golfer])}")
    
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
        self.pin_location = self.get_gps_location()
        if self.pin_location:
            self.range_label.setText("Pin Location Set")
            if self.drive_end:
                distance = geopy.distance.distance(self.drive_end, self.pin_location).meters
                self.range_label.setText(f"Range to Pin: {distance:.2f} m")
    
    def save_course(self):
        course_name = self.new_course_input.text().strip()
        if not course_name:
            return
        self.courses[course_name] = {"pin_location": self.pin_location}
        self.save_courses()
        self.course_dropdown.addItem(course_name)
        self.new_course_input.clear()
    
    def load_course(self):
        course_name = self.course_dropdown.currentText()
        if course_name == "New Course":
            return
        self.current_course = course_name
        if course_name in self.courses:
            self.pin_location = self.courses[course_name].get("pin_location", None)
            self.range_label.setText("Loaded Course Pins")
    
    def save_courses(self):
        with open("courses.json", "w") as file:
            json.dump(self.courses, file)
    
    def load_courses(self):
        try:
            with open("courses.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.show()
    sys.exit(app.exec())
