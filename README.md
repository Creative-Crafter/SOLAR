# SOLAR — Autonomous AI Agent

```
 ____         ___        _              _          ____  
/ ___|       / _ \      | |            / \        |  _ \ 
\___ \      | | | |     | |           / _ \       | |_) |
 ___) |  _  | |_| |  _  | |___   _   / ___ \   _  |  _ < 
|____/  (_)  \___/  (_) |_____| (_) /_/   \_\ (_) |_| \_\
```

**S**ystematic **O**nline or **L**ocal **A**utonomous **R**obot

> Voice-Driven · Local First · Open-Source

SOLAR is a **voice-activated AI agent** that runs fully on your Windows machine — handling calls, sending messages, writing code, and controlling your desktop through natural speech. No cloud required.

---

## ✨ Features

### 📞 Autonomous WhatsApp Call Handler
SOLAR monitors your desktop for incoming WhatsApp calls using Win32 `EnumWindows`. It screenshots the notification, runs it through a vision model to read the caller's name, then asks you by voice whether to answer — or declines with a custom voicemail, all autonomously.

```
SOLAR: "Incoming call from Anna Müller. Should I answer?"
  You: "No, I'm busy." → SOLAR answers, leaves VM, hangs up
```

### 👂 Custom Wake Word
Define your agent's name in `config.yaml`. SOLAR listens 24/7 using fully offline Vosk STT — no internet, no cloud microphone, zero latency.

### 💬 Cross-Platform Messaging
Send messages on **WhatsApp**, **Discord**, and **Instagram** using image recognition to navigate each app's UI. No official API required.

```
You: "say happy birthday to Thomas on whatsapp"
```

### 💻 Voice Code Generation
Say "code a…" and SOLAR generates it with the Malicus7862 DeepSeek Coder model, auto-copies to clipboard, then describes what was built.

```
You: "code a python web scraper"
```

### 🖥️ App & Window Manager
Open any app or URL and move its window to any connected monitor. Multi-monitor aware, including negative-coordinate secondary screens.

```
You: "open youtube.com"
```

### 📅 Voice Calendar Events
Describe a meeting in plain speech. SOLAR parses the time with `dateparser`, creates an `.ics` file, and opens it straight in your calendar app.

```
You: "deadline from 2pm to 4pm name it sprint review"
```

### 🧩 Multi-Model AI Routing
SOLAR automatically routes each task to the right model via Ollama on `localhost:11434`. Vision tasks go to the multimodal model, code to DeepSeek Coder, writing to DeepSeek v2, and general chat to the main model. No API keys, no data leaving your machine.

---

## 🔄 How It Works

```
🎙️  Wake Word       →  Vosk listens 24/7 for your custom name from config.yaml
🔊  Hear Command    →  A beep confirms activation; full command transcribed offline
🧠  Route & Execute →  Intent matched — messaging, coding, calls, apps, or chat
🔈  Speak Back      →  Kokoro TTS voices the response in your configured name & gender
```

---

## 🤖 Model Stack

### Local Models — `localhost` · No internet

| Model | Type | Used For |
|---|---|---|
| `llama3.2-vision:11b` | Vision | Call ID · general chat |
| `Malicus7862/deepseekcoder-6.7b-jarvis-gguf:latest` | Code | Voice code generation |
| `deepseek-v2:16b` | Text | Email · writing tasks |
| `Vosk small-en-us` | STT | Wake word · transcription |
| `Kokoro TTS` | TTS | Voice responses |

### Cloud Models — `localhost:11434` · Ollama cloud

| Model | Type | Used For |
|---|---|---|
| `Creative-Crafter/SOLAR-gemma3:27b_cloud` | Vision | Call ID · general chat |
| `qwen3-coder-next:cloud` | Code | Voice code generation |
| `deepseek-v3.2:cloud` | Text | Email · writing tasks |
| `Vosk small-en-us` | STT | Same as local |
| `Kokoro TTS` | TTS | Same as local |

> Vosk STT & Kokoro TTS are shared between both setups.

---

## ⚡ Installation

Both install scripts handle dependencies and config automatically. Run in **Administrator PowerShell**.

### 🖥️ Local Install
All models run on your GPU · No cloud inference · ~20 GB VRAM required

```powershell
irm https://solar.creative-crafter.de/install-local.ps1 | iex
```

### ☁️ Cloud Install
Ollama cloud models · No powerful GPU needed · Requires an Ollama account

```powershell
irm https://solar.creative-crafter.de/install-cloud.ps1 | iex
```

### Requirements

| | |
|---|---|
| 🪟 OS | Windows 10 / 11 |
| 🐍 Python | 3.11.0 |
| 🦙 Ollama | v0.12+ |
| 🎙️ Hardware | Microphone |
| 💾 Storage | ~20 GB free (local models) |

---

## 🛠️ Extending SOLAR

SOLAR is built to be hacked on. Add new skills in `skills.py` or swap in different Ollama models. Every line is public.

```
config.yaml   →  Set your wake word name, voice gender, and model preferences
skills.py     →  Add new voice-triggered capabilities
```

---

## 📄 License

Licensed under the **Apache 2.0 License** — free to use, fork, and extend.

---

## 🔗 Links

- 🌐 [Website](https://solar.creative-crafter.de/)
- 🐙 [GitHub](https://github.com/Creative-Crafter/SOLAR)
- 🦙 [Ollama Model Library](https://ollama.com/library)

---

> © 2025 SOLAR Project — Apache 2.0 License · v0.1 Alpha