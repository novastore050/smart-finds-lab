# Installation

You need three things: **Python 3.9+**, **FFmpeg**, and three small Python packages.
Node.js is **not** required.

After installing, open a terminal in the `Smart-Finds-Lab` folder and run:

```bash
python scripts/sfl.py doctor
```

It should end with `RESULT: everything needed is installed.`

---

## Windows 10/11

### 1. Python
1. Download Python from https://www.python.org/downloads/ (the big yellow button).
2. Run the installer. **Tick "Add python.exe to PATH"** at the bottom of the first screen, then click *Install Now*.
3. Open a **new** Command Prompt and check the version. It should print `Python 3.x.x`:

```bash
python --version
```

If `python` is not recognised, try `py --version` and use `py` instead of `python` in every command.

### 2. FFmpeg
The easiest way is winget, which is built into Windows 10/11:

```bash
winget install --id Gyan.FFmpeg -e
```

Close the Command Prompt, open a new one, and check that it prints a version:

```bash
ffmpeg -version
```

Manual alternative: download the "release full" build from https://www.gyan.dev/ffmpeg/builds/, unzip it
to `C:\ffmpeg`, and add `C:\ffmpeg\bin` to PATH (Start → "Edit the system environment variables" →
Environment Variables → Path → New).

> Use a **full** build. It includes the subtitle renderer (libass) and H.264 encoder (libx264) this system needs.
> `doctor` tells you if anything is missing.

### 3. Python packages
In the `Smart-Finds-Lab` folder:

```bash
python -m pip install -r requirements.txt
```

### Opening a terminal in the folder
In File Explorer, open `Smart-Finds-Lab`, click the address bar, type `cmd`, and press Enter.

---

## macOS

1. Install Homebrew (https://brew.sh). Copy the one-line command from their page into Terminal.
2. Install Python and FFmpeg:

```bash
brew install python ffmpeg
```

3. In the `Smart-Finds-Lab` folder, install the Python packages:

```bash
python3 -m pip install -r requirements.txt
```

Use `python3` instead of `python` in all commands. If pip refuses with "externally managed
environment", create a virtual environment once:

```bash
python3 -m venv .venv
```
```bash
source .venv/bin/activate
```
```bash
pip install -r requirements.txt
```

After that, run `source .venv/bin/activate` each time you open a new Terminal.

---

## Linux (Ubuntu/Debian)

```bash
sudo apt install python3 python3-pip ffmpeg
```
```bash
python3 -m pip install -r requirements.txt
```

---

## Optional: exact automatic subtitles (Whisper)

Without Whisper, subtitles come from an `.srt` file you provide (exact timing) or from the narration
text in your timeline (timing is **estimated**). Installing faster-whisper lets the system listen to
your voice-over and create perfectly timed subtitles automatically:

```bash
python -m pip install faster-whisper
```

The first run downloads a speech model (about 500 MB) and transcription is slower on older
computers. It is free and runs offline on your computer.

Another good option: many voice-over tools (ElevenLabs, etc.) can export an `.srt` with the audio.
Use that and you don't need Whisper.

---

## Optional: Remotion
Not needed. All titles and animations are made with FFmpeg + ASS subtitles. Remotion (Node.js/React)
could be added later for very complex animated graphics. See "Extending the system" in
[TIMELINE-REFERENCE.md](TIMELINE-REFERENCE.md).

## Disk space
Keep at least 20 GB free. Working files go to `temp/`, which you can delete at any time.
