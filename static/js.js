var _WIDTH = 3;
var _HEIGHT = 4;

var board;
var turnSpan;

var game;
var player;

var currentMoves;
var isYourTurn;
var clickedOn;

function Loaded() {
  board = document.getElementById('board');
  turn_span = document.getElementById('turn');
  CreateBoard();

  document.getElementById('start-game').onclick = StartGame
}

function MakeBoardTD(id) {
  return "<td class='board_square' id='" + id + "'></td>";
}

function CreateBoard() {
  var content = "";
  content += "<table id='P2Bench'><tr>"
  content += MakeBoardTD("P1B0");
  content += MakeBoardTD("P1B1");
  content += MakeBoardTD("P1B2");
  content += "</tr></table>";
  content += "<table id='main-board'>";
  for (var y = 0; y < _HEIGHT; y++) {
    content += "<tr>";
    for (var x = 0; x < _WIDTH; x++) {
      content += MakeBoardTD(x.toString() + y.toString());
    }
    content += "</tr>";
  }
  content += "</table>";
  content += "<table id='P2Bench'><tr>"
  content += MakeBoardTD("P2B0");
  content += MakeBoardTD("P2B1");
  content += MakeBoardTD("P2B2");
  content += "</tr></table>";
  board.innerHTML = content;

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
  var aClient = new HttpClient();
  aClient.get('start_game', function(responseStr) {
    var response = JSON.parse(responseStr);
    game = response.game;
    player = response.player;
    aClient.get('get_game_status' + GetArgs(), UpdateGame);
  });
}

function UpdateGame(updateStr) {
  var update = JSON.parse(updateStr);

  clickedOn = ""
  isYourTurn = update.my_turn

  var playerStr = player == "0" ? "Player 1" : "Player 2";
  var turnStr = isYourTurn ? "Your Turn" : "Opponent's Turn";
  turn.innerHTML = playerStr + ": " + turnStr;

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
