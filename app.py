import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, hashlib, random

app = Flask(__name__)
app.secret_key = "quizapp_secret_2024"
DB = "quiz.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            question TEXT NOT NULL,
            option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT,
            correct TEXT NOT NULL,
            difficulty TEXT DEFAULT 'Medium',
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        );
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_id INTEGER,
            score INTEGER,
            total INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        );
    """)
    pw = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?,?,1)", ("admin", pw))
    for s in ["Python", "Java", "General Knowledge", "Mathematics", "Web Development"]:
        c.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (s,))
    conn.commit()

    subj = {row["name"]: row["id"] for row in c.execute("SELECT * FROM subjects")}

    samples = [
        # ── PYTHON ──
        (subj["Python"], "What is the output of print(type([]))?", "<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>", "A", "Easy"),
        (subj["Python"], "Which keyword defines a function in Python?", "func", "def", "define", "function", "B", "Easy"),
        (subj["Python"], "What does len([1,2,3]) return?", "2", "4", "3", "0", "C", "Easy"),
        (subj["Python"], "Which of these is a mutable data type in Python?", "tuple", "string", "list", "int", "C", "Easy"),
        (subj["Python"], "What is the correct file extension for Python files?", ".pt", ".pyt", ".py", ".python", "C", "Easy"),
        (subj["Python"], "What does the 'self' keyword represent in a class?", "The class itself", "The instance of the class", "A static method", "A global variable", "B", "Medium"),
        (subj["Python"], "What is a lambda function in Python?", "A named function", "An anonymous function", "A recursive function", "A built-in function", "B", "Medium"),
        (subj["Python"], "What is the output of: list(range(2, 10, 2))?", "[2,4,6,8]", "[2,4,6,8,10]", "[0,2,4,6,8]", "[2,6,10]", "A", "Medium"),
        (subj["Python"], "Which method removes and returns the last element of a list?", "remove()", "delete()", "pop()", "discard()", "C", "Medium"),
        (subj["Python"], "What does *args allow in a function?", "Keyword arguments", "Variable positional arguments", "Default arguments", "Type hints", "B", "Medium"),
        (subj["Python"], "What is the output of: {1,2,3} & {2,3,4}?", "{1,2,3,4}", "{2,3}", "{1,4}", "{}", "B", "Hard"),
        (subj["Python"], "What is a Python decorator?", "A design pattern", "A function that modifies another function", "A class method", "A module", "B", "Hard"),
        (subj["Python"], "What does __slots__ do in a Python class?", "Adds methods", "Restricts attribute creation to save memory", "Defines properties", "Enables inheritance", "B", "Hard"),
        (subj["Python"], "What is the GIL in Python?", "Global Import Lock", "Global Interpreter Lock", "General Input Library", "Global Instance List", "B", "Hard"),
        (subj["Python"], "What does itertools.chain() do?", "Sorts iterables", "Combines multiple iterables into one", "Filters items", "Zips iterables", "B", "Hard"),

        # ── JAVA ──
        (subj["Java"], "Entry point of a Java program?", "start()", "run()", "main()", "init()", "C", "Easy"),
        (subj["Java"], "What does JVM stand for?", "Java Visual Machine", "Java Virtual Machine", "Java Valid Machine", "Java Vector Machine", "B", "Easy"),
        (subj["Java"], "Which of these is NOT a Java primitive type?", "int", "float", "String", "char", "C", "Easy"),
        (subj["Java"], "What keyword creates an object in Java?", "create", "new", "make", "build", "B", "Easy"),
        (subj["Java"], "Which access modifier makes a member accessible everywhere?", "private", "protected", "default", "public", "D", "Easy"),
        (subj["Java"], "What is method overloading?", "Same name, different return type", "Same name, different parameters", "Extending a class method", "Overriding a parent method", "B", "Medium"),
        (subj["Java"], "What is the difference between == and .equals() in Java?", "No difference", "== compares references, .equals() compares content", "== compares content, .equals() compares references", "Only for strings", "B", "Medium"),
        (subj["Java"], "Which collection allows duplicate elements?", "Set", "Map", "List", "HashSet", "C", "Medium"),
        (subj["Java"], "What does the 'final' keyword do to a variable?", "Makes it static", "Makes it constant", "Makes it private", "Makes it global", "B", "Medium"),
        (subj["Java"], "What is the purpose of the 'super' keyword?", "To call child class method", "To refer to parent class", "To create static methods", "To define interfaces", "B", "Medium"),
        (subj["Java"], "What is a checked exception in Java?", "Exception at compile time", "Exception that must be handled or declared", "Runtime exception", "Error class", "B", "Hard"),
        (subj["Java"], "What is the purpose of the volatile keyword?", "Makes variable final", "Ensures visibility across threads", "Makes method synchronized", "Marks deprecated code", "B", "Hard"),
        (subj["Java"], "What does the transient keyword do?", "Prevents serialization of a field", "Makes field thread-safe", "Creates a temporary variable", "Marks a deprecated field", "A", "Hard"),
        (subj["Java"], "What is the diamond problem in Java?", "Multiple inheritance conflict", "Memory leak in generics", "NullPointerException", "Stack overflow", "A", "Hard"),
        (subj["Java"], "What is the purpose of Java's CompletableFuture?", "Synchronous task execution", "Asynchronous programming", "Thread locking", "Exception handling", "B", "Hard"),

        # ── GENERAL KNOWLEDGE ──
        (subj["General Knowledge"], "Capital of India?", "Mumbai", "Kolkata", "Chennai", "New Delhi", "D", "Easy"),
        (subj["General Knowledge"], "How many continents are there?", "5", "6", "7", "8", "C", "Easy"),
        (subj["General Knowledge"], "Who wrote Romeo and Juliet?", "Dickens", "Shakespeare", "Tolkien", "Twain", "B", "Easy"),
        (subj["General Knowledge"], "What is the chemical symbol for Gold?", "Go", "Gd", "Au", "Ag", "C", "Easy"),
        (subj["General Knowledge"], "Which planet is closest to the Sun?", "Venus", "Earth", "Mars", "Mercury", "D", "Easy"),
        (subj["General Knowledge"], "What is the largest ocean on Earth?", "Atlantic", "Indian", "Arctic", "Pacific", "D", "Medium"),
        (subj["General Knowledge"], "Who painted the Mona Lisa?", "Michelangelo", "Raphael", "Leonardo da Vinci", "Donatello", "C", "Medium"),
        (subj["General Knowledge"], "What is the speed of light in vacuum?", "3x10^6 m/s", "3x10^8 m/s", "3x10^10 m/s", "3x10^4 m/s", "B", "Medium"),
        (subj["General Knowledge"], "Which country has the most natural lakes?", "USA", "Russia", "Brazil", "Canada", "D", "Medium"),
        (subj["General Knowledge"], "What year did World War II end?", "1943", "1944", "1945", "1946", "C", "Medium"),
        (subj["General Knowledge"], "What is the Schrödinger's cat thought experiment about?", "Quantum superposition", "Relativity", "String theory", "Dark matter", "A", "Hard"),
        (subj["General Knowledge"], "Which economist proposed the 'invisible hand' concept?", "Keynes", "Marx", "Adam Smith", "Friedman", "C", "Hard"),
        (subj["General Knowledge"], "What is the Coriolis effect?", "Ocean tides", "Deflection of moving objects due to Earth's rotation", "Solar wind", "Magnetic pole shift", "B", "Hard"),
        (subj["General Knowledge"], "What does the Hubble constant measure?", "Speed of light", "Rate of universe expansion", "Galaxy size", "Black hole mass", "B", "Hard"),
        (subj["General Knowledge"], "Which ancient wonder still exists today?", "Colossus of Rhodes", "Great Pyramid of Giza", "Hanging Gardens", "Lighthouse of Alexandria", "B", "Hard"),

        # ── MATHEMATICS ──
        (subj["Mathematics"], "What is 12 x 12?", "124", "144", "132", "148", "B", "Easy"),
        (subj["Mathematics"], "Square root of 81?", "7", "8", "9", "10", "C", "Easy"),
        (subj["Mathematics"], "What is 15% of 200?", "20", "25", "30", "35", "C", "Easy"),
        (subj["Mathematics"], "What is the value of pi (approx)?", "3.14", "3.41", "3.12", "3.16", "A", "Easy"),
        (subj["Mathematics"], "What is 2^10?", "512", "1024", "2048", "256", "B", "Easy"),
        (subj["Mathematics"], "What is the sum of angles in a triangle?", "90°", "180°", "270°", "360°", "B", "Medium"),
        (subj["Mathematics"], "What is the derivative of x²?", "x", "2x", "2x²", "x/2", "B", "Medium"),
        (subj["Mathematics"], "Solve: 3x + 7 = 22, x = ?", "3", "4", "5", "6", "C", "Medium"),
        (subj["Mathematics"], "What is log₁₀(1000)?", "2", "3", "4", "10", "B", "Medium"),
        (subj["Mathematics"], "How many diagonals does a hexagon have?", "6", "8", "9", "12", "C", "Medium"),
        (subj["Mathematics"], "What is the integral of 1/x dx?", "x²/2", "ln|x|", "e^x", "1/x²", "B", "Hard"),
        (subj["Mathematics"], "What is Euler's identity? e^(iπ) + ? = 0", "1", "-1", "i", "0", "A", "Hard"),
        (subj["Mathematics"], "What is the determinant of [[1,2],[3,4]]?", "2", "-2", "10", "-10", "B", "Hard"),
        (subj["Mathematics"], "How many prime numbers are between 1 and 50?", "13", "14", "15", "16", "C", "Hard"),
        (subj["Mathematics"], "What is the Fibonacci sequence rule?", "Each number is doubled", "Each number is sum of two before", "Each number is squared", "Each number is prime", "B", "Hard"),

        # ── WEB DEVELOPMENT ──
        (subj["Web Development"], "What does HTML stand for?", "Hyper Text Markup Language", "High Text Machine Language", "Hyper Transfer Markup Language", "None", "A", "Easy"),
        (subj["Web Development"], "Which tag creates a hyperlink?", "<link>", "<a>", "<href>", "<url>", "B", "Easy"),
        (subj["Web Development"], "What does CSS stand for?", "Creative Style Sheets", "Cascading Style Sheets", "Computer Style Sheets", "Colorful Style Sheets", "B", "Easy"),
        (subj["Web Development"], "Which property changes text color in CSS?", "font-color", "text-color", "color", "foreground", "C", "Easy"),
        (subj["Web Development"], "What does DOM stand for?", "Document Object Model", "Data Object Management", "Document Oriented Model", "Dynamic Object Method", "A", "Easy"),
        (subj["Web Development"], "What is the purpose of the 'async' attribute in a script tag?", "Defers script execution", "Loads script asynchronously", "Makes script synchronous", "Prevents script loading", "B", "Medium"),
        (subj["Web Development"], "What HTTP method is used to update a resource?", "GET", "POST", "PUT", "DELETE", "C", "Medium"),
        (subj["Web Development"], "What does JSON stand for?", "JavaScript Object Notation", "Java Standard Object Notation", "JavaScript Oriented Network", "Joint Script Object Name", "A", "Medium"),
        (subj["Web Development"], "What is the CSS Box Model order from inside out?", "margin > border > padding > content", "content > padding > border > margin", "padding > content > margin > border", "border > content > padding > margin", "B", "Medium"),
        (subj["Web Development"], "Which CSS property controls the stacking order of elements?", "stack-order", "layer", "z-index", "order", "C", "Medium"),
        (subj["Web Development"], "What is CORS?", "A CSS framework", "Cross-Origin Resource Sharing", "A JavaScript library", "Client-side rendering", "B", "Hard"),
        (subj["Web Development"], "What is the difference between localStorage and sessionStorage?", "No difference", "localStorage persists after browser close, sessionStorage doesn't", "sessionStorage is larger", "localStorage is encrypted", "B", "Hard"),
        (subj["Web Development"], "What is a Service Worker?", "A backend API server", "A script running in background to enable offline features", "A database worker", "A CSS preprocessor", "B", "Hard"),
        (subj["Web Development"], "What is the purpose of the 'use strict' directive in JavaScript?", "Enables ES6 features", "Enforces stricter parsing and error handling", "Disables debugging", "Enables async functions", "B", "Hard"),
        (subj["Web Development"], "What is the Virtual DOM?", "A real browser DOM", "A lightweight copy of DOM used for efficient updates", "A server-side DOM", "A CSS preprocessor", "B", "Hard"),
    ]

    for q in samples:
        c.execute("""INSERT OR IGNORE INTO questions
            (subject_id,question,option_a,option_b,option_c,option_d,correct,difficulty)
            VALUES (?,?,?,?,?,?,?,?)""", q)
    conn.commit()
    conn.close()

# ── Auth ──────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    subjects = conn.execute("SELECT * FROM subjects").fetchall()
    counts = {row["subject_id"]: row["cnt"] for row in
              conn.execute("SELECT subject_id, COUNT(*) as cnt FROM questions GROUP BY subject_id")}
    conn.close()
    return render_template("index.html", subjects=subjects, username=session["username"], counts=counts)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
            conn.commit()
            conn.close()
            flash("Registered! Please login.", "success")
            return redirect(url_for("login"))
        except:
            flash("Username already exists.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = user["is_admin"]
            return redirect(url_for("index"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Quiz ──────────────────────────────────────────────
@app.route("/quiz/<int:subject_id>")
def quiz(subject_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    subject = conn.execute("SELECT * FROM subjects WHERE id=?", (subject_id,)).fetchone()
    all_questions = conn.execute("SELECT * FROM questions WHERE subject_id=?", (subject_id,)).fetchall()
    conn.close()
    if not all_questions:
        flash("No questions available for this subject yet.", "warning")
        return redirect(url_for("index"))
    # Shuffle and pick 10 random questions each time
    questions = random.sample(list(all_questions), min(10, len(all_questions)))
    return render_template("quiz.html", subject=subject, questions=questions)

@app.route("/submit/<int:subject_id>", methods=["POST"])
def submit(subject_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    # Get only the questions that were in this quiz session
    qids = [int(k[1:]) for k in request.form.keys() if k.startswith("q")]
    questions = conn.execute(
        f"SELECT * FROM questions WHERE id IN ({','.join('?'*len(qids))})", qids
    ).fetchall() if qids else []
    subject = conn.execute("SELECT * FROM subjects WHERE id=?", (subject_id,)).fetchone()
    score = 0
    results = []
    for q in questions:
        ans = request.form.get(f"q{q['id']}", "")
        correct = ans == q["correct"]
        if correct:
            score += 1
        results.append({
            "question": q["question"],
            "your_answer": ans,
            "correct": q["correct"],
            "is_correct": correct,
            "difficulty": q["difficulty"],
            "options": {"A": q["option_a"], "B": q["option_b"], "C": q["option_c"], "D": q["option_d"]}
        })
    conn.execute("INSERT INTO scores (user_id, subject_id, score, total) VALUES (?,?,?,?)",
                 (session["user_id"], subject_id, score, len(questions)))
    conn.commit()
    conn.close()
    return render_template("result.html", score=score, total=len(questions),
                           results=results, subject=subject)

# ── Leaderboard ───────────────────────────────────────
@app.route("/leaderboard")
def leaderboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    scores = conn.execute("""
        SELECT u.username, sub.name as subject, s.score, s.total, s.timestamp
        FROM scores s
        JOIN users u ON s.user_id = u.id
        JOIN subjects sub ON s.subject_id = sub.id
        ORDER BY s.score DESC LIMIT 20
    """).fetchall()
    conn.close()
    return render_template("leaderboard.html", scores=scores)

# ── Admin ─────────────────────────────────────────────
@app.route("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("index"))
    conn = get_db()
    questions = conn.execute("""
        SELECT q.*, s.name as subject_name FROM questions q
        JOIN subjects s ON q.subject_id = s.id ORDER BY s.name, q.difficulty
    """).fetchall()
    subjects = conn.execute("SELECT * FROM subjects").fetchall()
    conn.close()
    return render_template("admin/dashboard.html", questions=questions, subjects=subjects)

@app.route("/admin/add", methods=["GET","POST"])
def add_question():
    if not session.get("is_admin"):
        return redirect(url_for("index"))
    conn = get_db()
    subjects = conn.execute("SELECT * FROM subjects").fetchall()
    if request.method == "POST":
        conn.execute("""INSERT INTO questions
            (subject_id,question,option_a,option_b,option_c,option_d,correct,difficulty)
            VALUES (?,?,?,?,?,?,?,?)""",
            (request.form["subject_id"], request.form["question"],
             request.form["option_a"], request.form["option_b"],
             request.form["option_c"], request.form["option_d"],
             request.form["correct"], request.form["difficulty"]))
        conn.commit()
        conn.close()
        flash("Question added!", "success")
        return redirect(url_for("admin_dashboard"))
    conn.close()
    return render_template("admin/add_question.html", subjects=subjects)

@app.route("/admin/delete/<int:qid>")
def delete_question(qid):
    if not session.get("is_admin"):
        return redirect(url_for("index"))
    conn = get_db()
    conn.execute("DELETE FROM questions WHERE id=?", (qid,))
    conn.commit()
    conn.close()
    flash("Question deleted.", "info")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)