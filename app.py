"""
ROSE Website Backend

Handles:
- Website pages
- Newsletter subscriptions
- Contact Us submissions
- Post-payment donation verification
- Confirmation and notification emails
- Private admin login and data viewing
- Admin gallery uploads and deletion
"""

from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
    session,
    redirect
)

from pathlib import Path
from datetime import datetime
from email.message import EmailMessage
from dotenv import load_dotenv
from flask_cors import CORS
from werkzeug.utils import secure_filename

import smtplib
import os
import re
import threading
import html
import json


# ==========================================================
# ENVIRONMENT
# ==========================================================

load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "CHANGE-THIS-SECRET-KEY"
)

frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "*"
)

CORS(
    app,
    origins=frontend_origin
)


# ==========================================================
# DATA FILES
# ==========================================================

PRIVATE_DATA_FOLDER = BASE_DIR / "private_data"
PRIVATE_DATA_FOLDER.mkdir(exist_ok=True)

SUBSCRIBER_FILE = (
    PRIVATE_DATA_FOLDER / "subscribers.txt"
)

CONTACT_FILE = (
    PRIVATE_DATA_FOLDER / "contacts.txt"
)

DONOR_FILE = (
    PRIVATE_DATA_FOLDER / "donorDetails.txt"
)


# ==========================================================
# GALLERY
# ==========================================================

GALLERY_FOLDER = BASE_DIR / "gallery"
GALLERY_FOLDER.mkdir(exist_ok=True)

GALLERY_JSON_FILE = (
    BASE_DIR / "gallery_json.json"
)

ALLOWED_IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}

GALLERY_CATEGORIES = {
    "essential-support":
        "Essential Support",

    "education":
        "Education & Child Development",

    "health":
        "Health & Well-being",

    "women":
        "Women Empowerment",

    "skills":
        "Skills & Opportunities",

    "livelihoods":
        "Livelihoods & Employment",

    "social":
        "Social Empowerment"
}


# ==========================================================
# ROSE EMAIL
# ==========================================================

ROSE_EMAIL = "roseorg22@gmail.com"


# ==========================================================
# SMTP
# ==========================================================

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_EMAIL = os.getenv(
    "SMTP_EMAIL"
)

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD"
)


# ==========================================================
# ADMIN
# ==========================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD"
)


# ==========================================================
# UPI
# ==========================================================

ROSE_UPI_ID = os.getenv(
    "ROSE_UPI_ID",
    ""
)

ROSE_UPI_NAME = (
    "Rural Organisation For Social Emancipation"
)


# ==========================================================
# SESSION SECURITY
# ==========================================================

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=
        os.getenv(
            "SESSION_COOKIE_SECURE",
            "false"
        ).lower() == "true"
)


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def now_ist():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S IST"
    )


def clean_line(value):
    return (
        str(value)
        .replace("|", " ")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


def valid_email(email):
    pattern = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9-]+"
        r"(?:\.[A-Za-z0-9-]+)+$"
    )

    return (
        bool(
            re.fullmatch(
                pattern,
                email
            )
        )
        and len(email) <= 254
    )


def get_json_data():
    if not request.is_json:
        return {}

    try:
        data = request.get_json(
            silent=True
        )

        if isinstance(
            data,
            dict
        ):
            return data

        return {}

    except Exception as error:
        print(
            f"JSON parsing error: {error}"
        )
        return {}


def send_email(
    receiver,
    subject,
    body,
    html_body=None
):

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(
            "SMTP email credentials are not configured."
        )
        return False

    try:

        message = EmailMessage()

        message["From"] = SMTP_EMAIL
        message["To"] = receiver
        message["Subject"] = subject

        message.set_content(
            body
        )

        if html_body:
            message.add_alternative(
                html_body,
                subtype="html"
            )

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                SMTP_EMAIL,
                SMTP_PASSWORD
            )

            server.send_message(
                message
            )

        print(
            f"Email sent successfully to: {receiver}"
        )

        return True

    except Exception as error:

        print(
            f"Email error for {receiver}: {error}"
        )

        return False


def run_in_background(
    function,
    *args
):

    thread = threading.Thread(
        target=function,
        args=args,
        daemon=True
    )

    thread.start()


def already_subscribed(email):

    if not SUBSCRIBER_FILE.exists():
        return False

    with SUBSCRIBER_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if (
                not line
                or line.startswith("#")
            ):
                continue

            saved_email = (
                line
                .split("|", 1)[0]
                .strip()
            )

            if (
                saved_email.lower()
                == email.lower()
            ):
                return True

    return False


# ==========================================================
# GALLERY JSON HELPERS
# ==========================================================

def default_gallery_data():

    return {
        "sections": [

            {
                "id":
                    "essential-support",

                "title":
                    "Essential Support",

                "photos": []
            },

            {
                "id":
                    "education",

                "title":
                    "Education & Child Development",

                "photos": []
            },

            {
                "id":
                    "health",

                "title":
                    "Health & Well-being",

                "photos": []
            },

            {
                "id":
                    "women",

                "title":
                    "Women Empowerment",

                "photos": []
            },

            {
                "id":
                    "skills",

                "title":
                    "Skills & Opportunities",

                "photos": []
            },

            {
                "id":
                    "livelihoods",

                "title":
                    "Livelihoods & Employment",

                "photos": []
            },

            {
                "id":
                    "social",

                "title":
                    "Social Empowerment",

                "photos": []
            }
        ]
    }


def save_gallery_data(data):

    try:

        with GALLERY_JSON_FILE.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

        return True

    except OSError as error:

        print(
            f"Gallery JSON save error: {error}"
        )

        return False


def load_gallery_data():

    if not GALLERY_JSON_FILE.exists():

        data = default_gallery_data()

        save_gallery_data(data)

        return data

    try:

        with GALLERY_JSON_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if (
            not isinstance(data, dict)
            or not isinstance(
                data.get("sections"),
                list
            )
        ):

            raise ValueError(
                "Invalid gallery JSON structure."
            )

        return data

    except (
        OSError,
        json.JSONDecodeError,
        ValueError
    ) as error:

        print(
            f"Gallery JSON error: {error}"
        )

        return default_gallery_data()


def find_gallery_section(
    data,
    section_id
):

    for section in data.get(
        "sections",
        []
    ):

        if section.get(
            "id"
        ) == section_id:

            return section

    return None


def find_gallery_photo(
    data,
    filename
):

    for section in data.get(
        "sections",
        []
    ):

        for photo in section.get(
            "photos",
            []
        ):

            if photo.get(
                "filename"
            ) == filename:

                return section, photo

            if photo.get(
                "file"
            ) == f"/gallery/{filename}":

                return section, photo

            if photo.get(
                "file"
            ) == f"gallery/{filename}":

                return section, photo

    return None, None


def add_image_to_gallery_json(
    filename,
    category,
    title
):

    data = load_gallery_data()

    section = find_gallery_section(
        data,
        category
    )

    if section is None:
        return False

    if "photos" not in section:
        section["photos"] = []

    section["photos"].append({
        "filename":
            filename,

        "file":
            f"/gallery/{filename}",

        "title":
            title
    })

    return save_gallery_data(
        data
    )


def remove_image_from_gallery_json(
    filename
):

    data = load_gallery_data()

    for section in data.get(
        "sections",
        []
    ):

        photos = section.get(
            "photos",
            []
        )

        original_count = len(
            photos
        )

        section["photos"] = [

            photo

            for photo in photos

            if (
                photo.get("filename")
                != filename
            )

            and (
                photo.get("file")
                != f"/gallery/{filename}"
            )

            and (
                photo.get("file")
                != f"gallery/{filename}"
            )
        ]

        if len(
            section["photos"]
        ) < original_count:

            return save_gallery_data(
                data
            )

    return False


# ==========================================================
# PAGE ROUTES
# ==========================================================
@app.route("/")
def root():
    return send_from_directory(
        BASE_DIR,
        "index.html"
    )

@app.route("/index.html")
def home():

    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


@app.route("/newsletter.html")
def newsletter():

    return send_from_directory(
        BASE_DIR,
        "newsletter.html"
    )


@app.route("/contact.html")
def contact_page():

    return send_from_directory(
        BASE_DIR,
        "contact.html"
    )


@app.route("/donate.html")
def donate_page():

    return send_from_directory(
        BASE_DIR,
        "donate.html"
    )


@app.route("/aboutUs.html")
def about_us():

    return send_from_directory(
        BASE_DIR,
        "aboutUs.html"
    )


@app.route("/programs.html")
def programs():

    return send_from_directory(
        BASE_DIR,
        "programs.html"
    )


@app.route("/blog.html")
def blog():

    return send_from_directory(
        BASE_DIR,
        "blog.html"
    )


@app.route("/gallery_html.html")
def gallery_page():

    return send_from_directory(
        BASE_DIR,
        "gallery_html.html"
    )


# ==========================================================
# GALLERY JSON ROUTES
# ==========================================================

@app.route("/gallery_json.json")
def gallery_json():

    return jsonify(
        load_gallery_data()
    )


@app.route("/api/gallery")
def gallery_api():

    return jsonify(
        load_gallery_data()
    )


# ==========================================================
# NEWSLETTER EMAILS
# ==========================================================

def send_newsletter_emails(
    email,
    subscribed_at
):

    subject = (
        "ROSE Newsletter Subscription Confirmation"
    )

    plain = f"""
Dear Subscriber,

Thank you for subscribing to the ROSE Newsletter.

Your subscription was successfully received.

Subscription Email:

{email}

Subscription Date:

{subscribed_at}

You will receive updates about our programs,
success stories, events and other activities
of the Rural Organisation for Social Emancipation (ROSE).

Thank you for staying connected with ROSE.

Regards,

Rural Organisation for Social Emancipation (ROSE)

{ROSE_EMAIL}
"""

    safe_email = html.escape(
        email
    )

    safe_date = html.escape(
        subscribed_at
    )

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport"
content="width=device-width,initial-scale=1.0">
<title>ROSE Newsletter Confirmation</title>
</head>

<body style="
margin:0;
padding:30px;
background:#f3f3f3;
font-family:Arial,Helvetica,sans-serif;
color:#444;
">

<div style="
max-width:640px;
margin:auto;
background:#fff;
border-radius:16px;
padding:35px;
box-sizing:border-box;
">

<h1 style="
text-align:center;
color:#333;
">
Your subscription has been received.
</h1>

<p>
Dear Subscriber,
</p>

<p>
Thank you for subscribing to the ROSE Newsletter.
</p>

<p>
Your subscription was successfully received.
</p>

<div style="
background:#f7f8f9;
border-radius:8px;
padding:16px;
">

<div style="
color:#999;
font-size:14px;
">
Subscription Email
</div>

<div style="
font-size:16px;
font-weight:bold;
color:#1769d1;
">
{safe_email}
</div>

<div style="
color:#999;
font-size:14px;
margin-top:15px;
">
Subscription Date
</div>

<div style="
font-size:16px;
">
{safe_date}
</div>

</div>

<p style="
line-height:1.6;
">
You will receive updates about our programs,
success stories, events and other activities
of the Rural Organisation for Social Emancipation (ROSE).
</p>

<p>
Thank you for staying connected with ROSE.
</p>

<p>
Regards,<br>

<strong>
Rural Organisation for Social Emancipation (ROSE)
</strong>

<br>

{ROSE_EMAIL}
</p>

</div>

</body>
</html>
"""

    send_email(
        email,
        subject,
        plain,
        html_body
    )

    rose_body = f"""
A new newsletter subscription has been received.

Subscriber Email:

{email}

Subscription Date:

{subscribed_at}

The subscriber has been added to subscribers.txt.
"""

    send_email(
        ROSE_EMAIL,
        "New ROSE Newsletter Subscriber",
        rose_body
    )


# ==========================================================
# NEWSLETTER API
# ==========================================================

@app.route(
    "/subscribe",
    methods=["POST"]
)
def subscribe():

    data = get_json_data()

    email = data.get(
        "email",
        ""
    )

    if not isinstance(
        email,
        str
    ):

        email = ""

    email = email.strip()

    if not valid_email(email):

        return jsonify({
            "success":
                False,

            "message":
                "Please enter a valid email address."
        }), 400

    if already_subscribed(email):

        return jsonify({
            "success":
                False,

            "message":
                "This email is already subscribed."
        }), 200

    subscribed_at = now_ist()

    try:

        with SUBSCRIBER_FILE.open(
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                f"{email} | subscribed on: "
                f"{subscribed_at}\n"
            )

    except OSError as error:

        print(
            f"Subscriber file error: {error}"
        )

        return jsonify({
            "success":
                False,

            "message":
                "Unable to save your subscription. "
                "Please try again."
        }), 500

    print(
        f"New subscriber: {email} | "
        f"Subscribed on: {subscribed_at}"
    )

    run_in_background(
        send_newsletter_emails,
        email,
        subscribed_at
    )

    return jsonify({
        "success":
            True,

        "message":
            "Subscribed successfully!"
    }), 200


# ==========================================================
# CONTACT EMAILS
# ==========================================================

def send_contact_emails(
    name,
    email,
    subject,
    message,
    contacted_at
):

    visitor_subject = (
        "ROSE Contact Form Confirmation"
    )

    visitor_body = f"""
Dear {name},

Thank you for contacting the Rural Organisation
for Social Emancipation (ROSE).

We have successfully received your message.

Name:

{name}

Email:

{email}

Subject:

{subject}

Your Message:

{message}

Submitted on:

{contacted_at}

Our team will review your message and
get back to you as soon as possible.

Thank you for reaching out to ROSE.

Regards,

Rural Organisation for Social Emancipation (ROSE)

{ROSE_EMAIL}
"""

    safe_name = html.escape(name)
    safe_email = html.escape(email)
    safe_subject = html.escape(subject)
    safe_message = html.escape(message)
    safe_date = html.escape(contacted_at)

    visitor_html = f"""
<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width,initial-scale=1.0">

<title>ROSE Contact Confirmation</title>

</head>

<body style="
margin:0;
padding:30px;
background:#f3f3f3;
font-family:Arial,Helvetica,sans-serif;
color:#444;
">

<div style="
max-width:640px;
margin:auto;
background:#ffffff;
border-radius:16px;
padding:35px;
">

<h1 style="
text-align:center;
color:#34472b;
">
Your message has been received.
</h1>

<p>
Dear {safe_name},
</p>

<p style="line-height:1.6;">
Thank you for contacting the Rural Organisation
for Social Emancipation (ROSE).
</p>

<p style="line-height:1.6;">
We have successfully received your message.
</p>

<div style="
background:#f7f8f9;
border-radius:10px;
padding:18px;
">

<strong>Name</strong>

<p>{safe_name}</p>

<strong>Email</strong>

<p>{safe_email}</p>

<strong>Subject</strong>

<p>{safe_subject}</p>

<strong>Your Message</strong>

<div style="
background:#ffffff;
border:1px solid #e2e2e2;
border-radius:7px;
padding:12px;
line-height:1.6;
">

{safe_message}

</div>

<p>

<strong>Submitted on</strong><br>

{safe_date}

</p>

</div>

<p style="line-height:1.6;">
Our team will review your message and get back
to you as soon as possible.
</p>

<hr>

<p>
Thank you for reaching out to ROSE.
</p>

<p>

Regards,<br>

<strong>
Rural Organisation for Social Emancipation (ROSE)
</strong>

<br>

{ROSE_EMAIL}

</p>

</div>

</body>
</html>
"""

    send_email(
        email,
        visitor_subject,
        visitor_body,
        visitor_html
    )

    rose_subject = (
        f"New ROSE Contact Message - {subject}"
    )

    rose_body = f"""
A new Contact Us message has been received.

Name:

{name}

Email:

{email}

Subject:

{subject}

Message:

{message}

Submitted on:

{contacted_at}

The contact message has been saved in contacts.txt.
"""

    send_email(
        ROSE_EMAIL,
        rose_subject,
        rose_body
    )


# ==========================================================
# CONTACT API
# ==========================================================

@app.route(
    "/contact",
    methods=["POST"]
)




def submit_contact():

    data = get_json_data()

    name = data.get(
        "name",
        ""
    )

    email = data.get(
        "email",
        ""
    )

    subject = data.get(
        "subject",
        "General Inquiry"
    )

    message = data.get(
        "message",
        ""
    )

    if not isinstance(name, str):
        name = ""

    if not isinstance(email, str):
        email = ""

    if not isinstance(subject, str):
        subject = "General Inquiry"

    if not isinstance(message, str):
        message = ""

    name = name.strip()
    email = email.strip()
    subject = subject.strip()
    message = message.strip()

    if not name:

        return jsonify({
            "success":
                False,

            "message":
                "Please enter your name."
        }), 400

    if len(name) > 100:

        return jsonify({
            "success":
                False,

            "message":
                "Name must not exceed 100 characters."
        }), 400

    if not valid_email(email):

        return jsonify({
            "success":
                False,

            "message":
                "Please enter a valid email address."
        }), 400

    if not subject:
        subject = "General Inquiry"

    if len(subject) > 100:

        return jsonify({
            "success":
                False,

            "message":
                "Subject must not exceed 100 characters."
        }), 400

    if not message:

        return jsonify({
            "success":
                False,

            "message":
                "Please enter your message."
        }), 400

    if len(message) > 500:

        return jsonify({
            "success":
                False,

            "message":
                "Message must not exceed 500 characters."
        }), 400

    contacted_at = now_ist()

    clean_name = clean_line(name)
    clean_email = clean_line(email)
    clean_subject = clean_line(subject)
    clean_message = clean_line(message)

    try:

        with CONTACT_FILE.open(
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                f"{contacted_at} | "
                f"Name: {clean_name} | "
                f"Email: {clean_email} | "
                f"Subject: {clean_subject} | "
                f"Message: {clean_message}\n"
            )

    except OSError as error:

        print(
            f"Contact file error: {error}"
        )

        return jsonify({
            "success":
                False,

            "message":
                "Unable to save your message. "
                "Please try again."
        }), 500

    print(
        f"New contact: {clean_name} | "
        f"{clean_email} | "
        f"{clean_subject} | "
        f"{contacted_at}"
    )

    run_in_background(
        send_contact_emails,
        clean_name,
        clean_email,
        clean_subject,
        clean_message,
        contacted_at
    )

    return jsonify({
        "success":
            True,

        "message":
            "Thank you for contacting ROSE. "
            "Your message has been sent successfully."
    }), 200

# ==========================================================
# DONATION API
# ==========================================================

@app.route(
    "/donation",
    methods=["POST"]
)
def submit_donation():

    data = get_json_data()

    name = data.get("name", "")
    email = data.get("email", "")
    phone = data.get("phone", "")
    pan = data.get("pan", "")
    amount = data.get("amount", "")
    transaction_id = data.get("transaction_id", "")
    transaction_date = data.get("transaction_date", "")
    bank_name = data.get("bank_name", "")
    account_holder_name = data.get(
        "account_holder_name",
        ""
    )
    account_last_four = data.get(
        "last_four_digits",
        ""
    )
    payment_method = data.get(
        "payment_method",
        ""
    )


    # Make sure all values are strings
    name = str(name).strip()
    email = str(email).strip()
    phone = str(phone).strip()
    pan = str(pan).strip()
    amount =str(amount).strip()
    transaction_id = str(
        transaction_id
    ).strip()
    transaction_date = str(
        transaction_date
    ).strip()
    bank_name = str(
        bank_name
    ).strip()
    account_holder_name = str(
        account_holder_name
    ).strip()
    account_last_four = str(
        account_last_four
    ).strip()
    payment_method = str(
        payment_method
    ).strip()


    # ------------------------------------------------------
    # BASIC VALIDATION
    # ------------------------------------------------------

    if not name:

        return jsonify({
            "success": False,
            "message": "Please enter your name."
        }), 400


    if not valid_email(email):

        return jsonify({
            "success": False,
            "message": "Please enter a valid email address."
        }), 400


    if not amount:

        return jsonify({
            "success": False,
            "message": "Please enter the donation amount."
        }), 400


    if not transaction_id:

        return jsonify({
            "success": False,
            "message": "Please enter the transaction ID."
        }), 400


    if not transaction_date:

        return jsonify({
            "success": False,
            "message": "Please enter the transaction date."
        }), 400


    donated_at = now_ist()


    # ------------------------------------------------------
    # SAVE DONATION DETAILS
    # ------------------------------------------------------

    clean_name = clean_line(name)
    clean_email = clean_line(email)
    clean_phone = clean_line(phone)
    clean_pan = clean_line(pan)
    clean_amount = clean_line(amount)
    clean_transaction_id = clean_line(
        transaction_id
    )
    clean_transaction_date = clean_line(
        transaction_date
    )
    clean_bank_name = clean_line(
        bank_name
    )
    clean_account_holder_name = clean_line(
        account_holder_name
    )
    clean_account_last_four = clean_line(
        account_last_four
    )
    clean_payment_method = clean_line(
        payment_method
    )


    try:

        with DONOR_FILE.open(
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                f"{donated_at} | "
                f"Name: {clean_name} | "
                f"Email: {clean_email} | "
                f"Phone: {clean_phone} | "
                f"PAN: {clean_pan} | "
                f"Amount: {clean_amount} | "
                f"Transaction ID: "
                f"{clean_transaction_id} | "
                f"Transaction Date: "
                f"{clean_transaction_date} | "
                f"Bank Name: {clean_bank_name} | "
                f"Account Holder: "
                f"{clean_account_holder_name} | "
                f"Account Last Four: "
                f"{clean_account_last_four} | "
                f"Payment Method: "
                f"{clean_payment_method}\n"
            )


    except OSError as error:

        print(
            f"Donation file error: {error}"
        )

        return jsonify({
            "success": False,
            "message":
                "Unable to save your donation details. "
                "Please try again."
        }), 500


    print(
        f"New donation: {clean_name} | "
        f"{clean_email} | "
        f"Amount: {clean_amount} | "
        f"Transaction ID: "
        f"{clean_transaction_id} | "
        f"{donated_at}"
    )


    return jsonify({
        "success": True,
        "message":
            "Thank you for your donation. "
            "Your payment details have been "
            "submitted successfully."
    }), 200
# ==========================================================
# ADMIN AUTHENTICATION
# ==========================================================

def admin_required():

    return session.get(
        "admin_logged_in",
        False
    )


# ==========================================================
# ADMIN LOGIN PAGE
# ==========================================================

@app.route(
    "/admin",
    methods=["GET"]
)
def admin_page():

    return send_from_directory(
        BASE_DIR,
        "admin.html"
    )


# ==========================================================
# ADMIN LOGIN
# ==========================================================

@app.route(
    "/admin/login",
    methods=["POST"]
)
def admin_login():

    data = get_json_data()

    print("DONATION DEBUG DATA:", data)
    print("DONATION DEBUG AMOUNT:", repr(data.get("amount")), type(data.get("amount")))

    username = data.get(
        "username",
        ""
    )

    password = data.get(
        "password",
        ""
    )

    if not isinstance(
        username,
        str
    ):
        username = ""

    if not isinstance(
        password,
        str
    ):
        password = ""

    username = username.strip()

    if not ADMIN_USERNAME or not ADMIN_PASSWORD:

        return jsonify({
            "success":
                False,

            "message":
                "Admin credentials are not configured."
        }), 500

    if (
        username == ADMIN_USERNAME
        and password == ADMIN_PASSWORD
    ):

        session.clear()

        session["admin_logged_in"] = True
        session["admin_username"] = username

        return jsonify({
            "success":
                True,

            "message":
                "Login successful."
        }), 200

    return jsonify({
        "success":
            False,

        "message":
            "Invalid username or password."
    }), 401


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

@app.route(
    "/admin/dashboard",
    methods=["GET"]
)
def admin_dashboard():

    if not admin_required():

        return redirect(
            "/admin"
        )

    return send_from_directory(
        BASE_DIR,
        "admin_dashboard.html"
    )


# ==========================================================
# ADMIN LOGOUT
# ==========================================================

@app.route(
    "/admin/logout",
    methods=["GET"]
)
def admin_logout():

    session.clear()

    return redirect(
        "/admin"
    )


# ==========================================================
# ADMIN PRIVATE DATA
# ==========================================================

@app.route(
    "/admin/private-data",
    methods=["GET"]
)
def admin_private_data():

    if not admin_required():

        return jsonify({
            "success":
                False,

            "message":
                "Unauthorized."
        }), 401

    files = [
        SUBSCRIBER_FILE,
        CONTACT_FILE,
        DONOR_FILE
    ]

    result = {}

    for file_path in files:

        filename = file_path.name

        if not file_path.exists():

            result[filename] = ""

            continue

        try:

            result[filename] = (
                file_path.read_text(
                    encoding="utf-8"
                )
            )

        except OSError as error:

            print(
                f"Private data read error: {error}"
            )

            result[filename] = (
                "Unable to read this file."
            )

    return jsonify({
        "success":
            True,

        "files":
            result
    }), 200


# ==========================================================
# ADMIN GALLERY DATA
# ==========================================================

@app.route(
    "/admin/gallery/data",
    methods=["GET"]
)
def admin_gallery_data():

    if not admin_required():

        return jsonify({
            "success":
                False,

            "message":
                "Unauthorized."
        }), 401

    data = load_gallery_data()

    return jsonify(
        data
    ), 200


# ==========================================================
# ADMIN GALLERY UPLOAD
# ==========================================================

@app.route(
    "/admin/gallery/upload",
    methods=["POST"]
)
def upload_gallery_image():

    if not admin_required():

        return jsonify({
            "success":
                False,

            "message":
                "Unauthorized."
        }), 401

    images = request.files.getlist(
        "images"
    )

    if not images:

        return jsonify({
            "success":
                False,

            "message":
                "No images selected."
        }), 400

    category = request.form.get(
        "category",
        ""
    ).strip()

    if category not in GALLERY_CATEGORIES:

        return jsonify({
            "success":
                False,

            "message":
                "Please select a valid gallery section."
        }), 400

    title = request.form.get(
        "title",
        ""
    ).strip()

    if not title:

        title = GALLERY_CATEGORIES[
            category
        ]

    uploaded_files = []
    failed_files = []

    for image in images:

        if not image.filename:
            continue

        original_filename = (
            image.filename
        )

        extension = (
            Path(
                original_filename
            )
            .suffix
            .lower()
            .replace(
                ".",
                ""
            )
        )

        if extension not in ALLOWED_IMAGE_EXTENSIONS:

            failed_files.append(
                original_filename
            )

            continue

        filename = secure_filename(
            original_filename
        )

        if not filename:

            failed_files.append(
                original_filename
            )

            continue

        save_path = (
            GALLERY_FOLDER
            / filename
        )

        try:

            image.save(
                save_path
            )

            json_saved = (
                add_image_to_gallery_json(
                    filename,
                    category,
                    title
                )
            )

            if json_saved:

                uploaded_files.append(
                    filename
                )

            else:

                try:
                    save_path.unlink()
                except OSError:
                    pass

                failed_files.append(
                    original_filename
                )

        except OSError as error:

            print(
                f"Gallery upload error: {error}"
            )

            failed_files.append(
                original_filename
            )

    return jsonify({

        "success":
            len(uploaded_files) > 0,

        "uploaded":
            uploaded_files,

        "failed":
            failed_files,

        "message":
            f"{len(uploaded_files)} image(s) uploaded successfully."
    }), 200


# ==========================================================
# ADMIN GALLERY DELETE
# ==========================================================

@app.route(
    "/admin/gallery/delete",
    methods=["POST"]
)
def delete_gallery_images():

    if not admin_required():

        return jsonify({
            "success":
                False,

            "message":
                "Unauthorized."
        }), 401

    data = get_json_data()

    filenames = data.get(
        "filenames",
        []
    )

    if not isinstance(
        filenames,
        list
    ):

        filenames = []

    if not filenames:

        return jsonify({
            "success":
                False,

            "message":
                "No images selected for deletion."
        }), 400

    deleted_count = 0
    failed_count = 0

    for filename in filenames:

        if not isinstance(
            filename,
            str
        ):

            failed_count += 1
            continue

        safe_filename = secure_filename(
            filename
        )

        if (
            not safe_filename
            or safe_filename != filename
        ):

            failed_count += 1
            continue

        image_path = (
            GALLERY_FOLDER
            / safe_filename
        )

        try:

            json_removed = (
                remove_image_from_gallery_json(
                    safe_filename
                )
            )

            if image_path.exists():

                image_path.unlink()

                deleted_count += 1

            elif json_removed:

                deleted_count += 1

            else:

                failed_count += 1

        except OSError as error:

            print(
                f"Gallery delete error: {error}"
            )

            failed_count += 1

    return jsonify({

        "success":
            True,

        "deleted":
            deleted_count,

        "failed":
            failed_count,

        "message":
            f"{deleted_count} image(s) deleted."
    }), 200


# ==========================================================
# GALLERY IMAGE ROUTE
# ==========================================================

@app.route(
    "/gallery/<filename>"
)
def gallery_image(
    filename
):

    return send_from_directory(
        GALLERY_FOLDER,
        filename
    )


# ==========================================================
# START SERVER
# ==========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )