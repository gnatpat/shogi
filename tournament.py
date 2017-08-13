import collections
import itertools
import shogi
import shogi_ai
import random

def DoGame(player1, player2):
  players = {shogi._PLAYER1: player1, shogi._PLAYER2: player2}
  board = shogi.StartingBoard();
  player = shogi._PLAYER1
  count = 0
  boards_count = collections.defaultdict(int)
  print shogi.PrintBoard(board)
  while True:
    boards = shogi.Next(board, player)
    index = players[player](boards, player)
    board = boards[index]
    print shogi.PrintBoard(board)
    if shogi.HasWon(board, player):
      break
    player = shogi.OtherPlayer(player)
    boards_count[board] += 1
    if boards_count[board] == 3:
      print "DRAW", players
      return "DRAW"
  print player, "WINS", players
  return players[player]

def Tournament(players, repetitions):
  matchups = list(itertools.permutations(players, 2)) * repetitions
  results = (DoGame(*competitors) for competitors in matchups)
  winners = collections.Counter(results)
  print winners

if __name__=="__main__":
  random.seed(37)
  Tournament(shogi_ai.players, 1)
