import sys
import json  # noqa: F401
import os  # noqa: F401
import geopy.distance  # noqa: F401
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QSpinBox, QStackedWidget,  # noqa: F401
    QLineEdit, QDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt  # noqa: F401
import gpsd

data_file = "courses.json"

class OnScreenKeyboard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        self.input_field = QLineEdit(self)
        layout.addWidget(self.input_field)
        
        key_layout = QGridLayout()
        keys = [
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P',
            'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L',
            'Z', 'X', 'C', 'V', 'B', 'N', 'M'
        ]
        row, col = 0, 0
        for key in keys:
            button = QPushButton(key)
            button.clicked.connect(lambda checked, k=key: self.input_field.insert(k))
            key_layout.addWidget(button, row, col)
            col += 1
            if col > 9:
                col = 0
                row += 1
        
        layout.addLayout(key_layout)
        
        action_layout = QHBoxLayout()
        self.backspace_button = QPushButton("Backspace")
        self.backspace_button.clicked.connect(lambda: self.input_field.backspace())
        action_layout.addWidget(self.backspace_button)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        action_layout.addWidget(self.ok_button)
        
        layout.addLayout(action_layout)
        self.setLayout(layout)
    
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
