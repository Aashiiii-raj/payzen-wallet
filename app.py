from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ewp_secret_key_2024'

# ── MySQL Config ──────────────────────────────────────────────
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = ''          # change to your MySQL password
app.config['MYSQL_DB']       = 'ewp_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ── Helpers ───────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def gen_txn_id():
    return 'TXN' + uuid.uuid4().hex[:10].upper()

# ── Auth Routes ───────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip().lower()
        phone    = request.form['phone'].strip()
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        wallet_id = 'WLT' + uuid.uuid4().hex[:8].upper()

        cur.execute(
            "INSERT INTO users (name, email, phone, password, wallet_id, balance, role) "
            "VALUES (%s,%s,%s,%s,%s,%s,'user')",
            (name, email, phone, hashed, wallet_id, 0.00)
        )
        mysql.connection.commit()
        cur.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email'].strip().lower()
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password):
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['role']      = user['role']
            session['wallet_id'] = user['wallet_id']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('admin_dashboard') if user['role']=='admin' else url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# ── Wallet Dashboard ──────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()

    cur.execute(
        "SELECT * FROM transactions WHERE sender_id=%s OR receiver_id=%s "
        "ORDER BY created_at DESC LIMIT 5",
        (session['user_id'], session['user_id'])
    )
    recent_txns = cur.fetchall()
    cur.close()
    return render_template('wallet/dashboard.html', user=user, recent_txns=recent_txns)

# ── Add Money ─────────────────────────────────────────────────
@app.route('/add-money', methods=['GET','POST'])
@login_required
def add_money():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        if amount <= 0:
            flash('Enter a valid amount.', 'danger')
            return redirect(url_for('add_money'))

        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET balance=balance+%s WHERE id=%s", (amount, session['user_id']))
        txn_id = gen_txn_id()
        cur.execute(
            "INSERT INTO transactions (txn_id, sender_id, receiver_id, amount, txn_type, status, note) "
            "VALUES (%s,%s,%s,%s,'credit','success','Wallet top-up')",
            (txn_id, session['user_id'], session['user_id'], amount)
        )
        mysql.connection.commit()
        cur.close()
        flash(f'₹{amount:.2f} added successfully! Txn ID: {txn_id}', 'success')
        return redirect(url_for('dashboard'))
    return render_template('wallet/add_money.html')

# ── Send Money ────────────────────────────────────────────────
@app.route('/send-money', methods=['GET','POST'])
@login_required
def send_money():
    if request.method == 'POST':
        receiver_wallet = request.form['receiver_wallet'].strip().upper()
        amount  = float(request.form['amount'])
        note    = request.form.get('note', 'P2P Transfer')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE wallet_id=%s", (receiver_wallet,))
        receiver = cur.fetchone()

        if not receiver:
            flash('Wallet ID not found.', 'danger')
            cur.close()
            return redirect(url_for('send_money'))
        if receiver['id'] == session['user_id']:
            flash('Cannot send money to yourself.', 'danger')
            cur.close()
            return redirect(url_for('send_money'))

        cur.execute("SELECT balance FROM users WHERE id=%s", (session['user_id'],))
        sender = cur.fetchone()
        if sender['balance'] < amount:
            flash('Insufficient balance.', 'danger')
            cur.close()
            return redirect(url_for('send_money'))

        txn_id = gen_txn_id()
        cur.execute("UPDATE users SET balance=balance-%s WHERE id=%s", (amount, session['user_id']))
        cur.execute("UPDATE users SET balance=balance+%s WHERE id=%s", (amount, receiver['id']))
        cur.execute(
            "INSERT INTO transactions (txn_id, sender_id, receiver_id, amount, txn_type, status, note) "
            "VALUES (%s,%s,%s,%s,'debit','success',%s)",
            (txn_id, session['user_id'], receiver['id'], amount, note)
        )
        mysql.connection.commit()
        cur.close()
        flash(f'₹{amount:.2f} sent to {receiver["name"]}! Txn ID: {txn_id}', 'success')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT balance FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    return render_template('wallet/send_money.html', balance=user['balance'])

# ── Merchant Payment ──────────────────────────────────────────
@app.route('/pay-merchant', methods=['GET','POST'])
@login_required
def pay_merchant():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, merchant_code, category FROM merchants")
    merchants = cur.fetchall()

    if request.method == 'POST':
        merchant_id = int(request.form['merchant_id'])
        amount      = float(request.form['amount'])

        cur.execute("SELECT balance FROM users WHERE id=%s", (session['user_id'],))
        user = cur.fetchone()
        if user['balance'] < amount:
            flash('Insufficient balance.', 'danger')
            cur.close()
            return redirect(url_for('pay_merchant'))

        cur.execute("SELECT * FROM merchants WHERE id=%s", (merchant_id,))
        merchant = cur.fetchone()

        txn_id = gen_txn_id()
        cur.execute("UPDATE users SET balance=balance-%s WHERE id=%s", (amount, session['user_id']))
        cur.execute(
            "INSERT INTO transactions (txn_id, sender_id, receiver_id, amount, txn_type, status, note) "
            "VALUES (%s,%s,NULL,%s,'merchant_pay','success',%s)",
            (txn_id, session['user_id'], amount, f"Payment to {merchant['name']}")
        )
        mysql.connection.commit()
        cur.close()
        flash(f'₹{amount:.2f} paid to {merchant["name"]}! Txn ID: {txn_id}', 'success')
        return redirect(url_for('dashboard'))

    cur.close()
    return render_template('wallet/pay_merchant.html', merchants=merchants)

# ── Transaction History ───────────────────────────────────────
@app.route('/transactions')
@login_required
def transactions():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT t.*, "
        "  s.name AS sender_name, s.wallet_id AS sender_wallet, "
        "  r.name AS receiver_name, r.wallet_id AS receiver_wallet "
        "FROM transactions t "
        "LEFT JOIN users s ON t.sender_id   = s.id "
        "LEFT JOIN users r ON t.receiver_id = r.id "
        "WHERE t.sender_id=%s OR t.receiver_id=%s "
        "ORDER BY t.created_at DESC",
        (session['user_id'], session['user_id'])
    )
    txns = cur.fetchall()
    cur.close()
    return render_template('wallet/transactions.html', txns=txns, uid=session['user_id'])

# ── Complaints ────────────────────────────────────────────────
@app.route('/complaints', methods=['GET','POST'])
@login_required
def complaints():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        subject = request.form['subject'].strip()
        message = request.form['message'].strip()
        cur.execute(
            "INSERT INTO complaints (user_id, subject, message, status) VALUES (%s,%s,%s,'open')",
            (session['user_id'], subject, message)
        )
        mysql.connection.commit()
        flash('Complaint submitted! We will respond within 24 hours.', 'success')

    cur.execute(
        "SELECT * FROM complaints WHERE user_id=%s ORDER BY created_at DESC",
        (session['user_id'],)
    )
    my_complaints = cur.fetchall()
    cur.close()
    return render_template('complaints/complaints.html', complaints=my_complaints)

# ── Admin Dashboard ───────────────────────────────────────────
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM users WHERE role='user'")
    total_users = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM transactions")
    total_txns = cur.fetchone()['total']

    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM transactions WHERE txn_type='credit'")
    total_topup = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM complaints WHERE status='open'")
    open_complaints = cur.fetchone()['total']

    cur.execute("SELECT * FROM users WHERE role='user' ORDER BY created_at DESC LIMIT 10")
    users = cur.fetchall()

    cur.execute(
        "SELECT t.*, s.name AS sender_name FROM transactions t "
        "LEFT JOIN users s ON t.sender_id=s.id ORDER BY t.created_at DESC LIMIT 10"
    )
    recent_txns = cur.fetchall()

    cur.execute(
        "SELECT c.*, u.name AS user_name FROM complaints c "
        "JOIN users u ON c.user_id=u.id ORDER BY c.created_at DESC"
    )
    all_complaints = cur.fetchall()
    cur.close()

    return render_template('admin/dashboard.html',
        total_users=total_users, total_txns=total_txns,
        total_topup=total_topup, open_complaints=open_complaints,
        users=users, recent_txns=recent_txns, all_complaints=all_complaints
    )

@app.route('/admin/resolve-complaint/<int:cid>')
@login_required
@admin_required
def resolve_complaint(cid):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE complaints SET status='resolved' WHERE id=%s", (cid,))
    mysql.connection.commit()
    cur.close()
    flash('Complaint marked as resolved.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
