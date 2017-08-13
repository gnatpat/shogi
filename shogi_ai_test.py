import unittest
import shogi
import shogi_ai

class TestLikesMorePieces(unittest.TestCase):
  def testCountPieces(self):
    board = shogi.StartingBoard()
    self.assertEqual(shogi_ai._CountPieces(board, shogi._PLAYER1), 4)
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER1, shogi.Point(0, 0))
    self.assertEqual(shogi_ai._CountPieces(board, shogi._PLAYER1), 1)

if __name__ == '__main__':
  unittest.main()

