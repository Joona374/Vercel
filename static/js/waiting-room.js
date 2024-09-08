// Countdown start time in seconds
let timeLeft = 120;

// Function to update the countdown
function updateCountdown() {
  const countdownElement = document.getElementById("countdown");

  // Decrement time by 1 second
  timeLeft--;

  // Update the text content with the new time left
  countdownElement.textContent = timeLeft;

  // Check if time is up
  if (timeLeft <= 0) {
    clearInterval(timerInterval); // Stop the countdown
    countdownElement.textContent = "Time's up! Your game search timed out.";
    alert("Time's up! Your game search timed out."); // Optional: show an alert or take other action
  }
}

// Set the interval to call updateCountdown every 1000 milliseconds (1 second)
const timerInterval = setInterval(updateCountdown, 1000);

// Polling function to check if game is starting
function pollForGameStart() {
  fetch("/game-start")
    .then((response) => response.json())
    .then((data) => {
      if (data.start_game) {
        window.location.href = "/tictac"; // Redirect to the game page when "start_game" message is received
      } else {
        // Poll again after a short delay
        setTimeout(pollForGameStart, 1000); // Poll every 1 second
      }
    })
    .catch((error) => {
      console.error("Polling error:", error);
      setTimeout(pollForGameStart, 5000); // Retry after 5 seconds on error
    });
}

// Start polling for the game start
pollForGameStart();
