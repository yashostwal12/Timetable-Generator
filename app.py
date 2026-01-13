from flask import Flask, render_template, request, jsonify
import requests
import tempfile
import os
import json

from syllabus_og import subjects_extract
from website3 import faculty_details
from tt import (
    timegen,
    assign_all_faculty,
    pretty_print_tables,
    convert_hours_to_periods
)

app = Flask(__name__)

# -------------------------
# GLOBAL STORAGE (NO SESSION)
# -------------------------
GENERATED_TIMETABLES = None
META = None

# -------------------------
# GEMINI CONFIG
# -------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# -------------------------
# PAGES
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/help")
def help():
    return render_template("learn_more.html")

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/entry")
def entry():
    return render_template("manual-entry.html", subjects=[], faculty=[])

@app.route("/chatbot")
def chatbot_page():
    return render_template("chatbot.html")

# -------------------------
# API: FACULTY
# -------------------------
@app.route("/api/faculty", methods=["POST"])
def api_faculty():
    data = request.json
    url = data.get("url") if data else None

    if not url:
        return jsonify([])

    faculty = faculty_details(url)
    return jsonify(faculty)

# -------------------------
# API: SYLLABUS UPLOAD
# -------------------------
@app.route("/api/syllabus-upload", methods=["POST"])
def syllabus_upload():
    if "pdf" not in request.files:
        return jsonify([])

    pdf_file = request.files["pdf"]
    if pdf_file.filename == "":
        return jsonify([])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        pdf_file.save(temp.name)
        pdf_path = temp.name

    try:
        subjects = subjects_extract(pdf_path)
    finally:
        os.remove(pdf_path)

    return jsonify(subjects)

# -------------------------
# API: PROCESS DATA
# -------------------------
@app.route("/api/process-data", methods=["POST"])
def process_data():
    global GENERATED_TIMETABLES, META

    data = request.json or {}
    config = data.get("timetableConfig", {})
    subjects = data.get("subjects", [])

    if not config or not subjects:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    try:
        no_of_div = int(config["noOfDiv"])
        working_days = int(config["workingDays"])
        no_of_period = int(config["periodsPerDay"])
        lab_count = int(config["labCount"])
        practical_batches = int(config["practicalBatches"])
        lecture_duration = int(config["lectureDuration"])
        practical_duration = int(config["practicalDuration"])
    except Exception:
        return jsonify({"status": "error", "message": "Invalid config"}), 400

    tables = timegen(no_of_div, working_days, no_of_period)

    convert_hours_to_periods(
        subjects,
        lecture_duration=lecture_duration,
        practical_duration=practical_duration
    )

    assign_all_faculty(
        tables,
        working_days,
        no_of_period,
        subjects,
        lab_count,
        practical_batches
    )

    pretty_print_tables(tables)

    GENERATED_TIMETABLES = tables
    META = {
        "divisions": no_of_div,
        "working_days": working_days,
        "periods_per_day": no_of_period
    }

    return jsonify({"status": "ok", "redirect": "/timetables"})

# -------------------------
# PAGE: SHOW TIMETABLE
# -------------------------
@app.route("/timetables")
def show_timetables():
    if GENERATED_TIMETABLES is None:
        return "No timetable generated yet.", 400

    return render_template(
        "tt.html",
        tables=GENERATED_TIMETABLES,
        meta=META
    )

# -------------------------
# GEMINI HELPER (NOT A ROUTE)
# -------------------------
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def ask_gemini(question):
    global GENERATED_TIMETABLES, META

    if not GEMINI_API_KEY:
        return "Gemini API key is missing."

    if GENERATED_TIMETABLES is None:
        return "No timetable has been generated yet."

    prompt = f"""
You are a timetable assistant.
Answer ONLY using the timetable below.
If the answer is not present, say:
"I don't have that information in the timetable."

TIMETABLE (JSON):
{json.dumps(GENERATED_TIMETABLES, indent=2)}

METADATA:
{json.dumps(META, indent=2)}

USER QUESTION:
{question}
"""

    url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
)



    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
    except Exception as e:
        print("REQUEST ERROR:", e)
        return "Failed to contact Gemini."

    # DEBUG PRINT (keep this for now)
    print("RAW GEMINI RESPONSE:")
    print(json.dumps(data, indent=2))

    # HANDLE ERRORS SAFELY
    if "candidates" not in data:
        return "Gemini API error. Check server logs."

    if not data["candidates"]:
        return "Gemini returned no response."

    return data["candidates"][0]["content"]["parts"][0]["text"]


# -------------------------
# CHAT API (CALLED BY HTML)
# -------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("message")

    if not question:
        return jsonify({"reply": "Empty question."})

    reply = ask_gemini(question)
    return jsonify({"reply": reply})

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
