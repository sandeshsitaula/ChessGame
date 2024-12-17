let currentPlayer;
let isMatchEnded = false;
let matchResult = null;

function showMatchEndMessage(result) {
  let message;
  switch (result) {
    case "WIN":
      message = "Congratulations! You've won the match!";
      break;
    case "LOSS":
      message = "Match ended. Better luck next time!";
      break;
    case "DRAW":
      message = "Match ended in a draw!";
      break;
    default:
      return;
  }

  const goToLobby = confirm(message + "\n\nReturn to lobby?");
  if (goToLobby) {
    window.location.href = "/play/lobby/";
  }
}

function updateMatchState() {
  fetch(`/play/game-state/${matchId}/`)
    .then(response => response.json())
    .then(data => {
      if (data.status) {
        updateBoardPosition(data.board_state);
        currentPlayer = data.current_turn;
        updatePlayerTurnIndicator();
        toggleMoveControls();

        if (data.is_game_over && !isMatchEnded) {
          isMatchEnded = true;
          matchResult = data.outcome;
          showMatchEndMessage(matchResult);
        }
      }
    })
    .catch(error => console.error("Match state update error:", error));
}

// Handle page refreshes
window.onload = function() {
  if (isMatchEnded && matchResult) {
    showMatchEndMessage(matchResult);
  }
};

function executeMove() {
  const [fromPosition, toPosition] = $("#src-dst")
    .val()
    .toLowerCase()
    .split("-");

  if (fromPosition && toPosition) {
    fetch("/play/move/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken")
      },
      body: JSON.stringify({
        game_id: matchId,
        src: fromPosition,
        dst: toPosition
      })
    })
      .then(response => response.json())
      .then(data => {
        if (data.status) {
          // Update board visually
          const pieceHtml = $(`#${fromPosition}`).html();
          $(`#${fromPosition}`).html("");
          $(`#${toPosition}`).html(pieceHtml);

          $("#src-dst").val("");

          if (data.is_game_over) {
            isMatchEnded = true;
            showMatchEndMessage(data.outcome);
          }
        } else {
          alert(data.message);
        }
      })
      .catch(error => {
        console.error("Move execution error:", error);
        alert("Server communication error");
      });
  } else {
    alert("Please specify both source and destination positions");
  }
}

function updateBoardPosition(boardState) {
  for (let row = 1; row <= 8; row++) {
    for (let col = "a".charCodeAt(0); col <= "h".charCodeAt(0); col++) {
      const position = String.fromCharCode(col) + row;
      $(`#${position}`).html("");
    }
  }
  // Place pieces according to current position
  for (const [position, piece] of Object.entries(boardState)) {
    $(`#${position}`).html(piece);
  }
}

function updatePlayerTurnIndicator() {
  const turnDisplay = document.getElementById("current-turn");
  turnDisplay.textContent = currentPlayer;
  turnDisplay.style.color = currentPlayer === currentUser ? "green" : "red";
}

function toggleMoveControls() {
  const isPlayerTurn = currentPlayer === currentUser;
  $("#src-dst").prop("disabled", !isPlayerTurn);
  $("button").prop("disabled", !isPlayerTurn);
}

function clearMatchEndUI() {
  const endMatchElements = document.querySelectorAll(
    ".match-end-message, .new-match-button"
  );
  endMatchElements.forEach(element => element.remove());
}

// CSRF token handling
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Set up state polling
setInterval(updateMatchState, 1000);

// Initialize match state
updateMatchState();
