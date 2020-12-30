from flask import Flask, make_response, redirect, request, Response, render_template, url_for, flash, g
from flask_mailman import Mail, Message
# from flask_sslify import SSLify
from flask_session import Session
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy, Pagination
from sqlalchemy import text, and_, exc, func
from database import db_session, init_db
from celery import Celery
from models import User, Visitor, URL
from forms import UserLoginForm, URLForm
from urllib.parse import urlparse, urljoin
import config
import random
import datetime
import hashlib
import time
import redis
import uuid
import requests

# debug
debug = True
timeout = 0.50

# app config
app = Flask(__name__)
# sslify = SSLify(app)
app.config["SECRET_KEY"] = config.SECRET_KEY

# session persistence
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = redis.from_url("redis://localhost:6379")
app.config["SESSION_PERMANENT"] = True
sess = Session()
sess.init_app(app)


# Flask-Mail configuration
app.config["MAIL_SERVER"] = "smtp.mailgun.org"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = config.MAIL_USERNAME
app.config["MAIL_PASSWORD"] = config.MAIL_PASSWORD
app.config["MAIL_DEFAULT_SENDER"] = config.MAIL_DEFAULT_SENDER

# SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS
# db = SQLAlchemy(app)

# define our login_manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/auth/login"
login_manager.login_message = "Login required to access this site."
login_manager.login_message_category = "primary"

# disable strict slashes
app.url_map.strict_slashes = False

# Celery config
app.config["CELERY_BROKER_URL"] = config.CELERY_BROKER_URL
app.config["CELERY_RESULT_BACKEND"] = config.CELERY_RESULT_BACKEND
app.config["CELERY_ACCEPT_CONTENT"] = config.CELERY_ACCEPT_CONTENT
app.config.update(accept_content=["json", "pickle"])

# Initialize Celery
celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)

# Config mail
mail = Mail(app)

# on the apps first startup, init the db
@app.before_first_request
def create_db():
    """
    Create and init the database
    :return initialized database from models.py
    """
    init_db()
    

# clear all db sessions at the end of each request
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


# load the user
@login_manager.user_loader
def load_user(id):
    try:
        return db_session.query(User).get(int(id))
    except exc.SQLAlchemyError as err:
        return None


# run before each request
@app.before_request
def before_request():
    g.user = current_user


# tasks sections, for async functions, etc...
@celery.task(serializer="pickle")
def send_async_email(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)


@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ["Starting up", "Booting", "Repairing", "Loading", "Checking"]
    adjective = ["master", "radiant", "silent", "harmonic", "fast"]
    noun = ["solar array", "particle reshaper", "cosmic ray", "orbiter", "bit"]
    message = ""
    total = random.randint(10, 500)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = "{0} {1} {2}...".format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        
        self.update_state(
            state =  "PROGRESS", 
            meta = {
                "current": i, 
                "total": total,
                "status": message
            }
        )
        # log the result
        app.logger.info("New Message: {}".format(str(message)))
        time.sleep(1)
    
    return {
            "current": 100, 
            "total": 100, 
            "status": "Task completed!",
            "result": total
            }


# default routes
@app.route("/", methods=["GET", "POST"])
# @app.route("/index", methods=["GET", "POST"])
def index():
    """
    The default view
    :return: databoxes
    """
    form = URLForm()
    context = None

    if request.method == "POST":
        if "fetch-url" in request.form.keys(): # and form.validate_on_submit():
            url = form.url.data
            try:
                p = parse_url(url)
                if isinstance(p, tuple):
                    scheme, netloc, path, params, query = p[0], p[1], p[2], p[3], p[4]
                    # set the url scheme
                    if scheme.startswith("https"):
                        scheme = "https://"
                    else:
                        scheme = "http://"
                    
                    # rebuild the url string from the components
                    req_url = scheme + netloc + path + query
                    try:
                        # call the URL to make sure it's up
                        r = requests.request(
                            "GET",
                            req_url,
                            timeout=timeout
                        )

                        if r.status_code == 200:
                            # set the request headers to encode
                            headers = {}
                            headers["content-type"] = request.headers["Content-Type"]
                            headers["content-length"] = request.headers["Content-Length"]
                            headers["host"] = request.headers["host"]
                            headers["accept-encoding"] = request.headers["Accept-Encoding"]
                            headers["accept"] = request.headers["Accept"]
                            headers["timestamp"] = datetime.datetime.now()
                            headers_hash = hashlib.sha256(str(headers).encode()).hexdigest()
                            
                            try:
                                encoded = str(headers["timestamp"]).encode() + req_url.encode()
                                url_hash = hashlib.sha256(encoded).hexdigest()
                                short_hash = url_hash[:10]

                                try:
                                    # create a new short url
                                    new_url = URL(
                                        user_id=1,
                                        full_url=str(req_url),
                                        short_url=short_hash,
                                        full_hash=url_hash,
                                        raw_request_headers=headers_hash,
                                        request_headers_hash=headers_hash,
                                        global_id=str(uuid.uuid4()),
                                        created_on_date=datetime.datetime.now(),
                                        modified_date=datetime.datetime.now(),
                                        clicks=0,
                                        archived=False,
                                        is_url_active=True
                                    )
                                    # add the url to the table
                                    db_session.add(new_url)
                                    db_session.commit()
                                    new_url_id = new_url.id
                                    db_session.flush()
                                    flash("Success.  Created URL: {}".format(str(new_url_id)), 
                                        category="info")
                                    context = {
                                        "id": new_url_id,
                                        "full_url": url, 
                                        "full_hash": url_hash,
                                        "short_hash": short_hash,
                                        "clicks": 0,
                                        "active": True,
                                        "headers": headers,
                                        "hdr_hash": headers_hash,
                                        "url": {
                                            "scheme": scheme,
                                            "netloc": netloc,
                                            "path": path or None,
                                            "query": query or None
                                        }
                                    }

                                except exc.SQLAlchemyError as db_err:
                                    flash("A database error: {}".format(str(db_err)), category="danger")
                                    return redirect(url_for("index"))

                            except ValueError as err:
                                flash("Value Error: {}".format(str(err)), category="danger")
                                app.logger("Can not encode the input URL string.")
                                return redirect(url_for("index"))
                        else:
                            msg = "HTTP call returned error: {}".format(str(r.status_code))
                            flash("{}".format(msg), category="danger")
                            return redirect(url_for("index"))
                    
                    except requests.exceptions.ReadTimeout as read_timeout:
                        flash("{}".format(str(read_timeout)), category="danger")
                        return redirect(url_for("index"))
                    
                    except requests.HTTPError as http_err:
                        flash("{}".format(str(http_err)), category="danger")
                        return redirect(url_for("index"))

            except (ValueError, TypeError) as parse_error:
                flash("{}".format(str(parse_error)), category="danger")
                return redirect(url_for("index"))

    return render_template(
        "index.html",
        today=get_date(),
        form=form,
        context=context
    )


@app.route("/<id>", methods=["GET"])
def fetch_url(id):
    """
    Get the Long URL by the Hash
    """
    try:
        url_hash = str(id)
        try:
            url = db_session.query(URL).filter(
                URL.short_url == url_hash
            ).first()
            if url:
                full_url = url.full_url
                url.clicks += 1
                db_session.commit()
                db_session.flush()
                flash("URL Location found for: {}".format(str(url_hash)), category="info")
                return redirect(url.full_url)
            else:
                flash("No long URL found for the hash: {}".format(str(id)), category="danger")
                return redirect(url_for("index"))
        except exc.SQLAlchemyError as db_err:
            flash("Database error: {}".format(str(db_err)), category="danger")
            return redirect(url_for("index"))
    except ValueError as ve:
        flash("The hash for the URL is invalid: {}".format(str(ve)), category="danger")
        return redirect(url_for("index"))


@app.route("/auth/login", methods=["GET", "POST"])
def login():
    """
    Login user page
    """
    return render_template(
        "login.html", 
        today=get_date()
    )


@app.route('/logout', methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.errorhandler(404)
def page_not_found(err):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(err):
    return render_template("500.html"), 500


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ))


def parse_url(url):
    """
    Parse the URL
    :return tuple
    """
    try:
        str(url)
        parsed = urlparse(url)
        return parsed
    except ValueError as err:
        return "{}".format(str(err))

def get_date():
    # set the current date time for each page
    today = datetime.datetime.now().strftime("%c")
    return "{}".format(today)


@app.template_filter("formatdate")
def format_date(value):
    dt = value
    return dt.strftime("%Y-%m-%d %H:%M")


@app.template_filter("datemdy")
def format_date(value):
    dt = value
    return dt.strftime("%m/%d/%Y")


@app.template_filter("formatnumber")
def format_number(value):
    _val = int(value)
    return "{:,}".format(_val)


@app.template_filter("formatphonenumber")
def format_phone_number(value):
    phone_number = value.replace("(-)", "")
    return "{}-{}-{}".format(phone_number[:3], phone_number[3:6], phone_number[6:])


if __name__ == "__main__":
    port = 5580
    # start the application
    app.run(
        debug=debug,
        port=port
    )

