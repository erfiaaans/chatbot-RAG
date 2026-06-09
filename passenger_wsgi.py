import os
import sys

# 1. Menentukan path ke aplikasi Anda
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

# 2. Mengaktifkan virtual environment dari UV (jika ada)
# Ganti 'username' dengan username cPanel Anda
venv_path = os.path.join(app_dir, ".venv", "bin", "python")
if os.path.exists(venv_path):
    os.environ["PATH"] = (
        os.path.join(app_dir, ".venv", "bin") + os.pathsep + os.environ["PATH"]
    )

# 3. Import objek 'app' dari file app.py Anda
from app import app as application
