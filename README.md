# AI Rewrite Assistant

A lightweight **local AI rewriting assistant for Windows**.

Select any text → press a hotkey → instantly rewrite it using a **local LLM**.

The tool integrates with **Ollama / LM Studio compatible APIs** and provides a **floating toolbar near the cursor** for quick text transformation.

This project is designed to be **fast, private, and fully local**.

---

# Features

- Global hotkey trigger
- Works in **any application** (browser, IDE, Word, etc.)
- Uses **local AI models**
- Floating toolbar near the mouse cursor
- One-click rewrite actions
- Clipboard based workflow
- System tray support
- Packaged as a **standalone Windows executable**

---

# Demo Workflow

1. Select any text  
2. Press **Ctrl + Shift + Space**  
3. Floating toolbar appears  
4. Choose a rewrite action  

Example:

Original text
The experiment show that the result is very good.


Rewritten text


The experiment demonstrates that the results are highly promising.


---

# Supported Actions

The toolbar provides multiple rewriting modes:

- Rewrite
- Expand
- Shorten
- Academic Style
- Improve Grammar

All requests are processed by your **local AI model**.

---

# Requirements

Python **3.9+**

Install dependencies:


pip install PyQt6 keyboard pyperclip requests pystray pillow pywin32


---

# Running From Source

Run with administrator privileges (required for global hotkeys):


python ai_rewrite.py


After launching:

Hotkey


Ctrl + Shift + Space


A system tray icon will appear.

Right-click the tray icon to exit the program.

---

# Backend Configuration

The tool connects to a **local LLM server** compatible with the OpenAI API.

Supported backends:

## Ollama

Example endpoint:


http://localhost:11434/v1/chat/completions


Example models:


gemma3:4b
qwen2.5:3b


Start Ollama and pull a model:


ollama pull gemma3:4b


---

## LM Studio

Example endpoint:


http://localhost:1234/v1/chat/completions


Make sure a model is **loaded in LM Studio** before running the tool.

---

# Build Standalone EXE

This project includes build scripts for packaging with **PyInstaller**.

Install PyInstaller:


pip install pyinstaller


Build the executable:


build.bat


or manually:


pyinstaller build.spec


After building, the executable will be located in:


dist/


You can run it directly without installing Python.

---

# Project Structure


ai_rewrite_tool/
│
├── ai_rewrite.py
├── prompts.json
├── config.json
│
├── build.spec
├── build.bat
│
├── dist/
├── build/
│
└── README.md


---

# How It Works

The workflow of the assistant:


User selects text
↓
Hotkey triggered
↓
Copy text to clipboard
↓
Send request to local LLM
↓
Receive rewritten text
↓
Replace clipboard
↓
Paste back to application

Why This Tool

Most AI writing tools require:

Cloud APIs

Internet connection

Paid subscriptions

This project runs 100% locally, providing:

Privacy

Fast response

Zero API cost

Future Improvements

Planned improvements:

Streaming responses

Model selection UI

Custom prompt editor

Better floating UI

macOS support
