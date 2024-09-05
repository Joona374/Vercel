from flask import Flask, render_template, request, redirect
import os
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
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

@app.route("/test")
def test_mongodb():
    start_time = time.time()
    print("Connecting to MongoDB...")

    # Try to get a document from MongoDB
    try:
        first_doc = person_collection.find_one()
        if first_doc:
            print("First document retrieved:", first_doc)
        else:
            print("No documents found.")
    except Exception as e:
        print("Error accessing MongoDB:", e)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time to access MongoDB: {elapsed_time} seconds")

    return f"MongoDB connection test completed in {elapsed_time} seconds"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():

    # Get the name from the form
    message = request.form.get("name")
    if message:
        print(f"Name entered: {message}")  # Print the name in the console

        current_time = datetime.now()
        formatted_time = current_time.strftime("%B %d, %Y, %H:%M:%S")

        doc = {
            "time": formatted_time,
            "message": message
               }
        print(doc)
        person_collection.insert_one(doc)
        
        return f"Muru lähetti viestin: {message}!"  # Send a response to the user
    else:
        return "No message provided", 400

if __name__ == "__main__":
    app.run(debug=True)