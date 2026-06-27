import os
import uuid
import subprocess

import requests
from flask import (
    Flask, request, jsonify, session, render_template,
    redirect, url_for, abort
)

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, String, create_engine, exc, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
import secrets
import random
import time

u = uuid.uuid1()
seed = u.time - (u.time % 10_000_000 )
random.seed(seed)

app = Flask(__name__)
app.secret_key = str(random.getrandbits(256))

DATABASE_URL = "sqlite:///data/users.db"

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(BigInteger, nullable=False)

    def __init__(self, username, password_hash):
        u = uuid.uuid1()
        self.id = str(u)
        self.username = username
        self.password_hash = password_hash
        self.created_at = u.time

os.makedirs("data", exist_ok=True)
engine = create_engine(DATABASE_URL, echo=False, future=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def json_error(message, code=400):
    return jsonify({"success": False, "error": message}), code


ADMIN_PASSWORD = secrets.token_hex(32)

def create_admin():
    db = SessionLocal()
    try:
        admin = db.query(User).filter_by(username="admint").first()
        if not admin:
            admin = User(
                username="admint",
                password_hash=generate_password_hash(ADMIN_PASSWORD),
            )
            db.add(admin)
            db.commit()

    finally:
        db.close()

time.sleep(secrets.choice(range(1, 10)))

create_admin()

def require_login():
    validate_session()

def require_admin():
    validate_session()
    if session.get("username", "") != "admint":
        abort(403, "for admins only")

def validate_session():
    if not session.get("is_logged_in"):
        abort(401, "not logged in")

    user_id = session.get("user_id")
    username = session.get("username")

    if not user_id or not username:
        session.clear()
        abort(401, "invalid session")

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).one_or_none()
        if user is None or user.username != username:
            session.clear()
            abort(401, "session mismatch (username/id)")
    finally:
        db.close()


@app.route("/")
def index():
    if session.get("is_logged_in"):
        return redirect(url_for("profile", user_id=session["user_id"]))
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return json_error("username and password are required")
    if len(username) < 3:
        return json_error("username must be at least 3 characters")
    if len(password) < 6:
        return json_error("password must be at least 6 characters")

    db = SessionLocal()
    try:
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
        )
        db.add(user)
        db.commit()

        session["user_id"] = user.id
        session["username"] = user.username
        session["is_logged_in"] = True

        return jsonify({
            "success": True,
            "message": "Registered successfully",
            "redirect": f"/profile/{user.id}"
        })
    except exc.IntegrityError:
        db.rollback()
        return json_error("username already taken", 409)
    finally:
        db.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return json_error("username and password are required")

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).one_or_none()
        if user is None or not check_password_hash(user.password_hash, password):
            return json_error("invalid username or password", 401)

        session["user_id"] = user.id
        session["username"] = user.username
        session["is_logged_in"] = True

        return jsonify({
            "success": True,
            "message": f"Welcome {user.username}!",
            "redirect": f"/profile/{user.id}"
        })
    finally:
        db.close()


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out"})


@app.route("/profile/<user_id>")
def profile(user_id):
    require_login()
    current_id = session.get("user_id")
    current_username = session.get("username", "")

    if current_id != user_id and current_username != "admint":
        return json_error("forbidden: you can only view your own profile", 403)

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).one_or_none()
        if not user:
            return json_error("user not found", 404)
        return render_template(
            "profile.html",
            username=user.username,
        )
    finally:
        db.close()


REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


@app.route("/admin/create_report", methods=["GET", "POST"])
def admin_create_report():
    require_admin()

    if request.method == "GET":
        return render_template("report.html", user_id=session["user_id"])

    if request.is_json:
        data = request.get_json(force=True)
        report_name = (data.get("report_name") or "").strip()
    else:
        report_name = (request.form.get("report_name") or "").strip()

    if not report_name:
        return jsonify({"success": False, "error": "report_name required"}), 400

    path = os.path.join(REPORTS_DIR, f"{report_name}.txt")
    generate = f"echo 'Report: {report_name} - generated by admin' > {path}"

    try:
        subprocess.run(generate, shell=True, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": "command failed",
                        "details": e.stderr.decode(errors='ignore')}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "command timed out"}), 500

    return jsonify({"success": True, "report_file": path})

@app.route("/users")
def users():
    db = SessionLocal()
    try:
        all_users = db.query(User).all()
        users_data = [{"username": u.username, "created_at": u.created_at} for u in all_users]
    finally:
        db.close()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "users": users_data})

    return render_template("users.html")


@app.route("/random_cat")
def random_cat():
    require_login()

    try:
        r = requests.get("https://api.thecatapi.com/v1/images/search", timeout=8)
        if r.status_code != 200:
            raise Exception("Bad status code")

        data = r.json()
        if not isinstance(data, list) or not data or "url" not in data[0]:
            raise Exception("Invalid JSON")

        cat_url = data[0]["url"]
        return jsonify({"success": True, "cat_url": cat_url})

    except Exception as e:
        fallback = "https://cataas.com/cat"
        return jsonify({"success": True, "cat_url": fallback})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
