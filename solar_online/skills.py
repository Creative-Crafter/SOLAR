import subprocess
import pyautogui
import pygetwindow as gw
from screeninfo import get_monitors
import time
from datetime import datetime
import pyperclip
import re
import dateparser
from ics import Calendar, Event
import tempfile
import os
import requests

# ------------------- Window & Screen Management -------------------
def get_screen_position(screen_number):
    """Returns the (x, y) coordinates for the top-left of a specific monitor."""
    monitors = get_monitors()
    try:
        m = monitors[int(screen_number) - 1]  # 1-indexed
        return m.x, m.y
    except (IndexError, ValueError):
        print(f"⚠️ Screen {screen_number} not found. Defaulting to primary.")
        return 0, 0

def launch_and_move(target, screen_num=1):
    """
    Launches an app or website and moves its window to the specified screen.
    """
    is_url = target.startswith("http") or "www." in target
    
    if is_url:
        print(f"🌐 Opening website: {target}")
        cmd = f'start chrome --new-window "{target}"'
        subprocess.Popen(cmd, shell=True)
        search_title = "Google Chrome"
    else:
        print(f"🚀 Opening application: {target}")
        pyautogui.press('win')
        time.sleep(0.4)
        pyautogui.write(target)
        time.sleep(0.6)
        pyautogui.press('enter')
        search_title = target

    # Wait for the window to appear
    target_window = None
    for _ in range(20):  # ~10 seconds
        time.sleep(0.5)
        windows = gw.getWindowsWithTitle(search_title)
        if windows:
            target_window = windows[-1]  # Most recent match
            break

    if target_window:
        x, y = get_screen_position(screen_num)
        try:
            target_window.restore()
            time.sleep(0.2)
            target_window.moveTo(x + 50, y + 50)
            target_window.maximize()
            print(f"✅ Successfully placed {target} on Screen {screen_num}")
        except Exception as e:
            print(f"❌ Could not move window: {e}")
    else:
        print(f"⚠️ Timeout: Could not find a window for '{target}'")

# ------------------- Messaging Images -------------------
whatsapp = "whatsapp.png"
discord = "discord_search.png"
instagram1 = "insta1.png"
instagram2 = "insta2.png"
instagram3 = "insta3.png"

# ------------------- Sending Messages -------------------
def parse_sentence(sentence: str):
    """
    Erwartetes Format:
    'say <message> to <name> on <platform>'
    """
    pattern = r"^say\s+(.+?)\s+to\s+(.+?)\s+on\s+(.+)$"
    match = re.match(pattern, sentence)
    if not match:
        raise ValueError("Sentence does not match expected format: 'say <message> to <name> on <platform>'")
    message = match.group(1).strip()
    name = match.group(2).strip()
    platform = match.group(3).strip()
    return message, name, platform

def click_image_in_window(window, image_path, confidence=0.8):
    if not os.path.exists(image_path):
        print(f"{image_path} not found; skipping.")
        return False
    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
    if location:
        center = pyautogui.center(location)
        pyautogui.moveTo(center.x, center.y, duration=0.5)
        pyautogui.click()
        print(f"Clicked {image_path} button!")
        return True
    else:
        print(f"{image_path} button not found.")
        return False

def send_message_skill(command: str):
    """
    Sends a message based on the format:
    'say <message> to <name> on <platform>'
    Supported platforms: whatsapp, discord, instagram
    """
    try:
        message, name, platform = parse_sentence(command)
    except ValueError as e:
        return str(e)

    window = None
    print("Message:", message)
    print("Name:", name)
    print("Platform:", platform)

    if platform == "whatsapp" or platform == "what's up" or platform == "what's app":
        pyautogui.press("win")
        pyautogui.typewrite("Whatsapp")
        pyautogui.press("enter")
        time.sleep(1.5)
        click_image_in_window(window, whatsapp)
        pyautogui.typewrite(name)
        pyautogui.press("enter")
        pyautogui.typewrite(message)
        pyautogui.press("enter")
        return f"Message sent to {name} on WhatsApp."

    elif platform == "discord":
        pyautogui.press("win")
        pyautogui.typewrite("discord")
        pyautogui.press("enter")
        time.sleep(1.5)
        click_image_in_window(window, discord)
        time.sleep(0.5)
        pyautogui.typewrite(name)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(0.5)
        pyautogui.typewrite(message)
        pyautogui.press("enter")
        return f"Message sent to {name} on Discord."

    elif platform == "instagram":
        pyautogui.press("win")
        pyautogui.typewrite("instagram")
        pyautogui.press("enter")
        time.sleep(3)
        click_image_in_window(window, instagram1)
        time.sleep(3)
        click_image_in_window(window, instagram3)
        time.sleep(3)
        click_image_in_window(window, instagram2)
        time.sleep(3)
        pyautogui.typewrite(name)
        time.sleep(3)
        pyautogui.press("tab", presses=2)
        pyautogui.press("enter")
        pyautogui.typewrite(message)
        pyautogui.press("enter")
        return f"Message sent to {name} on Instagram."

    else:
        return f"Platform '{platform}' not supported."

# ------------------- External AI APIs -------------------
def ask_deepseek(prompt: str) -> str:
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "deepseek-v3.2:cloud", "prompt": prompt, "stream": False},
            timeout=60
        )
        return r.json().get("response", "").strip() if r.ok else f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Request failed: {e}"

def ask_ollama(prompt: str) -> str:
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "Creative-Crafter/SOLAR-gemma3:27b_cloud", "prompt": prompt, "stream": False},
            timeout=60
        )
        return r.json().get("response", "").strip() if r.ok else f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Request failed: {e}"
    
def ask_qwencoder(prompt: str) -> str:
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "qwen3-coder-next:cloud", "prompt": prompt, "stream": False},
            timeout=60
        )
        return r.json().get("response", "").strip() if r.ok else f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Request failed: {e}"

# ------------------- Text Command Processor -------------------
def process_text(command):
    command = command.lower()
    print("command: ", command)

    if "send message" in command or ("say" in command and "to" in command and "on" in command):
        return send_message_skill(command)

    elif "time" in command:
        now = datetime.now()
        current_time = now.strftime("%I:%M %p")
        return f"The current time is {current_time}."

    elif "date" in command:
        today = datetime.now()
        current_date = today.strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."

    elif "code" in command or "program" in command:
        code = ask_qwencoder("Do not text me any explanation, only the code. That's what you should make: " + command)
        pyperclip.copy(code)
        return ask_ollama("Describe this code. Only describe it. Code:\n\n" + str(code))

    elif "mail" in command or ("messege" in command and "to" in command):
        mail = ask_deepseek("Only write the messenge . nothing else" + command)
        subject = ask_deepseek("write a very short subject for this email: " + mail)
        return mail

    elif "deadline" in command:
        create_and_open_calendar_event(command)
        return "✅ Event created and opened in your calendar app."

    elif command.startswith("open "):
        target = command[5:].strip()
        launch_and_move(target)
        return f"{target} is now open and moved to the default screen."
    
    elif command.startswith("oh pen ") or command.startswith("oh pin "):
        target = command[6:].strip()
        launch_and_move(target)
        return f"{target} is now open and moved to the default screen."

    else:
        return ask_ollama(command)

# ------------------- Helper Functions -------------------
def extract_triple_quote_blocks(text):
    pattern = r"```([^\n]*)\n(.*?)\n?```"
    matches = re.findall(pattern, text, re.DOTALL)
    code_blocks = []
    for i, (lang, code) in enumerate(matches, 1):
        lang = lang.strip().lower()
        ext = {
            "python": ".py",
            "html": ".html",
            "js": ".js",
            "javascript": ".js",
            "css": ".css"
        }.get(lang, ".txt")
        filename = f"codeblock_{i}_{lang}{ext}"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code.strip())
        code_blocks.append(code.strip())
    return code_blocks

def extract_all_phone_numbers(text):
    pattern = r'(?:(?:\+|00)[1-9]\d{0,2})?[\s\-]?(?:\(?\d+\)?[\s\-]?){4,}'
    matches = re.findall(pattern, text)
    return [re.sub(r'[\s\-\(\)]', '', m) for m in matches]

def extract_event_details(command):
    title_match = re.search(r"(name it|called)\s+(.*?)[\.\n]?$", command, re.IGNORECASE)
    title = title_match.group(2).strip() if title_match else "Untitled Event"
    time_match = re.search(r"(from|between)\s+(.*?)\s+(to|and)\s+(.*?)([\.\n]|$)", command, re.IGNORECASE)
    if not time_match:
        return None
    start_time_str = time_match.group(2).strip()
    end_time_str = time_match.group(4).strip()
    date_match = re.search(r"(on\s+\w+ \d+|tomorrow|today|next \w+)", command, re.IGNORECASE)
    date_context = date_match.group(0) if date_match else "today"
    start_dt = dateparser.parse(f"{date_context} at {start_time_str}")
    end_dt = dateparser.parse(f"{date_context} at {end_time_str}")
    if not start_dt or not end_dt:
        return None
    return {"title": title, "start_dt": start_dt, "end_dt": end_dt}

def create_and_open_calendar_event(command):
    event_data = extract_event_details(command)
    if not event_data:
        print("⚠️  Could not extract event details.")
        return
    cal = Calendar()
    e = Event()
    e.name = event_data["title"]
    e.begin = event_data["start_dt"]
    e.end = event_data["end_dt"]
    cal.events.add(e)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ics")
    filepath = tmp_file.name
    tmp_file.close()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(str(cal))
    if os.name == "nt":
        os.startfile(filepath)
    elif os.uname().sysname == "Darwin":
        os.system(f"open '{filepath}'")
    else:
        os.system(f"xdg-open '{filepath}'")