import shogi
import functools
import random

def RandomShogiPlayer(boards, _):
  return random.randrange(len(boards))

def TakesFirstBoard(boards, _):
  return 0

def _CountPieces(board, player):
  return sum(1 for _, piece in board.iteritems() if piece.owner==player)

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
  return _CountPieces(board, player) * 1 + _DistanceToEnd(board, player) * 1

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
    return -1, -99
  max_value = max(values)
  return values.index(max_value), max_value

def _Min(boards, player, depth, func, parents):
  if depth == 0:
    values = [func(board) for board in boards]
  else:
    other_player = shogi.OtherPlayer(player)
    values = [
        _Max(shogi.Next(board, other_player), other_player, depth-1, func, parents + [board])[1]
        for board in boards]
  if not values:
    return -1, 99
  min_value = min(values)
  return values.index(min_value), min_value

players = [Mix, LikesMorePieces]
#players = [LikesMorePieces, LionToEnd]
#players = [LikesMorePieces, LionToEnd, RandomShogiPlayer, TakesFirstBoard, LikesMorePiecesDeep, LionToEndDeep]
