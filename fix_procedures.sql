-- Drop incorrectly named procedures (quoted names)
DROP PROCEDURE "getDashboardStats";
DROP PROCEDURE "getMonthlyRevenue";
DROP PROCEDURE "getRevenueByPaymentType";
DROP PROCEDURE "getMembersJoinedByMonth";
DROP PROCEDURE "getTopBorrowers";
DROP PROCEDURE "getOverdueBorrows";
DROP PROCEDURE "getMemberActivityReport";
DROP PROCEDURE "getBranchReport";
DROP PROCEDURE "getResourceReport";
DROP PROCEDURE "getAuditTrail";
DROP PROCEDURE "getPaymentLedger";
DROP PROCEDURE "searchMembers";
DROP PROCEDURE "addAnnouncement";
DROP PROCEDURE "toggleMemberActive";
DROP PROCEDURE "setMemberPassword";
DROP PROCEDURE "borrowResource";

-- Recreate procedures without quotes (case-insensitive)
CREATE OR REPLACE PROCEDURE getDashboardStats (
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT
            (SELECT COUNT(*) FROM "member_table"   WHERE "isActive" = 1)          AS active_members,
            (SELECT COUNT(*) FROM "member_table")                                  AS total_members,
            (SELECT COUNT(*) FROM "branch_table"   WHERE "isActive" = 1)          AS active_branches,
            (SELECT COUNT(*) FROM "resource_table" WHERE "availableCopies" > 0)   AS available_resources,
            (SELECT COUNT(*) FROM "resource_table")                                AS total_resources,
            (SELECT COUNT(*) FROM "show_table"
             WHERE  "eventDate" >= SYSDATE AND "isCancelled" = 0)           AS upcoming_shows,
            (SELECT NVL(SUM("amount"),0) FROM "payment_table")                    AS total_revenue,
            (SELECT NVL(SUM("amount"),0) FROM "payment_table"
             WHERE  "paymentDate" >= TRUNC(SYSDATE,'MM'))                   AS revenue_this_month,
            (SELECT COUNT(*) FROM "borrow_table" WHERE "returnDate" IS NULL)      AS active_borrows,
            (SELECT COUNT(*) FROM "borrow_table"
             WHERE  "borrowDate" < SYSDATE - 30
             AND    "returnDate" IS NULL)                                    AS overdue_borrows
        FROM DUAL;
END;
/

CREATE OR REPLACE PROCEDURE getMonthlyRevenue (
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT TO_CHAR(TRUNC("paymentDate",'MM'),'Mon YYYY') AS month_label,
               TRUNC("paymentDate",'MM')                     AS month_start,
               COUNT(*)                                      AS payment_count,
               SUM("amount")                                 AS total_revenue
        FROM   "payment_table"
        WHERE  "paymentDate" >= ADD_MONTHS(TRUNC(SYSDATE,'MM'), -11)
        GROUP BY TRUNC("paymentDate",'MM')
        ORDER BY TRUNC("paymentDate",'MM');
END;
/

CREATE OR REPLACE PROCEDURE getRevenueByPaymentType (
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT "paymentType",
               COUNT(*)       AS txn_count,
               SUM("amount")  AS total_amount,
               ROUND(SUM("amount") * 100 /
                   NULLIF((SELECT SUM("amount") FROM "payment_table"),0), 2) AS pct
        FROM   "payment_table"
        GROUP BY "paymentType"
        ORDER BY total_amount DESC;
END;
/

CREATE OR REPLACE PROCEDURE getMembersJoinedByMonth (
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT TO_CHAR(TRUNC("joinDate",'MM'),'Mon YYYY') AS month_label,
               TRUNC("joinDate",'MM')                     AS month_start,
               COUNT(*)                                   AS new_members,
               SUM(COUNT(*)) OVER (ORDER BY TRUNC("joinDate",'MM')) AS cumulative_members
        FROM   "member_table"
        WHERE  "joinDate" IS NOT NULL
        GROUP BY TRUNC("joinDate",'MM')
        ORDER BY TRUNC("joinDate",'MM');
END;
/

CREATE OR REPLACE PROCEDURE getTopBorrowers (
    p_limit  IN  NUMBER DEFAULT 10,
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT m."memberID",
               m."fullName"                  AS member_name,
               b."branchName",
               COUNT(br."borrowID")          AS total_borrows,
               SUM(CASE WHEN br."returnDate" IS NULL THEN 1 ELSE 0 END) AS active_borrows,
               MAX(br."borrowDate")          AS last_borrow_date
        FROM   "member_table"   m
        JOIN   "branch_table"   b  ON m."branchID"   = b."branchID"
        JOIN   "borrow_table"   br ON m."memberID"   = br."memberID"
        GROUP BY m."memberID", m."fullName", b."branchName"
        ORDER BY total_borrows DESC
        FETCH FIRST p_limit ROWS ONLY;
END;
/

CREATE OR REPLACE PROCEDURE getOverdueBorrows (
    p_days_threshold IN NUMBER DEFAULT 14,
    p_result         OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT br."borrowID",
               m."fullName"                            AS member_name,
               m."email",
               m."phoneNo",
               r."title"                               AS resource_title,
               br."borrowDate",
               TRUNC(SYSDATE - br."borrowDate")        AS days_overdue,
               b."branchName"
        FROM   "borrow_table"   br
        JOIN   "member_table"   m  ON br."memberID"   = m."memberID"
        JOIN   "resource_table" r  ON br."resourceID" = r."resourceID"
        JOIN   "branch_table"   b  ON m."branchID"    = b."branchID"
        WHERE  br."returnDate" IS NULL
          AND  br."borrowDate" < SYSDATE - p_days_threshold
        ORDER BY days_overdue DESC;
END;
/

CREATE OR REPLACE PROCEDURE getMemberActivityReport (
    p_memberID IN  NUMBER,
    p_result   OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT m."memberID",
               m."fullName",
               m."email",
               m."phoneNo",
               b."branchName",
               c."categoryName",
               m."joinDate",
               member_tenure_years(m."joinDate")               AS tenure_years,
               (SELECT COUNT(*) FROM "borrow_table"  WHERE "memberID" = m."memberID") AS total_borrows,
               (SELECT COUNT(*) FROM "borrow_table"  WHERE "memberID" = m."memberID" AND "returnDate" IS NULL) AS active_borrows,
               (SELECT NVL(SUM("amount"),0) FROM "payment_table" WHERE "memberID" = m."memberID") AS total_paid,
               (SELECT MAX("paymentDate")    FROM "payment_table" WHERE "memberID" = m."memberID") AS last_payment
        FROM   "member_table"   m
        JOIN   "branch_table"   b ON m."branchID"   = b."branchID"
        JOIN   "category_table" c ON m."categoryID" = c."categoryID"
        WHERE  m."memberID" = p_memberID;
END;
/

CREATE OR REPLACE PROCEDURE getBranchReport (
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT b."branchID",
               b."branchName",
               b."location",
               COUNT(DISTINCT m."memberID")                       AS total_members,
               SUM(CASE WHEN m."isActive"=1 THEN 1 ELSE 0 END)   AS active_members,
               COUNT(DISTINCT o."officialID")                     AS official_count,
               COUNT(DISTINCT s."showID")                         AS total_shows,
               NVL(SUM(p."amount"),0)                             AS total_revenue
        FROM   "branch_table"  b
        LEFT JOIN "member_table"   m ON b."branchID" = m."branchID"
        LEFT JOIN "official_table" o ON b."branchID" = o."branchID"
        LEFT JOIN "show_table"     s ON b."branchID" = s."branchID"
        LEFT JOIN "payment_table"  p ON m."memberID" = p."memberID"
        GROUP BY b."branchID", b."branchName", b."location"
        ORDER BY total_members DESC;
END;
/

CREATE OR REPLACE PROCEDURE getResourceReport (
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT r."resourceID",
               r."title",
               r."type",
               r."availableCopies",
               COUNT(br."borrowID")                                  AS total_borrows,
               SUM(CASE WHEN br."returnDate" IS NULL THEN 1 ELSE 0 END) AS currently_borrowed,
               ROUND(AVG(br."returnDate" - br."borrowDate"), 1)      AS avg_borrow_days,
               MAX(br."borrowDate")                                   AS last_borrowed
        FROM   "resource_table" r
        LEFT JOIN "borrow_table" br ON r."resourceID" = br."resourceID"
        GROUP BY r."resourceID", r."title", r."type", r."availableCopies"
        ORDER BY total_borrows DESC;
END;
/

CREATE OR REPLACE PROCEDURE getAuditTrail (
    p_limit  IN  NUMBER DEFAULT 50,
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT a."auditID",
               a."action",
               a."memberID",
               m."fullName"   AS member_name,
               a."changedBy",
               a."changeTime",
               a."oldEmail",
               a."newEmail",
               a."oldIsActive",
               a."newIsActive"
        FROM   "memberAuditLog_table" a
        LEFT JOIN "member_table" m ON a."memberID" = m."memberID"
        ORDER BY a."changeTime" DESC
        FETCH FIRST p_limit ROWS ONLY;
END;
/

CREATE OR REPLACE PROCEDURE getPaymentLedger (
    p_limit  IN  NUMBER DEFAULT 50,
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT l."ledgerID",
               l."paymentID",
               m."fullName"     AS member_name,
               l."amount",
               l."paymentType",
               l."actionTime",
               l."actionBy",
               l."notes"
        FROM   "paymentAuditLedger_table" l
        LEFT JOIN "member_table" m ON l."memberID" = m."memberID"
        ORDER BY l."actionTime" DESC
        FETCH FIRST p_limit ROWS ONLY;
END;
/

CREATE OR REPLACE PROCEDURE searchMembers (
    p_query  IN  VARCHAR2,
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT m."memberID",
               m."fullName",
               m."email",
               m."phoneNo",
               b."branchName",
               c."categoryName",
               m."isActive",
               m."joinDate"
        FROM   "member_table"   m
        JOIN   "branch_table"   b ON m."branchID"   = b."branchID"
        JOIN   "category_table" c ON m."categoryID" = c."categoryID"
        WHERE  UPPER(m."fullName") LIKE '%' || UPPER(p_query) || '%'
           OR  UPPER(m."email")    LIKE '%' || UPPER(p_query) || '%'
           OR  m."phoneNo"         LIKE '%' || p_query || '%'
        ORDER BY m."secondName", m."firstName";
END;
/

CREATE OR REPLACE PROCEDURE addAnnouncement (
    p_title    IN VARCHAR2,
    p_body     IN CLOB,
    p_branchID IN NUMBER,
    p_postedBy IN VARCHAR2,
    p_priority IN VARCHAR2 DEFAULT 'normal',
    p_tags     IN VARCHAR2 DEFAULT NULL
) AS
BEGIN
    INSERT INTO "announcement_table" (
        "title","body","branchID","postedBy","metadata"
    ) VALUES (
        p_title, p_body, p_branchID, p_postedBy,
        JSON_OBJECT(
            'priority' VALUE p_priority,
            'tags'     VALUE p_tags,
            'author'   VALUE p_postedBy
        )
    );
END;
/

CREATE OR REPLACE PROCEDURE toggleMemberActive (
    p_memberID IN NUMBER
) AS
BEGIN
    UPDATE "member_table"
    SET    "isActive" = CASE WHEN "isActive" = 1 THEN 0 ELSE 1 END
    WHERE  "memberID" = p_memberID;
END;
/

CREATE OR REPLACE PROCEDURE setMemberPassword (
    p_memberID IN NUMBER,
    p_pwdHash  IN VARCHAR2
) AS
BEGIN
    UPDATE "member_table"
    SET    "pwdHash" = p_pwdHash
    WHERE  "memberID" = p_memberID;
END;
/

CREATE OR REPLACE PROCEDURE borrowResource (
    p_memberID   IN NUMBER,
    p_resourceID IN NUMBER
) AS
    v_available NUMBER;
BEGIN
    SELECT "availableCopies"
    INTO   v_available
    FROM   "resource_table"
    WHERE  "resourceID" = p_resourceID
    FOR UPDATE;

    IF v_available <= 0 THEN
        RAISE_APPLICATION_ERROR(-20002, 'No copies available for resourceID: ' || p_resourceID);
    END IF;

    INSERT INTO "borrow_table" ("memberID", "resourceID", "borrowDate")
    VALUES (p_memberID, p_resourceID, SYSDATE);

    UPDATE "resource_table"
    SET    "availableCopies" = "availableCopies" - 1
    WHERE  "resourceID" = p_resourceID;
END;
/