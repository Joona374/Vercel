// Variable to track if the game is over
let gameOver = false;

// Function to make a move
function makeMove(cellIndex) {
  // Prevent further moves if the game is over
  if (gameOver) {
    alert("The game is over. Please reset the game to start a new one.");
    return;
  }

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

        // If the game is over (win or draw), disable further moves
        if (data.game_over) {
          gameOver = true; // Set the game over flag
          document.getElementById("status").textContent = data.message;
          document.getElementById("reset-button").disabled = false;
          return;
        }

        // Otherwise, update the status for the next turn
        document.getElementById("status").textContent =
          "Player " + data.next_turn + "'s turn";
      } else {
        alert(data.message); // Show error message (e.g., "Not your turn" or "Game over")
      }
    });
}

// Polling function to get game updates
function pollForUpdates() {
  fetch("/game-updates")
    .then((response) => response.json())
    .then((gameState) => {
      // Update the board for both players
      for (let i = 0; i < gameState.board.length; i++) {
        document.getElementById("cell-" + i).textContent = gameState.board[i];
      }

      // Handle game over (win or draw)
      if (gameState.game_over) {
        gameOver = true; // Set the game over flag
        document.getElementById("status").textContent = gameState.message;
        alert(gameState.message); // Optionally show an alert
        document.getElementById("reset-button").disabled = false;
      } else {
        document.getElementById("status").textContent =
          "Player " + gameState.next_turn + "'s turn";
      }

      // Handle game reset
      if (gameState.message === "The game has been reset.") {
        gameOver = false; // Reset the game over flag
        document.getElementById("status").textContent = gameState.message;

        // Clear the game board visually
        for (let i = 0; i < 9; i++) {
          document.getElementById("cell-" + i).textContent = "";
        }

        document.getElementById("reset-button").disabled = true; // Disable the reset button after the reset
      }

      // Poll again after a short delay if the game isn't over
      if (!gameOver) {
        setTimeout(pollForUpdates, 1000); // Poll every 1 second
      }
    })
    .catch((error) => {
      console.error("Polling error:", error);
      setTimeout(pollForUpdates, 5000); // Retry after 5 seconds on error
    });
}

// Function to restart polling after a game reset
function restartPolling() {
  gameOver = false; // Reset the game over flag
  pollForUpdates(); // Restart polling
}

// Start polling when the page loads
pollForUpdates();

// Handle Reset Button click
document.getElementById("reset-button").addEventListener("click", function () {
  fetch("/reset", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert("Game reset!");

        // Restart polling after the reset
        restartPolling();

        // Clear the game board visually (optional)
        for (let i = 0; i < 9; i++) {
          document.getElementById("cell-" + i).textContent = "";
        }

        // Disable the reset button again
        document.getElementById("reset-button").disabled = true;
      } else {
        alert("Error resetting the game.");
      }
    });
});
