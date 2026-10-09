import os, sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")
DB = os.path.join(os.path.dirname(__file__), "college_events.db")
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db

def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT NOT NULL,
            event_date TEXT NOT NULL, event_time TEXT NOT NULL, venue TEXT NOT NULL,
            description TEXT NOT NULL, eligibility TEXT NOT NULL, deadline TEXT NOT NULL DEFAULT '')""")
        db.execute("""CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL,
            student_name TEXT NOT NULL, email TEXT NOT NULL, department TEXT NOT NULL,
            year TEXT NOT NULL, registered_at TEXT NOT NULL,
            UNIQUE(event_id,email), FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE)""")
        if db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
            demo = [
              ("CodeSprint Challenge","Technical","2026-11-12","10:00 AM","Computer Lab 2","Beginner-friendly coding contest covering Python and problem solving.","BCA and interested students","2026-11-10"),
              ("Campus Cultural Fest","Cultural","2026-11-18","09:30 AM","Main Auditorium","Music, dance, short-film, and creative performances.","All students","2026-11-15"),
              ("AI and Future Skills Workshop","Workshop","2026-11-22","11:00 AM","Seminar Hall","Introduction to AI tools, responsible AI, and student project ideas.","All departments","2026-11-20")]
            db.executemany("INSERT INTO events(title,category,event_date,event_time,venue,description,eligibility,deadline) VALUES(?,?,?,?,?,?,?,?)", demo)

def admin_only(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            flash("Please sign in as administrator.", "warning")
            return redirect(url_for("login"))
        return fn(*a, **kw)
    return wrapper

def events():
    with connect() as db:
        return db.execute("SELECT * FROM events ORDER BY event_date").fetchall()

def answer(q):
    q = (q or "").strip().lower()
    es = events()
    if not q: return "Please type a question about college events."
    if any(x in q for x in ["hello","hi","hey","vanakkam"]):
        return "Hello! 👋 I'm EventMate. Ask me about upcoming events, dates, venues, eligibility, or registration."
    if any(x in q for x in ["register","registration","sign up","participate","join"]):
        return "Open the Events page and select Register on an event. Fill in your name, email, department, and year. Contact the organizer if you need help."
    if "certificate" in q:
        return "Certificate availability depends on the event organizer. Please check the event details or contact your coordinator."
    if any(x in q for x in ["upcoming","show events","event list","what events","events happening"]):
        if not es: return "No events are listed yet. Please check again later."
        return "Events currently listed:\\n" + "\\n".join(f"• {e['title']} — {e['event_date']}, {e['event_time']} at {e['venue']}" for e in es[:8]) + "\\nOpen the Events page for details."
    # Find an event by matching its title/category/venue/description.
    words = [w.strip("?!.,") for w in q.split() if len(w.strip("?!.,") ) > 2]
    for e in es:
        fields = " ".join(str(e[k]) for k in ["title","category","venue","description","eligibility"]).lower()
        if any(w in fields for w in words):
            return f"{e['title']} ({e['category']})\\nDate: {e['event_date']} at {e['event_time']}\\nVenue: {e['venue']}\\nEligibility: {e['eligibility']}\\nRegistration deadline: {e['deadline'] or 'Ask the organizer'}\\nDetails: {e['description']}"
    if any(x in q for x in ["date","when","time","schedule","venue","where","location"]):
        return "Try asking “Show upcoming events” or type an event name. I can answer from events added by the administrator."
    return "I can help with event schedules, workshops, venues, eligibility, registration, and certificates. Try “Show upcoming events” or ask about an event by name."

@app.route("/")
def home():
    return render_template("index.html", events=events())

@app.route("/events")
def event_list():
    return render_template("events.html", events=events())

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or request.form
    result = answer(data.get("message", ""))
    if request.is_json: return jsonify({"answer": result})
    return redirect(url_for("home"))

@app.route("/register/<int:event_id>", methods=["GET","POST"])
def register(event_id):
    with connect() as db: event = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not event: abort(404)
    if request.method == "POST":
        vals = [request.form.get(k,"").strip() for k in ["student_name","email","department","year"]]
        name,email,dept,year = vals
        if not all(vals) or "@" not in email or "." not in email.split("@")[-1]:
            flash("Enter all details and a valid email address.", "danger")
        else:
            try:
                with connect() as db:
                    db.execute("INSERT INTO registrations(event_id,student_name,email,department,year,registered_at) VALUES(?,?,?,?,?,?)",
                      (event_id,name,email.lower(),dept,year,datetime.now().isoformat(timespec="minutes")))
                flash("Registration successful! Details saved in this demo.", "success")
                return redirect(url_for("event_list"))
            except sqlite3.IntegrityError:
                flash("This email is already registered for this event.", "warning")
    return render_template("register.html", event=event)

@app.route("/admin/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASS:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.", "danger")
    return render_template("login.html")

@app.route("/admin")
@admin_only
def dashboard():
    with connect() as db:
        es = db.execute("""SELECT e.*, COUNT(r.id) AS total FROM events e
          LEFT JOIN registrations r ON e.id=r.event_id GROUP BY e.id ORDER BY e.event_date""").fetchall()
        total = db.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    return render_template("admin.html", events=es, total=total)

@app.route("/admin/add", methods=["GET","POST"])
@admin_only
def add_event():
    if request.method == "POST":
        keys = ["title","category","event_date","event_time","venue","description","eligibility","deadline"]
        v = [request.form.get(k,"").strip() for k in keys]
        if not all(v[:7]):
            flash("Complete all required fields.", "danger")
        else:
            with connect() as db:
                db.execute("INSERT INTO events(title,category,event_date,event_time,venue,description,eligibility,deadline) VALUES(?,?,?,?,?,?,?,?)",v)
            flash("Event added.", "success")
            return redirect(url_for("dashboard"))
    return render_template("add_event.html")

@app.route("/admin/delete/<int:event_id>", methods=["POST"])
@admin_only
def delete_event(event_id):
    with connect() as db: db.execute("DELETE FROM events WHERE id=?", (event_id,))
    flash("Event and its registrations deleted.", "info")
    return redirect(url_for("dashboard"))

@app.route("/admin/registrations")
@admin_only
def registration_list():
    with connect() as db:
        rows = db.execute("""SELECT r.*,e.title FROM registrations r JOIN events e ON e.id=r.event_id ORDER BY r.id DESC""").fetchall()
    return render_template("registrations.html", rows=rows)

@app.route("/admin/logout")
def logout():
    session.pop("admin",None)
    return redirect(url_for("home"))

@app.errorhandler(404)
def missing(_): return render_template("404.html"), 404

init_db()
if __name__ == "__main__":
    app.run(debug=True)
