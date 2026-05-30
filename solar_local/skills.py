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
        print(f" Screen {screen_number} not found. Defaulting to primary.")
        return 0, 0

def launch_and_move(target, screen_num=1):
    """
    Launches an app or website and moves its window to the specified screen.
    """
    is_url = target.startswith("http") or "www." in target
    
    if is_url:
        print(f" Opening website: {target}")
        cmd = f'start chrome --new-window "{target}"'
        subprocess.Popen(cmd, shell=True)
        search_title = "Google Chrome"
    else:
        print(f" Opening application: {target}")
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
            print(f" Successfully placed {target} on Screen {screen_num}")
        except Exception as e:
            print(f" Could not move window: {e}")
    else:
        print(f" Timeout: Could not find a window for '{target}'")

# ------------------- Messaging Images -------------------
whatsapp = "whatsapp.png"
discord = "discord_search.png"
instagram1 = "insta1.png"
instagram2 = "insta2.png"
instagram3 = "insta3.png"

# ------------------- Sending Messages -------------------
def normalize_model_output(output: str) -> str:
    output = output.strip()

    if output.startswith("```") and output.endswith("```"):
        output = output[3:-3].strip()
        if "\n" in output:
            first_line, rest = output.split("\n", 1)
            if not first_line.strip().startswith("/"):
                output = rest.strip()

    if output.startswith("`") and output.endswith("`"):
        output = output[1:-1].strip()

    command_match = re.search(
        r'(?im)^/(send|time|date|code|event|open)\b.*$',
        output
    )
    if command_match:
        output = command_match.group(0).strip()

    return output

def parse_send_command(output: str):
    """
    Erwartetes Format vom Modelfile:
    /send Message: "<message>"; Name: "<name>"; Platform: "<platform>"
    """
    pattern = (
        r'^/send\s+'
        r'Message:\s*"(?P<message>.*?)"\s*;\s*'
        r'Name:\s*"(?P<name>.*?)"\s*;\s*'
        r'Platform:\s*"(?P<platform>discord|whatsapp|instagram)"\s*$'
    )
    match = re.match(pattern, output.strip(), re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    message = match.group("message").strip()
    name = match.group("name").strip()
    platform = match.group("platform").strip().lower()

    if not message or not name or not platform:
        return None

    return message, name, platform

def parse_code_command(output: str):
    """
    Expected format from the Modelfile:
    /code "<clear description of the code the user wants>"
    """
    output = normalize_model_output(output)
    pattern = r'^/code\s+"(?P<request>.*?)"\s*$'
    match = re.match(pattern, output.strip(), re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    code_request = match.group("request").strip()
    if not code_request:
        return None

    return code_request

def parse_event_command(output: str):
    """
    Expected format from the Modelfile:
    /event name: "<event name>"; date-start: "<start date>"; time-start: "<start time>"; date-end: "<end date>"; time-end: "<end time>"
    """
    output = normalize_model_output(output)
    pattern = (
        r'^/event\s+'
        r'name:\s*"(?P<name>.*?)"\s*;\s*'
        r'date-start:\s*"(?P<date_start>.*?)"\s*;\s*'
        r'time-start:\s*"(?P<time_start>.*?)"\s*;\s*'
        r'date-end:\s*"(?P<date_end>.*?)"\s*;\s*'
        r'time-end:\s*"(?P<time_end>.*?)"\s*$'
    )
    match = re.match(pattern, output.strip(), re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    name = match.group("name").strip()
    date_start = match.group("date_start").strip()
    time_start = match.group("time_start").strip()
    date_end = match.group("date_end").strip()
    time_end = match.group("time_end").strip()

    if not all([name, date_start, time_start, date_end, time_end]):
        return None

    return name, date_start, time_start, date_end, time_end

def parse_open_command(output: str):
    """
    Expected format from the Modelfile:
    /open "<application or website the user wants to open>"
    """
    output = normalize_model_output(output)
    pattern = r'^/open\s+(?:"(?P<quoted_target>.*?)"|(?P<plain_target>.+?))\s*$'
    match = re.match(pattern, output.strip(), re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    target = (match.group("quoted_target") or match.group("plain_target")).strip()
    if not target:
        return None

    return target

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

def send_message_skill(message: str, name: str, platform: str):
    """
    Sends a message using parsed /send variables from process_text.
    Supported platforms: whatsapp, discord, instagram
    """
    message = message.strip()
    name = name.strip()
    platform = platform.strip().lower()

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
def ask_ollama(prompt: str) -> str:
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "Creative-Crafter/SOLAR-llama3.2-vision:11bv2", "prompt": prompt, "stream": False},
            timeout=60
        )
        return r.json().get("response", "").strip() if r.ok else f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Request failed: {e}"
    
def ask_deepseekcoder(prompt: str) -> str:
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "Malicus7862/deepseekcoder-6.7b-jarvis-gguf:latest", "prompt": prompt, "stream": False},
            timeout=60
        )
        return r.json().get("response", "").strip() if r.ok else f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Request failed: {e}"

# ------------------- Text Command Processor -------------------
def process_text(command):
    print("command: ", command)
    output = normalize_model_output(ask_ollama(command))

    if output.lower().startswith("/send"):
        parsed = parse_send_command(output)
        if not parsed:
            return "I could not understand the send command."

        message, name, platform = parsed
        return send_message_skill(message, name, platform)

    elif output.lower().startswith("/time"):
        now = datetime.now()
        current_time = now.strftime("%I:%M %p")
        return f"The current time is {current_time}."

    elif output.lower().startswith("/date"):
        today = datetime.now()
        current_date = today.strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."

    elif output.lower().startswith("/code"):
        code_request = parse_code_command(output)
        if not code_request:
            return "I could not understand the code command."

        code = ask_deepseekcoder("Return only the complete code. Do not include explanations, Markdown, or extra text. Task: " + code_request)
        pyperclip.copy(code)
        return "Here is the code. I also copied it to your clipboard:\n\n" + str(code)

    elif output.lower().startswith("/event"):
        parsed = parse_event_command(output)
        if not parsed:
            return "I could not understand the calendar event command."

        name, date_start, time_start, date_end, time_end = parsed
        return create_and_open_calendar_event_from_fields(
            name,
            date_start,
            time_start,
            date_end,
            time_end
        )



    elif output.lower().startswith("/open"):
        target = parse_open_command(output)
        if not target:
            return "I could not understand the open command."

        launch_and_move(target)
        return f"{target} is now open and moved to the default screen."

    else: return output

# ------------------- Helper Functions -------------------
def create_and_open_calendar_event_from_fields(name, date_start, time_start, date_end, time_end):
    start_dt = dateparser.parse(f"{date_start} {time_start}")
    end_dt = dateparser.parse(f"{date_end} {time_end}")

    if not start_dt or not end_dt:
        return "I could not parse the event date or time."

    event_data = {
        "title": name,
        "start_dt": start_dt,
        "end_dt": end_dt,
    }
    open_calendar_event(event_data)
    return f"Event created: {name}."

def open_calendar_event(event_data):
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
