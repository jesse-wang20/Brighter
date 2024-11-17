import cv2
from deepface import DeepFace
import tkinter as tk
from tkinter import ttk
import random
import requests

root = tk.Tk()
root.withdraw()  

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not video.isOpened():
    raise IOError("Cannot open webcam")

negative_emotions = {'sad', 'angry', 'fear'}

popup_open = False

quotes_array = []

def fetch_quotes():
    global quotes_array
    keywords = ['happiness', 'inspiration', 'kindness']
    for keyword in keywords:
        url = f"https://zenquotes.io/api/quotes/keyword={keyword}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                quotes = response.json()
                for quote in quotes:
                    quotes_array.append({
                        "quote": quote["q"],
                        "author": quote["a"]
                    })
            else:
                print(f"Failed to fetch quotes for keyword: {keyword}")
        except Exception as e:
            print(f"Error fetching quotes: {e}")

fetch_quotes()

def show_custom_popup():
    global popup_open
    if not popup_open and quotes_array: 
        popup_open = True

        random_quote = random.choice(quotes_array)
        quote_text = random_quote["quote"]
        author_name = random_quote["author"]

        popup = tk.Toplevel(root)
        popup.title("Positive Vibes 🌟")
        popup.geometry("350x200")  
        popup.resizable(False, False)

        window_width = 350
        window_height = 200
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        position_top = int((screen_height - window_height) / 2)
        position_right = int((screen_width - window_width) / 2)
        popup.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

        frame = ttk.Frame(popup, padding=20)
        frame.pack(expand=True, fill='both')

        quote_label = ttk.Label(
            frame, 
            text=f"\"{quote_text}\"", 
            font=("Helvetica", 12, "italic"), 
            foreground="#4CAF50",  # Green text
            wraplength=300, 
            anchor="center"
        )
        quote_label.pack(pady=10)

        author_label = ttk.Label(
            frame, 
            text=f"- {author_name}", 
            font=("Helvetica", 10, "bold"), 
            foreground="#000000",  # Black text
            anchor="center"
        )
        author_label.pack(pady=5)

        close_button = ttk.Button(
            frame, 
            text="Close", 
            command=lambda: (popup.destroy(), reset_popup())
        )
        close_button.pack(pady=10)

        popup.mainloop()

def reset_popup():
    global popup_open
    popup_open = False

while video.isOpened():
    _, frame = video.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for x, y, w, h in face:
        image = cv2.rectangle(frame, (x, y), (x + w, y + h), (89, 2, 236), 1)
        try:
            analyze = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            
            if isinstance(analyze, list):
                analyze = analyze[0]  
            
            dominant_emotion = analyze['dominant_emotion']

            if dominant_emotion in negative_emotions:
                show_custom_popup()

        except Exception as e: 
            print(e)
            print('No face detected')

    cv2.imshow('video', frame)
    key = cv2.waitKey(1)
    if key == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
root.destroy()  # Close the Tkinter root window
