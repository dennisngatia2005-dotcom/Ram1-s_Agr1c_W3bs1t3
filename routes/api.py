"""routes/api.py — JSON endpoints for charts, graphs and AJAX."""
from flask import Blueprint, jsonify, request
from db import fetchall, fetchone, call_proc

api_bp = Blueprint("api", __name__)


@api_bp.route("/stats")
def stats():
    rows = call_proc("getDashboardStats", [])
    return jsonify(rows[0] if rows else {})


@api_bp.route("/monthly-revenue")
def monthly_revenue():
    return jsonify(call_proc("getMonthlyRevenue", []))


@api_bp.route("/revenue-by-type")
def revenue_by_type():
    return jsonify(call_proc("getRevenueByPaymentType", []))


@api_bp.route("/members-growth")
def members_growth():
    return jsonify(call_proc("getMembersJoinedByMonth", []))


@api_bp.route("/members-per-branch")
def members_per_branch():
    return jsonify(fetchall('SELECT * FROM "membersPerBranch" ORDER BY "totalMembers" DESC'))


@api_bp.route("/revenue-by-branch")
def revenue_by_branch():
    return jsonify(fetchall('SELECT * FROM "revenueByBranch"'))


@api_bp.route("/resource-usage")
def resource_usage():
    return jsonify(fetchall("""
        SELECT * FROM "resourceUsage"
        ORDER BY "timesBorrowed" DESC FETCH FIRST 10 ROWS ONLY
    """))


@api_bp.route("/top-borrowers")
def top_borrowers():
    limit = int(request.args.get("limit", 10))
    return jsonify(call_proc("getTopBorrowers", [limit]))


@api_bp.route("/overdue-borrows")
def overdue_borrows():
    days = int(request.args.get("days", 14))
    return jsonify(call_proc("getOverdueBorrows", [days]))


@api_bp.route("/upcoming-shows")
def upcoming_shows():
    return jsonify(fetchall("""
        SELECT s."showID",s."town",
               TO_CHAR(s."eventDate",'DD Mon YYYY') AS event_date,
               b."branchName"
        FROM   "show_table" s JOIN "branch_table" b ON s."branchID"=b."branchID"
        WHERE  s."eventDate">=SYSDATE AND s."isCancelled"=0
        ORDER BY s."eventDate" FETCH FIRST 6 ROWS ONLY
    """))


@api_bp.route("/announcements")
def announcements():
    return jsonify(fetchall('SELECT * FROM "announcementSummary" ORDER BY "postedDate" DESC FETCH FIRST 5 ROWS ONLY'))


@api_bp.route("/oracle-feature-data")
def oracle_feature_data():
    """Live demo data for the Oracle features documentation page."""
    result = {}
    result["blockchain_count"] = fetchone("SELECT COUNT(*) AS cnt FROM \"paymentAuditLedger_table\"") or {"cnt": 0}
    result["immutable_count"]  = fetchone("SELECT COUNT(*) AS cnt FROM \"borrowHistory_table\"") or {"cnt": 0}
    result["audit_recent"]     = fetchall("""
        SELECT "action","memberID","changedBy",
               TO_CHAR("changeTime",'DD Mon YYYY HH24:MI') AS change_time
        FROM   "memberAuditLog_table"
        ORDER BY "changeTime" DESC FETCH FIRST 5 ROWS ONLY
    """)
    result["json_sample"]      = fetchall("""
        SELECT "title",
               JSON_VALUE("metadata",'$.priority') AS priority,
               JSON_VALUE("metadata",'$.author')   AS author
        FROM   "announcement_table"
        ORDER BY "postedDate" DESC FETCH FIRST 3 ROWS ONLY
    """)
    result["virtual_col"]      = fetchall("""
        SELECT "memberID","fullName","joinDate"
        FROM   "member_table"
        WHERE  "isActive"=1
        ORDER BY "joinDate" DESC FETCH FIRST 5 ROWS ONLY
    """)
    result["sql_macro_demo"]   = fetchall("""
        SELECT member_tenure_years("joinDate") AS tenure_years,
               COUNT(*) AS member_count
        FROM   "member_table"
        GROUP BY member_tenure_years("joinDate")
        ORDER BY tenure_years
    """)
    return jsonify(result)


@api_bp.route("/graph-data")
def graph_data():
    """Property graph-inspired adjacency data for the D3 network graph."""
    members = fetchall("""
        SELECT m."memberID" AS id, m."fullName" AS label,
               b."branchName" AS group_name
        FROM   "member_table" m JOIN "branch_table" b ON m."branchID"=b."branchID"
        WHERE  m."isActive"=1
        FETCH FIRST 30 ROWS ONLY
    """)
    borrows = fetchall("""
        SELECT DISTINCT b."memberID" AS source, b."resourceID"+1000 AS target
        FROM   "borrow_table" b
        FETCH FIRST 60 ROWS ONLY
    """)
    resources = fetchall("""
        SELECT r."resourceID"+1000 AS id, r."title" AS label, r."type" AS group_name
        FROM   "resource_table" r FETCH FIRST 20 ROWS ONLY
    """)
    nodes = members + resources
    return jsonify({"nodes": nodes, "links": borrows})