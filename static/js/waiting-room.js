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

// SSE connection logic for waiting room
// Open an SSE connection to /sse route
const eventSource = new EventSource("/sse");

// Listen for messages from the server
eventSource.onmessage = function (event) {
  if (event.data === "start_game") {
    eventSource.close();
    // Redirect to the game page when "start_game" message is received
    window.location.href = "/tictac";
  }
};
