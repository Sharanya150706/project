from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# =========================================================
# FLASK APP CONFIGURATION
# =========================================================

app = Flask(__name__)
app.secret_key = "billnova_secret_key"
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Folder automatically create karne ke liye
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# DATABASE CONFIGURATION (MYSQL WORKBENCH)
# =========================================================

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("MYSQLHOST", "127.0.0.1"),
        user=os.getenv("MYSQLUSER", "root"),
        password=os.getenv("MYSQLPASSWORD", "root123"),
        database=os.getenv("MYSQLDATABASE", "billnova"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        ssl_disabled=False
    )
    # Strict mode ko session level par disable karne ke liye line add ki hai
    cursor = conn.cursor()
    cursor.execute("SET SESSION sql_mode=''")
    cursor.close()

    return conn


# =========================================================
# UPLOAD CONFIGURATION
# =========================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "uploads",
    "logos"
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_decimal(value, default=Decimal("0.00")):
    try:
        if value is None or value == "":
            return default
        return Decimal(str(value))
    except Exception:
        return default


def money(value):
    value = get_decimal(value)
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# =========================================================
# NUMBER TO WORDS CONVERTER
# =========================================================

def number_to_words(number):
    number = int(Decimal(str(number)))

    if number == 0:
        return "Zero Rupees Only"

    ones = [
        "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"
    ]

    tens = [
        "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
    ]

    def two_digit(n):
        if n < 20:
            return ones[n]
        return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")

    def three_digit(n):
        if n < 100:
            return two_digit(n)
        return ones[n // 100] + " Hundred" + (" " + two_digit(n % 100) if n % 100 else "")

    result = []
    crore = number // 10000000
    number %= 10000000

    lakh = number // 100000
    number %= 100000

    thousand = number // 1000
    number %= 1000

    hundred = number

    if crore:
        result.append(three_digit(crore) + " Crore")
    if lakh:
        result.append(three_digit(lakh) + " Lakh")
    if thousand:
        result.append(three_digit(thousand) + " Thousand")
    if hundred:
        result.append(three_digit(hundred))

    return " ".join(result) + " Rupees Only"


# =========================================================
# AUTHENTICATION & HOME
# =========================================================

@app.route("/")
def home():
    return render_template("welcome.html")


# =========================================================
# REGISTRATION WITH VALIDATION
# =========================================================

import re

# Email Format Regex Pattern
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # 1. Empty Check
        if not full_name or not email or not phone or not password or not confirm_password:
            flash("Please enter valid details!", "error")
            return redirect(url_for("register"))

        # 2. Strict Email Validation (Regex)
        if not re.match(EMAIL_REGEX, email):
            flash("please enter valid email(e.g. user@domain.com)!", "error")
            return redirect(url_for("register"))

        # 3. Mobile Number Check (10 digits)
        if not phone.isdigit() or len(phone) != 10:
            flash("Mobile number must be of 10 digits!", "error")
            return redirect(url_for("register"))

        # 4. Password Length & Match
        if len(password) < 6:
            flash("Password must be of 6 characters!", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords doesnot matched!", "error")
            return redirect(url_for("register"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # 5. Database Duplicate Email Check
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = %s", (email,))
            if cursor.fetchone():
                flash("Email already registered, please enter new one", "error")
                return redirect(url_for("register"))

            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (full_name, email, phone, password_hash) VALUES (%s, %s, %s, %s)",
                (full_name, email, phone, password_hash)
            )
            conn.commit()
            flash("Account created successfully, please login.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            conn.rollback()
            flash(f"Registration Error: {str(e)}", "error")
            return redirect(url_for("register"))
        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")


# =========================================================
# LOGIN WITH VALIDATION & LOGOUT
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email aur Password both must to be filled!", "error")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("dashboard"))

        flash("Wrong email or password, try again please", "error")
        return redirect(url_for("login"))
    

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Successfully logout.", "info")
    return redirect(url_for("login"))
# =========================================================
# PRODUCTS MANAGEMENT
# =========================================================
@app.route("/products", methods=["GET", "POST"])
def products():
    if "user_id" not in session:
        flash("Please login to access products.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        hsn_code = request.form.get("hsn_code", "").strip()
        price = request.form.get("price", "0")
        gst_rate = request.form.get("gst_rate", "18")

        if product_name:
            cursor.execute("""
                INSERT INTO products (product_name, hsn_code, price, gst_rate, user_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (product_name, hsn_code, price, gst_rate, user_id))
            conn.commit()
            flash("Product added successfully!", "success")
            return redirect(url_for("products"))

    cursor.execute("SELECT * FROM products WHERE user_id = %s ORDER BY id DESC", (user_id,))
    product_list = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("products.html", products=product_list)


@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        product_name = request.form.get("product_name")
        hsn_code = request.form.get("hsn_code")
        price = get_decimal(request.form.get("price"))
        gst_rate = get_decimal(request.form.get("gst_rate"))
        quantity = int(request.form.get("quantity") or 0)

        cursor.execute(
            """
            UPDATE products
            SET product_name = %s, hsn_code = %s, price = %s, gst_rate = %s, quantity = %s
            WHERE id = %s
            """,
            (product_name, hsn_code, price, gst_rate, quantity, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Product updated successfully!", "success")
        return redirect(url_for("products"))

    cursor.execute("SELECT * FROM products WHERE id = %s", (id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        flash("Product not found!", "error")
        return redirect(url_for("products"))

    return render_template("edit_product.html", product=product)


@app.route("/delete_product/<int:id>", methods=["POST"])
def delete_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Product deleted successfully!", "success")
    return redirect(url_for("products"))


# =========================================================
# CUSTOMERS MANAGEMENT
# =========================================================

import re

# =========================================================
# CUSTOMERS MANAGEMENT (WITH FORM VALIDATION & DUES TRACKING)
# =========================================================
import re

# =========================================================
# CUSTOMERS MANAGEMENT (WITH FORM VALIDATION & DUES TRACKING)
# =========================================================
import re

@app.route("/customers", methods=["GET", "POST"])
def customers():
    if "user_id" not in session:
        flash("Please login to access customers.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == "POST":
            customer_name = request.form.get("customer_name", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            gstin = request.form.get("gstin", "").strip().upper()
            address = request.form.get("address", "").strip()

            # Backend Validation 1: Customer Name
            if not customer_name or len(customer_name) < 2:
                flash("Validation Error: Customer Name must be at least 2 characters.", "error")
                return redirect(url_for("customers"))

            # Backend Validation 2: Phone Number (10 digits)
            if phone and not re.match(r"^\d{10}$", phone):
                flash("Validation Error: Phone Number must be exactly 10 digits.", "error")
                return redirect(url_for("customers"))

            # Backend Validation 3: Email Address
            if email and not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
                flash("Validation Error: Invalid Email Address format.", "error")
                return redirect(url_for("customers"))

            # Backend Validation 4: GSTIN Format
            if gstin and not re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", gstin):
                flash("Validation Error: Invalid 15-character GSTIN format.", "error")
                return redirect(url_for("customers"))

            cursor.execute("""
                INSERT INTO customers (user_id, customer_name, phone, email, gstin, address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, customer_name, phone, email, gstin, address))

            conn.commit()
            flash("Customer account created & validated successfully! ✅", "success")
            return redirect(url_for("customers"))

        cursor.execute("""
            SELECT c.*, 
                   COALESCE(SUM(CASE WHEN i.payment_status = 'Pending' THEN i.grand_total ELSE 0 END), 0) as pending_due,
                   COALESCE(SUM(i.grand_total), 0) as total_business
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id AND i.user_id = %s
            WHERE c.user_id = %s
            GROUP BY c.id
            ORDER BY c.id DESC
        """, (user_id, user_id))
        customer_list = cursor.fetchall()

        return render_template("customers.html", customers=customer_list)

    except Exception as e:
        if conn: conn.rollback()
        flash(f"Customer route error: {str(e)}", "error")
        return redirect(url_for("dashboard"))
    finally:
        if cursor is not None: cursor.close()
        if conn is not None: conn.close()
@app.route("/delete_customer/<int:id>", methods=["POST"])
def delete_customer(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Customer deleted successfully!", "success")
    return redirect(url_for("customers"))


# =========================================================
# INVOICES DIRECTORY ROUTE
# =========================================================

# 1. Main Invoices Directory Route
@app.route("/invoices")
def invoices():
    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT i.*, c.customer_name 
        FROM invoices i 
        LEFT JOIN customers c ON i.customer_id = c.id 
        WHERE i.user_id = %s 
        ORDER BY i.id DESC
    """, (user_id,))
    invoices_list = cursor.fetchall()

    cursor.execute("SELECT * FROM customers WHERE user_id = %s", (user_id,))
    customers_list = cursor.fetchall()

    cursor.execute("SELECT * FROM products WHERE user_id = %s", (user_id,))
    products_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("invoices.html", invoices=invoices_list, customers=customers_list, products=products_list)


# 2. Multi-Item Create Invoice POST Route
@app.route("/invoices/create", methods=["POST"])
def create_invoice():
    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    customer_id = request.form.get("customer_id")
    invoice_date = request.form.get("invoice_date") or datetime.now().strftime('%Y-%m-%d')
    due_date = request.form.get("due_date")
    challan_no = request.form.get("challan_no", "").strip()
    po_no = request.form.get("po_no", "").strip()
    vehicle_no = request.form.get("vehicle_no", "").strip()
    state_code = request.form.get("state_code", "27").strip()
    transport_mode = request.form.get("transport_mode", "").strip()
    eway_bill_no = request.form.get("eway_bill_no", "").strip()
    reverse_charge = request.form.get("reverse_charge", "No").strip()

    product_ids = request.form.getlist("product_id[]")
    quantities = request.form.getlist("quantity[]")
    prices = request.form.getlist("price[]")

    if not customer_id or not product_ids:
        flash("Customer and at least one product are required!", "error")
        return redirect(url_for("invoices"))

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        total_subtotal = 0.0
        items_to_process = []
        first_product_id = None
        first_quantity = 1

        # Calculate line items subtotal & validate products
        for idx, (pid, qty_str) in enumerate(zip(product_ids, quantities)):
            if not pid:
                continue
            qty = int(qty_str) if qty_str and int(qty_str) > 0 else 1

            if idx == 0:
                first_product_id = pid
                first_quantity = qty

            cursor.execute("SELECT * FROM products WHERE id = %s AND user_id = %s", (pid, user_id))
            product = cursor.fetchone()

            if not product:
                flash("Product not found.", "error")
                return redirect(url_for("invoices"))

            rate_val = prices[idx] if idx < len(prices) and prices[idx] else product["price"]
            try:
                rate = float(rate_val)
            except (ValueError, TypeError):
                rate = float(product["price"])

            item_amount = rate * qty
            total_subtotal += item_amount
            items_to_process.append({
                "product_id": pid,
                "quantity": qty,
                "rate": rate,
                "amount": item_amount
            })

        if not items_to_process:
            flash("Please select valid product items.", "error")
            return redirect(url_for("invoices"))

        # Tax calculations
        cgst = total_subtotal * 0.09
        sgst = total_subtotal * 0.09
        grand_total = total_subtotal + cgst + sgst

        # --- SEQUENTIAL INVOICE NUMBER GENERATION (INV-2026-0024) ---
        cursor.execute(
            "SELECT invoice_number FROM invoices WHERE user_id = %s ORDER BY id DESC LIMIT 1", 
            (user_id,)
        )
        last_invoice = cursor.fetchone()

        current_year = datetime.now().strftime('%Y')
        next_number = 1

        if last_invoice and last_invoice.get("invoice_number"):
            parts = last_invoice["invoice_number"].split("-")
            if len(parts) >= 3 and parts[-1].isdigit():
                next_number = int(parts[-1]) + 1

        invoice_number = f"INV-{current_year}-{next_number:04d}"

        # MySQL Strict Mode safe conversions
        safe_price = float(total_subtotal) if total_subtotal is not None else 0.00
        safe_product_id = int(first_product_id) if first_product_id else 1
        safe_quantity = int(first_quantity) if first_quantity else 1

        # Insert into Invoices
        cursor.execute("""
            INSERT INTO invoices (
                user_id, customer_id, product_id, quantity, price, invoice_number, invoice_date, due_date, 
                subtotal, cgst, sgst, grand_total, challan_no, po_no, vehicle_no, state_code, 
                transport_mode, eway_bill_no, reverse_charge, payment_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
        """, (
            user_id, customer_id, safe_product_id, safe_quantity, safe_price, invoice_number, invoice_date, due_date,
            total_subtotal, cgst, sgst, grand_total, challan_no, po_no, vehicle_no, state_code,
            transport_mode, eway_bill_no, reverse_charge
        ))
        
        invoice_id = cursor.lastrowid

        # Insert Line Items & Deduct Stock
        for item in items_to_process:
            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, quantity, rate, amount)
                VALUES (%s, %s, %s, %s, %s)
            """, (invoice_id, item["product_id"], item["quantity"], item["rate"], item["amount"]))

            cursor.execute("""
                UPDATE products 
                SET stock = stock - %s 
                WHERE id = %s AND user_id = %s
            """, (item["quantity"], item["product_id"], user_id))

        conn.commit()
        flash(f"Invoice {invoice_number} created successfully! ✅", "success")
        return redirect(url_for("invoices"))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error creating invoice: {str(e)}", "error")
        return redirect(url_for("invoices"))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
# =========================================================
# VIEW INVOICE PDF / PRINT ROUTE
# =========================================================
@app.route("/invoices/<int:id>")
def view_invoice(id):
    if "user_id" not in session:
        flash("Please login to view invoice.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT i.*, c.customer_name, c.phone as cust_phone, c.email as cust_email, c.gstin as cust_gstin, c.address as cust_address
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.id = %s AND i.user_id = %s
        """, (id, user_id))
        invoice = cursor.fetchone()

        if not invoice:
            flash("Invoice not found.", "error")
            return redirect(url_for("invoices"))

        # Fetch All Line Items for this Invoice
        cursor.execute("""
            SELECT ii.*, p.product_name, p.hsn_code 
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            WHERE ii.invoice_id = %s
        """, (id,))
        items = cursor.fetchall()

        cursor.execute("SELECT * FROM company_settings WHERE user_id = %s", (user_id,))
        company = cursor.fetchone()

        return render_template("view_invoices.html", invoice=invoice, items=items, company=company)

    except Exception as e:
        flash(f"Error loading invoice: {str(e)}", "error")
        return redirect(url_for("invoices"))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# =========================================================
# MARK INVOICE PAID ROUTE
# =========================================================
@app.route("/invoices/paid/<int:invoice_id>", methods=["POST"])
def mark_invoice_paid(invoice_id):
    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE invoices SET payment_status = 'Paid' 
            WHERE id = %s AND user_id = %s
        """, (invoice_id, user_id))
        conn.commit()
        flash("Invoice marked as Paid successfully! ✅", "success")
    except Exception as e:
        if conn: conn.rollback()
        flash(f"Error updating status: {str(e)}", "error")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return redirect(url_for("invoices"))


# =========================================================
# DELETE INVOICE ROUTE
# =========================================================
@app.route("/invoices/delete/<int:id>", methods=["POST", "GET"])
def delete_invoice(id):
    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices WHERE id = %s AND user_id = %s", (id, user_id))
        conn.commit()
        flash("Invoice deleted successfully! 🗑️", "success")
    except Exception as e:
        if conn: conn.rollback()
        flash(f"Error deleting invoice: {str(e)}", "error")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return redirect(url_for("invoices"))

# =========================================================
# COMPANY SETTINGS
# =========================================================

@app.route("/company-settings", methods=["GET", "POST"])
@app.route("/company_settings", methods=["GET", "POST"])
def company_settings():
    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == "POST":
            company_name = request.form.get("company_name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            gstin = request.form.get("gstin", "").strip().upper()
            address = request.form.get("address", "").strip()
            pincode = request.form.get("pincode", "").strip()
            state_code = request.form.get("state_code", "27").strip()
            
            # Bank Details
            bank_name = request.form.get("bank_name", "").strip()
            account_no = request.form.get("account_no", "").strip()
            ifsc_code = request.form.get("ifsc_code", "").strip().upper()
            branch_name = request.form.get("branch_name", "").strip()

            if not company_name:
                flash("Company Name is required!", "error")
                return redirect(url_for("company_settings"))

            cursor.execute("SELECT * FROM company_settings WHERE user_id = %s", (user_id,))
            existing_company = cursor.fetchone()

            logo_filename = existing_company["logo"] if existing_company and existing_company.get("logo") else None

            # Logo Upload Handling
            if "logo" in request.files:
                file = request.files["logo"]
                if file and file.filename != "":
                    if allowed_file(file.filename):
                        filename = secure_filename(f"logo_user_{user_id}_{file.filename}")
                        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                        file.save(filepath)
                        logo_filename = filename
                    else:
                        flash("Invalid file format! Allowed: PNG, JPG, JPEG, WEBP", "error")
                        return redirect(url_for("company_settings"))

            if existing_company:
                cursor.execute("""
                    UPDATE company_settings 
                    SET company_name = %s, email = %s, phone = %s, gstin = %s, address = %s, 
                        pincode = %s, state_code = %s, logo = %s, bank_name = %s, account_no = %s, ifsc_code = %s, branch_name = %s
                    WHERE user_id = %s
                """, (company_name, email, phone, gstin, address, pincode, state_code, logo_filename, bank_name, account_no, ifsc_code, branch_name, user_id))
            else:
                cursor.execute("""
                    INSERT INTO company_settings (user_id, company_name, email, phone, gstin, address, pincode, state_code, logo, bank_name, account_no, ifsc_code, branch_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, company_name, email, phone, gstin, address, pincode, state_code, logo_filename, bank_name, account_no, ifsc_code, branch_name))

            conn.commit()
            flash("Company Settings saved successfully! ✅", "success")
            return redirect(url_for("company_settings"))

        # GET Request
        cursor.execute("SELECT * FROM company_settings WHERE user_id = %s", (user_id,))
        company = cursor.fetchone()
        return render_template("company_settings.html", company=company)

    except Exception as e:
        if conn: conn.rollback()
        flash(f"Error saving settings: {str(e)}", "error")
        return redirect(url_for("company_settings"))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
# =========================================================
# REPORTS & DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login to access dashboard.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # User details fetch
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        # Stats calculations
        cursor.execute("SELECT COUNT(*) as total FROM invoices WHERE user_id = %s", (user_id,))
        total_invoices = cursor.fetchone()["total"]

        cursor.execute("SELECT COALESCE(SUM(grand_total), 0) as total FROM invoices WHERE user_id = %s", (user_id,))
        total_revenue = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM products WHERE user_id = %s", (user_id,))
        total_products = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM customers WHERE user_id = %s", (user_id,))
        total_customers = cursor.fetchone()["total"]

        # Recent invoices fetch
        cursor.execute("""
            SELECT i.*, c.customer_name 
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.user_id = %s
            ORDER BY i.id DESC LIMIT 5
        """, (user_id,))
        recent_invoices = cursor.fetchall()

        # Safe Low stock products fetch
        low_stock_products = []
        try:
            cursor.execute("""
                SELECT * FROM products 
                WHERE user_id = %s AND stock < 5 
                ORDER BY stock ASC LIMIT 5
            """, (user_id,))
            low_stock_products = cursor.fetchall()
        except Exception:
            low_stock_products = []

        chart_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        chart_data = [0, 0, 0, 0, 0, 0]

        cursor.close()
        conn.close()

        return render_template(
            "dashboard.html",
            user=user,
            total_revenue=total_revenue,
            total_invoices=total_invoices,
            total_products=total_products,
            total_customers=total_customers,
            recent_invoices=recent_invoices,
            low_stock_products=low_stock_products,
            chart_labels=chart_labels,
            chart_data=chart_data
        )

    except Exception as e:
        if cursor: cursor.close()
        if conn: conn.close()
        flash(f"Dashboard error: {str(e)}", "error")
        return redirect(url_for("login"))


# =========================================================
# REPORTS ROUTE WITH MONTHLY GRAPH DATA
# =========================================================
# =========================================================
# REPORTS ROUTE WITH PROFIT & LOSS (P&L) CALCULATIONS
# =========================================================
# =========================================================
# REPORTS & P&L TRACKER ROUTE
# =========================================================
@app.route("/reports")
def reports():
    if "user_id" not in session:
        flash("Please login to view reports.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Sales Summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bills,
                COALESCE(SUM(subtotal), 0) as total_taxable,
                COALESCE(SUM(total_gst), 0) as total_gst,
                COALESCE(SUM(grand_total), 0) as total_grand
            FROM invoices WHERE user_id = %s
        """, (user_id,))
        summary = cursor.fetchone()

        # Purchases Summary (Total Inventory Expense)
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total_purchase_cost 
            FROM purchases WHERE user_id = %s
        """, (user_id,))
        purchase_summary = cursor.fetchone()
        total_purchase = float(purchase_summary["total_purchase_cost"] or 0.0)

        # Profit & Loss Calculation
        total_sales = float(summary["total_grand"] or 0.0)
        net_profit = total_sales - total_purchase

        # Monthly Breakdown
        cursor.execute("""
            SELECT 
                DATE_FORMAT(created_at, '%b %Y') as month_name,
                COUNT(*) as bill_count,
                COALESCE(SUM(grand_total), 0) as monthly_total
            FROM invoices WHERE user_id = %s
            GROUP BY DATE_FORMAT(created_at, '%Y-%m'), DATE_FORMAT(created_at, '%b %Y')
            ORDER BY MIN(created_at) ASC
        """, (user_id,))
        monthly_reports = cursor.fetchall()

        chart_labels = [r["month_name"] for r in monthly_reports] or ["Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026", "May 2026", "Jun 2026"]
        chart_data = [float(r["monthly_total"]) for r in monthly_reports] or [0, 0, 0, 0, 0, 0]

        cursor.close()
        conn.close()

        return render_template(
            "reports.html", 
            summary=summary, 
            total_purchase=total_purchase,
            net_profit=net_profit,
            monthly_reports=monthly_reports,
            chart_labels=chart_labels,
            chart_data=chart_data
        )
    except Exception as e:
        if cursor: cursor.close()
        if conn: conn.close()
        flash(f"Reports error: {str(e)}", "error")
        return redirect(url_for("dashboard"))
# =========================================================
# PURCHASES MANAGEMENT ROUTE (WITH AUTO-STOCK ADDITION)
# =========================================================
@app.route("/purchases", methods=["GET", "POST"])
def purchases():
    if "user_id" not in session:
        flash("Please login to access purchases.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        try:
            supplier_name = request.form.get("supplier_name", "").strip()
            purchase_invoice_no = request.form.get("purchase_invoice_no", "").strip()
            product_id = request.form.get("product_id")
            quantity = int(request.form.get("quantity") or 1)
            purchase_price = float(request.form.get("purchase_price") or 0.0)
            total_amount = round(quantity * purchase_price, 2)

            # 1. Insert Purchase Entry
            cursor.execute("""
                INSERT INTO purchases 
                (user_id, supplier_name, purchase_invoice_no, product_id, quantity, purchase_price, total_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, supplier_name, purchase_invoice_no, product_id, quantity, purchase_price, total_amount))

            # 2. Auto-increase Product Stock (+)
            cursor.execute("""
                UPDATE products 
                SET stock = stock + %s 
                WHERE id = %s AND user_id = %s
            """, (quantity, product_id, user_id))

            conn.commit()
            flash("Purchase record saved and stock increased successfully!", "success")
            return redirect(url_for("purchases"))

        except Exception as e:
            conn.rollback()
            flash(f"Error recording purchase: {str(e)}", "error")
            return redirect(url_for("purchases"))
        finally:
            cursor.close()
            conn.close()

    # GET Request: Fetch Purchases & Products
    cursor.execute("""
        SELECT pur.*, p.product_name 
        FROM purchases pur
        LEFT JOIN products p ON pur.product_id = p.id
        WHERE pur.user_id = %s
        ORDER BY pur.id DESC
    """, (user_id,))
    purchase_list = cursor.fetchall()

    cursor.execute("SELECT * FROM products WHERE user_id = %s ORDER BY id DESC", (user_id,))
    product_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("purchases.html", purchases=purchase_list, products=product_list)
# =========================================================
# SUPPLIERS MANAGEMENT ROUTE
# =========================================================
@app.route("/suppliers", methods=["GET", "POST"])
def suppliers():
    if "user_id" not in session:
        flash("Please login to access suppliers.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        try:
            supplier_name = request.form.get("supplier_name", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            gstin = request.form.get("gstin", "").strip()
            address = request.form.get("address", "").strip()

            cursor.execute("""
                INSERT INTO suppliers (user_id, supplier_name, phone, email, gstin, address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, supplier_name, phone, email, gstin, address))

            conn.commit()
            flash("Supplier registered successfully!", "success")
            return redirect(url_for("suppliers"))

        except Exception as e:
            conn.rollback()
            flash(f"Error adding supplier: {str(e)}", "error")
            return redirect(url_for("suppliers"))
        finally:
            cursor.close()
            conn.close()

    cursor.execute("SELECT * FROM suppliers WHERE user_id = %s ORDER BY id DESC", (user_id,))
    supplier_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("suppliers.html", suppliers=supplier_list)
# =========================================================
# PRODUCT STOCK LEDGER & TRANSACTION HISTORY ROUTE
# =========================================================
@app.route("/products/<int:product_id>/history")
def product_history(product_id):
    if "user_id" not in session:
        flash("Please login to view stock ledger.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch Product Details
        cursor.execute("SELECT * FROM products WHERE id = %s AND user_id = %s", (product_id, user_id))
        product = cursor.fetchone()

        if not product:
            flash("Product not found.", "error")
            return redirect(url_for("products"))

        # Fetch Stock Inward (Purchases)
        cursor.execute("""
            SELECT supplier_name as ref_name, purchase_invoice_no as ref_no, quantity, 
                   purchase_price as unit_price, total_amount, created_at, 'INWARD (PURCHASE)' as type
            FROM purchases 
            WHERE product_id = %s AND user_id = %s
        """, (product_id, user_id))
        purchases_log = cursor.fetchall()

        # Fetch Stock Outward (Sales Invoices)
        cursor.execute("""
            SELECT c.customer_name as ref_name, i.invoice_number as ref_no, i.quantity, 
                   i.subtotal / i.quantity as unit_price, i.grand_total as total_amount, i.created_at, 'OUTWARD (SALES)' as type
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.product_id = %s AND i.user_id = %s
        """, (product_id, user_id))
        sales_log = cursor.fetchall()

        # Merge and sort transactions chronologically
        history_logs = purchases_log + sales_log
        history_logs.sort(key=lambda x: x["created_at"], reverse=True)

        return render_template("product_history.html", product=product, logs=history_logs)

    except Exception as e:
        flash(f"Error fetching ledger history: {str(e)}", "error")
        return redirect(url_for("products"))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)