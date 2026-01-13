from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

#  MySQL Connection
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Ayush@2005",
    database="timetables1",
    port=3306
)

cursor = db.cursor()

#  Home Page
@app.route("/")
def index():
    return render_template("index.html")

#  Insert Data into MySQL
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    branch = request.form["branch"]

    sql = "INSERT INTO students (name, branch) VALUES (%s, %s)"
    cursor.execute(sql, (name, branch))
    db.commit()

    return " Data Stored Successfully!"

if __name__ == "__main__":
    app.run(debug=True)