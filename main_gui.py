import sys
import gps
import folium
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView
from geopy.distance import geodesic

class GolfRangeFinder(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize attributes to prevent AttributeError
        self.player_location = None
        self.hole_location = None

        self.initUI()

        # Start GPS thread
        self.gps_thread = threading.Thread(target=self.get_gps_position, daemon=True)
        self.gps_thread.start()

    def initUI(self):
        self.setWindowTitle("Golf Range Finder")
        self.setGeometry(100, 100, 800, 480)  # Adjusted for Raspberry Pi touchscreen
        
        layout = QVBoxLayout()

        self.mapView = QWebEngineView()
        layout.addWidget(self.mapView)

        self.btnSetHole = QPushButton("Set Hole Location")
        self.btnSetHole.clicked.connect(self.set_hole_location)
        layout.addWidget(self.btnSetHole)

        self.distanceLabel = QLabel("Distance to Hole: N/A")
        layout.addWidget(self.distanceLabel)

        self.setLayout(layout)
        
        # Ensure map updates only if player_location is set
        self.update_map()

    def get_gps_position(self):
        session = gps.gps(mode=gps.WATCH_ENABLE)
        while True:
            try:
                report = session.next()
                if report['class'] == 'TPV' and hasattr(report, 'lat') and hasattr(report, 'lon'):
                    self.player_location = (report.lat, report.lon)
                    self.update_map()
            except KeyError:
                pass
            except StopIteration:
                break

    def set_hole_location(self):
        if self.player_location:
            self.hole_location = self.player_location
            QMessageBox.information(self, "Hole Set", "Hole location saved!")
        else:
            QMessageBox.warning(self, "GPS Error", "Waiting for GPS signal...")

    def update_map(self):
        # Ensure map updates only if player_location is available
        if self.player_location:
            lat, lon = self.player_location
            map_obj = folium.Map(location=[lat, lon], zoom_start=18)

            folium.Marker([lat, lon], tooltip="Your Location").add_to(map_obj)

            if self.hole_location:
                folium.Marker(self.hole_location, tooltip="Hole", icon=folium.Icon(color='red')).add_to(map_obj)
                distance = geodesic(self.player_location, self.hole_location).meters
                self.distanceLabel.setText(f"Distance to Hole: {distance:.2f} m")

            map_obj.save("map.html")
            self.mapView.setHtml(open("map.html").read(), baseUrl='')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GolfRangeFinder()
    window.show()
    sys.exit(app.exec())
