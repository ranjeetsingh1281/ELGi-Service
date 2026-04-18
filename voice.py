import speech_recognition as sr
import pyttsx3
import pandas as pd

engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 बोलो Boss...")
        audio = r.listen(source)

    try:
        return r.recognize_google(audio)
    except:
        return ""

def run_voice():

    df = pd.read_excel("Master_Data.xlsx")

    text = listen().lower()

    if "machine status" in text:

        count = len(df)

        speak(f"Total {count} machines available Boss")

    elif "overdue" in text:

        over_col = next((c for c in df.columns if "over" in c.lower()), None)

        overdue = len(df[df[over_col] > 0])

        speak(f"{overdue} machines overdue Boss")

run_voice()
