# Windows Installation Guide

## Quick Start (3 Steps)

### Step 1: Install Python

Download and install Python 3.12 or higher from [python.org](https://www.python.org/downloads/)

**Important:** During installation, check the box that says **"Add Python to PATH"**

### Step 2: Install DMP

1. Extract the DMP folder to your desired location (e.g., `C:\DMP`)
2. Double-click `install.bat`
3. Follow the prompts to create your admin account

### Step 3: Run DMP

Double-click `start.bat` - the application will open in your browser automatically.

---

## Daily Usage

| Action | How |
|--------|-----|
| **Start** | Double-click `start.bat` |
| **Stop** | Press `Ctrl+C` in the console window, or double-click `stop.bat` |
| **Access** | Open http://localhost:8000 in your browser |

---

## GUI Launcher (Optional)

For a graphical interface instead of batch files, use the Tkinter launcher:

```bash
# Run the launcher
python launcher.py
```

**Features:**
- Start/Stop server with visual status indicator
- Port configuration
- Auto-open browser option
- Log output display
- System tray minimization

**Build standalone executable:**
```bash
# Install PyInstaller
pip install pyinstaller pystray pillow

# Build .exe
pyinstaller launcher.spec

# Find executable in dist/DMP Launcher.exe
```

---

## Troubleshooting

### "Python is not recognized"

- Reinstall Python and make sure to check "Add Python to PATH"
- Or manually add Python to your system PATH

### "Port 8000 already in use"

- Run `stop.bat` to stop any existing server
- Or change the port in `start.bat` (edit `8000` to another number like `8080`)

### "Database errors"

- Delete `db.sqlite3` file
- Run `install.bat` again to recreate the database

### Reset everything

1. Delete the `venv` folder
2. Delete `db.sqlite3`
3. Delete `.env`
4. Run `install.bat` again

---

## Accessing from Other Computers

By default, DMP runs on `0.0.0.0:8000` which allows access from other computers on your network.

1. Find your computer's IP address (run `ipconfig` in Command Prompt)
2. Other computers can access DMP at `http://YOUR-IP:8000`

**Note:** You may need to allow Python through Windows Firewall.

---

## Updating DMP

1. Stop the server (`stop.bat` or Ctrl+C)
2. Replace the files with the new version (keep your `db.sqlite3` and `.env`)
3. Run `install.bat` to update dependencies
4. Start again with `start.bat`
