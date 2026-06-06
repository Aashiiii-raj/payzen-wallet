"""
Run this ONCE to add 10 demo users with balances and transactions.
    python seed_users.py
"""
import MySQLdb
from werkzeug.security import generate_password_hash
import uuid
import random
from datetime import datetime, timedelta

# ── Connect to MySQL ──────────────────────────────────────────
conn = MySQLdb.connect(host='localhost', user='root', passwd='', db='ewp_db')
cur  = conn.cursor()

# ── 10 Demo Users ─────────────────────────────────────────────
users = [
    ('Ravi Kumar',    'ravi@test.com',   '9876543210', 5000.00),
    ('Priya Sharma',  'priya@test.com',  '9123456780', 3500.00),
    ('Amit Singh',    'amit@test.com',   '9988776655', 7200.00),
    ('Neha Gupta',    'neha@test.com',   '9876501234', 1500.00),
    ('Rohit Verma',   'rohit@test.com',  '9765432100', 9000.00),
    ('Sneha Patel',   'sneha@test.com',  '9654321099', 2200.00),
    ('Vikram Rao',    'vikram@test.com', '9543210988', 6800.00),
    ('Anjali Mehta',  'anjali@test.com', '9432109877', 4100.00),
    ('Suresh Nair',   'suresh@test.com', '9321098766', 3300.00),
    ('Kavya Reddy',   'kavya@test.com',  '9210987655', 8500.00),
]

print("\n🚀 Adding demo users...")
wallet_ids = {}

for name, email, phone, balance in users:
    # skip if already exists
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        print(f"   ⚠️  Skipped (already exists): {email}")
        continue

    hashed    = generate_password_hash('test123')
    wallet_id = 'WLT' + uuid.uuid4().hex[:8].upper()
    wallet_ids[email] = {'wallet_id': wallet_id, 'balance': balance}

    cur.execute(
        "INSERT INTO users (name, email, phone, password, wallet_id, balance, role) "
        "VALUES (%s,%s,%s,%s,%s,%s,'user')",
        (name, email, phone, hashed, wallet_id, balance)
    )
    print(f"   ✅ Added: {name} | {wallet_id} | ₹{balance}")

conn.commit()

# ── Add demo transactions ──────────────────────────────────────
print("\n💸 Adding demo transactions...")

# fetch all user ids and wallet ids
cur.execute("SELECT id, name, email, wallet_id FROM users WHERE role='user'")
db_users = cur.fetchall()  # (id, name, email, wallet_id)

def gen_txn_id():
    return 'TXN' + uuid.uuid4().hex[:10].upper()

# Add money (credit) transactions
for uid, name, email, wid in db_users:
    for _ in range(random.randint(1, 3)):
        amount = random.choice([500, 1000, 2000, 5000])
        txn_id = gen_txn_id()
        cur.execute(
            "INSERT INTO transactions (txn_id, sender_id, receiver_id, amount, txn_type, status, note) "
            "VALUES (%s,%s,%s,%s,'credit','success','Wallet top-up')",
            (txn_id, uid, uid, amount)
        )
        print(f"   💰 Top-up ₹{amount} for {name}")

# P2P transfers between random users
if len(db_users) >= 2:
    for _ in range(8):
        sender   = random.choice(db_users)
        receiver = random.choice([u for u in db_users if u[0] != sender[0]])
        amount   = random.choice([100, 200, 500, 1000])
        txn_id   = gen_txn_id()
        note     = random.choice(['Lunch split', 'Rent share', 'Movie tickets', 'Coffee', 'Gift'])
        cur.execute(
            "INSERT INTO transactions (txn_id, sender_id, receiver_id, amount, txn_type, status, note) "
            "VALUES (%s,%s,%s,%s,'debit','success',%s)",
            (txn_id, sender[0], receiver[0], amount, note)
        )
        print(f"   📤 {sender[1]} → {receiver[1]} ₹{amount} ({note})")

# Merchant payments
cur.execute("SELECT id FROM merchants LIMIT 8")
merchant_ids = [row[0] for row in cur.fetchall()]
cur.execute("SELECT id, name FROM merchants LIMIT 8")
merchants_data = cur.fetchall()

if merchants_data:
    for uid, name, email, wid in db_users:
        for _ in range(random.randint(1, 2)):
            m = random.choice(merchants_data)
            amount = random.choice([199, 299, 499, 999, 1499])
            txn_id = gen_txn_id()
            cur.execute(
                "INSERT INTO transactions (txn_id, sender_id, receiver_id, amount, txn_type, status, note) "
                "VALUES (%s,%s,NULL,%s,'merchant_pay','success',%s)",
                (txn_id, uid, amount, f"Payment to {m[1]}")
            )
            print(f"   🏪 {name} paid ₹{amount} to {m[1]}")

# Demo complaints
complaints = [
    ('Transaction Failed',                'My payment of ₹500 failed but money was deducted.'),
    ('Unable to Add Money',               'Getting error while adding money via UPI.'),
    ('Money Deducted But Not Received',   'Sent ₹1000 to friend but they did not receive it.'),
    ('Merchant Payment Issue',            'Netflix payment failed twice today.'),
    ('Account Hacked / Unauthorized Access', 'Noticed unknown transaction of ₹200 in my account.'),
]

print("\n📋 Adding demo complaints...")
for i, (uid, name, email, wid) in enumerate(db_users[:5]):
    subject, message = complaints[i]
    cur.execute(
        "INSERT INTO complaints (user_id, subject, message, status) VALUES (%s,%s,%s,'open')",
        (uid, subject, message)
    )
    print(f"   📝 Complaint from {name}: {subject}")

conn.commit()
cur.close()
conn.close()

print("\n" + "="*50)
print("✅ ALL DONE! Here's what was added:")
print("="*50)
print("👥 10 demo users (password: test123 for all)")
print("💸 Multiple top-up transactions")
print("📤 8 P2P money transfers")
print("🏪 Merchant payments")
print("📋 5 customer complaints")
print("\n🔐 Login with any user:")
print("   Email:    ravi@test.com")
print("   Password: test123")
print("\n🔐 Admin login:")
print("   Email:    admin@ewp.com")
print("   Password: admin123")
print("="*50)
