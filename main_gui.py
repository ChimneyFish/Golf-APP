import sys
import geopy.distance
import gpsd
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QSpinBox
)
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt

class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Range Finder & Scorekeeper")
        self.setFixedSize(800, 480)
        
        self.scores = [[0] * 18 for _ in range(4)]
        self.current_page = 0  # 0 for Front 9, 1 for Back 9
        self.course_data = {}
        self.load_course_data()
        
        gpsd.connect()
        
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#4CAF50"))
        self.setPalette(palette)
        
        layout = QVBoxLayout()
        self.title_label = QLabel("🏌 Golf Scorecard & GPS Tracker", self)
        self.title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.score_grid = QGridLayout()
        self.score_spinboxes = [[None] * 18 for _ in range(4)]
        
        for player in range(4):
            player_label = QLabel(f"P{player + 1}")
            player_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            player_label.setStyleSheet("color: white;")
            self.score_grid.addWidget(player_label, player, 0)
            
            for i in range(9):
                score_spinbox = QSpinBox()
                score_spinbox.setRange(0, 10)
                score_spinbox.setFixedSize(40, 40)
                score_spinbox.setStyleSheet("background-color: white; font-size: 14px;")
                score_spinbox.valueChanged.connect(lambda value, p=player, h=i: self.update_score(p, h, value))
                
                self.score_spinboxes[player][i] = score_spinbox
                self.score_grid.addWidget(score_spinbox, player, i + 1)
        
        layout.addLayout(self.score_grid)
        
        self.total_score_label = QLabel("Total Scores: P1: 0 | P2: 0 | P3: 0 | P4: 0")
        self.total_score_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.total_score_label.setStyleSheet("color: yellow;")
        layout.addWidget(self.total_score_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.next_button = QPushButton("Next 9 Holes")
        self.next_button.clicked.connect(self.switch_page)
        layout.addWidget(self.next_button)
        
        self.save_button = QPushButton("💾 Save Course Data")
        self.save_button.clicked.connect(self.save_course_data)
        layout.addWidget(self.save_button)
        
        self.setLayout(layout)
        self.update_ui()
    
    def update_score(self, player, hole, value):
        self.scores[player][hole] = value
        total_scores = [sum(self.scores[p]) for p in range(4)]
        self.total_score_label.setText(
            f"Total: P1: {total_scores[0]} | P2: {total_scores[1]} | P3: {total_scores[2]} | P4: {total_scores[3]}"
        )
    
    def switch_page(self):
        self.current_page = 1 - self.current_page  # Toggle between 0 and 1
        self.update_ui()
    
    def update_ui(self):
        start_hole = 9 * self.current_page
        for player in range(4):
            for i in range(9):
                self.score_spinboxes[player][i].setValue(self.scores[player][start_hole + i])
        self.next_button.setText("Previous 9 Holes" if self.current_page else "Next 9 Holes")
    
    def save_course_data(self):
        self.course_data['scores'] = self.scores
        with open("golf_course_data.json", "w") as file:
            json.dump(self.course_data, file)
    
    def load_course_data(self):
        try:
            with open("golf_course_data.json", "r") as file:
                self.course_data = json.load(file)
                self.scores = self.course_data.get('scores', [[0] * 18 for _ in range(4)])
        except FileNotFoundError:
            self.course_data = {}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.show()
    sys.exit(app.exec())
