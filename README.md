@'
# SpendSense 💰

SpendSense is a modern personal finance management web application built with **Flask, SQLite, HTML, CSS, and JavaScript**.

It helps users track income and expenses, manage transactions and budgets, analyze spending patterns, and generate informative financial reports through a clean and responsive interface.

---

## 🚀 Features

### 🔐 Authentication

- User signup
- User login
- Session-based authentication
- Password hashing
- Logout
- User-specific financial data

### 📊 Dashboard

- Current financial balance
- Monthly income
- Monthly expenses
- Monthly savings
- Recent transactions
- Expense category breakdown
- Daily spending analysis
- Potential savings calculation
- Financial health indicator

### 💳 Transactions

- Add income and expenses
- View transaction history
- Transaction categories
- Transaction dates
- Transaction notes
- Search transactions
- Filter by income and expense
- Edit transactions
- Delete transactions
- Income and expense totals
- User-specific transaction records

### 💰 Budgets

- Category-based budgets
- Budget tracking
- Spending comparison against budgets
- Budget progress information

### 📈 Analytics

- Spending analysis
- Category-based financial analysis
- Financial activity visualization
- Data-driven spending insights

### 📑 Reports

- Total income
- Total expenses
- Net savings
- Savings rate
- Top spending category
- Transaction count
- Total tracked months
- Monthly financial analysis
- Average monthly income
- Average monthly expenses
- Best saving month
- Highest spending month
- Financial health status
- Financial insights
- Potential savings
- Interactive Chart.js visualizations
- Income vs expenses
- Spending category distribution
- Savings trend
- Cash flow analysis
- Monthly financial trends

---

## 🎨 UI / Design

SpendSense includes:

- Responsive dashboard layout
- Modern gradient-based design
- Rounded cards
- Financial summary cards
- Interactive charts
- Category progress indicators
- Responsive transaction tables
- Clean navigation
- Mobile-friendly layouts
- Positive and negative financial indicators
- Indian Rupee (₹) formatting

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| SQLite | Database |
| Jinja2 | Template rendering |
| HTML5 | Page structure |
| CSS3 | Styling and responsive design |
| JavaScript | Client-side functionality |
| Chart.js | Interactive financial charts |
| Werkzeug | Password hashing |
| PowerShell | Development and project management |
| Git | Version control |
| GitHub | Source code hosting |

---

## 📁 Project Structure

```text
finance based/
│
├── app/
│   ├── app.py
│   │
│   ├── templates/
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── dashboard.html
│   │   ├── transactions.html
│   │   ├── budgets.html
│   │   ├── analytics.html
│   │   └── reports.html
│   │
│   └── static/
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   └── app.js
│       └── favicon.svg
│
├── database/
│   ├── db.py
│   └── add_budgets.py
│
├── .gitignore
├── README.md
└── ...