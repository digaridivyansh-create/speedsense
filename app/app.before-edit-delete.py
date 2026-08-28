from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database.db import get_connection


app = Flask(__name__)

app.secret_key = "spendsense-development-secret-key"


# =========================================
# HOME
# =========================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================
# SIGNUP PAGE
# =========================================

@app.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")


# =========================================
# SIGNUP
# =========================================

@app.route("/signup", methods=["POST"])
def signup():

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return "Email and password are required.", 400

    if len(password) < 8:
        return "Password must contain at least 8 characters.", 400

    connection = get_connection()

    try:
        password_hash = generate_password_hash(password)

        connection.execute(
            """
            INSERT INTO users
            (email, password_hash, created_at)
            VALUES (?, ?, datetime('now'))
            """,
            (email, password_hash)
        )

        connection.commit()

    except Exception as error:

        connection.rollback()

        if "UNIQUE constraint failed" in str(error):
            return "An account with this email already exists.", 409

        print("Signup error:", error)

        return "Unable to create account.", 500

    finally:
        connection.close()

    return redirect("/login")
# =========================================
# LOGIN PAGE
# =========================================

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


# =========================================
# LOGIN
# =========================================

@app.route("/login", methods=["POST"])
def login():

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return "Email and password are required.", 400

    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT id, email, password_hash
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()
    finally:
        connection.close()

    if user is None:
        return "Invalid email or password.", 401

    if not check_password_hash(
        user["password_hash"],
        password
    ):
        return "Invalid email or password.", 401

    session.clear()
    session["user_id"] = user["id"]
    session["user_email"] = user["email"]

    return redirect("/dashboard")


# =========================================
# DASHBOARD
# =========================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_connection()

    try:
        user_id = session["user_id"]

        income_row = connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE user_id = ?
              AND transaction_type = 'income'
              AND strftime('%Y-%m', transaction_date) =
                  strftime('%Y-%m', 'now')
            """,
            (user_id,)
        ).fetchone()

        expense_row = connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE user_id = ?
              AND transaction_type = 'expense'
              AND strftime('%Y-%m', transaction_date) =
                  strftime('%Y-%m', 'now')
            """,
            (user_id,)
        ).fetchone()

        recent_transactions = connection.execute(
            """
            SELECT
                id,
                title,
                amount,
                transaction_type,
                category,
                transaction_date,
                notes
            FROM transactions
            WHERE user_id = ?
            ORDER BY transaction_date DESC, id DESC
            LIMIT 10
            """,
            (user_id,)
        ).fetchall()

        category_rows = connection.execute(
            """
            SELECT
                category,
                COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE user_id = ?
              AND transaction_type = 'expense'
              AND strftime('%Y-%m', transaction_date) =
                  strftime('%Y-%m', 'now')
            GROUP BY category
            ORDER BY total DESC
            """,
            (user_id,)
        ).fetchall()

        daily_rows = connection.execute(
            """
            SELECT
                transaction_date,
                COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE user_id = ?
              AND transaction_type = 'expense'
              AND strftime('%Y-%m', transaction_date) =
                  strftime('%Y-%m', 'now')
            GROUP BY transaction_date
            ORDER BY transaction_date
            """,
            (user_id,)
        ).fetchall()

    finally:
        connection.close()

    total_income = float(income_row["total"] or 0)
    total_expenses = float(expense_row["total"] or 0)
    total_balance = total_income - total_expenses
    savings = total_balance

    # =========================================
    # FINANCIAL HEALTH + POTENTIAL SAVINGS
    # =========================================

    potential_savings = max(
        0,
        total_income - total_expenses
    )

    if total_income <= 0:
        financial_health = 0 if total_expenses > 0 else 50
    else:
        financial_health = round(
            ((total_income - total_expenses) / total_income) * 100
        )
        financial_health = max(
            0,
            min(100, financial_health)
        )

    if financial_health >= 81:
        financial_health_label = "Excellent"
        financial_insight = "Your finances are in excellent shape. Keep maintaining your current spending habits."
    elif financial_health >= 61:
        financial_health_label = "Good"
        financial_insight = "Your finances are looking good. A little more control over spending could improve your savings."
    elif financial_health >= 41:
        financial_health_label = "Fair"
        financial_insight = "Your finances are balanced, but reducing unnecessary expenses could strengthen your savings."
    elif financial_health >= 21:
        financial_health_label = "Needs Attention"
        financial_insight = "Your expenses are taking a significant share of your income. Consider reducing non-essential spending."
    else:
        financial_health_label = "Critical"
        financial_insight = "Your expenses currently exceed your income. Focus on essential spending and reducing unnecessary expenses."

    category_totals = {
        "Food": 0,
        "Transport": 0,
        "Shopping": 0,
        "Bills": 0
    }

    for row in category_rows:
        category = row["category"]
        if category in category_totals:
            category_totals[category] = float(row["total"] or 0)

    max_category_total = max(
        category_totals.values(),
        default=0
    )

    daily_spending = {
        "Mon": 0,
        "Tue": 0,
        "Wed": 0,
        "Thu": 0,
        "Fri": 0,
        "Sat": 0,
        "Sun": 0
    }

    from datetime import datetime

    for row in daily_rows:
        try:
            date_obj = datetime.strptime(
                row["transaction_date"],
                "%Y-%m-%d"
            )
            day_name = date_obj.strftime("%a")

            if day_name in daily_spending:
                daily_spending[day_name] += float(row["total"] or 0)

        except (ValueError, TypeError):
            pass

    chart_max = max(
        1000,
        max(daily_spending.values(), default=0)
    )

    return render_template(
        "dashboard.html",
        email=session.get("user_email"),
        total_balance=total_balance,
        total_income=total_income,
        total_expenses=total_expenses,
        savings=savings,
        recent_transactions=recent_transactions,
        category_totals=category_totals,
        max_category_total=max_category_total,
        daily_spending=daily_spending,
        chart_max=chart_max,
        financial_health=financial_health,
        financial_insight=financial_insight,
        financial_health_label=financial_health_label,
        potential_savings=potential_savings
    )


# =========================================
# ADD TRANSACTION
# =========================================

@app.route("/transactions/add", methods=["POST"])
def add_transaction():

    if "user_id" not in session:
        return redirect("/login")

    title = request.form.get("title", "").strip()
    amount = request.form.get("amount", "").strip()
    transaction_type = request.form.get("transaction_type", "").strip().lower()
    category = request.form.get("category", "").strip()
    transaction_date = request.form.get("transaction_date", "").strip()
    notes = request.form.get("notes", "").strip()

    if not title or not amount or not transaction_type or not category or not transaction_date:
        return "All required transaction fields must be filled.", 400

    if transaction_type not in ("income", "expense"):
        return "Invalid transaction type.", 400

    try:
        amount = float(amount)
    except ValueError:
        return "Amount must be a valid number.", 400

    if amount <= 0:
        return "Amount must be greater than zero.", 400

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO transactions
            (
                user_id,
                title,
                amount,
                transaction_type,
                category,
                transaction_date,
                notes,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                session["user_id"],
                title,
                amount,
                transaction_type,
                category,
                transaction_date,
                notes
            )
        )

        connection.commit()

    except Exception as error:
        connection.rollback()
        print("Transaction error:", error)
        return "Unable to save transaction.", 500

    finally:
        connection.close()

    return redirect("/dashboard")



# =========================================
# TRANSACTIONS PAGE
# =========================================

@app.route("/transactions")
def transactions():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_connection()

    try:
        user_id = session["user_id"]

        transactions = connection.execute(
            """
            SELECT
                id,
                title,
                amount,
                transaction_type,
                category,
                transaction_date,
                notes
            FROM transactions
            WHERE user_id = ?
            ORDER BY transaction_date DESC, id DESC
            """,
            (user_id,)
        ).fetchall()

        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total_transactions,
                COALESCE(SUM(CASE
                    WHEN transaction_type = 'income' THEN amount
                    ELSE 0
                END), 0) AS total_income,
                COALESCE(SUM(CASE
                    WHEN transaction_type = 'expense' THEN amount
                    ELSE 0
                END), 0) AS total_expenses
            FROM transactions
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

    finally:
        connection.close()

    return render_template(
        "transactions.html",
        transactions=transactions,
        total_transactions=summary["total_transactions"],
        total_income=float(summary["total_income"] or 0),
        total_expenses=float(summary["total_expenses"] or 0)
    )

# LOGOUT
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================
# RUN SERVER
# =========================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5001
    )













