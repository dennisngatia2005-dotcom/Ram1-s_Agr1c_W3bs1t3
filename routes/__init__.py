"""routes/admin.py"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from db import fetchall, fetchone, get_conn, call_proc, execute
from config import Config
import oracledb

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == Config.ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin.dashboard"))
        flash("Wrong password.", "error")
    return render_template("admin_login.html")


@admin_bp.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("public.index"))


@admin_bp.route("/")
@admin_required
def dashboard():
    stats         = call_proc("getDashboardStats", [])
    stats         = stats[0] if stats else {}
    branch_report = call_proc("getBranchReport", [])
    top_borrowers = call_proc("getTopBorrowers", [10])
    overdue       = call_proc("getOverdueBorrows", [14])
    announcements = fetchall('SELECT * FROM "announcementSummary" ORDER BY "postedDate" DESC FETCH FIRST 5 ROWS ONLY')
    return render_template("admin_dashboard.html",
                           stats=stats, branch_report=branch_report,
                           top_borrowers=top_borrowers, overdue=overdue,
                           announcements=announcements)


@admin_bp.route("/members")
@admin_required
def members():
    query = request.args.get("q","").strip()
    if query:
        rows = call_proc("searchMembers", [query])
    else:
        rows = fetchall("""
            SELECT m."memberID",m."fullName",m."email",m."phoneNo",
                   b."branchName",c."categoryName",m."joinDate",m."isActive"
            FROM   "member" m
            JOIN   "branch"   b ON m."branchID"=b."branchID"
            JOIN   "category" c ON m."categoryID"=c."categoryID"
            ORDER BY m."secondName",m."firstName"
        """)
    return render_template("admin_members.html", members=rows, query=query)


@admin_bp.route("/members/<int:mid>")
@admin_required
def member_detail(mid):
    profile  = call_proc("getMemberActivityReport", [mid])
    profile  = profile[0] if profile else {}
    payments = call_proc("getMemberPayments", [mid])
    borrows  = fetchall("""
        SELECT r."title",r."type",b."borrowDate",b."returnDate",
               TRUNC(NVL(b."returnDate",SYSDATE)-b."borrowDate") AS days
        FROM   "borrow" b JOIN "resource" r ON b."resourceID"=r."resourceID"
        WHERE  b."memberID"=:mid ORDER BY b."borrowDate" DESC
    """, {"mid": mid})
    return render_template("admin_member_detail.html",
                           profile=profile, payments=payments, borrows=borrows)


@admin_bp.route("/members/toggle/<int:mid>", methods=["POST"])
@admin_required
def toggle_member(mid):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.callproc("toggleMemberActive", [mid])
                conn.commit()
    except oracledb.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.members"))


@admin_bp.route("/members/delete/<int:mid>", methods=["POST"])
@admin_required
def delete_member(mid):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.callproc("deleteMember", [mid])
                conn.commit()
        flash("Member deleted.", "success")
    except oracledb.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.members"))


@admin_bp.route("/resources")
@admin_required
def resources():
    rows = call_proc("getResourceReport", [])
    return render_template("admin_resources.html", resources=rows)


@admin_bp.route("/resources/add", methods=["POST"])
@admin_required
def add_resource():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.callproc("addResource", [
                    request.form["title"],
                    request.form["type"],
                    int(request.form["copies"])
                ])
                conn.commit()
        flash("Resource added.", "success")
    except oracledb.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.resources"))


@admin_bp.route("/shows/add", methods=["POST"])
@admin_required
def add_show():
    execute("""
        INSERT INTO "show" ("branchID","town","eventDate")
        VALUES (:bid,:town,TO_DATE(:dt,'YYYY-MM-DD'))
    """, {"bid": int(request.form["branchID"]),
          "town": request.form["town"], "dt": request.form["eventDate"]})
    flash("Show added.", "success")
    return redirect(url_for("public.shows"))


@admin_bp.route("/announcements/add", methods=["POST"])
@admin_required
def add_announcement():
    try:
        bid = request.form.get("branchID") or None
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.callproc("addAnnouncement", [
                    request.form["title"],
                    request.form["body"],
                    int(bid) if bid else None,
                    request.form.get("postedBy","Admin"),
                    request.form.get("priority","normal"),
                    request.form.get("tags","")
                ])
                conn.commit()
        flash("Announcement posted.", "success")
    except oracledb.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/audit")
@admin_required
def audit():
    audit_log = call_proc("getAuditTrail", [100])
    ledger    = call_proc("getPaymentLedger", [50])
    return render_template("admin_audit.html", audit_log=audit_log, ledger=ledger)


@admin_bp.route("/analytics")
@admin_required
def analytics():
    monthly_rev  = call_proc("getMonthlyRevenue", [])
    rev_by_type  = call_proc("getRevenueByPaymentType", [])
    growth       = call_proc("getMembersJoinedByMonth", [])
    resource_rep = call_proc("getResourceReport", [])
    return render_template("admin_analytics.html",
                           monthly_rev=monthly_rev, rev_by_type=rev_by_type,
                           growth=growth, resource_rep=resource_rep)