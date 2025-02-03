import sys
import geopy.distance
import gpsd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, 
    QGridLayout, QSpinBox, QLineEdit
)
from PyQt6.QtCore import Qt


class OnScreenKeyboard(QWidget):
    """Custom on-screen keyboard for touch-based input."""
    
    def __init__(self, target_input):
        super().__init__()
        self.target_input = target_input  # Reference to the input field
        self.setWindowTitle("On-Screen Keyboard")
        self.setGeometry(200, 200, 600, 300)
        
        layout = QVBoxLayout()
        self.keys = [
            "QWERTYUIOP",
            "ASDFGHJKL",
            "ZXCVBNM"
        ]
        
        grid = QGridLayout()
        for row, key_row in enumerate(self.keys):
            for col, key in enumerate(key_row):
                btn = QPushButton(key)
                btn.setFixedSize(50, 50)
                btn.clicked.connect(lambda _, k=key: self.add_character(k))
                grid.addWidget(btn, row, col)
        
        # Space, Backspace, and Enter
        space_btn = QPushButton("Space")
        space_btn.setFixedSize(200, 50)
        space_btn.clicked.connect(lambda: self.add_character(" "))

        backspace_btn = QPushButton("Backspace")
        backspace_btn.setFixedSize(100, 50)
        backspace_btn.clicked.connect(self.remove_character)

        enter_btn = QPushButton("Enter")
        enter_btn.setFixedSize(100, 50)
        enter_btn.clicked.connect(self.close)  # Close keyboard when enter is pressed

        control_layout = QGridLayout()
        control_layout.addWidget(space_btn, 0, 0, 1, 2)
        control_layout.addWidget(backspace_btn, 0, 2)
        control_layout.addWidget(enter_btn, 0, 3)

        layout.addLayout(grid)
        layout.addLayout(control_layout)
        self.setLayout(layout)

    def add_character(self, char):
        """Append a character to the input field."""
        current_text = self.target_input.text()
        self.target_input.setText(current_text + char)

    def remove_character(self):
        """Remove the last character from the input field."""
        current_text = self.target_input.text()
        self.target_input.setText(current_text[:-1])


class GolfRangeFinder(QWidget):
    """Main Golf Range Finder & Scorekeeper Application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setGeometry(100, 100, 500, 500)
        
        self.scores = [0] * 18
        self.drive_start = None
        self.drive_end = None
        self.pin_location = None
        
        gpsd.connect()  # Connect to GPS daemon
        
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Title Label
        self.title_label = QLabel("Golf Scorecard", self)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # Course Name Input
        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("Enter Course Name")
        self.course_name_input.setReadOnly(True)  # Prevent direct typing
        self.course_name_input.setStyleSheet("font-size: 16px; padding: 5px;")
        self.course_name_input.mousePressEvent = self.show_keyboard  # Open keyboard on tap
        layout.addWidget(self.course_name_input)
        
        # Score Grid
        self.score_grid = QGridLayout()
        self.score_labels = []
        self.score_spinboxes = []
        
        for i in range(18):
            hole_label = QLabel(f"Hole {i + 1}")
            score_spinbox = QSpinBox()
            score_spinbox.setRange(0, 10)
            score_spinbox.setValue(self.scores[i])
            score_spinbox.valueChanged.connect(lambda value, idx=i: self.update_score(idx, value))
            
            self.score_labels.append(hole_label)
            self.score_spinboxes.append(score_spinbox)
            
            self.score_grid.addWidget(hole_label, i // 9, (i % 9) * 2)
            self.score_grid.addWidget(score_spinbox, i // 9, (i % 9) * 2 + 1)
        
        layout.addLayout(self.score_grid)
        
        # Total Score Display
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
        
        # Reset Button
        reset_button = QPushButton("Reset Scores")
        reset_button.clicked.connect(self.reset_scores)
        layout.addWidget(reset_button)
        
        self.setLayout(layout)

    def show_keyboard(self, event):
        """Show the on-screen keyboard when the user taps the course name input field."""
        self.keyboard = OnScreenKeyboard(self.course_name_input)
        self.keyboard.show()
    
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
