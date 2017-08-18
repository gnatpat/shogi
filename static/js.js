var _WIDTH = 3;
var _HEIGHT = 4;

var board_div;
var status_span;

var game;
var player;

var current_moves;
var is_your_turn;
var clicked_on = "";

function Loaded() {
  board_div = document.getElementById('board');
  status_span = document.getElementById('turn');
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
  var other_player = 1 - player;
  board_div.innerHTML = "";
  var content = "";
  content += MakeBench(other_player);
  content += "<table id='main-board'>";
  for (var y = 0; y < _HEIGHT; y++) {
    content += "<tr>";
    for (var x = 0; x < _WIDTH; x++) {
      var x_to_use = x;
      var y_to_use = y;
      if (player == 0) {
        y_to_use = _HEIGHT - y - 1;
      } else {
        x_to_use = _WIDTH - x - 1;
      }
      content += MakeBoardTD(x_to_use.toString() + y_to_use.toString());
    }
    content += "</tr>";
  }
  content += "</table>";
  content += MakeBench(player);
  board_div.innerHTML = content;
  ClearAllBackgrounds();

  AddClickEventListeners();
}

function AddClickEventListeners() {
  var board_squares = document.getElementsByClassName("board_square");
  for (var i = 0; i < board_squares.length; i++) {
    var board_square = board_squares[i]
    board_square.onclick = function() {
      if (!is_your_turn) {
        return;
      }
      ClearAllBackgrounds();
      if (clicked_on != "") {
        if (this.id in current_moves[clicked_on]) {
          var from = clicked_on;
          clicked_on = "";
          is_your_turn = false;
          Move(from, this.id);
          return;
        }
      }
      var possible_moves = current_moves[this.id]
      Object.keys(possible_moves).forEach(function(pos) {
        document.getElementById(pos).style.backgroundColor = "yellow";
      });
      clicked_on = this.id;
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
    var board_square = board_squares[i];
    var x = parseInt(board_square.id[0]);
    var y = parseInt(board_square.id[1]);
    if ((x + y) % 2 == 0) board_square.style.backgroundColor = "#cccccc";
    else board_square.style.backgroundColor = "#ffffff";
  }
}


function StartGame() {
  status_span.innerHTML = "Waiting for another player...";
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

  ClearAllCells()
  Object.keys(update.board).forEach(function(key) {
    var str = update.board[key][0][0] + update.board[key][1];
    document.getElementById(key).innerHTML = str;
  });

  var player_str = player == 0 ? "Player 1" : "Player 2";

  var is_game_over = (update.status == "won" ||
                      update.status == "lost" ||
                      update.status == "draw");

  if (is_game_over) {
    var status_str = "";
    if (update.status == "won") {
      status_str = "You won.";
    } else if (update.status == "lost") {
      status_str = "You lost.";
    } else if (update.status == "draw") {
      status_str = "You drew.";
    }
    status_span.innerHTML = player_str + ": " + status_str;
    return;
  }

  is_your_turn = update.my_turn
  var turn_str = is_your_turn ? "Your Turn" : "Opponent's Turn";
  status_span.innerHTML = player_str + ": " + turn_str;

  if (is_your_turn) {
    current_moves = update.moves;
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
