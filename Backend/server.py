from flask import Flask, render_template, request, session, flash, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager, login_required, UserMixin, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import time, os, requests, urllib.parse, json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db.sqlite3'
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Authentication credentials for raspberry on basic http auth endpoint. In ideal situation we would be using a CA but this project is on LAN
USERNAME = "pythoniot"
PASSWORD = "sha256$L2gFoqDlw7dyQapp$fda2cf4d5843b98553e8eff1da76064547bf35e704e213ea99c8bc29da928992"

# http authentication
@auth.verify_password
def authentication(uname,pword):
    if uname and pword:
        if uname == USERNAME and check_password_hash(PASSWORD, pword):
            return True
        else:
            return False
    return False

# DB and tables
class Medications(db.Model):
    __tablename__ = 'medications'
    def __init__(self, cylinderNum, timings, dosage):
        self.cylinderNum = cylinderNum
        self.timings = timings
        self.dosage = dosage
    
    id = db.Column(db.Integer, primary_key=True)
    cylinderNum = db.Column(db.Integer, nullable=False)
    timings = db.Column(db.JSON, nullable=False)
    dosage = db.Column(db.Integer, nullable=False)
        
class Mappings(db.Model):
    __tablename__ = 'mappings'
    def __init__(self, cylinderNum, medicationName):
        self.cylinderNum = cylinderNum
        self.medicationName = medicationName

    id = db.Column(db.Integer, primary_key=True)
    cylinderNum = db.Column(db.Integer, unique=True, nullable=False)
    medicationName = db.Column(db.String(255), nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Users(UserMixin, db.Model):
    __tablename__= 'users'
    def __init__(self, username, password, number):
        self.username = username
        self.password = password
        self.number = number

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(25), nullable=False)

# create db and tables if don't exist
db.create_all()
print(Mappings.query.all())

# User creation for testing purposes
# user = Users(username="test", password=generate_password_hash("password"), number="90202365")
# db.session.add(user)
# db.session.commit()

# temp = Mappings(1,"ibuprofen")
# temp2 = Mappings(2, "paracetamol")
# db.session.add(temp)
# db.session.add(temp2)
# db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Endpoints
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form.get('username')
        pword = request.form.get('password')
        user = Users.query.filter_by(username=uname).first()
        if user and check_password_hash(user.password, pword):
            login_user(user)
            return redirect(url_for("main"))
        else:
            flash('Please check your login details and try again.')
            return redirect(url_for("login"))
    else:
        return "login page"

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        requestData = request.get_json()
        uname = requestData['username']
        pword = requestData['password']
        phoneNumber = requestData['phoneNumber']
        mappingData = requestData['mapping']
        stockData = requestData['stocks']

        user = Users(username=uname, password=generate_password_hash(pword), number=phoneNumber)
        db.session.add(user)
        newMapping1 = Mappings.query.filter_by(cylinderNum=1).update(dict(stock=stockData['cyl1'], medicationName=mappingData['cyl1']))
        newMapping2 = Mappings.query.filter_by(cylinderNum=2).update(dict(stock=stockData['cyl2'], medicationName=mappingData['cyl2']))
        newMapping3 = Mappings.query.filter_by(cylinderNum=3).update(dict(stock=stockData['cyl3'], medicationName=mappingData['cyl3']))
        newMapping4 = Mappings.query.filter_by(cylinderNum=4).update(dict(stock=stockData['cyl4'], medicationName=mappingData['cyl4']))
        db.session.commit()

        return redirect(url_for('login'))

    else:
        users = []
        for user in Users.query.all():
            users.append(user.__dict__)
        if users:
            return redirect(url_for('login'))
        return render_template("")


@app.route("/", methods=["GET"])
@login_required
def main():
    return "Dashboard"

@app.route("/config", methods=["GET", "POST"])
@login_required
def config():
    if request.method == "POST":
        requestData = request.get_json()
        timings = requestData['timings']
        medication = requestData['medication']
        dose = requestData['dose']
        cylinder = Mappings.query.filter_by(medicationName=medication).first().cylinderNum
        try:
            newDose = Medications(cylinder, timings, dose)
            db.session.add(newDose).commit()
        except:
            flash("Error adding dosage and medication, please check input and try again.")
            return redirect(url_for('config'))
    else:
        med1 = Mappings.query.filter_by(cylinderNum=1).first().medicationName
        med2 = Mappings.query.filter_by(cylinderNum=2).first().medicationName
        med3 = Mappings.query.filter_by(cylinderNum=3).first().medicationName
        med4 = Mappings.query.filter_by(cylinderNum=4).first().medicationName
        
        return render_template('.html', med1=med1, med2=med2, med3=med3, med4=med4)

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        requestData = request.get_json()
        phoneNumber = requestData['phoneNumber']
        try:
            user = Users.query.filter_by(username=current_user.username).update(dict(number=int(phoneNumber)))
        except:
            flash('Error changing number, please check number and try again.')
            return redirect(url_for('settings'))
    else:

        return current_user.number

@app.route("/medsettings", methods=["GET", "POST"])
@login_required
def medSettings():
    if request.method == "POST":
        requestData = request.get_json()
        dosageData = requestData['dosage']
        stockData = requestData['stock']
        mappingData= requestData['mapping']
        update1 = Mappings.query.filter_by(cylinderNum=1).update(dict(stock=stockData['cyl1'], medicationName=mappingData['cyl1']))
        update2 = Mappings.query.filter_by(cylinderNum=2).update(dict(stock=stockData['cyl2'], medicationName=mappingData['cyl2']))
        update3 = Mappings.query.filter_by(cylinderNum=3).update(dict(stock=stockData['cyl3'], medicationName=mappingData['cyl3']))
        update4 = Mappings.query.filter_by(cylinderNum=4).update(dict(stock=stockData['cyl4'], medicationName=mappingData['cyl4']))

        flash("Successfully changed settings")
        return redirect(url_for('medSettings'))
        
    else:
        dosage = Medications.query.all()
        
        return render_template(".html",
        stock1=Mappings.query.filter_by(cylinderNum=1).first().stock,
        stock2=Mappings.query.filter_by(cylinderNum=2).first().stock,
        stock3=Mappings.query.filter_by(cylinderNum=3).first().stock,
        stock4=Mappings.query.filter_by(cylinderNum=4).first().stock,
        mapping1=Mappings.query.filter_by(cylinderNum=1).first().medicationName,
        mapping2=Mappings.query.filter_by(cylinderNum=2).first().medicationName,
        mapping3=Mappings.query.filter_by(cylinderNum=3).first().medicationName,
        mapping4=Mappings.query.filter_by(cylinderNum=4).first().medicationName)

# Endpoint for raspberry
@app.route("/retrconfig", methods=["GET"])
@auth.login_required
def retrconfig():
    data = Medications.query.all()

@app.route("/sendmessage", methods=["POST"])
@auth.login_required
def sendMessage():
    number = Users.query.first().number
    message = ""
    x = requests.get(f"https://api.callmebot.com/whatsapp.php?phone={number}&text={urllib.parse.quote_plus(message)}&apikey=[your_apikey]")

@app.route("/getstock", methods=["GET"])
@auth.login_required
def getStock():
    stock = {
        "cyl1": Mappings.query.filter_by(cylinderNum=1).first().stock,
        "cyl2": Mappings.query.filter_by(cylinderNum=2).first().stock,
        "cyl3": Mappings.query.filter_by(cylinderNum=3).first().stock,
        "cyl4": Mappings.query.filter_by(cylinderNum=4).first().stock
    }
    return stock

@app.route("/updateStock", methods=["GET"])
@auth.login_required
def updateStock():
    pass

if __name__ == "__main__":
    app.run(debug=True, port=1234)

