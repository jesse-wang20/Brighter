from PyQt5.QtGui import QImage, QPixmap, QIcon, QPainter, QColor
from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSpinBox
)
from PyQt5.QtCore import QTimer, Qt, QPointF, QTimeLine
import sys
import time
import cv2
from deepface import DeepFace
import random
import requests
import math
import webbrowser

class PopupWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent 

        self.setWindowFlags(Qt.Window)  
        self.setAttribute(Qt.WA_DeleteOnClose)  

    def closeEvent(self, event):
        if self.parent_app:
            self.parent_app.close_popup()  
        event.accept() 

class EmotionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brighter")
        self.setGeometry(100, 100, 640, 480)
        self.setWindowIcon(QIcon('star.png'))

        self.popup_open = False
        self.last_popup_time = 0
        self.pause_until = 0
        self.popup_cooldown = 10
        self.negative_emotions = {"sad", "angry", "fear"}
        self.quotes = self.fetch_quotes()

        self.video_capture = cv2.VideoCapture(0)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        self.emotion_buffer = []
        self.buffer_size = 20
        
        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_video)
        self.timer.start(30)


    def init_ui(self):
        layout = QVBoxLayout()

        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)
        layout.addWidget(self.video_label)

        sensitivity_layout = QHBoxLayout()
        sensitivity_label = QLabel("Sensitivity:")
        self.sensitivity_spinbox = QSpinBox()
        self.sensitivity_spinbox.setRange(1, self.buffer_size)  
        self.sensitivity_spinbox.setValue(self.buffer_size // 2) 
        sensitivity_layout.addWidget(sensitivity_label)
        sensitivity_layout.addWidget(self.sensitivity_spinbox)
        layout.addLayout(sensitivity_layout)

        self.setLayout(layout)



    def process_video(self):
        ret, frame = self.video_capture.read()
        if not ret:
            return

        # Convert frame for display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        current_time = time.time()

        for x, y, w, h in faces:
            # Draw a rectangle around the face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            try:
                analyze = DeepFace.analyze(frame[y:y+h, x:x+w], actions=["emotion"], enforce_detection=False)
                if isinstance(analyze, list):
                    analyze = analyze[0]
                dominant_emotion = analyze["dominant_emotion"]

                cv2.putText(
                    frame,
                    f"Emotion: {dominant_emotion}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA
                )

                self.emotion_buffer.append(dominant_emotion)
                if len(self.emotion_buffer) > self.buffer_size:
                    self.emotion_buffer.pop(0)

                sensitivity = self.sensitivity_spinbox.value()
                negative_count = sum(1 for e in self.emotion_buffer if e in self.negative_emotions)
                if (
                    negative_count >= sensitivity
                    and (current_time - self.last_popup_time >= self.popup_cooldown)
                    and (current_time >= self.pause_until)
                    and not self.popup_open
                ):
                    self.last_popup_time = current_time
                    self.show_quote_popup()

            except Exception as e:
                print(e)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def show_quote_popup(self):
        if self.popup_open:
            return 

        self.popup_open = True
        self.last_popup_time = time.time()

        self.popup = PopupWindow(self)
        self.popup.setWindowTitle("Cheer Up!")
        self.popup.setStyleSheet("background-color: #fce4ec; font-family: Arial;")
        self.popup.setWindowIcon(QIcon('star.png'))

        self.popup.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.popup.activateWindow()
        self.popup.raise_()

        screen_rect = QApplication.desktop().screenGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        popup_width = 400
        popup_height = 300

        pos_x = screen_width - popup_width - 10  
        pos_y = screen_height - popup_height - 50 

        self.popup.setGeometry(pos_x, pos_y, popup_width, popup_height)

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

        support_button = QPushButton("24/7 Mental Health Support")
        support_button.setStyleSheet("background-color: #ff4081; color: white;")
        support_button.clicked.connect(lambda: webbrowser.open("https://www.mentalhealth.gov/get-help/immediate-help"))
        layout.addWidget(support_button)

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


    def close_popup(self):
        self.popup.close()
        self.popup_open = False

    def set_pause(self, minutes):
        self.pause_until = time.time() + minutes * 60
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Breathe Exercise")
        self.setGeometry(300, 300, 400, 400)
        self.setStyleSheet("background-color: #e3f2fd;")
        self.setWindowIcon(QIcon('star.png'))

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 20px; color: #0d47a1;")
        self.label.setGeometry(50, 20, 300, 50)

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
    window = EmotionApp()
    window.show()
    sys.exit(app.exec_())
