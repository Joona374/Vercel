from flask import Flask, session, render_template, request, redirect, Response, jsonify
import os
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime, timedelta
import time
import uuid
import queue
import json

app = Flask(__name__)
app.secret_key = "salasana"
app.permanent_session_lifetime = timedelta(days=1)

connections = {}
sse_queues = {}


def get_mongodb_client():
    try:
        load_dotenv(find_dotenv())
        password = os.environ.get("MONGODB_PWD")
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
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    latest_doc = person_collection.find_one(sort=[("_id", -1)])

    user_id = session["user_id"]
    print(f"User id {user_id}")

    last_message_time = latest_doc["time"]
    return render_template("index.html", last_message_time=last_message_time)

@app.route("/submit", methods=["POST"])
def submit():

    user_id = session.get("user_id")
    print(f"Message from user {user_id}")

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


player_x_id = None
player_o_id = None
player_in_turn = "X"
game_board = [""] * 9  # 3x3 grid

@app.route("/tictac")
def play_game():
    for id, que in sse_queues.items():
        print(f"{session["user_id"]} prints {id}, {que}")
    if session["user_id"] == player_x_id:
        player_role = "X"
    elif session["user_id"] == player_o_id:
        player_role = "O"
    return render_template("tictactoe.html", player_role=player_role)

# Function to check if a player has won
def check_winner(board):
    # All possible winning combinations (rows, columns, diagonals)
    winning_combinations = [
        [0, 1, 2],  # Row 1
        [3, 4, 5],  # Row 2
        [6, 7, 8],  # Row 3
        [0, 3, 6],  # Column 1
        [1, 4, 7],  # Column 2
        [2, 5, 8],  # Column 3
        [0, 4, 8],  # Diagonal 1
        [2, 4, 6],  # Diagonal 2
    ]

    # Check if any winning combination is fully occupied by the same player
    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] and board[combo[0]] != "":
            return board[combo[0]]  # Return the winner ("X" or "O")
    
    return None  # No winner yet

# Function to check if the game is a draw (all spaces filled)
def check_draw(board):
    return all(cell != "" for cell in board)  # If no empty cells, it's a draw

@app.route("/reset", methods=["POST"])
def reset_game():
    global game_board, player_in_turn

    # Reset the game board and player turn
    game_board = [""] * 9
    player_in_turn = "X"  # Reset to Player X's turn

    # Notify both players via SSE that the game has been reset
    for queue in sse_queues.values():
        queue.put({
            "board": game_board,
            "next_turn": player_in_turn,
            "message": "The game has been reset."
        })

    return jsonify({"success": True})

# Handle player moves
@app.route("/make-move", methods=["POST"])
def make_move():
    global player_in_turn, game_board
    user_id = session.get("user_id")
    data = request.get_json()
    cell_index = data.get("cell")

    # Check if the cell is already taken
    if game_board[cell_index] != "":
        return jsonify({"success": False, "message": "Ruutu on jo varattu!"})

    # Check if it's the player's turn
    if (player_in_turn == "X" and user_id == player_x_id) or (player_in_turn == "O" and user_id == player_o_id):
        game_board[cell_index] = player_in_turn  # Make the move
        next_turn = "O" if player_in_turn == "X" else "X"
        player_in_turn = next_turn  # Switch turns

        # Check for a winner after the move
        winner = check_winner(game_board)
        if winner:
            # Notify both players of the winner via SSE
            for queue in sse_queues.values():
                queue.put({
                    "board": game_board,
                    "winner": winner,
                    "message": f"Player {winner} wins!",
                    "game_over": True
                })
            return jsonify({"success": True, "mark": game_board[cell_index], "message": f"Player {winner} wins this!", "game_over": True})

        # Check for a draw
        if check_draw(game_board):
            # Notify both players of a draw via SSE
            for queue in sse_queues.values():
                queue.put({
                    "board": game_board,
                    "message": "It's a draw!",
                    "game_over": True
                })
            return jsonify({"success": True, "mark": game_board[cell_index], "message": "It's a draw!", "game_over": True})

        # If no winner and no draw, continue the game
        # Notify both players of the next turn
        for queue in sse_queues.values():
            print(f"Tämä on que: {queue}")
            queue.put({
                "board": game_board,
                "next_turn": player_in_turn
            })

        return jsonify({"success": True, "mark": game_board[cell_index], "next_turn": player_in_turn})
    else:
        return jsonify({"success": False, "message": "Ei sinun vuoro!"})


# SSE to send real-time game updates
@app.route("/game-updates")
def game_updates():
    user_id = session.get("user_id")

    def event_stream():
        if user_id not in sse_queues:
            print("Käydäänkö me täällä????")
            sse_queues[user_id] = queue.Queue()

        while True:
            try:
                message = sse_queues[user_id].get(timeout=10)
                yield f"data: {json.dumps(message)}\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"

    return Response(event_stream(), content_type="text/event-stream")


# Function to check if a player has won
def check_winner(board):
    # All possible winning combinations (rows, columns, diagonals)
    winning_combinations = [
        [0, 1, 2],  # Row 1
        [3, 4, 5],  # Row 2
        [6, 7, 8],  # Row 3
        [0, 3, 6],  # Column 1
        [1, 4, 7],  # Column 2
        [2, 5, 8],  # Column 3
        [0, 4, 8],  # Diagonal 1
        [2, 4, 6],  # Diagonal 2
    ]

    # Check if any winning combination is fully occupied by the same player
    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] and board[combo[0]] != "":
            return board[combo[0]]  # Return the winner ("X" or "O")
    
    return None  # No winner yet

# Function to check if the game is a draw (all spaces filled)
def check_draw(board):
    return all(cell != "" for cell in board)  # If no empty cells, it's a draw



@app.route("/waiting-room")
def join_waiting_room():
    global player_x_id, player_o_id, sse_queues

    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())  # Generate a unique user ID

    user_id = session["user_id"]

    if not player_x_id:
        print(f"Waiting room was empty but not anymore. User {user_id} is X.")
        player_x_id = user_id
        
        # Initialize SSE queue for Player X
        sse_queues[player_x_id] = queue.Queue()

        return render_template("waiting-room.html")

    else:
        # Assign Player O and notify Player X via SSE
        player_o_id = user_id
        print(f"User {player_o_id} is playing O.")

        if user_id not in sse_queues:
            sse_queues[user_id] = queue.Queue()

        # Notify Player X that the game is starting
        if player_x_id in sse_queues:
            sse_queues[player_x_id].put("start_game")

        # Redirect Player O to the game page
        return redirect("/tictac")




@app.route('/sse')
def sse():
    user_id = session.get('user_id')

    def event_stream():
        # Continuously check for messages in the user's message queue
        while True:
            if user_id in sse_queues:
                try:
                    # Get the next message from the user's queue
                    message = sse_queues[user_id].get(timeout=10)
                    yield f"data: {message}\n\n"
                except queue.Empty:
                    # Keep the connection alive by sending a keep-alive message if no message
                    yield ": keep-alive\n\n"

    # Return the event stream response for SSE
    return Response(event_stream(), content_type='text/event-stream')


@app.route('/send_message/<target_user_id>')
def send_message(target_user_id):
    if target_user_id in sse_queues:
        # Put the message in the target user's queue
        sse_queues[target_user_id].put(f"Hello user {target_user_id}, you have a special message!")
        print(f"Message sent to user {target_user_id}")
    else:
        print("User not found")

    return f"Message sent to user {target_user_id}"






if __name__ == "__main__":
    app.run(debug=True)