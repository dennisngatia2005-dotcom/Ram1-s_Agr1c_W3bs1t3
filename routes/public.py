"""routes/public.py"""
from flask import Blueprint, render_template
from db import fetchall, fetchone, call_proc
import threading
from .members import manager
public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    stats        = call_proc("getDashboardStats", [])
    stats        = stats[0] if stats else {}
    announcements = fetchall("""
        SELECT "announcementID","title",SUBSTR("body",1,180) AS excerpt,
               "postedDate","postedBy",
               JSON_VALUE("metadata",'$.priority') AS priority,
               b."branchName"
        FROM   "announcement_table" a
        LEFT JOIN "branch_table" b ON a."branchID" = b."branchID"
        ORDER BY "postedDate" DESC
        FETCH FIRST 4 ROWS ONLY
    """)
    shows = fetchall("""
        SELECT s."showID",s."town",s."eventDate",b."branchName",b."location"
        FROM   "show_table" s JOIN "branch_table" b ON s."branchID"=b."branchID"
        WHERE  s."eventDate">=SYSDATE AND s."isCancelled"=0
        ORDER BY s."eventDate" FETCH FIRST 6 ROWS ONLY
    """)
    branches = fetchall("""
        SELECT b."branchID",b."branchName",b."location",
               COUNT(m."memberID") AS member_count
        FROM   "branch_table" b LEFT JOIN "member_table" m ON b."branchID"=m."branchID"
        WHERE  b."isActive"=1
        GROUP BY b."branchID",b."branchName",b."location"
        ORDER BY b."branchName"
    """)
    return render_template("index.html", stats=stats,
                           announcements=announcements, shows=shows, branches=branches)


@public_bp.route("/about")
def about():
    officials = fetchall("""
        SELECT o."fullName",o."position",o."phoneNo",b."branchName"
        FROM "official_table" o JOIN "branch_table" b ON o."branchID"=b."branchID"
        ORDER BY o."position"
    """)
    return render_template("about.html", officials=officials)

def threaded_function():#reducing slugishness of the app by running the manager function in a separate thread
    from .members import manager
    thread = threading.Thread(target=manager)
    thread.start()
@public_bp.route("/resources")
def resources():
    resources = fetchall("""
        SELECT r."resourceID",r."title",r."type",r."availableCopies",
               COUNT(b."borrowID") AS times_borrowed
        FROM   "resource_table" r LEFT JOIN "borrow_table" b ON r."resourceID"=b."resourceID"
        GROUP BY r."resourceID",r."title",r."type",r."availableCopies"
        ORDER BY r."title"
    """)
    return render_template("resources.html", resources=resources)


@public_bp.route("/shows")
def shows():
    branches = fetchall('SELECT "branchID","branchName" FROM "branch_table" WHERE "isActive"=1 ORDER BY "branchName"')
    upcoming = fetchall("""
        SELECT s."showID",s."town",s."eventDate",b."branchName",b."location",s."isCancelled"
        FROM "show_table" s JOIN "branch_table" b ON s."branchID"=b."branchID"
        WHERE s."eventDate">=SYSDATE ORDER BY s."eventDate"
    """)
    past = fetchall("""
        SELECT s."showID",s."town",s."eventDate",b."branchName",b."location"
        FROM "show_table" s JOIN "branch_table" b ON s."branchID"=b."branchID"
        WHERE s."eventDate"<SYSDATE ORDER BY s."eventDate" DESC
        FETCH FIRST 10 ROWS ONLY
    """)
    return render_template("shows.html", upcoming=upcoming, past=past, branches=branches)


@public_bp.route("/join")
def join():
    categories = fetchall('SELECT "categoryID","categoryName","entryFee","annualFee" FROM "category_table" ORDER BY "entryFee"')
    branches   = fetchall('SELECT "branchID","branchName","location" FROM "branch_table" WHERE "isActive"=1 ORDER BY "branchName"')
    return render_template("join.html", categories=categories, branches=branches)


@public_bp.route("/oracle-features")
def oracle_features():
    return render_template("oracle_features.html")