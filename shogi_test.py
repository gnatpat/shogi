import shogi
from shogi import Point
import functools
import unittest

class MainTest(unittest.TestCase):

  def testGetStartBoard(self):
    board = shogi.StartingBoard()

    self.assertEqual(shogi.GetPiece(board, Point(0, 0)), shogi._ELEPHANT)
    self.assertEqual(shogi.GetPiece(board, Point(1, 0)), shogi._LION)
    self.assertEqual(shogi.GetPiece(board, Point(2, 0)), shogi._GIRAFFE)
    self.assertEqual(shogi.GetPiece(board, Point(1, 1)), shogi._CHICK)
    self.assertEqual(shogi.GetOwner(board, Point(0, 0)), shogi._PLAYER1)
    self.assertEqual(shogi.GetOwner(board, Point(1, 0)), shogi._PLAYER1)
    self.assertEqual(shogi.GetOwner(board, Point(2, 0)), shogi._PLAYER1)
    self.assertEqual(shogi.GetOwner(board, Point(1, 1)), shogi._PLAYER1)
    self.assertEqual(shogi.GetPiece(board, Point(2, 3)), shogi._ELEPHANT)
    self.assertEqual(shogi.GetPiece(board, Point(1, 3)), shogi._LION)
    self.assertEqual(shogi.GetPiece(board, Point(0, 3)), shogi._GIRAFFE)
    self.assertEqual(shogi.GetPiece(board, Point(1, 2)), shogi._CHICK)
    self.assertEqual(shogi.GetOwner(board, Point(2, 3)), shogi._PLAYER2)
    self.assertEqual(shogi.GetOwner(board, Point(1, 3)), shogi._PLAYER2)
    self.assertEqual(shogi.GetOwner(board, Point(0, 3)), shogi._PLAYER2)
    self.assertEqual(shogi.GetOwner(board, Point(1, 2)), shogi._PLAYER2)

  def testGetPossibleBoardsChick(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER1, Point(1, 1))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    self.assertEqual(len(boards), 1)
    self.assertEqual(shogi.GetPiece(boards[0], Point(1, 2)), shogi._CHICK)
    self.assertEqual(shogi.GetOwner(boards[0], Point(1, 2)), shogi._PLAYER1)

  def testGetPossibleBoardsGiraffe(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._GIRAFFE, shogi._PLAYER1, Point(1, 1))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    expected_positions = [Point(1, 2), Point(1, 0), Point(0, 1), Point(2, 1)]
    expected_boards = []
    for pos in expected_positions:
      new_board = shogi.EmptyBoard()
      shogi.SetToken(new_board, shogi._GIRAFFE, shogi._PLAYER1, pos)
      expected_boards.append(new_board)

    self.assertItemsEqual(boards, expected_boards)

  def testGetPossibleBoardsElephant(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._ELEPHANT, shogi._PLAYER1, Point(1, 1))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    expected_positions = [Point(2, 2), Point(0, 2), Point(0, 0), Point(2, 0)]
    expected_boards = []
    for pos in expected_positions:
      new_board = shogi.EmptyBoard()
      shogi.SetToken(new_board, shogi._ELEPHANT, shogi._PLAYER1, pos)
      expected_boards.append(new_board)

    self.assertItemsEqual(boards, expected_boards)

  def testGetPossibleBoardsLion(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._LION, shogi._PLAYER1, Point(1, 1))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    expected_positions = [
        Point(2, 2), Point(0, 2), Point(0, 0), Point(2, 0), 
        Point(1, 2), Point(1, 0), Point(0, 1), Point(2, 1)]
    expected_boards = []
    for pos in expected_positions:
      new_board = shogi.EmptyBoard()
      shogi.SetToken(new_board, shogi._LION, shogi._PLAYER1, pos)
      expected_boards.append(new_board)

    self.assertItemsEqual(boards, expected_boards)

  def testGetPossibleBoardsLion(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._CHICKEN, shogi._PLAYER1, Point(1, 1))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    expected_positions = [
        Point(2, 2), Point(0, 2), Point(1, 0), 
        Point(1, 2), Point(0, 1), Point(2, 1)]
    expected_boards = []
    for pos in expected_positions:
      new_board = shogi.EmptyBoard()
      shogi.SetToken(new_board, shogi._CHICKEN, shogi._PLAYER1, pos)
      expected_boards.append(new_board)

    self.assertItemsEqual(boards, expected_boards)

  def testGetPossibleBoardsNextToBottomLeft(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._LION, shogi._PLAYER1, Point(0, 0))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    expected_positions = [Point(1, 0), Point(1, 1), Point(0, 1)]
    expected_boards = []
    for pos in expected_positions:
      new_board = shogi.EmptyBoard()
      shogi.SetToken(new_board, shogi._LION, shogi._PLAYER1, pos)
      expected_boards.append(new_board)

    self.assertItemsEqual(boards, expected_boards)

  def testGetPossibleBoardsNextToTopRight(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._LION, shogi._PLAYER1, Point(2, 3))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    expected_positions = [Point(2, 2), Point(1, 2), Point(1, 3)]
    expected_boards = []
    for pos in expected_positions:
      new_board = shogi.EmptyBoard()
      shogi.SetToken(new_board, shogi._LION, shogi._PLAYER1, pos)
      expected_boards.append(new_board)

    self.assertItemsEqual(boards, expected_boards)

  def testGetPossibleBoardsWithMultiple(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER1, Point(1, 0))
    shogi.SetToken(board, shogi._GIRAFFE, shogi._PLAYER1, Point(1, 2))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    expected_boards = []
    expected_positions = [Point(2, 2), Point(0, 2), Point(1, 3), Point(1, 1)]
    for pos in expected_positions:
      new_board = shogi.EmptyBoard()
      shogi.SetToken(new_board, shogi._CHICK, shogi._PLAYER1, Point(1, 0))
      shogi.SetToken(new_board, shogi._GIRAFFE, shogi._PLAYER1, pos)
      expected_boards.append(new_board)
    new_board = shogi.EmptyBoard()
    shogi.SetToken(new_board, shogi._GIRAFFE, shogi._PLAYER1, Point(1, 2))
    shogi.SetToken(new_board, shogi._CHICK, shogi._PLAYER1, Point(1, 1))
    expected_boards.append(new_board)

    self.assertItemsEqual(boards, expected_boards)

  def testCantTakeYourself(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER1, Point(1, 0))
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER1, Point(1, 1))

    expected_board = shogi.EmptyBoard()
    shogi.SetToken(expected_board, shogi._CHICK, shogi._PLAYER1, Point(1, 0))
    shogi.SetToken(expected_board, shogi._CHICK, shogi._PLAYER1, Point(1, 2))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    self.assertEqual(len(boards), 1)
    self.assertEqual(boards[0], expected_board)

  def testChickTurnsIntoChicken(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER1, Point(1, 2))

    expected_board = shogi.EmptyBoard()
    shogi.SetToken(expected_board, shogi._CHICKEN, shogi._PLAYER1, Point(1, 3))

    boards = list(shogi.Next(board, shogi._PLAYER1))

    self.assertEqual(len(boards), 1)
    self.assertEqual(boards[0], expected_board)

  def testPlayer2GoesTheOtherWay(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER2, Point(1, 2))

    boards = list(shogi.Next(board, shogi._PLAYER2))

    expected_board = shogi.EmptyBoard()
    shogi.SetToken(expected_board, shogi._CHICK, shogi._PLAYER2, Point(1, 1))

    self.assertEqual(len(boards), 1)
    self.assertEqual(boards[0], expected_board)

  def testTakenOpponentGoesOnBench(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER2, Point(1, 2))
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER1, Point(1, 1))

    boards = list(shogi.Next(board, shogi._PLAYER2))

    expected_board = shogi.EmptyBoard()
    shogi.SetToken(expected_board, shogi._CHICK, shogi._PLAYER2, Point(1, 1))
    shogi.SetToken(expected_board, shogi._CHICK, shogi._PLAYER2,
                   shogi._PLAYER2BENCH[0])

    self.assertEqual(len(boards), 1)
    self.assertEqual(boards[0], expected_board)

  def testTakenChickenBecomesChick(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER2, Point(1, 2))
    shogi.SetToken(board, shogi._CHICKEN, shogi._PLAYER1, Point(1, 1))

    boards = list(shogi.Next(board, shogi._PLAYER2))

    expected_board = shogi.EmptyBoard()
    shogi.SetToken(expected_board, shogi._CHICK, shogi._PLAYER2, Point(1, 1))
    shogi.SetToken(expected_board, shogi._CHICK, shogi._PLAYER2,
                   shogi._PLAYER2BENCH[0])

    self.assertEqual(len(boards), 1)
    self.assertEqual(boards[0], expected_board)

  def testBoardIsInCheck(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._LION, shogi._PLAYER1, Point(1, 1))
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER2, Point(1, 2))

    self.assertTrue(shogi.IsInCheck(board, shogi._PLAYER1))

  def testBoardIsNotInCheck(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._LION, shogi._PLAYER1, Point(1, 1))
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER2, Point(1, 3))

    self.assertFalse(shogi.IsInCheck(board, shogi._PLAYER1))

  def testCantMoveIntoCheck(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._LION, shogi._PLAYER2, Point(0, 3))
    shogi.SetToken(board, shogi._GIRAFFE, shogi._PLAYER1, Point(1, 3))
    shogi.SetToken(board, shogi._GIRAFFE, shogi._PLAYER1, Point(1, 2))
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER1, Point(0, 2))

    self.assertTrue(shogi.IsInCheck(board, shogi._PLAYER2))
    self.assertEqual(len(list(shogi.Next(board, shogi._PLAYER2))), 0)

  def testHasWonByCheckmate(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._LION, shogi._PLAYER2, Point(0, 3))
    shogi.SetToken(board, shogi._GIRAFFE, shogi._PLAYER1, Point(1, 3))
    shogi.SetToken(board, shogi._GIRAFFE, shogi._PLAYER1, Point(1, 2))
    shogi.SetToken(board, shogi._CHICK, shogi._PLAYER1, Point(0, 2))

    self.assertTrue(shogi.HasWon(board, shogi._PLAYER1))

  def testHasWonByReachingTheEnd(self):
    board = shogi.EmptyBoard()
    shogi.SetToken(board, shogi._LION, shogi._PLAYER2, Point(0, 0))
    shogi.SetToken(board, shogi._LION, shogi._PLAYER1, Point(0, 2))
    
    self.assertTrue(shogi.HasWon(board, shogi._PLAYER2))



if __name__ == '__main__':
  unittest.main()
