from flask import Flask, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import time, os

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db.sqlite3'
db = SQLAlchemy(app)

# One time run to setup tables
class Medications(db.Model):
    __tablename__ = 'medications'
    def __init__(self, medicationName, timings, dosage):
        self.medicationName = medicationName
        self.timings = timings
        self.dosage = dosage
    
    id = db.Column(db.Integer, primary_key=True)
    medicationName = db.Column(db.String(100), nullable=False)
    timings = db.Column(db.JSON, nullable=False)
    dosage = db.Column(db.Integer, nullable=False)
        
class Mappings(db.Model):
    __tablename__ = 'mappings'
    def __init__(self, cylinderNum, medicationName):
        self.cylinderNum = cylinderNum
        self.medicationName = medicationName

    id = db.Column(db.Integer, primary_key=True)
    cylinderNum = db.Column(db.Integer, nullable=False)
    medicationName = db.Column(db.String(100), nullable=False)
    db.UniqueConstraint(cylinderNum)

# create db and tables if don't exist
db.create_all()

# Endpoints
@app.route("/", methods=["GET"])
def main():
    return "Alive"

@app.route("/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        requestData = request.get_json()
        timings = requestData['timings']
        medication = requestData['medication']
        dose = requestData['dose']
        obj = Mappings.query.filter_by(medicationName=medication).first()
    else:
        return "alive"

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        return
    else:
        return

@app.route("/medsettings", methods=["GET", "POST"])
def medSettings():
    if request.method == "POST":
        return
    else:
        return

if __name__ == "__main__":
    app.run(debug=True, port=1234)

