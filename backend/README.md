MediVerse U-Net Backend (shim)
================================

This folder contains a lightweight FastAPI shim to emulate the U-Net analysis backend.

Usage
-----

1. (Optional) Create a virtual environment and install dependencies:

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt

2. Start the server:

   python -m uvicorn main:app --host 0.0.0.0 --port 8050

3. Visit `http://localhost:8050/docs` to inspect the API.

When you are ready to replace the shim with your real U-Net implementation, copy your files
into this folder (e.g. from your `unet_final`), update dependencies, and replace `main.py`.
