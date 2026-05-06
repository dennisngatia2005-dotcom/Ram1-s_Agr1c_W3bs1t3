"""routes/members.py"""
from importlib.resources import path
from pathlib import Path
from urllib import response

from urllib import response

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from db import fetchall, fetchone, get_conn, call_proc
import oracledb, bcrypt

members_bp = Blueprint("members", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "member_id" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("members.login"))
        return f(*args, **kwargs)
    return decorated


@members_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        pwd   = request.form.get("password","")
        row   = fetchone("""
            SELECT "memberID","firstName","secondName","pwdHash","isActive"
            FROM   "member_table" WHERE UPPER("email")=UPPER(:e)
        """, {"e": email})
        if row and row["isactive"] == 1:
            stored = row["pwdhash"]
            # If no password set yet, allow login by memberID as first-time PIN
            if stored is None:
                pin = request.form.get("pin","")
                if pin == str(row["memberid"]):
                    session["member_id"]   = row["memberid"]
                    session["member_name"] = f"{row['firstname']} {row['secondname']}"
                    flash("Welcome! Please set a password.", "success")
                    return redirect(url_for("members.dashboard"))
            elif bcrypt.checkpw(pwd.encode(), stored.encode()):
                session["member_id"]   = row["memberid"]
                session["member_name"] = f"{row['firstname']} {row['secondname']}"
                return redirect(url_for("members.dashboard"))
        flash("Invalid credentials or inactive account.", "error")
    return render_template("member_login.html")


@members_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("public.index"))
           
@members_bp.route("/set-password", methods=["POST"])
@login_required
def set_password():
    pwd  = request.form.get("password","")
    if len(pwd) < 6:
        flash("Password must be at least 6 characters.", "error")
        return redirect(url_for("members.dashboard"))
    hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.callproc("setMemberPassword", [session["member_id"], hashed])
            conn.commit()
    flash("Password updated successfully.", "success")
    return redirect(url_for("members.dashboard"))


@members_bp.route("/dashboard")
@login_required
def dashboard():
    mid     = session["member_id"]
    profile = call_proc("getMemberActivityReport", [mid])
    profile = profile[0] if profile else {}
    borrows = fetchall("""
        SELECT r."title",r."type",b."borrowDate",b."borrowID",
               TRUNC(SYSDATE-b."borrowDate") AS days_held
        FROM   "borrow_table" b JOIN "resource_table" r ON b."resourceID"=r."resourceID"
        WHERE  b."memberID"=:mid AND b."returnDate" IS NULL
        ORDER BY b."borrowDate"
    """, {"mid": mid})
    payments = fetchall("""
        SELECT "paymentType","amount","paymentDate"
        FROM   "payment_table" WHERE "memberID"=:mid
        ORDER BY "paymentDate" DESC FETCH FIRST 10 ROWS ONLY
    """, {"mid": mid})
    return render_template("member_dashboard.html",
                           profile=profile, borrows=borrows, payments=payments)


@members_bp.route("/borrow/<int:resource_id>", methods=["POST"])
@login_required
def borrow(resource_id):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.callproc("borrowResource", [session["member_id"], resource_id])
                conn.commit()
        flash("Resource borrowed successfully!", "success")
    except oracledb.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("public.resources"))


@members_bp.route("/return/<int:borrow_id>", methods=["POST"])
@login_required
def return_resource(borrow_id):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.callproc("returnResource", [borrow_id])
                conn.commit()
        flash("Resource returned. Thank you!", "success")
    except oracledb.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("members.dashboard"))

@members_bp.route("/pay", methods=["POST"])
@login_required
def make_payment():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.callproc("makePayment", [
                    session["member_id"],
                    float(request.form["amount"]),
                    request.form["payment_type"]
                ])
                conn.commit()
        flash("Payment recorded.", "success")
    except oracledb.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("members.dashboard"))


@members_bp.route("/register", methods=["POST"])
def register():
    data = request.form
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.callproc("addMember", [
                    data["firstName"], data["secondName"],
                    data["email"].strip().lower(), data["phoneNo"],
                    int(data["branchID"]), int(data["categoryID"])
                ])
                conn.commit()
                row = fetchone('SELECT "memberID" FROM "member_table" WHERE "email"=:e',
                               {"e": data["email"].strip().lower()})
                mid = row["memberid"] if row else "?"
        flash(f"Welcome! Your Member ID is {mid}. Use it as your first-time PIN to log in.", "success")
        return redirect(url_for("members.login"))
    except oracledb.DatabaseError as e:
        flash(str(e), "error")
        return redirect(url_for("public.join"))