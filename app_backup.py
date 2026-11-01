from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "billnova_secret_key"


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="root123",
        database="billnova"
    )


# =========================================================
# UPLOAD CONFIGURATION
# =========================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "uploads",
    "logos"
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
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
# NUMBER TO WORDS
# =========================================================

def number_to_words(number):

    number = int(Decimal(str(number)))

    if number == 0:
        return "Zero Rupees Only"

    ones = [
        "",
        "One",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
        "Ten",
        "Eleven",
        "Twelve",
        "Thirteen",
        "Fourteen",
        "Fifteen",
        "Sixteen",
        "Seventeen",
        "Eighteen",
        "Nineteen"
    ]

    tens = [
        "",
        "",
        "Twenty",
        "Thirty",
        "Forty",
        "Fifty",
        "Sixty",
        "Seventy",
        "Eighty",
        "Ninety"
    ]

    def two_digit(n):

        if n < 20:
            return ones[n]

        return (
            tens[n // 10]
            + (" " + ones[n % 10] if n % 10 else "")
        )

    def three_digit(n):

        if n < 100:
            return two_digit(n)

        return (
            ones[n // 100]
            + " Hundred"
            + (" " + two_digit(n % 100) if n % 100 else "")
        )

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
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("welcome.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Simple login for current project
        if username == "admin" and password == "admin123":
            return redirect(url_for("dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products", methods=["GET", "POST"])
def products():

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
            INSERT INTO products
            (
                product_name,
                hsn_code,
                price,
                gst_rate,
                quantity
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                product_name,
                hsn_code,
                price,
                gst_rate,
                quantity
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Product added successfully!", "success")

        return redirect(url_for("products"))

    cursor.execute(
        """
        SELECT *
        FROM products
        ORDER BY id DESC
        """
    )

    product_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "products.html",
        products=product_list
    )


# =========================================================
# EDIT PRODUCT
# =========================================================

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
            SET
                product_name = %s,
                hsn_code = %s,
                price = %s,
                gst_rate = %s,
                quantity = %s
            WHERE id = %s
            """,
            (
                product_name,
                hsn_code,
                price,
                gst_rate,
                quantity,
                id
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Product updated successfully!", "success")

        return redirect(url_for("products"))

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE id = %s
        """,
        (id,)
    )

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if not product:
        flash("Product not found!", "error")
        return redirect(url_for("products"))

    return render_template(
        "edit_product.html",
        product=product
    )


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route("/delete_product/<int:id>", methods=["POST"])
def delete_product(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM products
        WHERE id = %s
        """,
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Product deleted successfully!", "success")

    return redirect(url_for("products"))


# =========================================================
# CUSTOMERS
# =========================================================

@app.route("/customers", methods=["GET", "POST"])
def customers():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        customer_name = request.form.get("customer_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        gstin = request.form.get("gstin")
        address = request.form.get("address")
        state = request.form.get("state")
        state_code = request.form.get("state_code")

        cursor.execute(
            """
            INSERT INTO customers
            (
                customer_name,
                phone,
                email,
                gstin,
                address,
                state,
                state_code
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                customer_name,
                phone,
                email,
                gstin,
                address,
                state,
                state_code
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Customer added successfully!", "success")

        return redirect(url_for("customers"))

    cursor.execute(
        """
        SELECT *
        FROM customers
        ORDER BY id DESC
        """
    )

    customer_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "customers.html",
        customers=customer_list
    )


# =========================================================
# EDIT CUSTOMER
# =========================================================

@app.route("/edit_customer/<int:id>", methods=["GET", "POST"])
def edit_customer(id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        customer_name = request.form.get("customer_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        gstin = request.form.get("gstin")
        address = request.form.get("address")
        state = request.form.get("state")
        state_code = request.form.get("state_code")

        cursor.execute(
            """
            UPDATE customers
            SET
                customer_name = %s,
                phone = %s,
                email = %s,
                gstin = %s,
                address = %s,
                state = %s,
                state_code = %s
            WHERE id = %s
            """,
            (
                customer_name,
                phone,
                email,
                gstin,
                address,
                state,
                state_code,
                id
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Customer updated successfully!", "success")

        return redirect(url_for("customers"))

    cursor.execute(
        """
        SELECT *
        FROM customers
        WHERE id = %s
        """,
        (id,)
    )

    customer = cursor.fetchone()

    cursor.close()
    conn.close()

    if not customer:
        flash("Customer not found!", "error")
        return redirect(url_for("customers"))

    return render_template(
        "edit_customer.html",
        customer=customer
    )


# =========================================================
# DELETE CUSTOMER
# =========================================================

@app.route("/delete_customer/<int:id>", methods=["POST"])
def delete_customer(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM customers
        WHERE id = %s
        """,
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Customer deleted successfully!", "success")

    return redirect(url_for("customers"))


# =========================================================
# INVOICES
# =========================================================

@app.route("/invoices", methods=["GET", "POST"])
def invoices():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =====================================================
    # CREATE INVOICE
    # =====================================================

    if request.method == "POST":

        try:

            customer_id = request.form.get("customer_id")

            if not customer_id:
                flash("Please select a customer.", "error")
                return redirect(url_for("invoices"))

            # -------------------------------------------------
            # MULTIPLE PRODUCT SUPPORT
            # -------------------------------------------------

            product_ids = request.form.getlist("product_ids[]")
            quantities = request.form.getlist("quantities[]")

            # -------------------------------------------------
            # OLD SINGLE PRODUCT FORM SUPPORT
            # -------------------------------------------------

            if not product_ids:

                old_product_id = request.form.get("product_id")
                old_quantity = request.form.get("quantity")

                if old_product_id and old_quantity:

                    product_ids = [old_product_id]
                    quantities = [old_quantity]

            if not product_ids:

                flash("Please select at least one product.", "error")
                return redirect(url_for("invoices"))

            if len(product_ids) != len(quantities):

                flash("Invalid product and quantity data.", "error")
                return redirect(url_for("invoices"))

            # -------------------------------------------------
            # BILL DETAILS
            # -------------------------------------------------

            payment_status = request.form.get(
                "payment_status",
                "Pending"
            )

            payment_mode = request.form.get(
                "payment_mode",
                "Cash"
            )

            due_date = request.form.get("due_date") or None

            notes = request.form.get("notes") or ""

            terms_conditions = request.form.get(
                "terms_conditions"
            ) or ""

            challan_no = request.form.get(
                "challan_no"
            ) or ""

            challan_date = request.form.get(
                "challan_date"
            ) or None

            po_no = request.form.get(
                "po_no"
            ) or ""

            po_date = request.form.get(
                "po_date"
            ) or None

            vehicle_no = request.form.get(
                "vehicle_no"
            ) or ""

            freight = get_decimal(
                request.form.get("freight")
            )

            packing = get_decimal(
                request.form.get("packing")
            )

            forwarding = get_decimal(
                request.form.get("forwarding")
            )

            round_off = get_decimal(
                request.form.get("round_off")
            )

            # -------------------------------------------------
            # IGST
            # -------------------------------------------------

            igst_total = Decimal("0.00")

            # -------------------------------------------------
            # TOTALS
            # -------------------------------------------------

            invoice_subtotal = Decimal("0.00")
            invoice_cgst = Decimal("0.00")
            invoice_sgst = Decimal("0.00")
            invoice_total_gst = Decimal("0.00")

            item_data = []

            # =================================================
            # PROCESS EACH PRODUCT
            # =================================================

            for product_id, quantity_value in zip(
                product_ids,
                quantities
            ):

                try:
                    product_id = int(product_id)
                    quantity = int(quantity_value)

                except ValueError:

                    flash(
                        "Invalid product or quantity.",
                        "error"
                    )

                    return redirect(
                        url_for("invoices")
                    )

                if quantity <= 0:

                    flash(
                        "Quantity must be greater than zero.",
                        "error"
                    )

                    return redirect(
                        url_for("invoices")
                    )

                # -------------------------------------------------
                # GET PRODUCT
                # -------------------------------------------------

                cursor.execute(
                    """
                    SELECT *
                    FROM products
                    WHERE id = %s
                    """,
                    (product_id,)
                )

                product = cursor.fetchone()

                if not product:

                    flash(
                        "Product not found.",
                        "error"
                    )

                    return redirect(
                        url_for("invoices")
                    )

                # -------------------------------------------------
                # STOCK VALIDATION
                # -------------------------------------------------

                available_stock = int(
                    product.get("quantity") or 0
                )

                if quantity > available_stock:

                    flash(
                        f"Not enough stock for "
                        f"{product['product_name']}. "
                        f"Available stock: {available_stock}",
                        "error"
                    )

                    return redirect(
                        url_for("invoices")
                    )

                # -------------------------------------------------
                # PRICE
                # -------------------------------------------------

                price = get_decimal(
                    product.get("price")
                )

                gst_rate = get_decimal(
                    product.get("gst_rate")
                )

                # -------------------------------------------------
                # CALCULATIONS
                # -------------------------------------------------

                subtotal = money(
                    price * quantity
                )

                total_gst = money(
                    subtotal * gst_rate / Decimal("100")
                )

                cgst = money(
                    total_gst / Decimal("2")
                )

                sgst = money(
                    total_gst - cgst
                )

                amount = money(
                    subtotal + total_gst
                )

                # -------------------------------------------------
                # TOTALS
                # -------------------------------------------------

                invoice_subtotal += subtotal

                invoice_cgst += cgst

                invoice_sgst += sgst

                invoice_total_gst += total_gst

                # -------------------------------------------------
                # STORE ITEM
                # -------------------------------------------------

                item_data.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "price": price,
                    "gst_rate": gst_rate,
                    "subtotal": subtotal,
                    "cgst": cgst,
                    "sgst": sgst,
                    "total_gst": total_gst,
                    "amount": amount
                })

            # =================================================
            # ADDITIONAL CHARGES
            # =================================================

            additional_charges = (
                freight
                + packing
                + forwarding
            )

            # =================================================
            # GRAND TOTAL
            # =================================================

            before_round_off = (
                invoice_subtotal
                + invoice_total_gst
                + additional_charges
                + igst_total
            )

            grand_total = money(
                before_round_off + round_off
            )

            # =================================================
            # MAIN INVOICE TABLE
            # =================================================

            # First item is stored in legacy columns
            # for compatibility with old reports/templates.

            first_item = item_data[0]

            cursor.execute(
                """
                INSERT INTO invoices
                (
                    customer_id,
                    product_id,
                    quantity,
                    subtotal,
                    cgst,
                    sgst,
                    total_gst,
                    gst,
                    grand_total,
                    total,
                    payment_status,
                    payment_mode,
                    due_date,
                    notes,
                    terms_conditions,
                    challan_no,
                    challan_date,
                    po_no,
                    po_date,
                    vehicle_no,
                    freight,
                    packing,
                    forwarding,
                    igst,
                    round_off
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s
                )
                """,
                (
                    customer_id,
                    first_item["product_id"],
                    first_item["quantity"],
                    invoice_subtotal,
                    invoice_cgst,
                    invoice_sgst,
                    invoice_total_gst,
                    invoice_total_gst,
                    grand_total,
                    grand_total,
                    payment_status,
                    payment_mode,
                    due_date,
                    notes,
                    terms_conditions,
                    challan_no,
                    challan_date,
                    po_no,
                    po_date,
                    vehicle_no,
                    freight,
                    packing,
                    forwarding,
                    igst_total,
                    round_off
                )
            )

            invoice_id = cursor.lastrowid

            # =================================================
            # CREATE INVOICE NUMBER
            # =================================================

            invoice_number = (
                f"INV-{datetime.now().year}-"
                f"{invoice_id:04d}"
            )

            cursor.execute(
                """
                UPDATE invoices
                SET invoice_number = %s
                WHERE id = %s
                """,
                (
                    invoice_number,
                    invoice_id
                )
            )

            # =================================================
            # INSERT ALL ITEMS
            # =================================================

            for item in item_data:

                cursor.execute(
                    """
                    INSERT INTO invoice_items
                    (
                        invoice_id,
                        product_id,
                        quantity,
                        price,
                        gst_rate,
                        subtotal,
                        cgst,
                        sgst,
                        total_gst,
                        amount
                    )
                    VALUES
                    (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        invoice_id,
                        item["product_id"],
                        item["quantity"],
                        item["price"],
                        item["gst_rate"],
                        item["subtotal"],
                        item["cgst"],
                        item["sgst"],
                        item["total_gst"],
                        item["amount"]
                    )
                )

                # =================================================
                # REDUCE STOCK
                # =================================================

                cursor.execute(
                    """
                    UPDATE products
                    SET quantity = quantity - %s
                    WHERE id = %s
                    """,
                    (
                        item["quantity"],
                        item["product_id"]
                    )
                )

            # =================================================
            # COMMIT
            # =================================================

            conn.commit()

            cursor.close()
            conn.close()

            flash(
                f"Invoice {invoice_number} created successfully!",
                "success"
            )

            return redirect(
                url_for(
                    "invoice_details",
                    id=invoice_id
                )
            )

        except Exception as e:

            conn.rollback()

            cursor.close()
            conn.close()

            flash(
                f"Error creating invoice: {str(e)}",
                "error"
            )

            return redirect(
                url_for("invoices")
            )

    # =========================================================
    # GET INVOICES
    # =========================================================

    cursor.execute(
        """
        SELECT
            i.*,
            c.customer_name,
            p.product_name
        FROM invoices i
        LEFT JOIN customers c
            ON i.customer_id = c.id
        LEFT JOIN products p
            ON i.product_id = p.id
        ORDER BY i.id DESC
        """
    )

    invoice_list = cursor.fetchall()

    # =========================================================
    # CUSTOMERS
    # =========================================================

    cursor.execute(
        """
        SELECT *
        FROM customers
        ORDER BY customer_name
        """
    )

    customer_list = cursor.fetchall()

    # =========================================================
    # PRODUCTS
    # =========================================================

    cursor.execute(
        """
        SELECT *
        FROM products
        ORDER BY product_name
        """
    )

    product_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "invoices.html",
        invoices=invoice_list,
        customers=customer_list,
        products=product_list
    )


# =========================================================
# DELETE INVOICE
# =========================================================

@app.route("/delete_invoice/<int:id>", methods=["POST"])
def delete_invoice(id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # =====================================================
        # GET ALL ITEMS
        # =====================================================

        cursor.execute(
            """
            SELECT
                product_id,
                quantity
            FROM invoice_items
            WHERE invoice_id = %s
            """,
            (id,)
        )

        items = cursor.fetchall()

        # =====================================================
        # OLD INVOICE SUPPORT
        # =====================================================

        if not items:

            cursor.execute(
                """
                SELECT
                    product_id,
                    quantity
                FROM invoices
                WHERE id = %s
                """,
                (id,)
            )

            old_invoice = cursor.fetchone()

            if old_invoice:

                items = [old_invoice]

        # =====================================================
        # RESTORE STOCK
        # =====================================================

        for item in items:

            cursor.execute(
                """
                UPDATE products
                SET quantity = quantity + %s
                WHERE id = %s
                """,
                (
                    item["quantity"],
                    item["product_id"]
                )
            )

        # =====================================================
        # DELETE ITEMS
        # =====================================================

        cursor.execute(
            """
            DELETE FROM invoice_items
            WHERE invoice_id = %s
            """,
            (id,)
        )

        # =====================================================
        # DELETE INVOICE
        # =====================================================

        cursor.execute(
            """
            DELETE FROM invoices
            WHERE id = %s
            """,
            (id,)
        )

        conn.commit()

        flash(
            "Invoice deleted and stock restored successfully!",
            "success"
        )

    except Exception as e:

        conn.rollback()

        flash(
            f"Error deleting invoice: {str(e)}",
            "error"
        )

    cursor.close()
    conn.close()

    return redirect(
        url_for("invoices")
    )


# =========================================================
# INVOICE DETAILS
# =========================================================

@app.route("/invoice/<int:id>")
def invoice_details(id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =====================================================
    # MAIN INVOICE
    # =====================================================

    cursor.execute(
        """
        SELECT
            i.*,
            c.customer_name,
            c.phone,
            c.email,
            c.gstin AS customer_gstin,
            c.address AS customer_address,
            c.state AS customer_state,
            c.state_code AS customer_state_code
        FROM invoices i
        LEFT JOIN customers c
            ON i.customer_id = c.id
        WHERE i.id = %s
        """,
        (id,)
    )

    invoice = cursor.fetchone()

    if not invoice:

        cursor.close()
        conn.close()

        flash(
            "Invoice not found!",
            "error"
        )

        return redirect(
            url_for("invoices")
        )

    # =====================================================
    # ALL INVOICE ITEMS
    # =====================================================

    cursor.execute(
        """
        SELECT
            ii.*,
            p.product_name,
            p.hsn_code
        FROM invoice_items ii
        LEFT JOIN products p
            ON ii.product_id = p.id
        WHERE ii.invoice_id = %s
        ORDER BY ii.id
        """,
        (id,)
    )

    items = cursor.fetchall()

    # =====================================================
    # OLD INVOICE SUPPORT
    # =====================================================

    if not items:

        cursor.execute(
            """
            SELECT
                i.product_id,
                i.quantity,
                p.product_name,
                p.hsn_code,
                p.price,
                p.gst_rate
            FROM invoices i
            LEFT JOIN products p
                ON i.product_id = p.id
            WHERE i.id = %s
            """,
            (id,)
        )

        old_item = cursor.fetchone()

        if old_item:

            price = get_decimal(
                old_item.get("price")
            )

            gst_rate = get_decimal(
                old_item.get("gst_rate")
            )

            quantity = int(
                old_item.get("quantity") or 0
            )

            subtotal = money(
                price * quantity
            )

            total_gst = money(
                subtotal * gst_rate / Decimal("100")
            )

            cgst = money(
                total_gst / Decimal("2")
            )

            sgst = money(
                total_gst - cgst
            )

            amount = money(
                subtotal + total_gst
            )

            old_item.update({
                "subtotal": subtotal,
                "cgst": cgst,
                "sgst": sgst,
                "total_gst": total_gst,
                "amount": amount
            })

            items = [old_item]

    # =====================================================
    # COMPANY SETTINGS
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM company_settings
        ORDER BY id
        LIMIT 1
        """
    )

    company = cursor.fetchone()

    # =====================================================
    # AMOUNT IN WORDS
    # =====================================================

    grand_total = get_decimal(
        invoice.get("grand_total")
    )

    amount_words = number_to_words(
        grand_total
    )

    cursor.close()
    conn.close()

    return render_template(
        "invoice_details.html",
        invoice=invoice,
        items=items,
        company=company,
        amount_words=amount_words
    )


# =========================================================
# COMPANY SETTINGS
# =========================================================

@app.route(
    "/company_settings",
    methods=["GET", "POST"]
)
def company_settings():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =====================================================
    # SAVE SETTINGS
    # =====================================================

    if request.method == "POST":

        company_name = request.form.get(
            "company_name"
        ) or ""

        owner_name = request.form.get(
            "owner_name"
        ) or ""

        gstin = request.form.get(
            "gstin"
        ) or ""

        address = request.form.get(
            "address"
        ) or ""

        phone = request.form.get(
            "phone"
        ) or ""

        email = request.form.get(
            "email"
        ) or ""

        state = request.form.get(
            "state"
        ) or ""

        state_code = request.form.get(
            "state_code"
        ) or ""

        bank_name = request.form.get(
            "bank_name"
        ) or ""

        account_number = request.form.get(
            "account_number"
        ) or ""

        ifsc_code = request.form.get(
            "ifsc_code"
        ) or ""

        bank_branch = request.form.get(
            "bank_branch"
        ) or ""

        # =================================================
        # EXISTING SETTINGS
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM company_settings
            ORDER BY id
            LIMIT 1
            """
        )

        existing = cursor.fetchone()

        old_logo = (
            existing.get("logo")
            if existing
            else None
        )

        logo_path = old_logo

        # =================================================
        # LOGO UPLOAD
        # =================================================

        if "logo" in request.files:

            file = request.files["logo"]

            if file and file.filename:

                if allowed_file(file.filename):

                    extension = (
                        file.filename
                        .rsplit(".", 1)[1]
                        .lower()
                    )

                    filename = (
                        "company_logo_"
                        + str(uuid.uuid4())
                        + "."
                        + extension
                    )

                    file.save(
                        os.path.join(
                            UPLOAD_FOLDER,
                            filename
                        )
                    )

                    logo_path = (
                        "uploads/logos/"
                        + filename
                    )

                else:

                    flash(
                        "Invalid logo format. "
                        "Use PNG, JPG, JPEG or WEBP.",
                        "error"
                    )

                    cursor.close()
                    conn.close()

                    return redirect(
                        url_for(
                            "company_settings"
                        )
                    )

        # =================================================
        # UPDATE OR INSERT
        # =================================================

        if existing:

            cursor.execute(
                """
                UPDATE company_settings
                SET
                    company_name = %s,
                    owner_name = %s,
                    gstin = %s,
                    address = %s,
                    phone = %s,
                    email = %s,
                    state = %s,
                    state_code = %s,
                    bank_name = %s,
                    account_number = %s,
                    ifsc_code = %s,
                    bank_branch = %s,
                    logo = %s
                WHERE id = %s
                """,
                (
                    company_name,
                    owner_name,
                    gstin,
                    address,
                    phone,
                    email,
                    state,
                    state_code,
                    bank_name,
                    account_number,
                    ifsc_code,
                    bank_branch,
                    logo_path,
                    existing["id"]
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO company_settings
                (
                    company_name,
                    owner_name,
                    gstin,
                    address,
                    phone,
                    email,
                    state,
                    state_code,
                    bank_name,
                    account_number,
                    ifsc_code,
                    bank_branch,
                    logo
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    company_name,
                    owner_name,
                    gstin,
                    address,
                    phone,
                    email,
                    state,
                    state_code,
                    bank_name,
                    account_number,
                    ifsc_code,
                    bank_branch,
                    logo_path
                )
            )

        conn.commit()

        cursor.close()
        conn.close()

        flash(
            "Company settings saved successfully!",
            "success"
        )

        return redirect(
            url_for("company_settings")
        )

    # =====================================================
    # GET SETTINGS
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM company_settings
        ORDER BY id
        LIMIT 1
        """
    )

    company = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "company_settings.html",
        company=company
    )


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =====================================================
    # TOTAL INVOICES
    # =====================================================

    cursor.execute(
        """
        SELECT COUNT(*) AS total_invoices
        FROM invoices
        """
    )

    total_invoices = cursor.fetchone()

    # =====================================================
    # TOTAL SALES
    # =====================================================

    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(grand_total),
                0
            ) AS total_sales
        FROM invoices
        """
    )

    total_sales = cursor.fetchone()

    # =====================================================
    # TOTAL GST
    # =====================================================

    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(total_gst),
                0
            ) AS total_gst
        FROM invoices
        """
    )

    total_gst = cursor.fetchone()

    # =====================================================
    # RECENT INVOICES
    # =====================================================

    cursor.execute(
        """
        SELECT
            i.*,
            c.customer_name
        FROM invoices i
        LEFT JOIN customers c
            ON i.customer_id = c.id
        ORDER BY i.id DESC
        LIMIT 20
        """
    )

    recent_invoices = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "reports.html",
        total_invoices=total_invoices["total_invoices"],
        total_sales=total_sales["total_sales"],
        total_gst=total_gst["total_gst"],
        invoices=recent_invoices
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =====================================================
    # TOTAL PRODUCTS
    # =====================================================

    cursor.execute(
        """
        SELECT COUNT(*) AS total_products
        FROM products
        """
    )

    total_products = cursor.fetchone()

    # =====================================================
    # TOTAL CUSTOMERS
    # =====================================================

    cursor.execute(
        """
        SELECT COUNT(*) AS total_customers
        FROM customers
        """
    )

    total_customers = cursor.fetchone()

    # =====================================================
    # TOTAL INVOICES
    # =====================================================

    cursor.execute(
        """
        SELECT COUNT(*) AS total_invoices
        FROM invoices
        """
    )

    total_invoices = cursor.fetchone()

    # =====================================================
    # TOTAL SALES
    # =====================================================

    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(grand_total),
                0
            ) AS total_sales
        FROM invoices
        """
    )

    total_sales = cursor.fetchone()

    # =====================================================
    # RECENT INVOICES
    # =====================================================

    cursor.execute(
        """
        SELECT
            i.*,
            c.customer_name,
            p.product_name
        FROM invoices i
        LEFT JOIN customers c
            ON i.customer_id = c.id
        LEFT JOIN products p
            ON i.product_id = p.id
        ORDER BY i.id DESC
        LIMIT 10
        """
    )

    recent_invoices = cursor.fetchall()

    # =====================================================
    # LOW STOCK PRODUCTS
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE quantity <= 5
        ORDER BY quantity ASC
        """
    )

    low_stock = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_products=total_products["total_products"],
        total_customers=total_customers["total_customers"],
        total_invoices=total_invoices["total_invoices"],
        total_sales=total_sales["total_sales"],
        recent_invoices=recent_invoices,
        low_stock=low_stock
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )