"""Flask application for the Study Group Finder Phase 1 prototype."""

import os
from datetime import date, datetime, time
from functools import wraps
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from backend.db import get_db_connection
except ModuleNotFoundError:
    from db import get_db_connection

BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
load_dotenv(BACKEND_DIR / ".env")

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def json_body():
    return request.get_json(silent=True) or {}


def login_required(route):
    @wraps(route)
    def wrapped(*args, **kwargs):
        if "student_id" not in session:
            return jsonify({"error": "You must be logged in."}), 401
        return route(*args, **kwargs)
    return wrapped


def close_db(connection, cursor=None):
    if cursor is not None:
        cursor.close()
    if connection is not None and connection.is_connected():
        connection.close()


def json_safe(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


def serialize_rows(rows):
    return [{key: json_safe(value) for key, value in row.items()} for row in rows]


def fetch_meeting_times(cursor, group_ids):
    if not group_ids:
        return {}
    placeholders = ",".join(["%s"] * len(group_ids))
    cursor.execute(
        f"""
        SELECT group_id, day_of_week, start_time, end_time
        FROM group_meeting_times
        WHERE group_id IN ({placeholders})
        ORDER BY FIELD(day_of_week,
            'monday','tuesday','wednesday','thursday',
            'friday','saturday','sunday'), start_time
        """,
        tuple(group_ids),
    )
    result = {group_id: [] for group_id in group_ids}
    for row in serialize_rows(cursor.fetchall()):
        result.setdefault(row["group_id"], []).append(row)
    return result


@app.get("/")
def home():
    return app.send_static_file("login.html")


@app.get("/api/health")
def health():
    connection = None
    try:
        connection = get_db_connection()
        return jsonify({"status": "ok", "database": "connected"})
    except (mysql.connector.Error, RuntimeError) as error:
        return jsonify({"status": "error", "database": str(error)}), 503
    finally:
        close_db(connection)


@app.get("/api/courses")
def list_courses():
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT course_id, course_code, course_name FROM courses ORDER BY course_code")
        return jsonify({"courses": cursor.fetchall()})
    except (mysql.connector.Error, RuntimeError) as error:
        return jsonify({"error": str(error)}), 500
    finally:
        close_db(connection, cursor)


@app.post("/api/auth/signup")
def signup():
    data = json_body()
    required = ("first_name", "last_name", "email", "password", "date_of_birth", "gender")
    missing = [field for field in required if not str(data.get(field, "")).strip()]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    email = str(data["email"]).strip().lower()
    if not email.endswith("@sdsu.edu"):
        return jsonify({"error": "Please use an @sdsu.edu email address."}), 400
    if len(str(data["password"])) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO students
                (student_email, password_hash, first_name, last_name,
                 date_of_birth, gender, major, phone_number)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (email, generate_password_hash(
    str(data["password"]),
    method="pbkdf2:sha256"
),
             str(data["first_name"]).strip(), str(data["last_name"]).strip(),
             data["date_of_birth"], str(data["gender"]).strip(),
             data.get("major") or None, data.get("phone_number") or None),
        )
        connection.commit()
        student_id = cursor.lastrowid
        session["student_id"] = student_id
        session["email"] = email
        return jsonify({"message": "Account created.", "student_id": student_id}), 201
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({"error": "An account with that email already exists."}), 409
    except (mysql.connector.Error, RuntimeError) as error:
        if connection:
            connection.rollback()
        return jsonify({"error": str(error)}), 500
    finally:
        close_db(connection, cursor)


@app.post("/api/auth/login")
def login():
    data = json_body()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT student_id, first_name, last_name, student_email, password_hash FROM students WHERE student_email=%s",
            (email,),
        )
        student = cursor.fetchone()
        if student is None or not check_password_hash(student["password_hash"], password):
            return jsonify({"error": "Invalid email or password."}), 401
        session["student_id"] = student["student_id"]
        session["email"] = student["student_email"]
        student.pop("password_hash")
        return jsonify({"message": "Logged in.", "student": student})
    except (mysql.connector.Error, RuntimeError) as error:
        return jsonify({"error": str(error)}), 500
    finally:
        close_db(connection, cursor)


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out."})


@app.get("/api/auth/me")
@login_required
def current_student():
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT student_id, student_email, first_name, last_name,
                   date_of_birth, gender, major, phone_number, created_at
            FROM students WHERE student_id=%s
            """,
            (session["student_id"],),
        )
        student = cursor.fetchone()
        return jsonify({"student": serialize_rows([student])[0]})
    finally:
        close_db(connection, cursor)


@app.put("/api/profile")
@login_required
def update_profile():
    data = json_body()
    required = ("first_name", "last_name", "email", "date_of_birth", "gender")
    missing = [field for field in required if not str(data.get(field, "")).strip()]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    email = str(data["email"]).strip().lower()
    if not email.endswith("@sdsu.edu"):
        return jsonify({"error": "Please use an @sdsu.edu email address."}), 400
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE students SET student_email=%s, first_name=%s, last_name=%s,
                date_of_birth=%s, gender=%s, major=%s, phone_number=%s
            WHERE student_id=%s
            """,
            (email, data["first_name"].strip(), data["last_name"].strip(),
             data["date_of_birth"], data["gender"], data.get("major") or None,
             data.get("phone_number") or None, session["student_id"]),
        )
        connection.commit()
        session["email"] = email
        return jsonify({"message": "Profile updated."})
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({"error": "That email is already being used."}), 409
    finally:
        close_db(connection, cursor)


@app.get("/api/my-courses")
@login_required
def my_courses():
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.course_id, c.course_code, c.course_name,
                   COUNT(DISTINCT sg.group_id) AS group_count
            FROM enrollments e
            JOIN courses c ON c.course_id=e.course_id
            LEFT JOIN study_groups sg ON sg.course_id=c.course_id
            WHERE e.student_id=%s
            GROUP BY c.course_id, c.course_code, c.course_name
            ORDER BY c.course_code
            """,
            (session["student_id"],),
        )
        return jsonify({"courses": cursor.fetchall()})
    finally:
        close_db(connection, cursor)


@app.post("/api/my-courses")
@login_required
def add_course():
    course_id = json_body().get("course_id")
    if not course_id:
        return jsonify({"error": "course_id is required."}), 400
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s,%s)",
                       (session["student_id"], course_id))
        connection.commit()
        return jsonify({"message": "Course added."}), 201
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({"error": "You already added this course."}), 409
    finally:
        close_db(connection, cursor)


@app.delete("/api/my-courses/<int:course_id>")
@login_required
def remove_course(course_id):
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM enrollments WHERE student_id=%s AND course_id=%s",
                       (session["student_id"], course_id))
        connection.commit()
        return jsonify({"message": "Course removed."})
    finally:
        close_db(connection, cursor)


@app.get("/api/groups")
def list_groups():
    course_id = request.args.get("course_id")
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT g.group_id, g.group_name, g.description, g.course_id,
                   c.course_code, c.course_name, g.creator_id, g.leader_id,
                   g.meeting_format, g.meeting_location, g.maximum_capacity,
                   COUNT(gm.student_id) AS member_count
            FROM study_groups g
            JOIN courses c ON c.course_id=g.course_id
            LEFT JOIN group_members gm ON gm.group_id=g.group_id
        """
        params = []
        if course_id:
            query += " WHERE g.course_id=%s"
            params.append(course_id)
        query += " GROUP BY g.group_id, c.course_id ORDER BY g.group_name"
        cursor.execute(query, tuple(params))
        groups = cursor.fetchall()
        times = fetch_meeting_times(cursor, [g["group_id"] for g in groups])
        for group in groups:
            group["meeting_times"] = times.get(group["group_id"], [])
        return jsonify({"groups": serialize_rows(groups)})
    finally:
        close_db(connection, cursor)


@app.get("/api/groups/<int:group_id>")
def group_details(group_id):
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT g.*, c.course_code, c.course_name, COUNT(gm.student_id) AS member_count
            FROM study_groups g
            JOIN courses c ON c.course_id=g.course_id
            LEFT JOIN group_members gm ON gm.group_id=g.group_id
            WHERE g.group_id=%s GROUP BY g.group_id, c.course_id
            """,
            (group_id,),
        )
        group = cursor.fetchone()
        if not group:
            return jsonify({"error": "Group not found."}), 404
        group["meeting_times"] = fetch_meeting_times(cursor, [group_id]).get(group_id, [])
        cursor.execute(
            """
            SELECT s.student_id, s.first_name, s.last_name, s.major, gm.joined_at
            FROM group_members gm JOIN students s ON s.student_id=gm.student_id
            WHERE gm.group_id=%s ORDER BY gm.joined_at
            """,
            (group_id,),
        )
        group["members"] = serialize_rows(cursor.fetchall())
        current_id = session.get("student_id")
        group["is_member"] = any(m["student_id"] == current_id for m in group["members"])
        group["is_leader"] = current_id == group["leader_id"]
        return jsonify({"group": serialize_rows([group])[0]})
    finally:
        close_db(connection, cursor)


@app.post("/api/groups")
@login_required
def create_group():
    data = json_body()
    required = ("course_id", "group_name", "meeting_format", "maximum_capacity")
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    if data["meeting_format"] not in {"in_person", "online", "hybrid"}:
        return jsonify({"error": "Invalid meeting format."}), 400
    try:
        capacity = int(data["maximum_capacity"])
        if capacity < 2:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Capacity must be at least 2."}), 400
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        connection.start_transaction()
        cursor.execute(
            """
            INSERT INTO study_groups
                (course_id,creator_id,leader_id,group_name,description,
                 meeting_format,meeting_location,maximum_capacity)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (data["course_id"], session["student_id"], session["student_id"],
             str(data["group_name"]).strip(), str(data.get("description", "")).strip(),
             data["meeting_format"], data.get("meeting_location") or None, capacity),
        )
        group_id = cursor.lastrowid
        cursor.execute("INSERT INTO group_members (group_id,student_id) VALUES (%s,%s)",
                       (group_id, session["student_id"]))
        for meeting in data.get("meeting_times", []):
            cursor.execute(
                "INSERT INTO group_meeting_times (group_id,day_of_week,start_time,end_time) VALUES (%s,%s,%s,%s)",
                (group_id, meeting["day_of_week"], meeting["start_time"], meeting["end_time"]),
            )
        connection.commit()
        return jsonify({"message": "Group created.", "group_id": group_id}), 201
    except mysql.connector.IntegrityError as error:
        if connection:
            connection.rollback()
        if error.errno == 1062:
            return jsonify({"error": "You already created a group for this course."}), 409
        return jsonify({"error": str(error)}), 409
    except (mysql.connector.Error, RuntimeError, KeyError) as error:
        if connection:
            connection.rollback()
        return jsonify({"error": str(error)}), 500
    finally:
        close_db(connection, cursor)


@app.post("/api/groups/<int:group_id>/join")
@login_required
def join_group(group_id):
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()
        cursor.execute("SELECT group_id,maximum_capacity FROM study_groups WHERE group_id=%s FOR UPDATE", (group_id,))
        group = cursor.fetchone()
        if not group:
            connection.rollback()
            return jsonify({"error": "Group not found."}), 404
        cursor.execute("SELECT COUNT(*) member_count FROM group_members WHERE group_id=%s", (group_id,))
        if cursor.fetchone()["member_count"] >= group["maximum_capacity"]:
            connection.rollback()
            return jsonify({"error": "This group is already full."}), 409
        cursor.execute("INSERT INTO group_members (group_id,student_id) VALUES (%s,%s)",
                       (group_id, session["student_id"]))
        connection.commit()
        return jsonify({"message": "Joined group."}), 201
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({"error": "You are already a member of this group."}), 409
    finally:
        close_db(connection, cursor)


@app.delete("/api/groups/<int:group_id>/leave")
@login_required
def leave_group(group_id):
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT leader_id FROM study_groups WHERE group_id=%s", (group_id,))
        group = cursor.fetchone()
        if not group:
            return jsonify({"error": "Group not found."}), 404
        if group["leader_id"] == session["student_id"]:
            return jsonify({"error": "The leader must delete the group instead."}), 409
        cursor.execute("DELETE FROM group_members WHERE group_id=%s AND student_id=%s",
                       (group_id, session["student_id"]))
        connection.commit()
        return jsonify({"message": "Left group."})
    finally:
        close_db(connection, cursor)


@app.get("/api/my-groups")
@login_required
def my_groups():
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT g.group_id,g.group_name,g.course_id,c.course_code,c.course_name,
                   g.leader_id,g.meeting_format,g.meeting_location,
                   g.maximum_capacity,COUNT(all_members.student_id) AS member_count
            FROM group_members mine
            JOIN study_groups g ON g.group_id=mine.group_id
            JOIN courses c ON c.course_id=g.course_id
            LEFT JOIN group_members all_members ON all_members.group_id=g.group_id
            WHERE mine.student_id=%s
            GROUP BY g.group_id,c.course_id ORDER BY g.group_name
            """,
            (session["student_id"],),
        )
        groups = cursor.fetchall()
        times = fetch_meeting_times(cursor, [g["group_id"] for g in groups])
        for group in groups:
            group["meeting_times"] = times.get(group["group_id"], [])
        return jsonify({"groups": serialize_rows(groups), "student_id": session["student_id"]})
    finally:
        close_db(connection, cursor)


@app.delete("/api/groups/<int:group_id>/members/<int:student_id>")
@login_required
def remove_member(group_id, student_id):
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT leader_id FROM study_groups WHERE group_id=%s", (group_id,))
        group = cursor.fetchone()
        if not group or group["leader_id"] != session["student_id"]:
            return jsonify({"error": "Only the group leader can remove members."}), 403
        if student_id == session["student_id"]:
            return jsonify({"error": "The leader cannot remove themselves."}), 409
        cursor.execute("DELETE FROM group_members WHERE group_id=%s AND student_id=%s", (group_id, student_id))
        connection.commit()
        return jsonify({"message": "Member removed."})
    finally:
        close_db(connection, cursor)


@app.delete("/api/groups/<int:group_id>")
@login_required
def delete_group(group_id):
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM study_groups WHERE group_id=%s AND leader_id=%s",
                       (group_id, session["student_id"]))
        if cursor.rowcount == 0:
            connection.rollback()
            return jsonify({"error": "Only the group leader can delete this group."}), 403
        connection.commit()
        return jsonify({"message": "Group deleted."})
    finally:
        close_db(connection, cursor)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
