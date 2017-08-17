var _WIDTH = 3;
var _HEIGHT = 4;

var boardDiv;
var statusSpan;

var game;
var player;

var currentMoves;
var isYourTurn;
var clickedOn;

function Loaded() {
  boardDiv = document.getElementById('board');
  statusSpan = document.getElementById('turn');
  player = 0;
  CreateBoard(0);

  document.getElementById('start-game').onclick = StartGame
}

function MakeBoardTD(id) {
  return "<td class='board_square' id='" + id + "'></td>";
}

function MakeBench(for_player) {
  var player_as_str = (parseInt(for_player) + 1).toString();
  var content = "";
  content += "<table id='P" + player_as_str + "Bench'><tr>"
  content += MakeBoardTD("P" + player_as_str + "B0");
  content += MakeBoardTD("P" + player_as_str + "B1");
  content += MakeBoardTD("P" + player_as_str + "B2");
  content += "</tr></table>";
  return content;
}

function CreateBoard() {
  var otherPlayer = 1 - player;
  boardDiv.innerHTML = "";
  var content = "";
  content += MakeBench(otherPlayer);
  content += "<table id='main-board'>";
  for (var y = 0; y < _HEIGHT; y++) {
    content += "<tr>";
    for (var x = 0; x < _WIDTH; x++) {
      // We need to switch the board around depending on which player is viewing it.
      var xToUse = x;
      var yToUse = y;
      if (player == 0) {
        yToUse = _HEIGHT - y - 1;
      } else {
        xToUse = _WIDTH - x - 1;
      }
      content += MakeBoardTD(xToUse.toString() + yToUse.toString());
    }
    content += "</tr>";
  }
  content += "</table>";
  content += MakeBench(player);
  boardDiv.innerHTML = content;

  AddClickEventListeners();
}

function AddClickEventListeners() {
  var board_squares = document.getElementsByClassName("board_square");
  for (var i = 0; i < board_squares.length; i++) {
    var board_square = board_squares[i]
    board_square.onclick = function() {
      if (!isYourTurn) {
        return;
      }
      ClearAllBackgrounds()
      if (clickedOn != "") {
        if (this.id in currentMoves[clickedOn]) {
          Move(clickedOn, this.id);
          return;
        }
      }
      var possibleMoves = currentMoves[this.id]
      Object.keys(possibleMoves).forEach(function(pos) {
        document.getElementById(pos).style.backgroundColor = "yellow";
      });
      clickedOn = this.id;
    }
  }
}

function ClearAllCells() {
  var board_squares = document.getElementsByClassName("board_square");
  for (var i = 0; i < board_squares.length; i++) {
    var board_square = board_squares[i]
    board_square.innerHTML = "";
  }
}

function ClearAllBackgrounds() {
  var board_squares = document.getElementsByClassName("board_square");
  for (var i = 0; i < board_squares.length; i++) {
    var board_square = board_squares[i]
    board_square.style.backgroundColor = "white";
  }
}


function StartGame() {
  statusSpan.innerHTML = "Waiting for another player...";
  var aClient = new HttpClient();
  aClient.get('start_game', function(responseStr) {
    var response = JSON.parse(responseStr);
    game = response.game;
    player = response.player;
    CreateBoard();
    aClient.get('get_game_status' + GetArgs(), UpdateGame);
  });
}

function UpdateGame(updateStr) {
  var update = JSON.parse(updateStr);

  clickedOn = ""
  isYourTurn = update.my_turn

  var playerStr = player == "0" ? "Player 1" : "Player 2";
  var turnStr = isYourTurn ? "Your Turn" : "Opponent's Turn";
  statusSpan.innerHTML = playerStr + ": " + turnStr;

  ClearAllCells();
  Object.keys(update.board).forEach(function(key) {
    var str = update.board[key][0][0] + update.board[key][1][6];
    document.getElementById(key).innerHTML = str;
  });
  if (isYourTurn) {
    currentMoves = update.moves;
  } else {
    var aClient = new HttpClient();
    aClient.get("wait_for_my_turn" + GetArgs(), UpdateGame);
  }
}

function Move(from, to) {
  var aClient = new HttpClient();
  aClient.get('move' + GetArgs() + '&from=' + from + '&to=' + to,
      UpdateGame);
}

function GetArgs() {
  return "?game=" + game + "&player=" + player;
}
