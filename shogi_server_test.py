import shogi_server
import unittest


def _ReadFile(path):
  handler = shogi_server.Handler(path, None, None, None)
  handler.ReadFile()
  return handler.code

class ReadFileTest(unittest.TestCase):

  def testServesFilesInStatic(self):
    self.assertEqual(_ReadFile('index.html'), 200)
    self.assertEqual(_ReadFile('img/../index.html'), 200)

  def testRefusesFilesOutsideStatic(self):
    self.assertEqual(_ReadFile('../server.py'), 404)
    self.assertEqual(_ReadFile('img/../../server.py'), 404)

if __name__ == '__main__':
  unittest.main()
