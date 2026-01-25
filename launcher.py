"""
DMP Launcher - Windows GUI for Django Server Management

Features:
- Start/Stop server with status indicator
- Port configuration
- Auto-open browser option
- System tray minimization (Windows only)
- Log output display
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import sys
import os
import webbrowser
import signal
import queue
from datetime import datetime

# Optional: System tray support (Windows only)
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_SUPPORT = True
except ImportError:
    TRAY_SUPPORT = False


class DMPLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("DMP - Device Management Platform")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)

        # State
        self.server_process = None
        self.is_running = False
        self.log_queue = queue.Queue()
        self.tray_icon = None

        # Configuration
        self.port = tk.StringVar(value="8000")
        self.auto_open_browser = tk.BooleanVar(value=True)
        self.minimize_to_tray = tk.BooleanVar(value=False)

        # Build UI
        self._create_ui()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start log reader
        self._start_log_reader()

        # Log startup message
        self._log("DMP Launcher started", "info")
        self._log(f"Working directory: {os.path.dirname(os.path.abspath(__file__))}", "info")

    def _create_ui(self):
        """Create the main UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(header_frame, text="DMP Server Control",
                  font=("Segoe UI", 14, "bold")).pack(side="left")

        # Status indicator
        self.status_frame = ttk.Frame(header_frame)
        self.status_frame.pack(side="right")

        self.status_dot = tk.Canvas(self.status_frame, width=16, height=16,
                                    highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 5))
        self._draw_status_dot("#f14c4c")  # Red

        self.status_label = ttk.Label(self.status_frame, text="Stopped",
                                      font=("Segoe UI", 10))
        self.status_label.pack(side="left")

        # Control Panel
        control_frame = ttk.LabelFrame(main_frame, text="Server Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)

        # Port configuration
        ttk.Label(control_frame, text="Port:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        port_entry = ttk.Entry(control_frame, textvariable=self.port, width=10)
        port_entry.grid(row=0, column=1, sticky="w")

        # Checkboxes
        ttk.Checkbutton(control_frame, text="Auto-open browser",
                        variable=self.auto_open_browser).grid(row=0, column=2, padx=(20, 0))

        if TRAY_SUPPORT and sys.platform == "win32":
            ttk.Checkbutton(control_frame, text="Minimize to tray",
                            variable=self.minimize_to_tray).grid(row=0, column=3, padx=(20, 0))

        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(15, 0))

        self.start_btn = ttk.Button(button_frame, text="Start Server",
                                    command=self._start_server, width=15)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="Stop Server",
                                   command=self._stop_server, width=15, state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 10))

        ttk.Button(button_frame, text="Open Browser",
                   command=self._open_browser, width=15).pack(side="left", padx=(0, 10))

        ttk.Button(button_frame, text="Clear Log",
                   command=self._clear_log, width=15).pack(side="left")

        # Log Output
        log_frame = ttk.LabelFrame(main_frame, text="Server Log", padding="5")
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                                   font=("Consolas", 9),
                                                   state="disabled",
                                                   bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Configure log colors
        self.log_text.tag_configure("info", foreground="#4ec9b0")
        self.log_text.tag_configure("warning", foreground="#dcdcaa")
        self.log_text.tag_configure("error", foreground="#f14c4c")
        self.log_text.tag_configure("success", foreground="#6a9955")

        # Footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self.url_label = ttk.Label(footer_frame, text="Server URL: Not running",
                                   foreground="gray")
        self.url_label.pack(side="left")

    def _draw_status_dot(self, color):
        """Draw status indicator dot"""
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 14, 14, fill=color, outline="")

    def _log(self, message, level="info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put((f"[{timestamp}] {message}\n", level))

    def _start_log_reader(self):
        """Process log queue and update UI"""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                self.log_text.config(state="normal")
                self.log_text.insert(tk.END, message, level)
                self.log_text.see(tk.END)
                self.log_text.config(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100, self._start_log_reader)

    def _start_server(self):
        """Start Django development server"""
        if self.is_running:
            messagebox.showwarning("Warning", "Server is already running!")
            return

        port = self.port.get()
        if not port.isdigit() or not (1024 <= int(port) <= 65535):
            messagebox.showerror("Error", "Invalid port number. Use 1024-65535.")
            return

        self._log(f"Starting server on port {port}...", "info")

        # Find the manage.py location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        manage_py = os.path.join(script_dir, "manage.py")

        if not os.path.exists(manage_py):
            self._log("Error: manage.py not found!", "error")
            return

        # Find Python executable (prefer venv)
        if sys.platform == "win32":
            venv_python = os.path.join(script_dir, "venv", "Scripts", "python.exe")
        else:
            venv_python = os.path.join(script_dir, "venv", "bin", "python")

        if os.path.exists(venv_python):
            python_exe = venv_python
            self._log(f"Using virtual environment Python", "info")
        else:
            python_exe = sys.executable
            self._log(f"Using system Python: {python_exe}", "warning")

        try:
            # Start Django server
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            self.server_process = subprocess.Popen(
                [python_exe, manage_py, "runserver", f"0.0.0.0:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=script_dir,
                creationflags=creationflags,
                text=True,
                bufsize=1
            )

            self.is_running = True
            self._update_ui_state()

            # Start output reader thread
            threading.Thread(target=self._read_server_output, daemon=True).start()

            self._log(f"Server started on port {port}", "success")
            self.url_label.config(text=f"Server URL: http://localhost:{port}")

            # Auto-open browser
            if self.auto_open_browser.get():
                self.root.after(2000, self._open_browser)

        except Exception as e:
            self._log(f"Failed to start server: {str(e)}", "error")

    def _read_server_output(self):
        """Read server output in background thread"""
        if self.server_process:
            try:
                for line in iter(self.server_process.stdout.readline, ''):
                    if line:
                        # Determine log level from content
                        level = "info"
                        line_lower = line.lower()
                        if "error" in line_lower or "exception" in line_lower:
                            level = "error"
                        elif "warning" in line_lower:
                            level = "warning"
                        elif "200" in line or "GET" in line or "POST" in line:
                            level = "success"

                        self._log(line.strip(), level)
            except Exception:
                pass

            # Process ended
            self.is_running = False
            self.root.after(0, self._update_ui_state)
            self._log("Server stopped", "warning")

    def _stop_server(self):
        """Stop Django development server"""
        if not self.is_running or not self.server_process:
            return

        self._log("Stopping server...", "warning")

        try:
            if sys.platform == "win32":
                self.server_process.terminate()
            else:
                os.kill(self.server_process.pid, signal.SIGTERM)

            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()

        except Exception as e:
            self._log(f"Error stopping server: {str(e)}", "error")

        self.is_running = False
        self.server_process = None
        self._update_ui_state()
        self._log("Server stopped", "info")
        self.url_label.config(text="Server URL: Not running")

    def _update_ui_state(self):
        """Update UI based on server state"""
        if self.is_running:
            self._draw_status_dot("#4ec9b0")  # Green
            self.status_label.config(text="Running")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        else:
            self._draw_status_dot("#f14c4c")  # Red
            self.status_label.config(text="Stopped")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    def _open_browser(self):
        """Open browser to server URL"""
        port = self.port.get()
        url = f"http://localhost:{port}"
        webbrowser.open(url)
        self._log(f"Opening browser: {url}", "info")

    def _clear_log(self):
        """Clear log output"""
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

    def _on_close(self):
        """Handle window close"""
        if self.minimize_to_tray.get() and TRAY_SUPPORT and sys.platform == "win32":
            self._minimize_to_tray()
        else:
            self._quit()

    def _minimize_to_tray(self):
        """Minimize to system tray (Windows only)"""
        if not TRAY_SUPPORT or sys.platform != "win32":
            return

        self.root.withdraw()

        if not self.tray_icon:
            # Create tray icon
            image = self._create_tray_image()
            menu = pystray.Menu(
                pystray.MenuItem("Show", self._show_from_tray),
                pystray.MenuItem("Start Server", self._start_server),
                pystray.MenuItem("Stop Server", self._stop_server),
                pystray.MenuItem("Exit", self._quit)
            )
            self.tray_icon = pystray.Icon("DMP", image, "DMP Launcher", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _create_tray_image(self):
        """Create tray icon image"""
        size = 64
        image = Image.new('RGB', (size, size), color='#2d2d2d')
        draw = ImageDraw.Draw(image)

        # Draw a simple "D" for DMP
        draw.rectangle([10, 10, 54, 54], outline='#4ec9b0', width=3)

        return image

    def _show_from_tray(self):
        """Show window from tray"""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.deiconify()

    def _quit(self):
        """Quit application"""
        if self.is_running:
            if messagebox.askyesno("Confirm Exit",
                                   "Server is still running. Stop it and exit?"):
                self._stop_server()
            else:
                return

        if self.tray_icon:
            self.tray_icon.stop()

        self.root.destroy()


def main():
    root = tk.Tk()

    # Set theme
    style = ttk.Style()
    if sys.platform == "win32":
        style.theme_use("vista")
    elif sys.platform == "darwin":
        style.theme_use("aqua")
    else:
        style.theme_use("clam")

    # Set icon (if available)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "static", "favicon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    app = DMPLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
