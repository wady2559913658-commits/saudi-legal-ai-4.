import os
import sys
import time
import threading
import urllib.request
from pathlib import Path

import uvicorn
import webview

def resource_path(relative):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / relative

# Store the SQLite database in the current user's profile.
if os.name == "nt":
    data_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SaudiLegalAI"
else:
    data_dir = Path.home() / ".saudi-legal-ai"
data_dir.mkdir(parents=True, exist_ok=True)
os.chdir(data_dir)

from backend.main import app

def serve():
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="error", access_log=False)

server_thread = threading.Thread(target=serve, daemon=True)
server_thread.start()

ready = False
for _ in range(120):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=0.5) as response:
            if response.status == 200:
                ready = True
                break
    except Exception:
        time.sleep(0.25)

if not ready:
    raise RuntimeError("تعذر تشغيل خدمة Saudi Legal AI المحلية.")

window = webview.create_window(
    "Saudi Legal AI | المساعد القانوني السعودي",
    "http://127.0.0.1:8765/",
    width=1280,
    height=850,
    min_size=(900, 620),
    text_select=True,
)
webview.start(gui="edgechromium")
