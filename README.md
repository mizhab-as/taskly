# ⚡ Taskly — Modern Task & Productivity Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-teal.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-black.svg)](https://flask.palletsprojects.org/)
[![PWA Ready](https://img.shields.io/badge/PWA-Ready-17B897.svg)](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
[![Vercel Deployment](https://img.shields.io/badge/Deploy-Vercel-000000.svg)](https://vercel.com)
[![Android APK](https://img.shields.io/badge/Android-PWA%2FCapacitor-3DDC84.svg)](https://developer.android.com/)

**Taskly** is a fast, visually stunning, dual-mode productivity application designed for managing tasks, lists, and schedules effortlessly. Built with a responsive **Vanilla CSS** design system, **Ultra-Reflective AMOLED Black Dark Mode**, interactive **Calendar View**, REST API backend, and **Offline PWA & Capacitor Android** support.

---

## 📸 Screenshots Showcase

### 1. Main Dashboard & Analytics
![Dashboard](screenshots/01_dashboard.png)
*Hero greeting, progress ring chart, quick list access, and productivity statistics.*

---

### 2. List Detail & Priority Task Management
![List Detail](screenshots/02_list_detail.png)
*Filter tasks by status (All, Active, Completed), sort by priority (High, Medium, Low), and set due dates.*

---

### 3. Add & Edit Task Modal
![Add Task Modal](screenshots/03_add_task_modal.png)
*Interactive task creation with custom priority pills and due date pickers.*

---

### 4. Custom List Creation & Emoji Picker
![Create List Modal](screenshots/04_create_list_modal.png)
*Create custom list categories with tailored color palettes and emoji badges.*

---

### 5. Profile Popover & Ultra AMOLED Dark Theme
![Profile Popover](screenshots/05_profile_popover.png)
*Profile stats, streak tracking, account settings, and instant toggle for **Ultra Reflective AMOLED Black Theme**.*

---

### 6. Keyboard Shortcuts Modal
![Keyboard Shortcuts](screenshots/06_keyboard_shortcuts.png)
*Boost speed with built-in hotkeys (`N` for new task, `C` for calendar, `/` for search, `Esc` to navigate).*

---

### 7. Instant Live Search
![Live Search](screenshots/07_live_search.png)
*Real-time task search with keyword highlighting across all lists and categories.*

---

## ✨ Key Features

- 📱 **Dual Engine Architecture**: Automatically connects to the Python Flask REST API backend when available, and seamlessly falls back to `localStorage` for complete offline operation.
- 🎨 **Ultra Reflective AMOLED Black Theme**: Features true `#000000` pitch black backgrounds for OLED display energy efficiency, glossy metallic cards, glassmorphism specular borders, and neon pops.
- 📅 **Interactive Calendar View**: View tasks by scheduled date, switch months/years, and manage daily schedules visually.
- 🔍 **Instant Live Search**: Perform instant real-time searches across all tasks with highlighted keyword matches.
- 📦 **Data Exporting**: Standalone CLI & API endpoints to download your full task history in structured **JSON** or **CSV** format.
- ⏰ **Background Reminders Daemon**: Background process that monitors overdue tasks and delivers desktop notifications.
- 📲 **Android App & PWA Ready**: Install natively on Android devices via PWA or build a native APK using Capacitor.
- ☁️ **Vercel Cloud Deployment**: Pre-configured `vercel.json` for 1-click cloud deployment.

---

## 🚀 Quick Start (Local Development)

### 1. Run via Start Script (Recommended)

Simply execute the launcher script:

```bash
./start.sh
```

This script automatically:
1. Installs Python dependencies (`Flask`, `flask-cors`, `gunicorn`).
2. Frees port `5050` if previously occupied.
3. Launches the Flask REST API server (`python/server.py`).
4. Starts the background reminder daemon (`python/reminders.py`).
5. Opens `http://localhost:5050` in your default browser.

### 2. Manual Launch

```bash
# Install dependencies
pip install -r requirements.txt

# Start the Flask API & static web server
python3 python/server.py
```

To stop all background processes:
```bash
./stop.sh
```

---

## 📱 Android Phone Installation (PWA & APK)

Taskly supports **two simple methods** for running natively on Android devices:

### Method 1: Web PWA Installation (Instant — No Build Required)

1. Host or open Taskly in **Google Chrome** or **Microsoft Edge** on your Android device.
2. Tap the menu icon (`⋮`) in the top-right corner.
3. Select **"Install app"** or **"Add to Home screen"**.
4. Taskly will install as a standalone Android app with full app launcher icon, native splash screen, and offline support!

### Method 2: Native Android APK Build (Capacitor)

Taskly comes pre-configured with `capacitor.config.json`. To build an Android APK:

```bash
# 1. Install Capacitor CLI & Android package
npm install @capacitor/core @capacitor/cli @capacitor/android

# 2. Add Android platform
npx cap add android

# 3. Open project in Android Studio to build APK
npx cap open android
```

From Android Studio, click **Build > Build Bundle(s) / APK(s) > Build APK** to generate your `.apk` file for Android phones.

---

## ☁️ Vercel Deployment Guide

Taskly is pre-configured for 1-click deployment on **Vercel** via `vercel.json` using `@vercel/python`.

### Option A: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to Vercel
vercel
```

### Option B: GitHub Integration

1. Push this repository to GitHub.
2. Go to [Vercel Dashboard](https://vercel.com/new).
3. Import the repository — Vercel will automatically detect `vercel.json` and deploy your app instantly!

---

## 🛠️ REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | `GET` | Health check & server status |
| `/api/data` | `GET` | Fetch all task and list data |
| `/api/data` | `POST` | Save/update task and list database |
| `/api/export/json` | `GET` | Download timestamped JSON backup |
| `/api/export/csv` | `GET` | Download tasks formatted as CSV |
| `/api/overdue` | `GET` | Fetch uncompleted overdue tasks |

### CLI Data Export

You can also export data directly from the terminal:

```bash
python3 python/export.py          # Exports JSON & CSV to exports/
python3 python/export.py --json   # JSON only
python3 python/export.py --csv    # CSV only
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| <kbd>N</kbd> | Open Add Task Modal |
| <kbd>C</kbd> | Toggle Calendar View |
| <kbd>/</kbd> | Focus Live Search Bar |
| <kbd>Esc</kbd> | Return to Dashboard / Clear Search |
| <kbd>Enter</kbd> | Submit Form / Modal |

---

## 📁 Repository Structure

```
taskly/
├── frontend/                 # Web App Frontend (HTML5, Vanilla CSS, JS)
│   ├── index.html            # App Markup & Modals
│   ├── style.css             # Design System & Eye-Comfort Dark Theme
│   ├── app.js                # App Logic, State, Calendar & API Bridge
│   ├── manifest.json         # PWA Manifest Config
│   └── sw.js                 # PWA Service Worker
├── python/                   # Backend Python Scripts & Utilities
│   ├── server.py             # Python Flask REST API & Static File Server
│   ├── export.py             # CLI Data Export Utility
│   ├── reminders.py          # Background Desktop Reminder Daemon
│   └── take_screenshots.py   # Automated Playwright Screenshot Generator
├── screenshots/              # High-resolution documentation screenshots
├── data/                     # Data persistence directory (tasks.json)
├── start.sh                  # Main executable launcher script
├── stop.sh                   # Shutdown script
├── vercel.json               # Vercel deployment configuration
├── capacitor.config.json     # Capacitor Android configuration
└── requirements.txt          # Python dependencies
```

---

## 📄 License

This project is licensed under the **MIT License**. Feel free to modify and adapt for personal or commercial productivity projects!
