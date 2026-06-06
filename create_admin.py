"""
Run this script ONCE to insert the admin user with a correct password hash.
    python create_admin.py
"""
from werkzeug.security import generate_password_hash
import MySQLdb

conn = MySQLdb.connect(host='localhost', user='root', passwd='', db='ewp_db')
cur  = conn.cursor()

hashed = generate_password_hash('admin123')

cur.execute("DELETE FROM users WHERE email='admin@ewp.com'")
cur.execute(
    "INSERT INTO users (name, email, phone, password, wallet_id, balance, role) "
    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
    ('Admin', 'admin@ewp.com', '9999999999', hashed, 'WLT-ADMIN-001', 0.00, 'admin')
)
conn.commit()
cur.close()
conn.close()
print("✅ Admin user created: admin@ewp.com / admin123")
