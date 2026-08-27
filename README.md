\# SpendSense



\## Day 1 — Project Foundation, Authentication \& Dashboard



\### Overview



Today we started building SpendSense, a privacy-focused personal finance web application.



The main objective of Day 1 was to establish the core application foundation, including the Flask backend, SQLite database, user registration, secure login, sessions, logout, protected dashboard access, and homepage navigation.



\---



\# 1. Project Setup



We created the initial SpendSense project structure.



```text

finance based/

│

├── .venv/

│

├── app/

│   ├── app.py

│   │

│   ├── templates/

│   │   ├── index.html

│   │   ├── signup.html

│   │   ├── login.html

│   │   └── dashboard.html

│   │

│   └── static/

│

├── database/

│   └── spendsense.db

│

└── README.md

