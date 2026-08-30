import os

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

app.secret_key = os.environ.get("SECRET_KEY", "spendsense-development-secret-key")


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


# =========================================
# BUDGETS
# =========================================

@app.route("/budgets")
def budgets():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_connection()

    try:
        user_id = session["user_id"]

        budgets = connection.execute(
            """
            SELECT
                b.id,
                b.category,
                b.amount,
                b.month,
                COALESCE(SUM(t.amount), 0) AS spent
            FROM budgets b
            LEFT JOIN transactions t
                ON t.user_id = b.user_id
                AND t.category = b.category
                AND t.transaction_type = 'expense'
                AND strftime('%Y-%m', t.transaction_date) = b.month
            WHERE b.user_id = ?
              AND b.month = strftime('%Y-%m', 'now')
            GROUP BY b.id, b.category, b.amount, b.month
            ORDER BY b.category
            """,
            (user_id,)
        ).fetchall()

    finally:
        connection.close()

    # =========================================
    # BUDGET INTELLIGENCE
    # =========================================

    budget_data = []

    for budget in budgets:

        amount = float(budget["amount"] or 0)
        spent = float(budget["spent"] or 0)

        remaining = amount - spent

        if amount > 0:
            percentage = (spent / amount) * 100
        else:
            percentage = 0

        budget_data.append({
            "id": budget["id"],
            "category": budget["category"],
            "amount": amount,
            "month": budget["month"],
            "spent": spent,
            "remaining": remaining,
            "percentage": percentage
        })

    return render_template(
        "budgets.html",
        email=session.get("user_email", ""),
        budgets=budget_data
    )


@app.route("/budgets/add", methods=["POST"])
def add_budget():

    if "user_id" not in session:
        return redirect("/login")

    category = request.form.get("category", "").strip()
    amount = request.form.get("amount", "").strip()

    try:
        amount = float(amount)

        if amount <= 0:
            raise ValueError

    except ValueError:
        return "Invalid budget amount.", 400

    if not category:
        return "Category is required.", 400

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO budgets
            (user_id, category, amount, month, created_at)
            VALUES (?, ?, ?, strftime('%Y-%m', 'now'), datetime('now'))
            """,
            (
                session["user_id"],
                category,
                amount
            )
        )

        connection.commit()

    except Exception as error:

        connection.rollback()

        if "UNIQUE constraint failed" in str(error):
            return "A budget for this category already exists this month.", 409

        print("Budget error:", error)

        return "Unable to create budget.", 500

    finally:
        connection.close()

    return redirect("/budgets")


@app.route("/budgets/<int:budget_id>/delete", methods=["POST"])
def delete_budget(budget_id):

    if "user_id" not in session:
        return redirect("/login")

    connection = get_connection()

    try:

        connection.execute(
            """
            DELETE FROM budgets
            WHERE id = ?
              AND user_id = ?
            """,
            (
                budget_id,
                session["user_id"]
            )
        )

        connection.commit()

    finally:
        connection.close()

    return redirect("/budgets")

@app.route("/dashboard")
def dashboard():
    spending_period = request.args.get("period", "this")
    if spending_period not in ("this", "last"):
        spending_period = "this"

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
                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'income'
                            THEN amount
                            ELSE 0
                        END
                    ), 0
                ) AS total_income,
                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'expense'
                            THEN amount
                            ELSE 0
                        END
                    ), 0
                ) AS total_expenses
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


# =========================================
# EDIT TRANSACTION
# =========================================

@app.route("/transactions/<int:transaction_id>/edit", methods=["POST"])
def edit_transaction(transaction_id):

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
        result = connection.execute(
            """
            UPDATE transactions
            SET
                title = ?,
                amount = ?,
                transaction_type = ?,
                category = ?,
                transaction_date = ?,
                notes = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                title,
                amount,
                transaction_type,
                category,
                transaction_date,
                notes,
                transaction_id,
                session["user_id"]
            )
        )

        if result.rowcount == 0:
            connection.rollback()
            return "Transaction not found.", 404

        connection.commit()

    except Exception as error:
        connection.rollback()
        print("Edit transaction error:", error)
        return "Unable to update transaction.", 500

    finally:
        connection.close()

    return redirect("/transactions")


# =========================================
# DELETE TRANSACTION
# =========================================

@app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
def delete_transaction(transaction_id):

    if "user_id" not in session:
        return redirect("/login")

    connection = get_connection()

    try:
        result = connection.execute(
            """
            DELETE FROM transactions
            WHERE id = ?
              AND user_id = ?
            """,
            (
                transaction_id,
                session["user_id"]
            )
        )

        if result.rowcount == 0:
            connection.rollback()
            return "Transaction not found.", 404

        connection.commit()

    except Exception as error:
        connection.rollback()
        print("Delete transaction error:", error)
        return "Unable to delete transaction.", 500

    finally:
        connection.close()

    return redirect("/transactions")




# LOGOUT
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================
# RUN SERVER
# =========================================


# =========================================
# EDIT BUDGET
# =========================================

@app.route("/budgets/<int:budget_id>/edit", methods=["POST"])
def edit_budget(budget_id):

    if "user_id" not in session:
        return redirect("/login")

    category = request.form.get("category", "").strip()
    amount_raw = request.form.get("amount", "").strip()

    if not category or not amount_raw:
        return redirect("/budgets")

    try:
        amount = float(amount_raw)

        if amount <= 0:
            return redirect("/budgets")

    except ValueError:
        return redirect("/budgets")

    connection = get_connection()

    try:

        user_id = session["user_id"]

        budget = connection.execute(
            """
            SELECT id, month
            FROM budgets
            WHERE id = ?
              AND user_id = ?
            """,
            (budget_id, user_id)
        ).fetchone()

        if budget is None:
            return redirect("/budgets")

        try:

            connection.execute(
                """
                UPDATE budgets
                SET category = ?,
                    amount = ?
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    category,
                    amount,
                    budget_id,
                    user_id
                )
            )

            connection.commit()

        except Exception as error:

            connection.rollback()

            if "UNIQUE constraint failed" in str(error):
                return "A budget for this category already exists for this month.", 409

            print("Edit budget error:", error)
            return "Unable to edit budget.", 500

    finally:
        connection.close()

    return redirect("/budgets")


# =========================================
# ANALYTICS
# =========================================

@app.route("/analytics")
def analytics():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_connection()

    try:

        user_id = session["user_id"]

        # -----------------------------------------
        # CATEGORY SPENDING
        # -----------------------------------------

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

        # -----------------------------------------
        # DAILY SPENDING
        # -----------------------------------------

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

        # -----------------------------------------
        # MONTHLY SPENDING
        # -----------------------------------------

        monthly_rows = connection.execute(
            """
            SELECT
                strftime('%Y-%m', transaction_date) AS month,
                COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE user_id = ?
              AND transaction_type = 'expense'
            GROUP BY strftime('%Y-%m', transaction_date)
            ORDER BY month ASC
            LIMIT 6
            """,
            (user_id,)
        ).fetchall()

        # -----------------------------------------
        # TOTAL SPENDING
        # -----------------------------------------

        total_spending = connection.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE user_id = ?
              AND transaction_type = 'expense'
              AND strftime('%Y-%m', transaction_date) =
                  strftime('%Y-%m', 'now')
            """,
            (user_id,)
        ).fetchone()["total"]

    finally:
        connection.close()

    # =========================================
    # ANALYTICS CALCULATIONS
    # =========================================

    total_spending = float(total_spending or 0)

    # Average per active spending day
    if daily_rows:

        average_daily_spending = (
            total_spending / len(daily_rows)
        )

    else:

        average_daily_spending = 0

    # Highest spending day
    if daily_rows:

        highest_day_row = max(
            daily_rows,
            key=lambda row: float(row["total"] or 0)
        )

        highest_spending_day = (
            highest_day_row["transaction_date"]
        )

        highest_day_amount = float(
            highest_day_row["total"] or 0
        )

    else:

        highest_spending_day = ""
        highest_day_amount = 0

    # Top category
    if category_rows:

        top_category = category_rows[0]["category"]

        top_category_amount = float(
            category_rows[0]["total"] or 0
        )

        if total_spending > 0:

            top_category_percentage = round(
                (top_category_amount / total_spending) * 100
            )

        else:

            top_category_percentage = 0

    else:

        top_category = "No spending"
        top_category_amount = 0
        top_category_percentage = 0

    # =========================================
    # CHART DATA
    # =========================================

    monthly_labels = []
    monthly_values = []

    for row in monthly_rows:

        monthly_labels.append(
            row["month"]
        )

        monthly_values.append(
            float(row["total"] or 0)
        )

    return render_template(

        "analytics.html",

        email=session.get(
            "user_email",
            ""
        ),

        category_rows=category_rows,

        monthly_rows=monthly_rows,

        daily_rows=daily_rows,

        total_spending=total_spending,

        average_daily_spending=average_daily_spending,

        highest_spending_day=highest_spending_day,

        highest_day_amount=highest_day_amount,

        top_category=top_category,

        top_category_amount=top_category_amount,

        top_category_percentage=top_category_percentage,

        monthly_labels=monthly_labels,

        monthly_values=monthly_values
    )




# =========================================
# REPORTS
# =========================================

@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_connection()

    try:
        user_id = session["user_id"]

        monthly_rows = connection.execute(
            """
            SELECT
                strftime('%Y-%m', transaction_date) AS month,
                COALESCE(SUM(
                    CASE
                        WHEN transaction_type = 'income'
                        THEN amount ELSE 0
                    END
                ), 0) AS income,
                COALESCE(SUM(
                    CASE
                        WHEN transaction_type = 'expense'
                        THEN amount ELSE 0
                    END
                ), 0) AS expenses
            FROM transactions
            WHERE user_id = ?
            GROUP BY strftime('%Y-%m', transaction_date)
            ORDER BY month DESC
            LIMIT 12
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
            GROUP BY category
            ORDER BY total DESC
            """,
            (user_id,)
        ).fetchall()

        transaction_count = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM transactions
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()["total"]

        largest_expense = connection.execute(
            """
            SELECT
                title,
                category,
                amount,
                transaction_date
            FROM transactions
            WHERE user_id = ?
              AND transaction_type = 'expense'
            ORDER BY amount DESC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

        largest_income = connection.execute(
            """
            SELECT
                title,
                amount,
                transaction_date
            FROM transactions
            WHERE user_id = ?
              AND transaction_type = 'income'
            ORDER BY amount DESC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

    finally:
        connection.close()

    # =========================================
    # FINANCIAL TOTALS
    # =========================================

    monthly_data = []

    for row in monthly_rows:
        income = float(row["income"] or 0)
        expenses = float(row["expenses"] or 0)
        savings = income - expenses

        monthly_data.append({
            "month": row["month"],
            "income": income,
            "expenses": expenses,
            "savings": savings
        })

    total_income = sum(
        row["income"] for row in monthly_data
    )

    total_expenses = sum(
        row["expenses"] for row in monthly_data
    )

    net_savings = total_income - total_expenses

    months_tracked = len(monthly_data)

    average_monthly_income = (
        total_income / months_tracked
        if months_tracked > 0 else 0
    )

    average_monthly_expenses = (
        total_expenses / months_tracked
        if months_tracked > 0 else 0
    )

    if total_income > 0:
        savings_rate = round(
            (net_savings / total_income) * 100,
            1
        )
    else:
        savings_rate = 0

    # =========================================
    # TOP CATEGORY
    # =========================================

    top_category = (
        category_rows[0]["category"]
        if category_rows
        else "None"
    )

    top_category_amount = (
        float(category_rows[0]["total"] or 0)
        if category_rows
        else 0
    )

    # =========================================
    # BEST / WORST MONTH
    # =========================================

    best_month = None
    worst_month = None

    if monthly_data:
        best_month = max(
            monthly_data,
            key=lambda row: row["savings"]
        )

        worst_month = min(
            monthly_data,
            key=lambda row: row["savings"]
        )

    # =========================================
    # FINANCIAL HEALTH
    # =========================================

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
        financial_health_message = (
            "Your finances are in excellent shape. "
            "You are keeping spending comfortably below income."
        )

    elif financial_health >= 61:
        financial_health_label = "Good"
        financial_health_message = (
            "Your finances are healthy. "
            "Maintaining your current savings discipline can strengthen your position."
        )

    elif financial_health >= 41:
        financial_health_label = "Moderate"
        financial_health_message = (
            "Your finances are fairly balanced, "
            "but reducing unnecessary spending could improve your savings."
        )

    elif financial_health >= 21:
        financial_health_label = "Needs Attention"
        financial_health_message = (
            "Expenses are consuming a large share of your income. "
            "Review your largest spending categories."
        )

    else:
        financial_health_label = "Overspending"
        financial_health_message = (
            "Your expenses are currently exceeding your income. "
            "Focus on essential spending and reducing discretionary costs."
        )

    # =========================================
    # POTENTIAL SAVINGS
    # =========================================

    potential_savings = max(
        0,
        total_income - total_expenses
    )

    # =========================================
    # AUTOMATIC INSIGHTS
    # =========================================

    insights = []

    if top_category_amount > 0:
        insights.append(
            f"{top_category} is your largest expense category "
            f"at ₹{top_category_amount:,.2f}."
        )

    if savings_rate >= 30:
        insights.append(
            f"You are saving {savings_rate}% of your tracked income."
        )
    elif savings_rate >= 10:
        insights.append(
            f"Your savings rate is {savings_rate}%. "
            "There is room to increase your monthly savings."
        )
    elif total_income > 0:
        insights.append(
            "Your savings rate is low. "
            "Review recurring and discretionary expenses."
        )

    if best_month:
        insights.append(
            f"Your strongest tracked month was {best_month['month']} "
            f"with ₹{best_month['savings']:,.2f} saved."
        )

    if worst_month and worst_month["savings"] < 0:
        insights.append(
            f"{worst_month['month']} had a deficit of "
            f"₹{abs(worst_month['savings']):,.2f}."
        )

    if largest_expense:
        insights.append(
            f"Your largest individual expense was "
            f"₹{float(largest_expense['amount']):,.2f} "
            f"for {largest_expense['title']}."
        )

    # =========================================
    # REPORT PAGE DISPLAY METRICS
    # =========================================

    if best_month:
        best_saving_month_name = best_month["month"]
        best_saving_amount = max(0, float(best_month["savings"]))
    else:
        best_saving_month_name = "No data"
        best_saving_amount = 0.0

    if monthly_data:
        highest_spending_month = max(
            monthly_data,
            key=lambda row: float(row["expenses"] or 0)
        )
        highest_spending_month_name = highest_spending_month["month"]
        highest_spending_amount = float(
            highest_spending_month["expenses"] or 0
        )
    else:
        highest_spending_month_name = "No data"
        highest_spending_amount = 0.0

    return render_template(
        "reports.html",
        email=session.get("user_email", ""),

        monthly_rows=monthly_rows,
        monthly_data=monthly_data,
        category_rows=category_rows,

        transaction_count=transaction_count,
        months_tracked=months_tracked,

        total_income=total_income,
        total_expenses=total_expenses,
        net_savings=net_savings,
        savings_rate=savings_rate,

        average_monthly_income=average_monthly_income,
        average_monthly_expenses=average_monthly_expenses,

        top_category=top_category,
        top_category_amount=top_category_amount,

        best_month=best_month,
        worst_month=worst_month,

        largest_expense=largest_expense,
        largest_income=largest_income,

        potential_savings=potential_savings,

        financial_health=financial_health,
        financial_health_label=financial_health_label,
        financial_health_message=financial_health_message,

        insights=insights
    )

if __name__ == "__main__":
    app.run(
        debug=False,
        port=int(os.environ.get("PORT", 5001))
    )
