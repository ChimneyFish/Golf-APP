import sys
import json
import gpsd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, 
    QGridLayout, QSpinBox, QLineEdit, QFileDialog, QHBoxLayout
)


class OnScreenKeyboard(QWidget):
    """Custom on-screen keyboard for touch-based input."""
    
    def __init__(self, target_input):
        super().__init__()
        self.target_input = target_input
        self.setWindowTitle("On-Screen Keyboard")
        self.setGeometry(200, 200, 600, 300)
        
        layout = QVBoxLayout()
        self.keys = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        
        grid = QGridLayout()
        for row, key_row in enumerate(self.keys):
            for col, key in enumerate(key_row):
                btn = QPushButton(key)
                btn.setFixedSize(50, 50)
                btn.clicked.connect(lambda _, k=key: self.add_character(k))
                grid.addWidget(btn, row, col)
        
        space_btn = QPushButton("Space")
        space_btn.setFixedSize(200, 50)
        space_btn.clicked.connect(lambda: self.add_character(" "))

        backspace_btn = QPushButton("Backspace")
        backspace_btn.setFixedSize(100, 50)
        backspace_btn.clicked.connect(self.remove_character)

        enter_btn = QPushButton("Enter")
        enter_btn.setFixedSize(100, 50)
        enter_btn.clicked.connect(self.close)  # Close keyboard when done

        control_layout = QGridLayout()
        control_layout.addWidget(space_btn, 0, 0, 1, 2)
        control_layout.addWidget(backspace_btn, 0, 2)
        control_layout.addWidget(enter_btn, 0, 3)

        layout.addLayout(grid)
        layout.addLayout(control_layout)
        self.setLayout(layout)

    def add_character(self, char):
        """Append a character to the input field."""
        self.target_input.setText(self.target_input.text() + char)

    def remove_character(self):
        """Remove the last character from the input field."""
        self.target_input.setText(self.target_input.text()[:-1])


class GolfRangeFinder(QWidget):
    """Main Golf Range Finder & Multi-Golfer Scorekeeper."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setGeometry(100, 100, 600, 700)
        
        self.num_golfers = 4
        self.scores = [[0] * 18 for _ in range(self.num_golfers)]
        self.golfer_names = [f"Golfer {i + 1}" for i in range(self.num_golfers)]
        self.drive_start = None
        self.drive_end = None
        self.pin_location = None
        gpsd.connect()
        
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        self.title_label = QLabel("Golf Scorecard", self)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # Course Name Input
        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("Enter Course Name")
        self.course_name_input.setReadOnly(True)
        self.course_name_input.setStyleSheet("font-size: 16px; padding: 5px;")
        self.course_name_input.mousePressEvent = self.show_keyboard
        layout.addWidget(self.course_name_input)
        
        # Score Grid
        self.score_grid = QGridLayout()
        self.score_spinboxes = [[None] * 18 for _ in range(self.num_golfers)]
        
        # Golfer labels
        for g in range(self.num_golfers):
            golfer_label = QLabel(self.golfer_names[g])
            self.score_grid.addWidget(golfer_label, 0, g + 1)
        
        # Score Inputs
        for hole in range(18):
            hole_label = QLabel(f"Hole {hole + 1}")
            self.score_grid.addWidget(hole_label, hole + 1, 0)
            
            for g in range(self.num_golfers):
                score_spinbox = QSpinBox()
                score_spinbox.setRange(0, 10)
                score_spinbox.setValue(self.scores[g][hole])
                score_spinbox.valueChanged.connect(lambda value, h=hole, player=g: self.update_score(player, h, value))
                
                self.score_spinboxes[g][hole] = score_spinbox
                self.score_grid.addWidget(score_spinbox, hole + 1, g + 1)
        
        layout.addLayout(self.score_grid)
        
        # Total Score Display
        self.total_score_labels = [QLabel(f"{self.golfer_names[g]}: 0") for g in range(self.num_golfers)]
        for label in self.total_score_labels:
            label.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(label)
        
        # Save and Load Buttons
        btn_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Course")
        self.save_button.clicked.connect(self.save_course)
        btn_layout.addWidget(self.save_button)
        
        self.load_button = QPushButton("Load Course")
        self.load_button.clicked.connect(self.load_course)
        btn_layout.addWidget(self.load_button)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def show_keyboard(self, event):
        """Show the on-screen keyboard when the user taps the course name input field."""
        self.keyboard = OnScreenKeyboard(self.course_name_input)
        self.keyboard.show()

    def update_score(self, player, hole, value):
        self.scores[player][hole] = value
        self.total_score_labels[player].setText(f"{self.golfer_names[player]}: {sum(self.scores[player])}")
    
    def save_course(self):
        """Save the current course name and scores to a JSON file."""
        course_name = self.course_name_input.text().strip()
        if not course_name:
            return
        
        data = {"name": course_name, "scores": self.scores}
        filename = f"{course_name}.json"
        
        with open(filename, "w") as f:
            json.dump(data, f)
        print(f"Course saved as {filename}")

    def load_course(self):
        """Load a saved course from a JSON file."""
        filename, _ = QFileDialog.getOpenFileName(self, "Load Course", "", "JSON Files (*.json)")
        if not filename:
            return
        
        with open(filename, "r") as f:
            data = json.load(f)
        
        self.course_name_input.setText(data["name"])
        self.scores = data["scores"]
        
        for g in range(self.num_golfers):
            for h in range(18):
                self.score_spinboxes[g][h].setValue(self.scores[g][h])
        
        print(f"Loaded course: {data['name']}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.show()
    sys.exit(app.exec())
