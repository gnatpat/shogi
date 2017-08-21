(function() {
var _WIDTH = 3;
var _HEIGHT = 4;

var board_div;
var status_span;

var player_id;
var player;

var board;
var current_moves;
var is_your_turn;
var clicked_on = "";
var holding = "";
var holding_img = "";

window.onload = Loaded

function Loaded() {
  board_div = document.getElementById('board');
  status_span = document.getElementById('turn');
  player = 0;
  CreateBoard(0);

  document.getElementById('start-game').onclick = StartHumanGame
  document.getElementById('start-ai-game').onclick = StartAIGame

  var last_player_id = getCookie('player_id');
  if (last_player_id != "") {
    player_id = last_player_id;
    player = getCookie('player');
    CreateBoard();
    var client = new HttpClient();
    client.get('get_game_status' + GetArgs(), UpdateGame);
  }
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

  AddMoveEventListeners();
}

function StartHolding(element, evt) {
  holding = element.id;
  holding_img = element.innerHTML;
  element.innerHTML = "";
  document.getElementById('hidden').innerHTML = TokenToImgTag(board[element.id], "hidden");
  UpdateHoldingPos(evt);
}

function UpdateHoldingPos(e) {
  document.getElementById("img-hidden").style.left = e.clientX - 25;
  document.getElementById("img-hidden").style.top = e.clientY - 25;
}

function StopHolding() {
  document.getElementById(holding).innerHTML = holding_img;
  document.getElementById('hidden').innerHTML = "";
  holding = "";
}

function ColourPossibleMoves(from) {
  var possible_moves = current_moves[from]
  Object.keys(possible_moves).forEach(function(pos) {
    document.getElementById(pos).style.backgroundColor = "yellow";
  });
}

function AddMoveEventListeners() {
  var board_squares = document.getElementsByClassName("board_square");
  for (var i = 0; i < board_squares.length; i++) {
    var board_square = board_squares[i];
    board_square.onmousedown = function(e) {
      if (!is_your_turn) return;

      ClearAllBackgrounds();
      if (clicked_on != "") {
        var old_clicked_on = clicked_on;
        clicked_on = "";
        if (this.id in current_moves[old_clicked_on]) {
          Move(old_clicked_on, this.id);
          return;
        }
      }
      this.style.backgroundColor = "orange";
      if (!(this.id in current_moves)) {
        return;
      }
      StartHolding(this, e);
      ColourPossibleMoves(this.id);
    }
    board_square.onmouseup = function(e) {
      if (!is_your_turn) return;
      if (holding == "") return;

      var was_holding = holding;
      StopHolding();

      if (this.id == was_holding) {
        clicked_on = this.id;
        return;
      }

      ClearAllBackgrounds();
      if (this.id in current_moves[was_holding]) {
        Move(was_holding, this.id);
        return;
      }
    }
    board_square.onmouseenter = function(e) {
      if (holding == "") return;
      if (this.id in current_moves[holding]) {
        this.style.backgroundColor = "orange";
      }
    }
    board_square.onmouseleave = function(e) {
      if (holding == "") return;
      if (this.id in current_moves[holding]) {
        this.style.backgroundColor = "yellow";
      }
    }
  }
  document.body.onmousemove = function(e) {
    if (holding !== "") {
      UpdateHoldingPos(e);
    }
  }
  document.body.onmouseup = function(e) {
    if (holding !== "") {
      StopHolding();
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

function StartHumanGame() {
  StartGame('start_game')
}

function StartAIGame() {
  StartGame('start_ai_game')
}

function StartGame(url) {
  status_span.innerHTML = "Waiting for another player...";
  var aClient = new HttpClient();
  aClient.get(url, function(responseStr) {
    var response = JSON.parse(responseStr);
    player_id = response.player_id;
    player = response.player;
    setCookie('player_id', player_id)
    setCookie('player', player)
    CreateBoard();
    aClient.get('get_game_status' + GetArgs(), UpdateGame);
  });
}

function TokenToImage(token) {
  var up_or_down = (token[1] == player ? "up" : "down");
  return "img/" + token[0] + "_" + up_or_down + ".png";
}

function TokenToImgTag(token, id) {
  return "<img draggable=false width=50 height=50 " +
    "src='" + TokenToImage(token) + "' + id='img-" + id + "'/>";
}

function UpdateBoard(new_board) {
  board = new_board
  ClearAllCells()
  Object.keys(board).forEach(function(key) {
    document.getElementById(key).innerHTML = TokenToImgTag(board[key], key);
  });
}


function UpdateGame(updateStr) {
  var update = JSON.parse(updateStr);

  UpdateBoard(update.board)

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

  is_your_turn = (update.current_player == player)
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
  is_your_turn = false;
  UpdateBoard(current_moves[from][to])
  var aClient = new HttpClient();
  aClient.get('move' + GetArgs() + '&from=' + from + '&to=' + to,
      UpdateGame);
}

function GetArgs() {
  return "?player=" + player_id;
}

})();
