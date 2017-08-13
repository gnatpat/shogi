import copy
import functools
import random

from collections import namedtuple

_WIDTH = 3
_HEIGHT = 4

_CHICK = "chick"
_CHICKEN = "chicken"
_ELEPHANT = "elephant"
_GIRAFFE = "giraffe"
_LION = "lion"

_PLAYER1 = "player1"
_PLAYER2 = "player2"
_PLAYER_TO_NUMBER = {_PLAYER1: 0, _PLAYER2: 1}

_PLAYER1BENCH = ["P1B" + str(i) for i in xrange(3)]
_PLAYER2BENCH = ["P2B" + str(i) for i in xrange(3)]

Token = namedtuple('Token', ['piece', 'owner'])
Point = namedtuple('Point', ['x', 'y'])
Offset = namedtuple('Offset', ['x', 'y'])

_ORDER = _PLAYER2BENCH + _PLAYER1BENCH + (
    [Point(x, y) for x in xrange(_WIDTH) for y in xrange(_HEIGHT)])

class Board(dict):

  def __hash__(self):
    return hash(''.join(self.get(pos, ' ')[0] for pos in _ORDER))

class bcolors:
  BLUE = '\033[94m'
  RED = '\033[91m'
  ENDC = '\033[0m'

def StartingBoard():
  board = EmptyBoard()
  board[Point(0, 0)] = Token(_ELEPHANT, _PLAYER1)
  board[Point(1, 0)] = Token(_LION, _PLAYER1)
  board[Point(2, 0)] = Token(_GIRAFFE, _PLAYER1)
  board[Point(1, 1)] = Token(_CHICK, _PLAYER1)

  board[Point(2, 3)] = Token(_ELEPHANT, _PLAYER2)
  board[Point(1, 3)] = Token(_LION, _PLAYER2)
  board[Point(0, 3)] = Token(_GIRAFFE, _PLAYER2)
  board[Point(1, 2)] = Token(_CHICK, _PLAYER2)

  return board

def EmptyBoard():
  return Board()

def CopyBoard(board):
  return Board(board)

def GetPiece(board, pos):
  return board[pos].piece

def GetOwner(board, pos):
  return board[pos].owner

def GetToken(board, pos):
  return board[pos]

def SetToken(board, piece, owner, pos):
  token = Token(piece, owner)
  board[pos] = token

def ClearToken(board, pos):
  del board[pos]

def IsOwnedBy(board, owner, pos):
  if pos not in board:
    return False
  return GetOwner(board, pos) == owner

def _ToChar(token):
  out = ""
  if token.owner == _PLAYER1:
    out += bcolors.BLUE
  else:
    out += bcolors.RED
  if token.piece == _CHICKEN:
    out += "C"
  else:
    out += token.piece[0]
  out += bcolors.ENDC
  return out

def PrintBoard(board):
  out = "=" * (_WIDTH + 2)
  out += "\n"
  char_board = []
  for _ in xrange(_HEIGHT):
    char_board.append([" "] * _WIDTH)
  benches = [[" "] * 3, [" "] * 3]
  for pos, token in board.iteritems():
    if _IsOnBench(pos):
      player = int(pos[1]) - 1
      spot = int(pos[3])
      benches[player][spot] = _ToChar(token)
    else:
      x, y = pos
      char_board[y][x] = _ToChar(token)
  out += "".join(benches[1])
  out += "\n"
  out += "+" + "=" * _WIDTH + "+"
  out += "\n"
  for y in reversed(xrange(_HEIGHT)):
    out += "|"
    out += "".join(char_board[y])
    out += "|\n"
  out += "+" + "=" * _WIDTH + "+"
  out += "\n"
  out += "".join(benches[0])
  out += "\n"
  out += "=" * (_WIDTH + 2)
  return out

def IsInCheck(board, player):
  return any(map(functools.partial(_IsLionDead, player=player),
    _PossibleBoards(board, OtherPlayer(player), ignore_check=True)))

def OtherPlayer(player):
  if player == _PLAYER1: return _PLAYER2
  if player == _PLAYER2: return _PLAYER1

def Next(board, player):
  if _IsLionAtEnd(board, OtherPlayer(player)):
    return []
  return list(_PossibleBoards(board, player))

def _PossibleBoards(board, player, ignore_check=False):
  for pos in _ORDER:
    for new_board, _ in _PossibleBoardsAndPos(board, player, pos, ignore_check):
      yield new_board

def _PossibleBoardsAndPos(board, player, pos, ignore_check=False):
  if ignore_check==False:
    new_boards_and_pos = filter(
        lambda board_and_pos: not IsInCheck(board_and_pos[0], player),
        _PossibleBoardsAndPos(board, player, pos, True))
    for x in new_boards_and_pos:
      yield x
    return
   
  if not IsOwnedBy(board, player, pos):
    return
  token = GetToken(board, pos)
  possible_positions = _GetPossiblePositions(board, token, pos)
  for possible_position in possible_positions:
    new_board = CopyBoard(board)
    if IsOwnedBy(board, OtherPlayer(player), possible_position):
      other_token = GetToken(board, possible_position)
      other_piece = _GetPieceAfterTaking(other_token.piece)
      next_bench_spot = _GetNextBenchSpot(board, token.owner)
      if next_bench_spot:
        SetToken(new_board, other_piece, token.owner, next_bench_spot)

    special = _DoSpecial(new_board, token, pos, possible_position)
    if special:
      yield special
      continue

    ClearToken(new_board, pos)
    SetToken(new_board, token.piece, token.owner, possible_position)

    yield new_board, possible_position

def _GetBench(player):
  if player == _PLAYER1: return _PLAYER1BENCH
  if player == _PLAYER2: return _PLAYER2BENCH

def _GetNextBenchSpot(board, player):
  bench = _GetBench(player)
  for pos in bench:
    if pos not in board:
      return pos
  return None

def _GetPossiblePositions(board, token, pos):
  if _IsOnBench(pos):
    return filter(lambda point: not IsOwnedBy(board, _PLAYER1, point), 
        filter(lambda point: not IsOwnedBy(board, _PLAYER2, point), 
        (Point(x, y) for x in xrange(_WIDTH) for y in xrange(_HEIGHT))))
  offsets = _GetOffsets(token.piece)
  return filter(lambda new_pos: not IsOwnedBy(board, token.owner, new_pos),
      filter(_IsValidPosition,
      map(functools.partial(_AddOffset, pos), 
      map(functools.partial(_SwitchDirectionForPlayer, token.owner), offsets))))

def _SwitchDirectionForPlayer(player, offset):
  if player == _PLAYER1:
    return offset
  return Offset(offset.x, offset.y * -1)


def _IsValidPosition(pos):
  return pos.x >= 0 and pos.y >= 0 and pos.x < _WIDTH and pos.y < _HEIGHT

def _AddOffset(pos, offset):
  return Point(pos.x + offset.x, pos.y + offset.y)

class Offsets:
  N = Offset(0, 1)
  S = Offset(0, -1)
  E = Offset(1, 0)
  W = Offset(-1, 0)
  NE = Offset(1, 1)
  NW = Offset(-1, 1)
  SE = Offset(1, -1)
  SW = Offset(-1, -1)

_CHICK_OFFSETS = [Offsets.N]
_GIRAFFE_OFFSETS = [Offsets.N, Offsets.E, Offsets.S, Offsets.W]
_ELEPHANT_OFFSETS = [Offsets.NE, Offsets.NW, Offsets.SE, Offsets.SW]
_LION_OFFSETS = [Offsets.N, Offsets.E, Offsets.S, Offsets.W, Offsets.NE, Offsets.NW, Offsets.SE, Offsets.SW]
_CHICKEN_OFFSETS = [Offsets.N, Offsets.S, Offsets.E, Offsets.W, Offsets.NW, Offsets.NE]

def _GetOffsets(piece):
  if piece == _CHICK:
    return _CHICK_OFFSETS
  if piece == _GIRAFFE:
    return _GIRAFFE_OFFSETS
  if piece == _ELEPHANT:
    return _ELEPHANT_OFFSETS
  if piece == _LION:
    return _LION_OFFSETS
  if piece == _CHICKEN:
    return _CHICKEN_OFFSETS

def GetLastRow(player):
  return 3 if player == _PLAYER1 else 0

def _IsLastRow(pos, player):
  return pos.y == GetLastRow(player)

def _DoSpecial(board, token, old_pos, possible_position):
  if (token.piece == _CHICK and _IsLastRow(possible_position, token.owner)
      and not _IsOnBench(old_pos)):
    new_board = CopyBoard(board)
    ClearToken(new_board, old_pos)
    SetToken(new_board, _CHICKEN, token.owner, possible_position)
    return new_board, possible_position

def _GetPieceAfterTaking(piece):
  if piece == _CHICKEN:
    return _CHICK
  return piece

def _IsOnBench(pos):
  return pos in _PLAYER1BENCH or pos in _PLAYER2BENCH

def _IsLionDead(board, player):
  lion = FindLion(board, player)
  return not lion or _IsOnBench(lion)

def _IsLionAtEnd(board, player):
  lion = FindLion(board, player)
  return lion and _IsLastRow(lion, player)

def FindLion(board, player):
  pos_of_lion = [pos for pos, token in board.iteritems()
                  if token.owner == player and token.piece == _LION]
  if not pos_of_lion:
    return None
  return pos_of_lion[0]

