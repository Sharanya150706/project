create database billnova;
use billnova;
create table admin(
admin_id int primary key auto_increment,
username varchar(50) not null unique,
password varchar(255) not null
);
show tables;
select * from admin;
insert into admin(username, password)
values('admin','admin123');
select * from admin;
USE billnova;
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL
);
show tables;
select * from products;
USE billnova;

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(100),
    address VARCHAR(255)
);
select * from customers;
USE billnova;

CREATE TABLE bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    bill_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(10,2) NOT NULL,
    tax DECIMAL(10,2) DEFAULT 0,
    grand_total DECIMAL(10,2) NOT NULL
);
select * from bills;
CREATE TABLE bill_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL
);
select * from bill_items;
CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT,
    total DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
select * from invoices;
USE billnova;
use billnova;
desc products;
desc customers;

ALTER TABLE invoices
ADD COLUMN subtotal DECIMAL(10,2) AFTER quantity,
ADD COLUMN gst DECIMAL(10,2) DEFAULT 0 AFTER subtotal,
ADD COLUMN grand_total DECIMAL(10,2) AFTER gst;
describe invoices;
alter table invoices
add column cgst decimal(10,2) ,
add column sgst decimal(10,2),
add column total_gst decimal(10,2);
desc invoices;
show tables;
USE billnova;

ALTER TABLE products
ADD COLUMN hsn_code VARCHAR(20) AFTER product_name,
ADD COLUMN gst_rate DECIMAL(5,2) DEFAULT 18.00 AFTER price;
desc products;
USE billnova;

ALTER TABLE customers
ADD COLUMN gstin VARCHAR(15) AFTER email;

DESC customers;
USE billnova;

CREATE TABLE company_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    gstin VARCHAR(15),
    address VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(100),
    state VARCHAR(50),
    state_code VARCHAR(10),
    logo VARCHAR(255)
);
desc company_settings;
USE billnova;

CREATE TABLE IF NOT EXISTS company_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    owner_name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    gstin VARCHAR(20),
    state VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DESC company_settings;
USE billnova;

ALTER TABLE company_settings
ADD COLUMN owner_name VARCHAR(100) AFTER company_name,
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER logo;

DESC company_settings;
USE billnova;

ALTER TABLE products
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER quantity;

DESC products;

USE billnova;

-- =====================================================
-- CUSTOMERS: GST + STATE DETAILS
-- =====================================================

ALTER TABLE customers
ADD COLUMN gstin VARCHAR(20) NULL,
ADD COLUMN state VARCHAR(100) NULL,
ADD COLUMN state_code VARCHAR(10) NULL;


-- =====================================================
-- INVOICES: PROFESSIONAL INVOICE DETAILS
-- =====================================================

ALTER TABLE invoices
ADD COLUMN invoice_number VARCHAR(50) NULL,
ADD COLUMN payment_status VARCHAR(30) DEFAULT 'Pending',
ADD COLUMN payment_mode VARCHAR(30) DEFAULT 'Not Selected',
ADD COLUMN due_date DATE NULL,
ADD COLUMN notes TEXT NULL,
ADD COLUMN terms_conditions TEXT NULL;


-- =====================================================
-- COMPANY: OWNER NAME
-- =====================================================

ALTER TABLE company_settings
ADD COLUMN owner_name VARCHAR(255) NULL;


-- =====================================================
-- GENERATE INVOICE NUMBERS FOR OLD INVOICES
-- =====================================================

UPDATE invoices
SET invoice_number =
    CONCAT(
        'INV-',
        YEAR(created_at),
        '-',
        LPAD(id, 4, '0')
    )
WHERE invoice_number IS NULL;


-- =====================================================
-- MAKE INVOICE NUMBER UNIQUE
-- =====================================================

ALTER TABLE invoices
ADD UNIQUE (invoice_number);

SET SQL_SAFE_UPDATES = 0;

UPDATE invoices
SET invoice_number =
    CONCAT('INV-', YEAR(created_at), '-', LPAD(id, 4, '0'))
WHERE invoice_number IS NULL;

SET SQL_SAFE_UPDATES = 1;
select id, invoice_number
from invoices
order by id;

USE billnova;

-- ==========================================
-- BILLNOVA FINAL DATABASE UPDATE
-- ==========================================

-- 1. CUSTOMER DETAILS
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS gstin VARCHAR(30) NULL,
ADD COLUMN IF NOT EXISTS state VARCHAR(100) NULL,
ADD COLUMN IF NOT EXISTS state_code VARCHAR(10) NULL;


-- 2. INVOICE DETAILS
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(50) NULL,
ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) NOT NULL DEFAULT 'Pending',
ADD COLUMN IF NOT EXISTS payment_mode VARCHAR(30) NOT NULL DEFAULT 'Not Selected',
ADD COLUMN IF NOT EXISTS due_date DATE NULL,
ADD COLUMN IF NOT EXISTS notes TEXT NULL,
ADD COLUMN IF NOT EXISTS terms_conditions TEXT NULL;


-- 3. COMPANY DETAILS
ALTER TABLE company_settings
ADD COLUMN if not EXISTS owner_name VARCHAR(150) NULL;


-- 4. OLD INVOICES KE LIYE INVOICE NUMBER GENERATE KARNA
SET SQL_SAFE_UPDATES = 0;

UPDATE invoices
SET invoice_number =
    CONCAT(
        'INV-',
        YEAR(created_at),
        '-',
        LPAD(id, 4, '0')
    )
WHERE invoice_number IS NULL
   OR invoice_number = '';

SET SQL_SAFE_UPDATES = 1;


-- 5. INVOICE NUMBER KO UNIQUE BANANA
ALTER TABLE invoices
ADD UNIQUE INDEX uq_invoices_invoice_number (invoice_number);

use billnova;
desc customers;
desc invoices;
desc company_settings;

alter table customers add column state varchar(100) null;
add column state_code varchar(10) null;

USE billnova;

ALTER TABLE customers ADD COLUMN state VARCHAR(100) NULL;
ALTER TABLE customers ADD COLUMN state_code VARCHAR(10) NULL;

USE billnova;

ALTER TABLE invoices ADD COLUMN challan_no VARCHAR(100) NULL;

ALTER TABLE invoices ADD COLUMN challan_date DATE NULL;

ALTER TABLE invoices ADD COLUMN po_no VARCHAR(100) NULL;

ALTER TABLE invoices ADD COLUMN po_date DATE NULL;

ALTER TABLE invoices ADD COLUMN vehicle_no VARCHAR(50) NULL;

ALTER TABLE invoices ADD COLUMN freight DECIMAL(10,2) DEFAULT 0;

ALTER TABLE invoices ADD COLUMN packing DECIMAL(10,2) DEFAULT 0;

ALTER TABLE invoices ADD COLUMN forwarding DECIMAL(10,2) DEFAULT 0;

ALTER TABLE invoices ADD COLUMN igst DECIMAL(10,2) DEFAULT 0;

ALTER TABLE invoices ADD COLUMN round_off DECIMAL(10,2) DEFAULT 0;

ALTER TABLE company_settings ADD COLUMN bank_name VARCHAR(150) NULL;

ALTER TABLE company_settings ADD COLUMN account_number VARCHAR(100) NULL;

ALTER TABLE company_settings ADD COLUMN ifsc_code VARCHAR(50) NULL;

ALTER TABLE company_settings ADD COLUMN bank_branch VARCHAR(150) NULL;

USE billnova;

CREATE TABLE invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    gst_rate DECIMAL(5,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    cgst DECIMAL(10,2) NOT NULL,
    sgst DECIMAL(10,2) NOT NULL,
    total_gst DECIMAL(10,2) NOT NULL,
    amount DECIMAL(10,2) NOT NULL
);

desc invoice_items ; 	
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
show tables;
desc users;
select id,full_name,email,phone,password,created_at from users;
use billnova;
desc invoices;
alter table users
change password password_hash varchar(255) not null;

USE billnova;

-- Ensure invoice_items table exists
CREATE TABLE IF NOT EXISTS invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10,2) DEFAULT 0.00,
    gst_rate DECIMAL(5,2) DEFAULT 18.00,
    subtotal DECIMAL(10,2) DEFAULT 0.00,
    cgst DECIMAL(10,2) DEFAULT 0.00,
    sgst DECIMAL(10,2) DEFAULT 0.00,
    total_gst DECIMAL(10,2) DEFAULT 0.00,
    amount DECIMAL(10,2) DEFAULT 0.00,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

-- Ensure fallback columns exist in invoices table
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS grand_total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(50);
USE billnova;

-- Add missing columns to existing invoices table
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS grand_total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(50);

USE billnova;

ALTER TABLE invoices ADD COLUMN grand_total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN invoice_number VARCHAR(50);

USE billnova;

-- Ensure all required columns exist in invoices table
ALTER TABLE invoices ADD COLUMN subtotal DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN total_gst DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN gst DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN grand_total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN payment_status VARCHAR(50) DEFAULT 'Paid';
ALTER TABLE invoices ADD COLUMN payment_mode VARCHAR(50) DEFAULT 'Cash';

-- Ensure invoice_items table exists
CREATE TABLE IF NOT EXISTS invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10,2) DEFAULT 0.00,
    gst_rate DECIMAL(5,2) DEFAULT 18.00,
    subtotal DECIMAL(10,2) DEFAULT 0.00,
    total_gst DECIMAL(10,2) DEFAULT 0.00,
    amount DECIMAL(10,2) DEFAULT 0.00,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);


SHOW TABLES;

USE billnova;

-- 1. Ensure invoices table has all essential fields
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(50);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS customer_id INT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS product_id INT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS quantity INT DEFAULT 1;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS subtotal DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total_gst DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS gst DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS grand_total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'Paid';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_mode VARCHAR(50) DEFAULT 'Cash';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;


USE billnova;

ALTER TABLE invoices ADD COLUMN invoice_number VARCHAR(50);
ALTER TABLE invoices ADD COLUMN customer_id INT;
ALTER TABLE invoices ADD COLUMN product_id INT;
ALTER TABLE invoices ADD COLUMN quantity INT DEFAULT 1;
ALTER TABLE invoices ADD COLUMN subtotal DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN total_gst DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN gst DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN grand_total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN total DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE invoices ADD COLUMN payment_status VARCHAR(50) DEFAULT 'Paid';
ALTER TABLE invoices ADD COLUMN payment_mode VARCHAR(50) DEFAULT 'Cash';
DESC INVOICES;
USE billnova;

-- Map all essential tables to user_id
ALTER TABLE invoices ADD COLUMN user_id INT;
ALTER TABLE products ADD COLUMN user_id INT;
ALTER TABLE customers ADD COLUMN user_id INT;
ALTER TABLE company_settings ADD COLUMN user_id INT;


select * from invoices;
USE billnova;

-- Purane products aur customers ko aapke user_id = 1 se bind kar rahe hain
UPDATE products SET user_id = 1 WHERE user_id IS NULL;
UPDATE customers SET user_id = 1 WHERE user_id IS NULL;
UPDATE invoices SET user_id = 1 WHERE user_id IS NULL;

USE billnova;

-- Safe Update mode off karein
SET SQL_SAFE_UPDATES = 0;

-- Data update query
UPDATE products SET user_id = 1 WHERE user_id IS NULL;
UPDATE customers SET user_id = 1 WHERE user_id IS NULL;
UPDATE invoices SET user_id = 1 WHERE user_id IS NULL;

-- Safe Update mode waapas ON karein
SET SQL_SAFE_UPDATES = 1;

USE billnova;

UPDATE products SET user_id = 1 WHERE user_id IS NULL AND id > 0;
UPDATE customers SET user_id = 1 WHERE user_id IS NULL AND id > 0;
UPDATE invoices SET user_id = 1 WHERE user_id IS NULL AND id > 0;

USE billnova;

-- Products table me stock column add kar rahe hain (default value 10)
ALTER TABLE products ADD COLUMN stock INT DEFAULT 10;

USE billnova;

CREATE TABLE IF NOT EXISTS purchases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    supplier_name VARCHAR(255) NOT NULL,
    purchase_invoice_no VARCHAR(100),
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    purchase_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
USE billnova;

CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    supplier_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(100),
    gstin VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
ALTER TABLE company_settings 
ADD COLUMN IF NOT EXISTS pincode VARCHAR(10),
ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS account_no VARCHAR(50),
ADD COLUMN IF NOT EXISTS ifsc_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS branch_name VARCHAR(150);

ALTER TABLE company_settings 
ADD COLUMN pincode VARCHAR(10),
ADD COLUMN bank_name VARCHAR(100),
ADD COLUMN account_no VARCHAR(50),
ADD COLUMN ifsc_code VARCHAR(20),
ADD COLUMN branch_name VARCHAR(150);

ALTER TABLE company_settings ADD COLUMN pincode VARCHAR(10);
ALTER TABLE company_settings ADD COLUMN bank_name VARCHAR(100);
ALTER TABLE company_settings ADD COLUMN account_no VARCHAR(50);
ALTER TABLE company_settings ADD COLUMN ifsc_code VARCHAR(20);
ALTER TABLE company_settings ADD COLUMN branch_name VARCHAR(150);

ALTER TABLE company_settings ADD COLUMN pincode VARCHAR(10);
ALTER TABLE company_settings ADD COLUMN bank_name VARCHAR(100);
ALTER TABLE company_settings ADD COLUMN account_no VARCHAR(50);
ALTER TABLE company_settings ADD COLUMN ifsc_code VARCHAR(20);
ALTER TABLE company_settings ADD COLUMN branch_name VARCHAR(150);

CREATE TABLE IF NOT EXISTS invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    rate DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

ALTER TABLE invoices 
ADD COLUMN invoice_date DATE,
ADD COLUMN reverse_charge VARCHAR(10) DEFAULT 'No',
ADD COLUMN transport_mode VARCHAR(50),
ADD COLUMN eway_bill_no VARCHAR(50),
ADD COLUMN discount_percent DECIMAL(5, 2) DEFAULT 0.00;

ALTER TABLE invoices ADD COLUMN state_code VARCHAR(10) DEFAULT '27';
ALTER TABLE invoices ADD COLUMN invoice_date DATE;
ALTER TABLE invoices ADD COLUMN due_date DATE;
ALTER TABLE invoices ADD COLUMN challan_no VARCHAR(50);
ALTER TABLE invoices ADD COLUMN po_no VARCHAR(50);
ALTER TABLE invoices ADD COLUMN vehicle_no VARCHAR(50);
ALTER TABLE invoices ADD COLUMN transport_mode VARCHAR(50);
ALTER TABLE invoices ADD COLUMN eway_bill_no VARCHAR(50);
ALTER TABLE invoices ADD COLUMN reverse_charge VARCHAR(10) DEFAULT 'No';
ALTER TABLE invoices ADD COLUMN discount_percent DECIMAL(5, 2) DEFAULT 0.00;

-- 1. Invoices Table Columns Update
ALTER TABLE invoices ADD COLUMN state_code VARCHAR(10) DEFAULT '27';
ALTER TABLE invoices ADD COLUMN invoice_date DATE;
ALTER TABLE invoices ADD COLUMN due_date DATE;
ALTER TABLE invoices ADD COLUMN challan_no VARCHAR(50);
ALTER TABLE invoices ADD COLUMN po_no VARCHAR(50);
ALTER TABLE invoices ADD COLUMN vehicle_no VARCHAR(50);
ALTER TABLE invoices ADD COLUMN transport_mode VARCHAR(50);
ALTER TABLE invoices ADD COLUMN eway_bill_no VARCHAR(50);
ALTER TABLE invoices ADD COLUMN reverse_charge VARCHAR(10) DEFAULT 'No';
ALTER TABLE invoices ADD COLUMN discount_percent DECIMAL(5, 2) DEFAULT 0.00;

-- 2. Invoice Items Table Columns Update
ALTER TABLE invoice_items ADD COLUMN rate DECIMAL(10, 2) DEFAULT 0.00;
ALTER TABLE invoice_items ADD COLUMN amount DECIMAL(10, 2) DEFAULT 0.00;
ALTER TABLE invoices MODIFY COLUMN price DECIMAL(10, 2) DEFAULT 0.00;

ALTER TABLE invoices ADD COLUMN price DECIMAL(10, 2) DEFAULT 0.00;
ALTER TABLE invoices MODIFY COLUMN price DECIMAL(10, 2) DEFAULT 0.00;

ALTER TABLE invoices 
MODIFY COLUMN price DECIMAL(10, 2) DEFAULT 0.00,
MODIFY COLUMN product_id INT NULL,
MODIFY COLUMN quantity INT DEFAULT 1;
ALTER TABLE invoices MODIFY price DECIMAL(10, 2) NULL DEFAULT 0.00;


ALTER TABLE invoices MODIFY COLUMN product_id INT NULL, MODIFY COLUMN quantity INT NULL;

ALTER TABLE invoices 
MODIFY COLUMN price DECIMAL(10, 2) NULL DEFAULT 0.00,
MODIFY COLUMN product_id INT NULL,
MODIFY COLUMN quantity INT DEFAULT 1;
USE billnova ; -- Apne DB ka naam rakhein

ALTER TABLE invoices MODIFY price DECIMAL(10, 2) DEFAULT 0.00;
ALTER TABLE invoices MODIFY product_id INT NULL;
ALTER TABLE invoices MODIFY quantity INT DEFAULT 1;

ALTER TABLE invoices MODIFY price DECIMAL(10, 2) DEFAULT 0.00;
ALTER TABLE invoices MODIFY product_id INT NULL;
ALTER TABLE invoices MODIFY quantity INT DEFAULT 1;

USE billnova; -- Apne exact database ka naam likhein

ALTER TABLE invoice_details MODIFY COLUMN price DECIMAL(10, 2) NULL DEFAULT 0.00;
ALTER TABLE invoices MODIFY COLUMN product_id INT NULL;
ALTER TABLE invoices MODIFY COLUMN quantity INT NULL DEFAULT ;

USE billnova_db; -- Apne database ka naam likhein

-- 1. Master Table Columns ko flexible banayein taaki summary total properly save ho
ALTER TABLE invoices MODIFY COLUMN price DECIMAL(10, 2) NULL DEFAULT 0.00;
ALTER TABLE invoices MODIFY COLUMN product_id INT NULL;
ALTER TABLE invoices MODIFY COLUMN quantity INT NULL DEFAULT 1;

-- 2. Verify karein ki invoice_items table exist karti hai
CREATE TABLE IF NOT EXISTS invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    rate DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
USE billnova_db; -- Ya jo bhi aapke database ka naam hai

ALTER TABLE invoices MODIFY COLUMN price DECIMAL(10, 2) NULL DEFAULT 0.00;
ALTER TABLE invoices MODIFY COLUMN product_id INT NULL;
ALTER TABLE invoices MODIFY COLUMN quantity INT NULL DEFAULT 1;

USE billnova; -- Apne DB ka naam yahan likhein

-- Invoices table ke columns ki strictness ko flexible banayein
ALTER TABLE invoices MODIFY COLUMN price DECIMAL(10, 2) NULL DEFAULT 0.00;
ALTER TABLE invoices MODIFY COLUMN product_id INT NULL;
ALTER TABLE invoices MODIFY COLUMN quantity INT NULL DEFAULT 1;

desc users;
select * from users;

USE defaultdb;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);