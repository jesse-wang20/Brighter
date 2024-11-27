import sys
import time
import cv2
from deepface import DeepFace
import random
import requests
from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSpinBox
)
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import QTimer, Qt, QPointF, QTimeLine
import math


class EmotionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brighter")
        self.setGeometry(100, 100, 400, 300)

        self.popup_open = False
        self.last_popup_time = 0
        self.pause_until = 0
        self.popup_cooldown = 10
        self.negative_emotions = {"sad", "angry", "fear"}
        self.quotes = self.fetch_quotes()

        self.video_capture = cv2.VideoCapture(0)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_video)
        self.timer.start(30)

    def fetch_quotes(self):
        # Manually defined URLS that represent quotes that could help.
        urls = [
            "https://zenquotes.io/api/quotes/keyword=happiness",
            "https://zenquotes.io/api/quotes/keyword=inspiration",
            "https://zenquotes.io/api/quotes/keyword=kindness",
        ]
        quotes = []
        for url in urls:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    quotes.extend(response.json())
            except Exception as e:
                print(f"Error fetching quotes: {e}")
        return quotes

    def process_video(self):
        # Begin video reading and face identification
        ret, frame = self.video_capture.read()
        if not ret:
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        current_time = time.time()

        for x, y, w, h in faces:
            try:
                # Retrieve the current emotion of the face we found, if it's one of the negative emotions, we want to handle the pop up
                analyze = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)
                if isinstance(analyze, list):
                    analyze = analyze[0]
                dominant_emotion = analyze["dominant_emotion"]

                if (
                    dominant_emotion in self.negative_emotions
                    and not self.popup_open
                    and (current_time - self.last_popup_time >= self.popup_cooldown)
                    and (current_time >= self.pause_until)
                ):
                    self.last_popup_time = current_time
                    self.show_quote_popup()

            except Exception as e:
                print(e)

    def show_quote_popup(self):
        self.popup_open = True
        self.last_popup_time = time.time()

        self.popup = QWidget()
        self.popup.setWindowTitle("Cheer Up!")
        self.popup.setGeometry(200, 200, 400, 300)
        self.popup.setStyleSheet("background-color: #fce4ec; font-family: Arial;")

        layout = QVBoxLayout()
        selected_quote = random.choice(self.quotes)
        self.quote_text = selected_quote["q"]
        self.author_name = selected_quote["a"]

        quote_label = QLabel(f'"{self.quote_text}"')
        quote_label.setWordWrap(True)
        quote_label.setStyleSheet("font-size: 18px; color: #880e4f;")
        layout.addWidget(quote_label)

        author_label = QLabel(f"- {self.author_name}")
        author_label.setStyleSheet("font-size: 14px; color: #6a1b9a;")
        author_label.setAlignment(Qt.AlignRight)
        layout.addWidget(author_label)

        # Define a button that allows the user to pause the popups
        pause_layout = QHBoxLayout()
        pause_label = QLabel("Pause popups for (minutes):")
        pause_label.setStyleSheet("font-size: 14px; color: #880e4f;")
        pause_spinbox = QSpinBox()
        pause_spinbox.setRange(1, 60)
        pause_spinbox.setStyleSheet("font-size: 14px; color: #6a1b9a;")
        pause_button = QPushButton("Set Pause")
        pause_button.setStyleSheet("background-color: #880e4f; color: white;")
        pause_button.clicked.connect(lambda: self.set_pause(pause_spinbox.value()))
        pause_layout.addWidget(pause_label)
        pause_layout.addWidget(pause_spinbox)
        pause_layout.addWidget(pause_button)
        layout.addLayout(pause_layout)

        # Define a button that defines the breathing exercises
        breathe_button = QPushButton("Try a Breathing Exercise")
        breathe_button.setStyleSheet("background-color: #6a1b9a; color: white;")
        breathe_button.clicked.connect(self.start_breathe_exercise)
        layout.addWidget(breathe_button)

        close_button = QPushButton("Close")
        close_button.setStyleSheet("background-color: #880e4f; color: white;")
        close_button.clicked.connect(self.close_popup)
        layout.addWidget(close_button)

        self.popup.setLayout(layout)
        self.popup.show()

    def set_pause(self, minutes):
        self.pause_until = time.time() + minutes * 60
        self.popup.close()
        self.popup_open = False

    def close_popup(self):
        self.popup.close()
        self.popup_open = False

    def start_breathe_exercise(self):
        self.breathe_popup = BreatheExercise()
        self.breathe_popup.show()

    def closeEvent(self, event):
        self.video_capture.release()
        cv2.destroyAllWindows()
        super().closeEvent(event)


class BreatheExercise(QWidget):
    # Define a class window for breathing exercises
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Breathe Exercise")
        self.setGeometry(300, 300, 400, 400)
        self.setStyleSheet("background-color: #e3f2fd;")

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 20px; color: #0d47a1;")
        self.label.setGeometry(50, 20, 300, 50)

        # Define a timelien for the loop
        self.timeline = QTimeLine(19000, self)
        self.timeline.setFrameRange(0, 360)
        self.timeline.frameChanged.connect(self.update_position)
        self.timeline.setLoopCount(0)
        self.timeline.start()
        self.resize(400, 400)
        self.angle = 0

    def update_position(self, frame):
        self.angle = frame
        self.update()
        
        # Approximate the locations for when the user should be performing breathing activities. 
        if frame < 76:
            self.label.setText("Breathe In")
        elif frame < 133:
            self.label.setText("Hold")
        else:
            self.label.setText("Breathe Out")

    def paintEvent(self, event):
        painter = QPainter(self)
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 3
        painter.setBrush(QColor(173, 216, 230))
        painter.drawEllipse(center, radius, radius)
        angle_radians = math.radians(self.angle)
        ball_x = center.x() + radius * math.cos(angle_radians)
        ball_y = center.y() + radius * math.sin(angle_radians)
        painter.setBrush(QColor(255, 99, 71))
        painter.drawEllipse(QPointF(ball_x, ball_y), 10, 10)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = EmotionApp()
    main_window.show()
    sys.exit(app.exec_())
