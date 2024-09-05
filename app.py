from flask import Flask, render_template, request, redirect
import os
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime, timedelta
import time


app = Flask(__name__)

def get_mongodb_client():
    try:
        password = "1363ArM1"  # Replace this with your actual method of getting the password
        connection_string = f"mongodb+srv://joona374:{password}@website.fuhd6.mongodb.net/?retryWrites=true&w=majority&appName=Website"
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)  # Timeout after 5 seconds
        print("MongoDB client initialized.")
        return client
    except ConnectionFailure as e:
        print("Could not connect to MongoDB:", e)
        return None

db_client = get_mongodb_client()
vercel_db = db_client["vercel_db"]
person_collection = vercel_db["person_collection"]


@app.route("/")
def index():
    latest_doc = person_collection.find_one(sort=[("_id", -1)])
    last_message_time = latest_doc["time"]
    return render_template("index.html", last_message_time=last_message_time)

@app.route("/submit", methods=["POST"])
def submit():
    # Get the name from the form
    message = request.form.get("name")
    if message:
        print(f"Name entered: {message}")  # Print the name in the console

        current_time = datetime.now()
        adjusted_time = current_time + timedelta(hours=3)
        formatted_time = adjusted_time.strftime("%B %d, %Y, %H:%M:%S")

        doc = {
            "time": formatted_time,
            "message": message
               }
        print(doc)
        person_collection.insert_one(doc)
        
        return render_template("new_message.html", viesti=message)
    else:
        return "No message provided", 400

@app.route("/messages")
def display_messages():
    messages = list(person_collection.find())

    return render_template("messages.html", viestit=messages)

if __name__ == "__main__":
    app.run(debug=True)