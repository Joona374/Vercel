// Function to make a move
function makeMove(cellIndex) {
  fetch("/make-move", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      cell: cellIndex,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("cell-" + cellIndex).textContent = data.mark;

        // If the game is over (win or draw), rely on SSE for status update
        if (data.game_over) {
          return;
        }

        // Otherwise, update the status for the next turn
        document.getElementById("status").textContent =
          "Player " + data.next_turn + "'s turn";
      } else {
        alert(data.message); // Show error message (e.g., "Not your turn")
      }
    });
}

let eventSource = null;

// Initialize SSE for real-time game updates
function initializeSSE() {
  if (eventSource) {
    eventSource.close(); // Close any previous connection
  }

  eventSource = new EventSource("/game-updates");

  eventSource.onopen = function () {
    console.log("SSE connection established for Player X");
  };

  eventSource.onerror = function (err) {
    console.error("SSE error for Player X:", err);
  };

  eventSource.onmessage = function (event) {
    const gameState = JSON.parse(event.data);
    console.log("Received SSE update for Player X:", gameState);

    // Update the board for both players
    for (let i = 0; i < gameState.board.length; i++) {
      document.getElementById("cell-" + i).textContent = gameState.board[i];
    }

    // Handle game over (win or draw)
    if (gameState.game_over) {
      document.getElementById("status").textContent = gameState.message;
      alert(gameState.message);
      document.getElementById("reset-button").disabled = false;
    } else {
      document.getElementById("status").textContent =
        "Player " + gameState.next_turn + "'s turn";
    }

    // Handle reset message
    if (gameState.message === "The game has been reset.") {
      document.getElementById("status").textContent = "Game has been reset!";
      alert("Game has been reset!");
      document.getElementById("reset-button").disabled = true;
    }
  };
}

initializeSSE(); // Establish SSE connection when the page loads or game resets

// Handle Reset Button click
document.getElementById("reset-button").addEventListener("click", function () {
  fetch("/reset", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
      } else {
        alert("Error resetting the game.");
      }
    });
});
