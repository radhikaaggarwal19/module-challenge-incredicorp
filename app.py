import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy  # Import SQLAlchemy here
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from google.cloud import secretmanager
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Secret key for session management

# GCP secret manager
client = secretmanager.SecretManagerServiceClient()
requests = "projects/99223452659/secrets/flaskcrud-secret/versions/1"
response = client.access_secret_version({"name":requests})
secret_dict = json.loads(response.payload.data.decode("utf-8"))

dbUsername = secret_dict["dbUsername"]
dbPassword = secret_dict["dbPassword"]
dbName = secret_dict["dbName"]
dbHost = secret_dict["dbHost"]
dbInstance = secret_dict["dbInstance"]
instanceUnixSocket = secret_dict["instanceUnixSocket"]
dbPort = 3306

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{dbUsername}:{dbPassword}@{dbHost}:{dbPort}/{dbName}?unix_socket={instanceUnixSocket}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app)

# # Cloud SQL connection settings (replace with your actual values)
# CLOUD_SQL_CONNECTION_NAME = 'module-challenge-incredicorp:us-central1:banking-db'
# DB_USER = 'flask_user'
# DB_PASSWORD = 'root'
# DB_NAME = 'banking_app_db'

# # SQLAlchemy configuration to connect to Cloud SQL
# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@/cloudsql/{CLOUD_SQL_CONNECTION_NAME}?unix_socket=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
# )
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # Initialize SQLAlchemy
# db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0)

    transactions_sent = db.relationship('Transaction', backref='sender', foreign_keys='Transaction.sender_id')
    transactions_received = db.relationship('Transaction', backref='receiver', foreign_keys='Transaction.receiver_id')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter(
        (Transaction.sender_id == user.id) | (Transaction.receiver_id == user.id)
    ).all()
    return render_template('index.html', user=user, transactions=transactions)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        balance = 0  # Initial balance
        new_user = User(username=username, password=password, balance=balance)

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            return "Username already exists!"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    amount = float(request.form['amount'])
    user = User.query.get(session['user_id'])
    user.balance += amount
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/send', methods=['POST'])
def send():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    amount = float(request.form['amount'])
    recipient_username = request.form['recipient']
    user = User.query.get(session['user_id'])
    recipient = User.query.filter_by(username=recipient_username).first()

    if recipient and user.balance >= amount:
        user.balance -= amount
        recipient.balance += amount
        db.session.commit()

        # Record the transaction
        # Corrected
        transaction = Transaction(sender=user, receiver=recipient, amount=amount)
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return "Insufficient balance or recipient not found!"

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return render_template('logout.html')

@app.route('/test-db-connection')
def test_db_connection():
    try:
        # Use text() to execute the raw SQL query
        result = db.session.execute(text('SELECT 1'))
        return 'Database connection successful!'
    except Exception as e:
        return f'Error connecting to database: {str(e)}'


if __name__ == '__main__':
    app.run(debug=True)
