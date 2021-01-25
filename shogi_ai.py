import shogi
import functools
import random

def RandomShogiPlayer(boards, _):
  return random.randrange(len(boards))

def TakesFirstBoard(boards, _):
  return 0

def _CountPieces(board, player):
  return sum(1 for _, piece in board.iteritems() if piece.owner==player)

def _SimpleEval(board, player):
  other=shogi.PLAYER1 if player==shogi.PLAYER2 else shogi.PLAYER1
  BoardEval = 0
  for idx, pos in board.iteritems():
    x, y = pos
    in_center = True if (x == 1 and y == 1) or (x == 1 and y == 2) else False
    if pos.owner==player:
      if pos.piece == shogi.CHICK:
        BoardEval += 20
        if in_center:
          BoardEval += 10
      elif pos.piece == shogi.CHICKEN:
        BoardEval += 30
        if in_center:
          BoardEval += 15
      elif pos.piece == shogi.ELEPHANT:
        BoardEval += 35
        if in_center:
          BoardEval += 15
      elif pos.piece == shogi.GIRAFFE:
        BoardEval += 40
        if in_center:
          BoardEval += 15
      elif pos.piece == shogi.LION:
        if in_center:
          BoardEval += 15
    elif pos.owner==other:
      if pos.piece == shogi.CHICK:
        BoardEval -= 20
        if in_center:
          BoardEval -= 10
      elif pos.piece == shogi.CHICKEN:
        BoardEval -= 30
        if in_center:
          BoardEval -= 15
      elif pos.piece == shogi.ELEPHANT:
        BoardEval -= 35
        if in_center:
          BoardEval -= 15
      elif pos.piece == shogi.GIRAFFE:
        BoardEval -= 40
        if in_center:
          BoardEval -= 15
      elif pos.piece == shogi.LION:
        if in_center:
          BoardEval -= 15

  return BoardEval

def LikesMorePieces(boards, player):
  return _Max(boards, player, 2, functools.partial(_CountPieces, player=player), [])[0]

def LikesMorePiecesDeep(boards, player):
  return _Max(boards, player, 4, functools.partial(_CountPieces, player=player), [])[0]

def _DistanceToEnd(board, player):
  return -1 * abs(shogi.GetLastRow(player) - shogi.GetY(shogi.FindLion(board, player)))

def LionToEnd(boards, player):
  return _Max(boards, player, 2, functools.partial(_DistanceToEnd, player=player), [])[0]
  
def LionToEndDeep(boards, player):
  return _Max(boards, player, 4, functools.partial(_DistanceToEnd, player=player), [])[0]

def _Mix(board, player):
  return _SimpleEval(board, player) * 1 # + _CountPieces(board, player) * 1 + _DistanceToEnd(board, player) * 1

def Mix(boards, player):
  return _Max(boards, player, 2, functools.partial(_Mix, player=player), [])[0]

def _Max(boards, player, depth, func, parents):
  if depth == 0:
    values = [func(board) for board in boards]
  else:
    other_player = shogi.OtherPlayer(player)
    values = [
        _Min(shogi.Next(board, other_player), other_player, depth-1, func, parents + [board])[1]
        for board in boards]
  if not values:
    return -1, -999
  max_value = max(values)
  return values.index(max_value), max_value + len(values)

def _Min(boards, player, depth, func, parents):
  if depth == 0:
    values = [func(board) for board in boards]
  else:
    other_player = shogi.OtherPlayer(player)
    values = [
        _Max(shogi.Next(board, other_player), other_player, depth-1, func, parents + [board])[1]
        for board in boards]
  if not values:
    return -1, 999
  min_value = min(values)
  return values.index(min_value), min_value - len(values)

players = [Mix, LikesMorePieces]
#players = [LikesMorePieces, LionToEnd]
#players = [LikesMorePieces, LionToEnd, RandomShogiPlayer, TakesFirstBoard, LikesMorePiecesDeep, LionToEndDeep]
