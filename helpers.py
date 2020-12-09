import secrets
from functools import wraps

from flask import redirect, request, session
from flask_mail import Message

from datetime import datetime

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login?next=" + request.path)
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorate routes to require admin login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login?next=" + request.path)
        if not session.get("admin"):
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


def contest_retrieve(session, request, db, contestid):
    solved_info = db.execute("SELECT * FROM contest_users WHERE contest_id=:cid AND user_id=:uid",
        cid=contestid, uid=session["user_id"])

    end = db.execute("SELECT end FROM contests WHERE id=:id", id=contestid)
    end = datetime.strptime(end[0]["end"], "%Y-%m-%d %H:%M:%S")

    if len(solved_info) == 0 and datetime.utcnow() < end:
        db.execute("INSERT INTO contest_users (contest_id, user_id) VALUES(:cid, :uid)",
            cid=contestid, uid=session["user_id"])

    solved_info = db.execute("SELECT problem_id FROM contest_solved WHERE contest_id=:cid AND user_id=:uid",
                                cid=contestid, uid=session["user_id"])

    solved_data = set()
    for row in solved_info:
        solved_data.add(row["problem_id"])

    data = []

    info = db.execute("SELECT * FROM contest_problems WHERE contest_id=:cid AND draft=0 ORDER BY category ASC, problem_id ASC",
        cid=contestid)
    for row in info:
        keys = {
            "problem_id": row["problem_id"],
            "name": row["name"],
            "category": row["category"],
            "solved": 1 if row["problem_id"] in solved_data else 0,
            "point_value": row["point_value"]
        }
        data.insert(len(data), keys)
    return data


def generate_password():
    password = secrets.token_urlsafe(16)
    return password


def send_email(subject, sender, recipients, text, mail):
    message = Message(subject, sender=sender, recipients=recipients, body=text)
    mail.send(message)

def read_file(filename):
    file = open(filename, 'r')
    contents = file.read()
    file.close()
    return contents
