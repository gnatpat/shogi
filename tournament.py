import collections
import itertools
import shogi
import shogi_player
import random

def DoGame(player1, player2):
  players = {shogi._PLAYER1: player1, shogi._PLAYER2: player2}
  board = shogi.StartingBoard();
  player = random.choice([shogi._PLAYER1, shogi._PLAYER2])
  count = 0
  while True:
    boards = shogi.Next(board, player)
    index = players[player](boards, player)
    board = boards[index]
    # print shogi.PrintBoard(board)
    if shogi.HasWon(board, player):
      break
    player = shogi.OtherPlayer(player)
    count += 1
    if count > 250:
      print "DRAW", players
      return "DRAW"
  print player, "WINS", players
  return players[player]

def Tournament(players, repetitions):
  matchups = list(itertools.combinations(players, 2)) * repetitions
  results = (DoGame(*competitors) for competitors in matchups)
  winners = collections.Counter(results)
  print winners

if __name__=="__main__":
  Tournament(shogi_player.players, 1)
