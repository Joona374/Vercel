from flask import Flask, render_template, request, redirect
import os
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from datetime import datetime



app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    # Get the name from the form
    message = request.form.get("name")
    if message:

        current_time = datetime.now()
        formatted_time = current_time.strftime("%B %d, %Y, %H:%M:%S")

        doc = {
            "time": formatted_time,
            "message": message
               }
        print(doc)
        # person_collection.insert_one(doc)
        
        return f"Muru lähetti viestin: {message}!"  # Send a response to the user
    else:
        return "No message provided", 400

def get_mongodb_client():
    # load_dotenv(find_dotenv())
    # password = os.environ.get("MONGODB_PWD")
    password = "1363ArM1"
    connection_string = f"mongodb+srv://joona374:{password}@website.fuhd6.mongodb.net/?retryWrites=true&w=majority&appName=Website"
    client = MongoClient(connection_string)

    return client



# db_client = get_mongodb_client()
# vercel_db = db_client["vercel_db"]
# person_collection = vercel_db["person_collection"]
# second_collection = vercel_db["second_collection"]
# files = vercel_db.list_collection_names()
# print(files)
app.run(debug=True)