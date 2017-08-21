import collections
import json
import logging
import multiprocessing
import os
import server
import shogi
import shogi_ai
import random

NUM_THREADS = 20


class Sections:
  WORKER = "worker"
  MATCH_MAKER = "match_maker"
  GAME_MOTHER = "game_mother"
  AI_MOTHER = "ai_mother"


class ContentTypes:
  PLAIN = ('Content-Type', 'text/plain')
  JSON = ('Content-Type', 'application/json')
  HTML = ('Content-Type', 'text/html')
  CSS = ('Content-Type', 'text/css')
  JAVASCRIPT = ('Content-Type', 'text/javascript')

Player = collections.namedtuple('Player', ['order', 'is_human'])

GameState = collections.namedtuple('GameState', ['game', 'players'])

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

  def Handle(self):
    if self.path=="start_game": 
      return self.StartGame()

    if self.path=="start_ai_game":
      return self.StartAIGame()

    if self.path=="get_game_status":
      player_id = int(self.env.args['player'])
      return self.GetStatus(player_id)

    if self.path=="move":
      player_id = int(self.env.args['player'])
      move_from = self.env.args['from']
      move_to = self.env.args['to']
      return self.Move(player_id, move_from, move_to)

    if self.path=="wait_for_my_turn":
      player_id = int(self.env.args['player'])
      return self.WaitForTurn(player_id)

    return self.ReadFile()

  def StartGame(self):
    MatchMaker.GetAnyQueue().put(("match", self.address))
    player_id, player = self.queue.get()
    payload = {'player_id': player_id, 'player': player }
    return json.dumps(payload)

  def StartAIGame(self):
    GameMother.GetAnyQueue().put(("new_board", self.address, [True, False]))
    player_id, ai_player_id = self.queue.get()
    payload = {'player_id': player_id, 'player': shogi.PLAYER1 }
    self._DoAITurnIfNeeded(player_id)
    return json.dumps(payload)

  def GetStatus(self, player_id):
    GameMother.GetQueue(player_id).put(("get_state", self.address, player_id))
    state = self.queue.get()
    game = state.game
    player = state.players[player_id].order

    payload = {}
    payload['board'] = game.board
    payload['status'] = game.status[player]
    payload['current_player'] = game.player
    if game.player == player:
      payload['moves'] = shogi.PossibleMoves(game.board, player)
    return json.dumps(payload)

  def Move(self, player_id, move_from, move_to):
    GameMother.GetQueue(player_id).put(("get_state", self.address, player_id))
    state = self.queue.get()
    game = state.game
    player = state.players[player_id].order

    if player != game.player:
      return self.GetStatus(player_id)

    boards = shogi.PossibleMoves(game.board, game.player)
    if move_to not in boards[move_from]:
      return self.GetStatus(player_id)

    next_board = boards[move_from][move_to]
    GameMother.GetQueue(player_id).put(("put_board", self.address, player_id, next_board))
    ack = self.queue.get()
    self._DoAITurnIfNeeded(player_id)
    return self.GetStatus(player_id)

  def WaitForTurn(self, player_id):
    GameMother.GetQueue(player_id).put(("wake_at_my_turn", self.address, player_id))
    # TODO(npat): timeout in ~30 seconds and clear the waking.
    ack = self.queue.get()
    return self.GetStatus(player_id)

  def _DoAITurnIfNeeded(self, player_id):
    GameMother.GetQueue(player_id).put(("get_state", self.address, player_id))
    state = self.queue.get()
    current_player = state.game.player
    for other_player_id, player in state.players.iteritems():
      if player.is_human or player.order != current_player:
        continue
      ai_address, ai_queue = Connections.Obtain(Sections.WORKER)
      process = multiprocessing.Process(
          target=DoAITurn, args=(ai_address, ai_queue, other_player_id))
      process.start()

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


class GameMother(Tasker):

  section = Sections.GAME_MOTHER

  @classmethod
  def GetQueue(cls, player_id):
    index = player_id % cls.num_instances
    return Connections.Get((cls.section, index))

  def __init__(self):
    super(GameMother, self).__init__()
    self.game_states = {}
    self.waiting = collections.defaultdict(list)
    self.AddFunction("get_state", self.GetState)
    self.AddFunction("put_board", self.PutBoard)
    self.AddFunction("wake_at_my_turn", self.WakeAtTurn)
    self.AddFunction("new_board", self.NewBoard)

  def GetState(self, caller, player_id):
    if not player_id in self.game_states:
      Connections.Get(caller).put(False)
      return
    state = self.game_states[player_id]
    Connections.Get(caller).put(state)

  def PutBoard(self, caller, player_id, board):
    game = self.game_states[player_id].game
    game.UpdateBoard(board)
    Connections.Get(caller).put(True)

    waiters = self.waiting[player_id]
    for waiter in waiters:
      Connections.Get(waiter).put(True)
    del self.waiting[player_id]

  def WakeAtTurn(self, caller, player_id):
    state = self.game_states[player_id]
    game = state.game
    player = state.players[player_id].order

    if game.player == player or game.is_over:
      Connections.Get(caller).put(True)
      return

    players = state.players
    for other_player_id in players.keys():
      if other_player_id != player_id:
        self.waiting[other_player_id].append(caller)

  def NewBoard(self, caller, human_or_ai=None):
    if not human_or_ai:
      human_or_ai = [True, True]

    player_1_id = random.getrandbits(32) * self.num_instances + self.address.index
    player_2_id = random.getrandbits(32) * self.num_instances + self.address.index

    game = shogi.Game()
    players = {player_1_id: Player(shogi.PLAYER1, human_or_ai[0]), 
               player_2_id: Player(shogi.PLAYER2, human_or_ai[1])}
    state = GameState(game, players)

    self.game_states[player_1_id] = state
    self.game_states[player_2_id] = state
    Connections.Get(caller).put((player_1_id, player_2_id))


class MatchMaker(Tasker):

  section = Sections.MATCH_MAKER

  def __init__(self):
    super(MatchMaker, self).__init__()
    self.waiting = None
    self.AddFunction('match', self.Match)

  def Match(self, caller):
    if self.waiting == None:
      self.waiting = caller
      return
    temp_address, temp_queue = Connections.Obtain(Sections.WORKER)
    GameMother.GetAnyQueue().put(('new_board', temp_address))
    player_1_id, player_2_id = temp_queue.get()
    Connections.Done(temp_address)
    Connections.Get(self.waiting).put((player_1_id, shogi.PLAYER1))
    Connections.Get(caller).put((player_2_id, shogi.PLAYER2))
    self.waiting = None


def DoAITurn(address, queue, player_id):
  GameMother.GetQueue(player_id).put(('get_state', address, player_id))
  state = queue.get()
  assert state.players[player_id].order == state.game.player

  possible_boards = shogi.Next(state.game.board, state.game.player)
  board_chosen = shogi_ai.Mix(possible_boards, state.game.player) 
  new_board = possible_boards[board_chosen]

  GameMother.GetQueue(player_id).put(('put_board', address, player_id, new_board))
  queue.get()
  Connections.Done(address)



def SetUp():
  MatchMaker.SetPoolSize(1)
  GameMother.SetPoolSize(1)
  Connections.AddQueues(Sections.WORKER, NUM_THREADS)

  MatchMaker.SpawnAll()
  GameMother.SpawnAll()
  server.Server(('', 8008), _EntryPoint).ServeForever(True)

if __name__=="__main__":
  SetUp()
