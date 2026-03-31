import streamlit as st
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import pyttsx3
import time
import tempfile
import cv2
from graphviz import Digraph

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(page_title="Morse Ultimate AI", layout="wide")

# ---------------- UI STYLE ---------------- #
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #020617, #0f172a);
}
.title {
    font-size: 55px;
    text-align: center;
    font-weight: bold;
    background: linear-gradient(90deg,#38bdf8,#818cf8,#22c55e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.card {
    background: rgba(30,41,59,0.6);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 25px;
    margin-top: 15px;
    box-shadow: 0 0 25px rgba(56,189,248,0.15);
}
.stButton button {
    width: 100%;
    height: 45px;
    border-radius: 12px;
    font-weight: bold;
    background: linear-gradient(90deg,#38bdf8,#6366f1);
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🚀 Morse AI Ultimate</div>', unsafe_allow_html=True)

# ---------------- MORSE (UPDATED WITH NUMBERS) ---------------- #
MORSE = {
    # Letters
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..',
    'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',

    # Numbers
    '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..',
    '9': '----.',

    ' ': '/'
}

REV = {v: k for k, v in MORSE.items()}

WORD_DICT = ["HELLO","HEY","HELP","HI","HOW","ARE","YOU","YES","NO","THANKS","OK","GOOD"]

# ---------------- FUNCTIONS ---------------- #
def text_to_morse(text):
    return " ".join([MORSE.get(c.upper(), "?") for c in text])

def morse_to_text(m):
    words = m.split(" / ")
    return " ".join(["".join([REV.get(l,"?") for l in w.split()]) for w in words])

def predict_word(text):
    return [w for w in WORD_DICT if w.startswith(text.upper())][:3]

# -------- VOICE -------- #
def listen_browser():
    audio = st.audio_input("🎤 Speak")
    if audio:
        r = sr.Recognizer()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio.read())
            filename = f.name
        with sr.AudioFile(filename) as source:
            data = r.record(source)
        try:
            return r.recognize_google(data)
        except:
            return "Error"
    return None

# -------- FLASHLIGHT -------- #
def flashlight_detector():
    cap = cv2.VideoCapture(0)
    frame_window = st.image([])

    THRESHOLD = 170
    DOT_TIME = 0.3

    prev_state = False
    start_time = 0
    morse = ""

    stop = st.button("Stop Flashlight")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        roi = gray[100:300,100:300]
        brightness = np.mean(roi)

        state = brightness > THRESHOLD

        if state and not prev_state:
            start_time = time.time()

        elif not state and prev_state:
            duration = time.time() - start_time
            morse += "." if duration < DOT_TIME else "-"

        prev_state = state

        cv2.putText(frame, morse, (10,50),0,1,(0,255,0),2)
        frame_window.image(frame, channels="BGR")

        if stop:
            break

    cap.release()
    st.success("Morse: " + morse)
    st.success("Text: " + morse_to_text(morse))

# -------- EYE BLINK WORD MODE -------- #
def eye_blink_words():
    eye_cascade = cv2.CascadeClassifier("haarcascade_eye.xml")
    cap = cv2.VideoCapture(0)
    frame_window = st.image([])

    prev_state = True
    start_time = 0
    morse = ""
    text = ""

    DOT_TIME = 0.25

    stop = st.button("Stop Eye")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        eyes = eye_cascade.detectMultiScale(gray,1.1,3)

        state = len(eyes)>0

        if not state and prev_state:
            start_time = time.time()

        elif state and not prev_state:
            duration = time.time() - start_time
            morse += "." if duration < DOT_TIME else "-"

        prev_state = state

        if len(morse)>=4:
            letter = REV.get(morse,"")
            if letter:
                text += letter
                morse=""

        suggestions = predict_word(text)

        cv2.putText(frame,"Text:"+text,(10,40),0,1,(255,255,0),2)
        frame_window.image(frame, channels="BGR")

        st.write("Suggestions:", suggestions)

        if stop:
            break

    cap.release()
    st.success("Final Text: "+text)

# -------- DFA -------- #
def show_dfa():
    dot = Digraph()
    dot.edge('q0','q1',label='.')
    dot.edge('q0','q2',label='-')
    return dot

def show_dfa_live(morse):
    dot = Digraph()
    current='q0'
    for s in morse:
        if s==".":
            dot.edge(current,'q1',color='green')
            current='q1'
        elif s=="-":
            dot.edge(current,'q2',color='red')
            current='q2'
    return dot

# ---------------- UI ---------------- #
tab1, tab2, tab3, tab4 = st.tabs(["✍ Text","🎤 Voice","💡 Vision","🧠 DFA"])

with tab1:
    t = st.text_input("Enter Text")
    if st.button("Convert to Morse"):
        st.success(text_to_morse(t))

    m = st.text_input("Enter Morse")
    if st.button("Convert to Text"):
        st.success(morse_to_text(m))

with tab2:
    v = listen_browser()
    if v:
        st.success(v)
        st.info(text_to_morse(v))

with tab3:
    col1,col2 = st.columns(2)
    with col1:
        if st.button("💡 Flashlight"):
            flashlight_detector()
    with col2:
        if st.button("👁 Eye Blink"):
            eye_blink_words()

with tab4:
    if st.button("Show DFA"):
        st.graphviz_chart(show_dfa())

    morse_input = st.text_input("Enter Morse for DFA")
    if st.button("Show DFA Path"):
        st.graphviz_chart(show_dfa_live(morse_input))

st.markdown("---")
st.markdown("✨ Built with TOC + AI + Computer Vision")