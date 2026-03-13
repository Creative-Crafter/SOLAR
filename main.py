import sys
import queue
import threading
import time
import re
import os
import json
import ctypes
import ctypes.wintypes

import numpy as np
import sounddevice as sd
import soundfile as sf
import pyautogui
from PIL import ImageGrab
from vosk import Model, KaldiRecognizer
from kokoro import KPipeline
from ollama import chat
from skills import process_text
import yaml

with open("config.yaml", "r", encoding="utf-8") as file:
    data = yaml.safe_load(file)


SCREENSHOT_PATH = "call.png"
CHECK_INTERVAL  = 2
ACCEPT_IMG      = "accept.png"
DECLINE_IMG     = "decline.png"

SAMPLE_RATE     = 24000
VOSK_RATE       = 16000
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"

_CALL_RE = re.compile(r'call', re.IGNORECASE)

stt_queue               = queue.Queue()
listening_for_wake_word = True
running                 = True
call_in_progress        = False

pipeline  = KPipeline(lang_code="a")
_tts_lock = threading.Lock()


def speak(text: str, voice: str = None) -> None:
    global data
    if voice is None:
        voice = data[0]["gender"]

    if not text:
        return
    print(data[0]["name"] + f": {text}")
    chunks = []
    for _, _, audio in pipeline(text, voice=voice):
        chunks.append(audio)
    if not chunks:
        return
    with _tts_lock:
        sd.play(np.concatenate(chunks), SAMPLE_RATE)
        sd.wait()

def play_beep() -> None:
    try:
        data, samplerate = sf.read("beep.wav", dtype="float32")
        sd.play(data, samplerate)
        sd.wait()
    except Exception:
        pass


def _main_audio_callback(indata, frames, time_, status):
    if status:
        print(status)
    stt_queue.put(bytes(indata))

_user32          = ctypes.windll.user32
_EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool,
                                       ctypes.wintypes.HWND,
                                       ctypes.wintypes.LPARAM)


def _get_window_title(hwnd: int) -> str:
    n = _user32.GetWindowTextLengthW(hwnd)
    if n == 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    _user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def find_call_hwnd():
    """
    Enumerate all visible top-level windows via Win32 EnumWindows.
    Returns the HWND of the first window whose title contains 'call', or None.
    Thread-safe — no COM initialisation required.
    """
    found = []

    def cb(hwnd, _):
        if not _user32.IsWindowVisible(hwnd):
            return True
        title = _get_window_title(hwnd)
        if _CALL_RE.search(title):
            found.append(hwnd)
            return False
        return True

    _user32.EnumWindows(_EnumWindowsProc(cb), 0)
    return found[0] if found else None


def _win32_rect(hwnd):
    """Return (left, top, right, bottom) for the given window handle."""
    rect = ctypes.wintypes.RECT()
    if not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError(f"GetWindowRect failed for hwnd={hwnd}")
    return rect.left, rect.top, rect.right, rect.bottom



def take_screenshot(hwnd: int, path: str):
    """
    Capture the window region using PIL ImageGrab.
    ImageGrab.grab(all_screens=True) correctly handles windows on secondary
    monitors that have negative X coordinates — pyautogui.screenshot() does not.
    """
    left, top, right, bottom = _win32_rect(hwnd)
    img = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    img.save(path)
    return img


def click_button(hwnd: int, image_path: str, confidence: float = 0.8) -> bool:
    """
    Grab the window region with ImageGrab, locate image_path inside it,
    and click the centre. Works on any monitor including negative-coord secondaries.
    """
    if not os.path.exists(image_path):
        return False

    left, top, right, bottom = _win32_rect(hwnd)
    region_img = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    location   = pyautogui.locate(image_path, region_img, confidence=confidence)

    if location:
        center = pyautogui.center(location)
        abs_x  = left + center.x
        abs_y  = top  + center.y
        pyautogui.moveTo(abs_x, abs_y, duration=0.5)
        pyautogui.click()
        return True

    return False

_call_stt_queue = queue.Queue()


def _call_audio_cb(indata, frames, time_, status):
    if status:
        print(status)
    _call_stt_queue.put(bytes(indata))


def listen_for_response() -> str:
    model      = Model(VOSK_MODEL_PATH)
    recognizer = KaldiRecognizer(model, VOSK_RATE)

    while not _call_stt_queue.empty():
        _call_stt_queue.get_nowait()

    with sd.RawInputStream(
        samplerate=VOSK_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=_call_audio_cb,
    ):
        deadline = time.time() + 12
        while time.time() < deadline:
            try:
                data = _call_stt_queue.get(timeout=1)
            except queue.Empty:
                continue
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text   = result.get("text", "").strip()
                if text:
                    return text.lower()

    return ""

def wait_for_call_to_end(check_interval: int = 2, timeout: int = 120) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if find_call_hwnd() is None:
            return
        time.sleep(check_interval)

def handle_call(hwnd: int) -> None:
    global call_in_progress
    call_in_progress = True

    take_screenshot(hwnd, SCREENSHOT_PATH)

    try:
        response = chat(
            model="Creative-Crafter/SOLAR-llama3.2-vision:11b",
            messages=[{
                "role": "user",
                "content": (
                    "This is a WhatsApp incoming call notification in a browser. "
                    "What is the name of the PERSON calling? "
                    "It is a human name — like Anna, Thomas, or Maria — "
                    "shown as large white text in the centre of the screen. "
                    "NOT WhatsApp. NOT Voicecall. NOT Annehmen. NOT Chrome. "
                    "Those are app or button labels, not the caller's name. "
                    'Reply ONLY with the human name inside quotation marks, '
                    'e.g.: "Anna Müller" — nothing else.'
                ),
                "images": [SCREENSHOT_PATH],
            }],
        )
    except Exception as e:
        call_in_progress = False
        return

    matches = re.findall(r'"(.*?)"', response.message.content)
    if not matches:
        call_in_progress = False
        return

    name = matches[0]

    speak(f"Incoming call from {name}. Should I answer?")
    user_response = listen_for_response()

    hwnd = find_call_hwnd() or hwnd

    if "yes" in user_response:
        click_button(hwnd, ACCEPT_IMG)
    elif "no" in user_response or "busy" in user_response:
        click_button(hwnd, ACCEPT_IMG)
        speak("Hi, here is " + data[0]["name"] + ". " + data[0]["user_name"] + " cannot speak right now, call again later.")
        time.sleep(1)
        click_button(hwnd, DECLINE_IMG)
    
    call_in_progress = False  # ← moved here, runs in ALL branches

def call_monitor_loop() -> None:
    global call_in_progress  # ← add this
    print("[Call Monitor] Running.")
    while running:
        hwnd = find_call_hwnd()
        if hwnd is not None and not call_in_progress:
            handle_call(hwnd)
            wait_for_call_to_end()
            call_in_progress = False
            print("[Call Monitor] Ready for next call.")
        time.sleep(CHECK_INTERVAL)

def process_and_send_command(command_text: str) -> None:
    global running
    if not command_text:
        return
    if "shutdown" in command_text.lower():
        speak("Shutting down. Goodbye!")
        running = False
        sys.exit(0)
    speak(process_text(command_text))




def run_speech_mode() -> None:
    global listening_for_wake_word, running, data

    model      = Model(VOSK_MODEL_PATH)
    recognizer = KaldiRecognizer(model, VOSK_RATE)
    print(data[0]["name"] + " is ready.")

    with sd.RawInputStream(
        samplerate=VOSK_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=_main_audio_callback,
    ):
        while running:
            audio_data = stt_queue.get()

            if call_in_progress:
                continue

            if not recognizer.AcceptWaveform(audio_data):
                continue

            result = json.loads(recognizer.Result())
            text   = result.get("text", "").lower()
            if not text:
                continue

            if listening_for_wake_word:
                if any(w in text for w in (data[0]["name"],)):
                    listening_for_wake_word = False
                    play_beep()
                    print("You: ", end="", flush=True)
            else:
                print(text)
                process_and_send_command(text)
                listening_for_wake_word = True

if __name__ == "__main__":
    threading.Thread(target=call_monitor_loop, daemon=True).start()
    run_speech_mode()