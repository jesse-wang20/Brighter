import cv2
from deepface import DeepFace
import tkinter as tk
from tkinter import ttk
import random
import requests
import webbrowser

root = tk.Tk()
root.withdraw()

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not video.isOpened():
    raise IOError("Cannot open webcam")

negative_emotions = {'sad', 'angry', 'fear'}
popup_open = False
quotes_array = []

# Fetch quotes from the API
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
        except Exception as e:
            print(f"Error fetching quotes: {e}")

fetch_quotes()

def open_help():
    webbrowser.open("https://www.samhsa.gov/find-help/national-helpline")

def show_custom_popup():
    global popup_open
    if not popup_open and quotes_array:
        popup_open = True

        random_quote = random.choice(quotes_array)
        quote_text = random_quote["quote"]
        author_name = random_quote["author"]

        popup = tk.Toplevel(root)
        popup.title("Positive Vibes 🌟")
        popup.geometry("400x300")
        popup.resizable(False, False)

        window_width = 400
        window_height = 300
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
            font=("Helvetica", 14, "italic"), 
            foreground="#4CAF50",  
            wraplength=360, 
            justify="center"
        )
        quote_label.pack(pady=10)

        author_label = ttk.Label(
            frame, 
            text=f"- {author_name}", 
            font=("Helvetica", 12, "bold"), 
            foreground="#555555",  
            anchor="center"
        )
        author_label.pack(pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20, fill="x")

        another_button = ttk.Button(
            button_frame, 
            text="Show Another Quote", 
            command=lambda: (popup.destroy(), reset_popup(), show_custom_popup())
        )
        another_button.pack(side="left", padx=10)

        help_button = ttk.Button(
            button_frame, 
            text="Get Help", 
            command=open_help
        )
        help_button.pack(side="right", padx=10)

        close_button = ttk.Button(
            frame, 
            text="Close", 
            command=lambda: (popup.destroy(), reset_popup())
        )
        close_button.pack(pady=10)

def reset_popup():
    global popup_open
    popup_open = False

def process_video():
    global popup_open
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
            if dominant_emotion in negative_emotions and not popup_open:
                root.after(0, show_custom_popup)
        except Exception as e: 
            print(e)
            print('No face detected')

    cv2.imshow('video', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        root.quit()
        return

    root.after(10, process_video)

root.after(0, process_video)
root.mainloop()

video.release()
cv2.destroyAllWindows()
