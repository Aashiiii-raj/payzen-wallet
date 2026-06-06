# ⚡ EWP — Ericsson Wallet Platform (College Project)

A full-stack digital wallet web application inspired by Ericsson's Wallet Platform,
built with **Flask + MySQL + Bootstrap 5**.

---

## 📁 Folder Structure

```
ewp/
├── app.py                  ← Flask application (all routes & logic)
├── schema.sql              ← MySQL database schema + seed data
├── create_admin.py         ← One-time script to create admin user
├── requirements.txt        ← Python dependencies
├── README.md
│
└── templates/
    ├── base.html           ← Shared layout (sidebar, topbar, nav)
    ├── auth/
    │   ├── login.html
    │   └── register.html
    ├── wallet/
    │   ├── dashboard.html
    │   ├── add_money.html
    │   ├── send_money.html
    │   ├── pay_merchant.html
    │   └── transactions.html
    ├── complaints/
    │   └── complaints.html
    └── admin/
        └── dashboard.html
```

---

## ✅ Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Login / Register** | Secure auth with hashed passwords |
| 2 | **Wallet Balance** | Real-time balance shown on dashboard |
| 3 | **Add Money** | Simulated top-up with quick amounts |
| 4 | **Send Money** | P2P transfer via Wallet ID |
| 5 | **Merchant Payment** | Pay from a list of merchants |
| 6 | **Transaction History** | Full table with type, amount, parties |
| 7 | **Customer Care** | Raise & track complaints |
| 8 | **Admin Dashboard** | Stats, user list, complaint resolution |
| 9 | **Professional UI** | Dark theme, Bootstrap 5, custom CSS |

---

## ⚙️ Setup — Step by Step

### Step 1 — Install Python packages

```bash
cd ewp
pip install -r requirements.txt
```

> On some systems use `pip3` instead of `pip`.
> If mysqlclient fails: `sudo apt install libmysqlclient-dev` (Linux)
> or install MySQL Connector: `pip install mysql-connector-python`

---

### Step 2 — Create the MySQL database

Open your MySQL terminal or phpMyAdmin and run:

```bash
mysql -u root -p < schema.sql
```

Or paste `schema.sql` contents into phpMyAdmin's SQL tab.

This creates:
- `ewp_db` database
- `users`, `transactions`, `merchants`, `complaints` tables
- 8 demo merchants seeded

---

### Step 3 — Create the Admin user

```bash
python create_admin.py
```

This creates: **admin@ewp.com / admin123**

---

### Step 4 — Update DB credentials in app.py

Edit the MySQL config block in `app.py`:

```python
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = 'your_mysql_password'   # ← change this
app.config['MYSQL_DB']       = 'ewp_db'
```

---

### Step 5 — Run the app

```bash
python app.py
```

Open your browser: **http://127.0.0.1:5000**

---

## 🔐 Demo Credentials

| Role  | Email            | Password  |
|-------|------------------|-----------|
| Admin | admin@ewp.com    | admin123  |
| User  | Register a new account |    |

---

## 🗄️ Database Tables

### `users`
| Column     | Type         | Notes                        |
|------------|--------------|------------------------------|
| id         | INT PK       | Auto-increment               |
| name       | VARCHAR(100) |                              |
| email      | VARCHAR(150) | Unique                       |
| phone      | VARCHAR(15)  |                              |
| password   | VARCHAR(255) | bcrypt hash                  |
| wallet_id  | VARCHAR(20)  | Unique, e.g. WLT3F8A1B2C    |
| balance    | DECIMAL(12,2)| Default 0.00                 |
| role       | ENUM         | 'user' or 'admin'            |

### `transactions`
| Column      | Type    | Notes                          |
|-------------|---------|--------------------------------|
| txn_id      | VARCHAR | e.g. TXN3A8F1C2D4E             |
| sender_id   | FK      | References users.id            |
| receiver_id | FK      | References users.id (nullable) |
| amount      | DECIMAL |                                |
| txn_type    | ENUM    | credit / debit / merchant_pay  |
| status      | ENUM    | success / failed / pending     |
| note        | VARCHAR | Optional memo                  |

### `merchants`
| Column        | Type    |
|---------------|---------|
| name          | VARCHAR |
| merchant_code | VARCHAR |
| category      | VARCHAR |

### `complaints`
| Column  | Type | Notes                             |
|---------|------|-----------------------------------|
| user_id | FK   | References users.id               |
| subject | VARCHAR |                              |
| message | TEXT |                                   |
| status  | ENUM | open / in_progress / resolved     |

---

## 🧠 How It Works — Code Flow

```
User visits /login
  → app.py: login() checks DB, sets session
  → Redirect to /dashboard

/dashboard
  → Fetches user balance + last 5 transactions from DB
  → Renders wallet/dashboard.html via base.html layout

/add-money (POST)
  → Updates users.balance += amount
  → Inserts a 'credit' transaction row

/send-money (POST)
  → Validates receiver wallet ID exists
  → Checks sender has sufficient balance
  → Deducts from sender, adds to receiver (2 UPDATEs)
  → Inserts 'debit' transaction row

/pay-merchant (POST)
  → Deducts from user balance
  → Inserts 'merchant_pay' transaction row

/complaints (POST)
  → Inserts complaint row for current user

/admin (GET)
  → Only accessible if session.role == 'admin'
  → Shows stats, user list, all complaints
  → /admin/resolve-complaint/<id> updates status to 'resolved'
```

---

## 🎨 UI Design Decisions

- **Dark theme** with `#0A0F1E` background — professional fintech look
- **Syne** font (headings) + **DM Sans** (body) — modern & readable
- **Brand color** `#0057FF` (deep blue) + **Accent** `#00D4AA` (teal)
- **CSS Variables** throughout for easy theme changes
- Bootstrap 5 for grid + components; custom CSS for all dark styling
- Sidebar navigation fixed on desktop, hidden on mobile

---

## 📌 Notes for College Submission

- This is a **simulation** — no real money moves
- Wallet IDs are randomly generated UUIDs
- Transaction IDs follow format `TXNxxxxxxxxxx`
- The admin panel is role-gated — regular users cannot access it
- All passwords stored as **PBKDF2-SHA256 hashes** (never plain text)

---

*Built as a college project inspired by Ericsson's Wallet Platform (EWP).*
