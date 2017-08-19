import collections
import json
import logging
import multiprocessing
import os
import server
import shogi
import random

NUM_THREADS = 10


class Sections:
  WORKER = "worker"
  MATCH_MAKER = "match_maker"
  GAME_MOTHER = "game_mother"


class ContentTypes:
  PLAIN = ('Content-Type', 'text/plain')
  JSON = ('Content-Type', 'application/json')
  HTML = ('Content-Type', 'text/html')
  CSS = ('Content-Type', 'text/css')
  JAVASCRIPT = ('Content-Type', 'text/javascript')


Address = collections.namedtuple('Address', ['section', 'index'])


class QueuePool(object):

  def __init__(self):
    self.queues = []
    self.access_queue = multiprocessing.Queue()

  def AddQueues(self, num_queues):
    for i in range(num_queues):
      self.queues.append(multiprocessing.Queue())
      self.access_queue.put(i)

  def Obtain(self):
    index = self.access_queue.get()
    return index, self.queues[index]

  def Done(self, index):
    self.access_queue.put(index)

  def Get(self, index):
    return self.queues[index]


class Connections(object):
  
  REGISTRY = {}

  @classmethod
  def AddQueues(cls, section, amount):
    assert section not in cls.REGISTRY
    cls.REGISTRY[section] = QueuePool()
    cls.REGISTRY[section].AddQueues(amount)

  @classmethod
  def Get(cls, address):
    section, index = address
    return cls.REGISTRY[section].Get(index)

  @classmethod
  def Obtain(cls, section):
    index, queue = cls.REGISTRY[section].Obtain()
    return Address(section, index), queue

  @classmethod
  def Done(cls, address):
    section, index = address
    return cls.REGISTRY[section].Done(index)


def _EntryPoint(path, env, start_response):
  assert path[0] == '/'
  path = path[1:]
  address, queue = Connections.Obtain(Sections.WORKER)
  handler = Handler(path, env, address, queue)
  try:
    contents = handler.Handle()
  except Exception as e:  # We need to be as broad as possible here.
    logging.exception("Could not handle a request to %s" % path)
    start_response(500, [ContentTypes.HTML])
    return [("<h1>500 Internal Server Error</h1>" +
             "<p>We're sorry, the server was unable to process your " +
             "request.</p>")]
  finally:
    Connections.Done(address)

  headers = [handler.content_type] + handler.headers
  start_response(handler.code, headers)
  return [contents]

class Handler(object):

  def __init__(self, path, env, address, queue):
    self.path = path
    self.env = env
    self.queue = queue
    self.address = address
    self.code = 200
    self.content_type = ContentTypes.JSON
    self.headers = []

  def _GetPlayerAndGame(self):
    game_id = int(self.env.args['game'])
    player_id = int(self.env.args['player'])
    return game_id, player_id

  def Handle(self):
    if self.path=="start_game": 
      return self.StartGame()

    if self.path=="get_game_status":
      game_id, player_id = self._GetPlayerAndGame()
      return self.GetStatus(game_id, player_id)

    if self.path=="move":
      game_id, player_id = self._GetPlayerAndGame()
      move_from = self.env.args['from']
      move_to = self.env.args['to']
      return self.Move(game_id, player_id, move_from, move_to)

    if self.path=="wait_for_my_turn":
      game_id, player_id = self._GetPlayerAndGame()
      return self.WaitForTurn(game_id, player_id)

    return self.ReadFile()

  def StartGame(self):
    MatchMaker.GetAnyQueue().put(("match", self.address))
    game_id, player_id = self.queue.get()
    return json.dumps({'game': game_id, 'player': player_id})

  def GetStatus(self, game_id, player_id):
    GameMother.GetQueue(game_id).put(("get_state", self.address, game_id, player_id))
    game = self.queue.get()

    payload = {}
    payload['board'] = game.board
    payload['status'] = game.status[player_id]
    payload['my_turn'] = (player_id == game.player)
    if payload['my_turn']:
      payload['moves'] = shogi.PossibleMoves(game.board, player_id)
    return json.dumps(payload)

  def Move(self, game_id, player_id, move_from, move_to):
    GameMother.GetQueue(game_id).put(("get_state", self.address, game_id, player_id))
    game = self.queue.get()

    if player_id != game.player:
      return self.GetStatus(game_id, player_id)

    boards = shogi.PossibleMoves(game.board, player_id)
    if move_to not in boards[move_from]:
      return self.GetStatus(game_id, player_id)

    next_board = boards[move_from][move_to]
    GameMother.GetQueue(game_id).put(("put_board", self.address, game_id, next_board))
    ack = self.queue.get()
    return self.GetStatus(game_id, player_id)

  def WaitForTurn(self, game_id, player_id):
    GameMother.GetQueue(game_id).put(("wake_at_my_turn", self.address, game_id, player_id))
    # TODO(npat): timeout in ~30 seconds and clear the waking.
    ack = self.queue.get()
    return self.GetStatus(game_id, player_id)

  def ReadFile(self):
    if self.path == '':
      self.path = 'index.html'

    file_path = 'static/' + self.path
    if os.path.isfile(file_path):
      if file_path.endswith(".html"): self.content_type = ContentTypes.HTML
      if file_path.endswith(".css"): self.content_type = ContentTypes.CSS
      if file_path.endswith(".js"): self.content_type = ContentTypes.JAVASCRIPT
      with open(file_path, 'r') as f:
        return f.read()
    else:
      self.code = 404
      self.content_type = ContentTypes.HTML
      return "<h1>404 Page Not Found<h1>"

class Tasker(object):

  num_instances = 0
  section = None

  @classmethod
  def SpawnAll(cls):
    for _ in xrange(cls.num_instances):
      instance = cls()
      process = multiprocessing.Process(target=instance.ServeForever)
      process.start()

  @classmethod
  def SetPoolSize(cls, num):
    Connections.AddQueues(cls.section, num)
    cls.num_instances = num

  @classmethod
  def GetAnyQueue(cls, *args):
    # Default to random distrubition
    return Connections.Get((cls.section, random.randrange(cls.num_instances)))

  def __init__(self):
    self.address, self.tasks = Connections.Obtain(self.section)
    self.functions = {}

  def AddFunction(self, name, function):
    self.functions[name] = function

  def ServeForever(self):
    while True:
      task = self.tasks.get()
      task_type = task[0]
      args = task[1:]
      if task_type not in self.functions:
        print "Task %s not a valid task type!" % task_type
        continue
      self.functions[task_type](*args)


class GameMother(Tasker):

  section = Sections.GAME_MOTHER

  @classmethod
  def GetQueue(cls, game_id):
    index = game_id % cls.num_instances
    return Connections.Get((cls.section, index))

  def __init__(self):
    super(GameMother, self).__init__()
    self.games = {}
    self.waiting = {}
    self.AddFunction("get_state", self.GetState)
    self.AddFunction("put_board", self.PutBoard)
    self.AddFunction("wake_at_my_turn", self.WakeAtTurn)

  def GetState(self, caller, game_id, player_id):
    if not game_id in self.games:
      self.games[game_id] = shogi.Game()
    Connections.Get(caller).put(self.games[game_id])

  def PutBoard(self, caller, game_id, board):
    self.games[game_id].UpdateBoard(board)
    Connections.Get(caller).put(True)

    waiter = self.waiting[game_id]
    if waiter:
      Connections.Get(waiter).put(True)
      del self.waiting[game_id]

  def WakeAtTurn(self, caller, game_id, player_id):
    game = self.games[game_id]

    if game.player == player_id or game.is_over:
      Connections.Get(caller).put(True)
      return

    if game_id in self.waiting:
      Connections.Get(self.waiting[game_id]).put(True)
    self.waiting[game_id] = caller


class MatchMaker(Tasker):

  section = Sections.MATCH_MAKER

  def __init__(self):
    super(MatchMaker, self).__init__()
    self.next_game_id = 0
    self.waiting = None
    self.AddFunction('match', self.Match)

  def Match(self, caller):
    if self.waiting == None:
      self.waiting = caller
      return
    Connections.Get(self.waiting).put((self.next_game_id, 0))
    Connections.Get(caller).put((self.next_game_id, 1))
    self.waiting = None
    self.next_game_id += 1


def SetUp():
  MatchMaker.SetPoolSize(1)
  GameMother.SetPoolSize(1)
  Connections.AddQueues(Sections.WORKER, NUM_THREADS)

  MatchMaker.SpawnAll()
  GameMother.SpawnAll()
  server.Server(('', 8008), _EntryPoint).ServeForever()

if __name__=="__main__":
  SetUp()
