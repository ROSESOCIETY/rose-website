"""

ROSE Website Backend

Handles:

\- Website pages

\- Newsletter subscriptions

\- Contact Us submissions

\- Post-payment donation verification

\- Confirmation and notification emails

\- Private admin login and data viewing

\- Admin gallery uploads and deletion

"""

from flask import (

    Flask,

    request,

    jsonify,

    send\_from\_directory,

    session,

    redirect

)

from pathlib import Path

from datetime import datetime

from email.message import EmailMessage

from dotenv import load\_dotenv

from flask\_cors import CORS

from werkzeug.utils import secure\_filename

import smtplib

import os

import re

import threading

import html

import json



\# ==========================================================

\# ENVIRONMENT

\# ==========================================================

load\_dotenv()

app = Flask(\_\_name\_\_)

BASE\_DIR = Path(\_\_file\_\_).resolve().parent

app.secret\_key = os.getenv(

    "FLASK\_SECRET\_KEY",

    "CHANGE-THIS-SECRET-KEY"

)

frontend\_origin = os.getenv(

    "FRONTEND\_ORIGIN",

    "\*"

)

CORS(

    app,

    origins=frontend\_origin

)



\# ==========================================================

\# DATA FILES

\# ==========================================================

PRIVATE\_DATA\_FOLDER = BASE\_DIR / "private\_data"

PRIVATE\_DATA\_FOLDER.mkdir(exist\_ok=True)

SUBSCRIBER\_FILE = (

    PRIVATE\_DATA\_FOLDER / "subscribers.txt"

)

CONTACT\_FILE = (

    PRIVATE\_DATA\_FOLDER / "contacts.txt"

)

DONOR\_FILE = (

    PRIVATE\_DATA\_FOLDER / "donorDetails.txt"

)



\# ==========================================================

\# GALLERY

\# ==========================================================

GALLERY\_FOLDER = BASE\_DIR / "gallery"

GALLERY\_FOLDER.mkdir(exist\_ok=True)

GALLERY\_JSON\_FILE = (

    BASE\_DIR / "gallery\_json.json"

)

ALLOWED\_IMAGE\_EXTENSIONS = {

    "jpg",

    "jpeg",

    "png",

    "webp"

}

GALLERY\_CATEGORIES = {

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



\# ==========================================================

\# ROSE EMAIL

\# ==========================================================

ROSE\_EMAIL = "roseorg22\@gmail.com"



\# ==========================================================

\# SMTP

\# ==========================================================

SMTP\_HOST = "smtp.gmail.com"

SMTP\_PORT = 587

SMTP\_EMAIL = os.getenv(

    "SMTP\_EMAIL"

)

SMTP\_PASSWORD = os.getenv(

    "SMTP\_PASSWORD"

)



\# ==========================================================

\# ADMIN

\# ==========================================================

ADMIN\_USERNAME = os.getenv(

    "ADMIN\_USERNAME"

)

ADMIN\_PASSWORD = os.getenv(

    "ADMIN\_PASSWORD"

)



\# ==========================================================

\# UPI

\# ==========================================================

ROSE\_UPI\_ID = os.getenv(

    "ROSE\_UPI\_ID",

    ""

)

ROSE\_UPI\_NAME = (

    "Rural Organisation For Social Emancipation"

)



\# ==========================================================

\# SESSION SECURITY

\# ==========================================================

app.config.update(

    SESSION\_COOKIE\_HTTPONLY=True,

    SESSION\_COOKIE\_SAMESITE="Lax",

    SESSION\_COOKIE\_SECURE=

        os.getenv(

            "SESSION\_COOKIE\_SECURE",

            "false"

        ).lower() == "true"

)



\# ==========================================================

\# HELPER FUNCTIONS

\# ==========================================================

def now\_ist():

    return datetime.now().strftime(

        "%Y-%m-%d %H:%M:%S IST"

    )



def clean\_line(value):

    return (

        str(value)

        .replace("|", " ")

        .replace("\r", " ")

        .replace("\n", " ")

        .strip()

    )



def valid\_email(email):

    pattern = (

        r"^[A-Za-z0-9.!#$%&'\*+/=?^\_\`{|}\~-]+"

        r"@[A-Za-z0-9-]+"

        r"(?:**\\.**[A-Za-z0-9-]+)+$"

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



def get\_json\_data():

    if not request.is\_json:

        return {}

    try:

        data = request.get\_json(

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



def send\_email(

    receiver,

    subject,

    body,

    html\_body=None

):

    if not SMTP\_EMAIL or not SMTP\_PASSWORD:

        print(

            "SMTP email credentials are not configured."

        )

        return False

    try:

        message = EmailMessage()

        message["From"] = SMTP\_EMAIL

        message["To"] = receiver

        message["Subject"] = subject

        message.set\_content(

            body

        )

        if html\_body:

            message.add\_alternative(

                html\_body,

                subtype="html"

            )

        with smtplib.SMTP(

            SMTP\_HOST,

            SMTP\_PORT

        ) as server:

            server.starttls()

            server.login(

                SMTP\_EMAIL,

                SMTP\_PASSWORD

            )

            server.send\_message(

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



def run\_in\_background(

    function,

    \*args

):

    thread = threading.Thread(

        target=function,

        args=args,

        daemon=True

    )

    thread.start()



def already\_subscribed(email):

    if not SUBSCRIBER\_FILE.exists():

        return False

    with SUBSCRIBER\_FILE.open(

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

            saved\_email = (

                line

                .split("|", 1)[0]

                .strip()

            )

            if (

                saved\_email.lower()

                == email.lower()

            ):

                return True

    return False



\# ==========================================================

\# GALLERY JSON HELPERS

\# ==========================================================

def default\_gallery\_data():

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



def save\_gallery\_data(data):

    try:

        with GALLERY\_JSON\_FILE.open(

            "w",

            encoding="utf-8"

        ) as file:

            json.dump(

                data,

                file,

                indent=2,

                ensure\_ascii=False

            )

        return True

    except OSError as error:

        print(

            f"Gallery JSON save error: {error}"

        )

        return False



def load\_gallery\_data():

    if not GALLERY\_JSON\_FILE.exists():

        data = default\_gallery\_data()

        save\_gallery\_data(data)

        return data

    try:

        with GALLERY\_JSON\_FILE.open(

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

        return default\_gallery\_data()



def find\_gallery\_section(

    data,

    section\_id

):

    for section in data.get(

        "sections",

        []

    ):

        if section.get(

            "id"

        ) == section\_id:

            return section

    return None



def find\_gallery\_photo(

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



def add\_image\_to\_gallery\_json(

    filename,

    category,

    title

):

    data = load\_gallery\_data()

    section = find\_gallery\_section(

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

    return save\_gallery\_data(

        data

    )



def remove\_image\_from\_gallery\_json(

    filename

):

    data = load\_gallery\_data()

    for section in data.get(

        "sections",

        []

    ):

        photos = section.get(

            "photos",

            []

        )

        original\_count = len(

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

        ) < original\_count:

            return save\_gallery\_data(

                data

            )

    return False



\# ==========================================================

\# PAGE ROUTES

\# ==========================================================

@app.route("/index.html")

def home():

    return send\_from\_directory(

        BASE\_DIR,

        "index.html"

    )



@app.route("/newsletter.html")

def newsletter():

    return send\_from\_directory(

        BASE\_DIR,

        "newsletter.html"

    )



@app.route("/contact.html")

def contact\_page():

    return send\_from\_directory(

        BASE\_DIR,

        "contact.html"

    )



@app.route("/donate.html")

def donate\_page():

    return send\_from\_directory(

        BASE\_DIR,

        "donate.html"

    )



@app.route("/aboutUs.html")

def about\_us():

    return send\_from\_directory(

        BASE\_DIR,

        "aboutUs.html"

    )



@app.route("/programs.html")

def programs():

    return send\_from\_directory(

        BASE\_DIR,

        "programs.html"

    )



@app.route("/blog.html")

def blog():

    return send\_from\_directory(

        BASE\_DIR,

        "blog.html"

    )



@app.route("/gallery\_html.html")

def gallery\_page():

    return send\_from\_directory(

        BASE\_DIR,

        "gallery\_html.html"

    )



\# ==========================================================

\# GALLERY JSON ROUTES

\# ==========================================================

@app.route("/gallery\_json.json")

def gallery\_json():

    return jsonify(

        load\_gallery\_data()

    )



@app.route("/api/gallery")

def gallery\_api():

    return jsonify(

        load\_gallery\_data()

    )



\# ==========================================================

\# NEWSLETTER EMAILS

\# ==========================================================

def send\_newsletter\_emails(

    email,

    subscribed\_at

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

{subscribed\_at}

You will receive updates about our programs,

success stories, events and other activities

of the Rural Organisation for Social Emancipation (ROSE).

Thank you for staying connected with ROSE.

Regards,

Rural Organisation for Social Emancipation (ROSE)

{ROSE\_EMAIL}

"""

    safe\_email = html.escape(

        email

    )

    safe\_date = html.escape(

        subscribed\_at

    )

    html\_body = f"""

\<!DOCTYPE html>

\<html>

\<head>

\<meta charset="UTF-8">

\<meta name="viewport"

content="width=device-width,initial-scale=1.0">

\<title>ROSE Newsletter Confirmation\</title>

\</head>

\<body style="

margin:0;

padding:30px;

background:#f3f3f3;

font-family\:Arial,Helvetica,sans-serif;

color:#444;

">

\<div style="

max-width:640px;

margin\:auto;

background:#fff;

border-radius:16px;

padding:35px;

box-sizing\:border-box;

">

\<h1 style="

text-align\:center;

color:#333;

">

Your subscription has been received.

\</h1>

\<p>

Dear Subscriber,

\</p>

\<p>

Thank you for subscribing to the ROSE Newsletter.

\</p>

\<p>

Your subscription was successfully received.

\</p>

\<div style="

background:#f7f8f9;

border-radius:8px;

padding:16px;

">

\<div style="

color:#999;

font-size:14px;

">

Subscription Email

\</div>

\<div style="

font-size:16px;

font-weight\:bold;

color:#1769d1;

">

{safe\_email}

\</div>

\<div style="

color:#999;

font-size:14px;

margin-top:15px;

">

Subscription Date

\</div>

\<div style="

font-size:16px;

">

{safe\_date}

\</div>

\</div>

\<p style="

line-height:1.6;

">

You will receive updates about our programs,

success stories, events and other activities

of the Rural Organisation for Social Emancipation (ROSE).

\</p>

\<p>

Thank you for staying connected with ROSE.

\</p>

\<p>

Regards,\<br>

\<strong>

Rural Organisation for Social Emancipation (ROSE)

\</strong>

\<br>

{ROSE\_EMAIL}

\</p>

\</div>

\</body>

\</html>

"""

    send\_email(

        email,

        subject,

        plain,

        html\_body

    )

    rose\_body = f"""

A new newsletter subscription has been received.

Subscriber Email:

{email}

Subscription Date:

{subscribed\_at}

The subscriber has been added to subscribers.txt.

"""

    send\_email(

        ROSE\_EMAIL,

        "New ROSE Newsletter Subscriber",

        rose\_body

    )



\# ==========================================================

\# NEWSLETTER API

\# ==========================================================

@app.route(

    "/subscribe",

    methods=["POST"]

)

def subscribe():

    data = get\_json\_data()

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

    if not valid\_email(email):

        return jsonify({

            "success":

                False,

            "message":

                "Please enter a valid email address."

        }), 400

    if already\_subscribed(email):

        return jsonify({

            "success":

                False,

            "message":

                "This email is already subscribed."

        }), 200

    subscribed\_at = now\_ist()

    try:

        with SUBSCRIBER\_FILE.open(

            "a",

            encoding="utf-8"

        ) as file:

            file.write(

                f"{email} | subscribed on: "

                f"{subscribed\_at}\n"

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

        f"Subscribed on: {subscribed\_at}"

    )

    run\_in\_background(

        send\_newsletter\_emails,

        email,

        subscribed\_at

    )

    return jsonify({

        "success":

            True,

        "message":

            "Subscribed successfully!"

    }), 200



\# ==========================================================

\# CONTACT EMAILS

\# ==========================================================

def send\_contact\_emails(

    name,

    email,

    subject,

    message,

    contacted\_at

):

    visitor\_subject = (

        "ROSE Contact Form Confirmation"

    )

    visitor\_body = f"""

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

{contacted\_at}

Our team will review your message and

get back to you as soon as possible.

Thank you for reaching out to ROSE.

Regards,

Rural Organisation for Social Emancipation (ROSE)

{ROSE\_EMAIL}

"""

    safe\_name = html.escape(name)

    safe\_email = html.escape(email)

    safe\_subject = html.escape(subject)

    safe\_message = html.escape(message)

    safe\_date = html.escape(contacted\_at)

    visitor\_html = f"""

\<!DOCTYPE html>

\<html>

\<head>

\<meta charset="UTF-8">

\<meta name="viewport"

content="width=device-width,initial-scale=1.0">

\<title>ROSE Contact Confirmation\</title>

\</head>

\<body style="

margin:0;

padding:30px;

background:#f3f3f3;

font-family\:Arial,Helvetica,sans-serif;

color:#444;

">

\<div style="

max-width:640px;

margin\:auto;

background:#ffffff;

border-radius:16px;

padding:35px;

">

\<h1 style="

text-align\:center;

color:#34472b;

">

Your message has been received.

\</h1>

\<p>

Dear {safe\_name},

\</p>

\<p style="line-height:1.6;">

Thank you for contacting the Rural Organisation

for Social Emancipation (ROSE).

\</p>

\<p style="line-height:1.6;">

We have successfully received your message.

\</p>

\<div style="

background:#f7f8f9;

border-radius:10px;

padding:18px;

">

\<strong>Name\</strong>

\<p>{safe\_name}\</p>

\<strong>Email\</strong>

\<p>{safe\_email}\</p>

\<strong>Subject\</strong>

\<p>{safe\_subject}\</p>

\<strong>Your Message\</strong>

\<div style="

background:#ffffff;

border:1px solid #e2e2e2;

border-radius:7px;

padding:12px;

line-height:1.6;

">

{safe\_message}

\</div>

\<p>

\<strong>Submitted on\</strong>\<br>

{safe\_date}

\</p>

\</div>

\<p style="line-height:1.6;">

Our team will review your message and get back

to you as soon as possible.

\</p>

\<hr>

\<p>

Thank you for reaching out to ROSE.

\</p>

\<p>

Regards,\<br>

\<strong>

Rural Organisation for Social Emancipation (ROSE)

\</strong>

\<br>

{ROSE\_EMAIL}

\</p>

\</div>

\</body>

\</html>

"""

    send\_email(

        email,

        visitor\_subject,

        visitor\_body,

        visitor\_html

    )

    rose\_subject = (

        f"New ROSE Contact Message - {subject}"

    )

    rose\_body = f"""

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

{contacted\_at}

The contact message has been saved in contacts.txt.

"""

    send\_email(

        ROSE\_EMAIL,

        rose\_subject,

        rose\_body

    )



\# ==========================================================

\# CONTACT API

\# ==========================================================

@app.route(

    "/contact",

    methods=["POST"]

)

def submit\_contact():

    data = get\_json\_data()

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

    if not valid\_email(email):

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

    contacted\_at = now\_ist()

    clean\_name = clean\_line(name)

    clean\_email = clean\_line(email)

    clean\_subject = clean\_line(subject)

    clean\_message = clean\_line(message)

    try:

        with CONTACT\_FILE.open(

            "a",

            encoding="utf-8"

        ) as file:

            file.write(

                f"{contacted\_at} | "

                f"Name: {clean\_name} | "

                f"Email: {clean\_email} | "

                f"Subject: {clean\_subject} | "

                f"Message: {clean\_message}\n"

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

        f"New contact: {clean\_name} | "

        f"{clean\_email} | "

        f"{clean\_subject} | "

        f"{contacted\_at}"

    )

    run\_in\_background(

        send\_contact\_emails,

        clean\_name,

        clean\_email,

        clean\_subject,

        clean\_message,

        contacted\_at

    )

    return jsonify({

        "success":

            True,

        "message":

            "Thank you for contacting ROSE. "

            "Your message has been sent successfully."

    }), 200

\# ==========================================================

\# DONATION API

\# ==========================================================

@app.route(

    "/donation",

    methods=["POST"]

)

def submit\_donation():

    data = get\_json\_data()

    name = data.get("name", "")

    email = data.get("email", "")

    phone = data.get("phone", "")

    pan = data.get("pan", "")

    amount = data.get("amount", "")

    transaction\_id = data.get("transaction\_id", "")

    transaction\_date = data.get("transaction\_date", "")

    bank\_name = data.get("bank\_name", "")

    account\_holder\_name = data.get(

        "account\_holder\_name",

        ""

    )

    account\_last\_four = data.get(

        "last\_four\_digits",

        ""

    )

    payment\_method = data.get(

        "payment\_method",

        ""

    )

    # Make sure all values are strings

    fields = [

        "name",

        "email",

        "phone",

        "pan",

        "amount",

        "transaction\_id",

        "transaction\_date",

        "bank\_name",

        "account\_holder\_name",

        "account\_last\_four",

        "payment\_method"

    ]

    for field in fields:

        value = data.get(field, "")

        if not isinstance(value, str):

            value = ""

        data[field] = value.strip()

    name = data["name"]

    email = data["email"]

    phone = data["phone"]

    pan = data["pan"]

    amount = data["amount"]

    transaction\_id = data["transaction\_id"]

    transaction\_date = data["transaction\_date"]

    bank\_name = data["bank\_name"]

    account\_holder\_name = data["account\_holder\_name"]

    account\_last\_four = data["account\_last\_four"]

    payment\_method = data["payment\_method"]

    # ------------------------------------------------------

    # BASIC VALIDATION

    # ------------------------------------------------------

    if not name:

        return jsonify({

            "success": False,

            "message": "Please enter your name."

        }), 400

    if not valid\_email(email):

        return jsonify({

            "success": False,

            "message": "Please enter a valid email address."

        }), 400

    if not amount:

        return jsonify({

            "success": False,

            "message": "Please enter the donation amount."

        }), 400

    if not transaction\_id:

        return jsonify({

            "success": False,

            "message": "Please enter the transaction ID."

        }), 400

    if not transaction\_date:

        return jsonify({

            "success": False,

            "message": "Please enter the transaction date."

        }), 400

    donated\_at = now\_ist()

    # ------------------------------------------------------

    # SAVE DONATION DETAILS

    # ------------------------------------------------------

    clean\_name = clean\_line(name)

    clean\_email = clean\_line(email)

    clean\_phone = clean\_line(phone)

    clean\_pan = clean\_line(pan)

    clean\_amount = clean\_line(amount)

    clean\_transaction\_id = clean\_line(transaction\_id)

    clean\_transaction\_date = clean\_line(transaction\_date)

    clean\_bank\_name = clean\_line(bank\_name)

    clean\_account\_holder\_name = clean\_line(

        account\_holder\_name

    )

    clean\_account\_last\_four = clean\_line(

        account\_last\_four

    )

    clean\_payment\_method = clean\_line(

        payment\_method

    )

    try:

        with DONOR\_FILE.open(

            "a",

            encoding="utf-8"

        ) as file:

            file.write(

                f"{donated\_at} | "

                f"Name: {clean\_name} | "

                f"Email: {clean\_email} | "

                f"Phone: {clean\_phone} | "

                f"PAN: {clean\_pan} | "

                f"Amount: {clean\_amount} | "

                f"Transaction ID: "

                f"{clean\_transaction\_id} | "

                f"Transaction Date: "

                f"{clean\_transaction\_date} | "

                f"Bank Name: {clean\_bank\_name} | "

                f"Account Holder: "

                f"{clean\_account\_holder\_name} | "

                f"Account Last Four: "

                f"{clean\_account\_last\_four} | "

                f"Payment Method: "

                f"{clean\_payment\_method}\n"

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

        f"New donation: {clean\_name} | "

        f"{clean\_email} | "

        f"Amount: {clean\_amount} | "

        f"Transaction ID: "

        f"{clean\_transaction\_id} | "

        f"{donated\_at}"

    )

    return jsonify({

        "success": True,

        "message":

            "Thank you for your donation. "

            "Your payment details have been "

            "submitted successfully."

    }), 200

\# ==========================================================

\# ADMIN AUTHENTICATION

\# ==========================================================

def admin\_required():

    return session.get(

        "admin\_logged\_in",

        False

    )



\# ==========================================================

\# ADMIN LOGIN PAGE

\# ==========================================================

@app.route(

    "/admin",

    methods=["GET"]

)

def admin\_page():

    return send\_from\_directory(

        BASE\_DIR,

        "admin.html"

    )



\# ==========================================================

\# ADMIN LOGIN

\# ==========================================================

@app.route(

    "/admin/login",

    methods=["POST"]

)

def admin\_login():

    data = get\_json\_data()

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

    if not ADMIN\_USERNAME or not ADMIN\_PASSWORD:

        return jsonify({

            "success":

                False,

            "message":

                "Admin credentials are not configured."

        }), 500

    if (

        username == ADMIN\_USERNAME

        and password == ADMIN\_PASSWORD

    ):

        session.clear()

        session["admin\_logged\_in"] = True

        session["admin\_username"] = username

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



\# ==========================================================

\# ADMIN DASHBOARD

\# ==========================================================

@app.route(

    "/admin/dashboard",

    methods=["GET"]

)

def admin\_dashboard():

    if not admin\_required():

        return redirect(

            "/admin"

        )

    return send\_from\_directory(

        BASE\_DIR,

        "admin\_dashboard.html"

    )



\# ==========================================================

\# ADMIN LOGOUT

\# ==========================================================

@app.route(

    "/admin/logout",

    methods=["GET"]

)

def admin\_logout():

    session.clear()

    return redirect(

        "/admin"

    )



\# ==========================================================

\# ADMIN PRIVATE DATA

\# ==========================================================

@app.route(

    "/admin/private-data",

    methods=["GET"]

)

def admin\_private\_data():

    if not admin\_required():

        return jsonify({

            "success":

                False,

            "message":

                "Unauthorized."

        }), 401

    files = [

        SUBSCRIBER\_FILE,

        CONTACT\_FILE,

        DONOR\_FILE

    ]

    result = {}

    for file\_path in files:

        filename = file\_path.name

        if not file\_path.exists():

            result[filename] = ""

            continue

        try:

            result[filename] = (

                file\_path.read\_text(

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



\# ==========================================================

\# ADMIN GALLERY DATA

\# ==========================================================

@app.route(

    "/admin/gallery/data",

    methods=["GET"]

)

def admin\_gallery\_data():

    if not admin\_required():

        return jsonify({

            "success":

                False,

            "message":

                "Unauthorized."

        }), 401

    data = load\_gallery\_data()

    return jsonify(

        data

    ), 200



\# ==========================================================

\# ADMIN GALLERY UPLOAD

\# ==========================================================

@app.route(

    "/admin/gallery/upload",

    methods=["POST"]

)

def upload\_gallery\_image():

    if not admin\_required():

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

    if category not in GALLERY\_CATEGORIES:

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

        title = GALLERY\_CATEGORIES[

            category

        ]

    uploaded\_files = []

    failed\_files = []

    for image in images:

        if not image.filename:

            continue

        original\_filename = (

            image.filename

        )

        extension = (

            Path(

                original\_filename

            )

            .suffix

            .lower()

            .replace(

                ".",

                ""

            )

        )

        if extension not in ALLOWED\_IMAGE\_EXTENSIONS:

            failed\_files.append(

                original\_filename

            )

            continue

        filename = secure\_filename(

            original\_filename

        )

        if not filename:

            failed\_files.append(

                original\_filename

            )

            continue

        save\_path = (

            GALLERY\_FOLDER

            / filename

        )

        try:

            image.save(

                save\_path

            )

            json\_saved = (

                add\_image\_to\_gallery\_json(

                    filename,

                    category,

                    title

                )

            )

            if json\_saved:

                uploaded\_files.append(

                    filename

                )

            else:

                try:

                    save\_path.unlink()

                except OSError:

                    pass

                failed\_files.append(

                    original\_filename

                )

        except OSError as error:

            print(

                f"Gallery upload error: {error}"

            )

            failed\_files.append(

                original\_filename

            )

    return jsonify({

        "success":

            len(uploaded\_files) > 0,

        "uploaded":

            uploaded\_files,

        "failed":

            failed\_files,

        "message":

            f"{len(uploaded\_files)} image(s) uploaded successfully."

    }), 200



\# ==========================================================

\# ADMIN GALLERY DELETE

\# ==========================================================

@app.route(

    "/admin/gallery/delete",

    methods=["POST"]

)

def delete\_gallery\_images():

    if not admin\_required():

        return jsonify({

            "success":

                False,

            "message":

                "Unauthorized."

        }), 401

    data = get\_json\_data()

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

    deleted\_count = 0

    failed\_count = 0

    for filename in filenames:

        if not isinstance(

            filename,

            str

        ):

            failed\_count += 1

            continue

        safe\_filename = secure\_filename(

            filename

        )

        if (

            not safe\_filename

            or safe\_filename != filename

        ):

            failed\_count += 1

            continue

        image\_path = (

            GALLERY\_FOLDER

            / safe\_filename

        )

        try:

            json\_removed = (

                remove\_image\_from\_gallery\_json(

                    safe\_filename

                )

            )

            if image\_path.exists():

                image\_path.unlink()

                deleted\_count += 1

            elif json\_removed:

                deleted\_count += 1

            else:

                failed\_count += 1

        except OSError as error:

            print(

                f"Gallery delete error: {error}"

            )

            failed\_count += 1

    return jsonify({

        "success":

            True,

        "deleted":

            deleted\_count,

        "failed":

            failed\_count,

        "message":

            f"{deleted\_count} image(s) deleted."

    }), 200



\# ==========================================================

\# GALLERY IMAGE ROUTE

\# ==========================================================

@app.route(

    "/gallery/\<filename>"

)

def gallery\_image(

    filename

):

    return send\_from\_directory(

        GALLERY\_FOLDER,

        filename

    )



\# ==========================================================

\# START SERVER

\# ==========================================================

if \_\_name\_\_ == "\_\_main\_\_":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=False

    )