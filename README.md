# ResumeParser (Local Web UI)

This adds a small Flask backend and a single-page web UI that uploads a PDF, calls your existing `process_resume` function, and shows/downloads results.

Requirements
- Python 3.8+
- Install dependencies:

```powershell
cd .\ResumeParser
python -m pip install -r requirements.txt
```

Run the server

```powershell
cd .\ResumeParser
python app.py
```

Open the UI
- Visit http://localhost:5000 in your browser.

Notes
- The server writes result files (`resume_result_<id>.json` and `.csv`) into the `ResumeParser` folder where `app.py` lives.
- This keeps your original parser logic and only adds an HTTP wrapper and a small frontend.
