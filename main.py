import cv2
from deepface import DeepFace
import tkinter as tk
from tkinter import messagebox

# Initialize Tkinter root (for the pop-up)
root = tk.Tk()
root.withdraw()  # Hide the root window, we only want to show the pop-up

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not video.isOpened():
    raise IOError("Cannot open webcam")

# Define negative emotions
negative_emotions = {'sad', 'angry', 'fear'}

# Variable to track if the pop-up is displayed
popup_open = False

def show_popup(message):
    print("SHOW POPUP")
    global popup_open
    if not popup_open:  # Only show pop-up if not already displayed
        popup_open = True
        # Show the message box
        messagebox.showinfo("Positive Message", message)
        popup_open = False  # Reset flag after pop-up is closed

while video.isOpened():
    _, frame = video.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for x, y, w, h in face:
        image = cv2.rectangle(frame, (x, y), (x + w, y + h), (89, 2, 236), 1)
        try:
            analyze = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            
            # Check if analyze is a list (multiple faces detected)
            if isinstance(analyze, list):
                analyze = analyze[0]  # Get the first detected face's analysis
            
            dominant_emotion = analyze['dominant_emotion']

            # Display a pop-up message for negative emotions
            if dominant_emotion in negative_emotions:
                positive_message = "You're amazing! Keep smiling!"
                # print(positive_message)
                # Show the pop-up
                print("call")
                show_popup(positive_message)
                root.after(0, show_popup, positive_message)

        except Exception as e: 
            print(e)
            print('no face')

    cv2.imshow('video', frame)
    key = cv2.waitKey(1)
    if key == ord('q'):
        break

# Clean up
video.release()
cv2.destroyAllWindows()
root.destroy()  # Close the Tkinter root window
