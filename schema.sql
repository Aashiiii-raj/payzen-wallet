-- ============================================================
-- EWP - Ericsson Wallet Platform  |  Database Schema
-- Run this in your MySQL client: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS ewp_db;
USE ewp_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)   NOT NULL,
    email       VARCHAR(150)   UNIQUE NOT NULL,
    phone       VARCHAR(15)    NOT NULL,
    password    VARCHAR(255)   NOT NULL,
    wallet_id   VARCHAR(20)    UNIQUE NOT NULL,
    balance     DECIMAL(12,2)  DEFAULT 0.00,
    role        ENUM('user','admin') DEFAULT 'user',
    created_at  DATETIME       DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    txn_id      VARCHAR(20)    UNIQUE NOT NULL,
    sender_id   INT,
    receiver_id INT,
    amount      DECIMAL(12,2)  NOT NULL,
    txn_type    ENUM('credit','debit','merchant_pay') NOT NULL,
    status      ENUM('success','failed','pending')    DEFAULT 'pending',
    note        VARCHAR(255),
    created_at  DATETIME       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id)   REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Merchants table
CREATE TABLE IF NOT EXISTS merchants (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    merchant_code VARCHAR(20)  UNIQUE NOT NULL,
    category      VARCHAR(50),
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- Complaints table
CREATE TABLE IF NOT EXISTS complaints (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    subject    VARCHAR(200) NOT NULL,
    message    TEXT         NOT NULL,
    status     ENUM('open','in_progress','resolved') DEFAULT 'open',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── Seed: Admin user (password = admin123) ─────────────────────
INSERT INTO users (name, email, phone, password, wallet_id, balance, role) VALUES
('Admin', 'admin@ewp.com', '9999999999',
 'pbkdf2:sha256:600000$abc$placeholder_replace_with_real_hash',
 'WLT-ADMIN-001', 0.00, 'admin');

-- NOTE: Use the script below to generate a real hash and update the admin password.

-- ── Seed: Demo merchants ───────────────────────────────────────
INSERT INTO merchants (name, merchant_code, category) VALUES
('Amazon India',       'AMZN001', 'E-Commerce'),
('Swiggy',             'SWGY001', 'Food Delivery'),
('Netflix India',      'NFLX001', 'Entertainment'),
('IRCTC',              'IRCTC01', 'Travel'),
('BookMyShow',         'BMS001',  'Entertainment'),
('Reliance Digital',   'RLNC001', 'Electronics'),
('Zomato',             'ZMTO001', 'Food Delivery'),
('BigBasket',          'BGBK001', 'Grocery');
