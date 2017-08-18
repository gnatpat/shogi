import json
import multiprocessing
import os
import server
import shogi
import random

NUM_THREADS = 10

class WebServer(object):

  def __init__(self, worker_queues, available_workers, game_mother_tasks, 
      match_making_tasks):
    self.worker_queues = worker_queues
    self.available_workers = available_workers
    self.game_mother_tasks = game_mother_tasks
    self.match_making_tasks = match_making_tasks

  def ServeForever(self):
    server.Server(('', 8008), self.EntryPoint).ServeForever()

  def EntryPoint(self, path, env, start_response):
    self.worker_index = self.available_workers.get()

    self.queue = self.worker_queues[self.worker_index]

    if path=="/start_game": 
      start_response(200, [('Content-Type', 'application/json')])
      response = self.StartGame()
    elif path=="/get_game_status":
      start_response(200, [('Content-Type', 'application/json')])
      game_id = int(env['args']['game'])
      player_id = int(env['args']['player'])
      response = self.GetStatus(game_id, player_id)
    elif path=="/move":
      start_response(200, [('Content-Type', 'application/json')])
      game_id = int(env['args']['game'])
      player_id = int(env['args']['player'])
      move_from = env['args']['from']
      move_to = env['args']['to']
      response = self.Move(game_id, player_id, move_from, move_to)
    elif path=="/wait_for_my_turn":
      start_response(200, [('Content-Type', 'application/json')])
      game_id = int(env['args']['game'])
      player_id = int(env['args']['player'])
      response = self.WaitForTurn(game_id, player_id)
    else:
      if path == '/':
        path = '/index.html'
      file_path = 'static/' + path[1:]
      if os.path.isfile(file_path):
        start_response(200, [])
        with open(file_path, 'r') as f:
          response = f.read()
      else:
        start_response(404, [('Content-Type', 'text/plain')])
        response = ["soz page not found", "maybe"]

    self.available_workers.put(self.worker_index)
    return response

  def StartGame(self):
    self.match_making_tasks.put(("match", self.worker_index))
    game_id, player_id = self.queue.get()
    return json.dumps({'game': game_id, 'player': player_id})

  def GetStatus(self, game_id, player_id):
    self.game_mother_tasks.put(("get_state", self.worker_index, game_id, player_id))
    game = self.queue.get()

    payload = {}
    payload['board'] = game.board
    payload['status'] = game.status[player_id]
    payload['my_turn'] = (player_id == game.player)
    if payload['my_turn']:
      payload['moves'] = shogi.PossibleMoves(game.board, player_id)
    return json.dumps(payload)

  def Move(self, game_id, player_id, move_from, move_to):
    self.game_mother_tasks.put(("get_state", self.worker_index, game_id, player_id))
    game = self.queue.get()

    if player_id != game.player:
      return self.GetStatus(game_id, player_id)

    boards = shogi.PossibleMoves(game.board, player_id)
    if move_to not in boards[move_from]:
      return self.GetStatus(game_id, player_id)

    next_board = boards[move_from][move_to]
    self.game_mother_tasks.put(("put_board", self.worker_index, game_id, next_board))
    ack = self.queue.get()
    return self.GetStatus(game_id, player_id)

  def WaitForTurn(self, game_id, player_id):
    self.game_mother_tasks.put(("wake_at_my_turn", self.worker_index, game_id, player_id))
    # TODO(npat): timeout in ~30 seconds and clear the waking.
    ack = self.queue.get()
    return self.GetStatus(game_id, player_id)

class Tasker(object):

  def __init__(self, tasks, worker_queues):
    self.tasks = tasks
    self.worker_queues = worker_queues
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

  def __init__(self, tasks, worker_queues):
    super(GameMother, self).__init__(tasks, worker_queues)
    self.games = {}
    self.waiting = {}
    self.AddFunction("get_state", self.GetState)
    self.AddFunction("put_board", self.PutBoard)
    self.AddFunction("wake_at_my_turn", self.WakeAtTurn)

  def GetState(self, from_worker, game_id, player_id):
    if not game_id in self.games:
      self.games[game_id] = shogi.Game()
    self.worker_queues[from_worker].put(self.games[game_id])

  def PutBoard(self, from_worker, game_id, board):
    self.games[game_id].UpdateBoard(board)
    self.worker_queues[from_worker].put(True)

    waiter = self.waiting[game_id]
    if waiter:
      self.worker_queues[waiter].put(True)
      del self.waiting[game_id]

  def WakeAtTurn(self, from_worker, game_id, player_id):
    game = self.games[game_id]

    if game.player == player_id or game.is_over:
      self.worker_queues[from_worker].put(True)
      return

    if game_id in self.waiting:
      self.worker_queues[self.waiting[game_id]].put(True)
    self.waiting[game_id] = from_worker

class MatchMaker(Tasker):

  def __init__(self, tasks, worker_queues):
    super(MatchMaker, self).__init__(tasks, worker_queues)
    self.next_game_id = 0
    self.waiting = None
    self.AddFunction('match', self.Match)

  def Match(self, from_worker):
    if self.waiting == None:
      self.waiting = from_worker
      return
    self.worker_queues[self.waiting].put((self.next_game_id, 0))
    self.worker_queues[from_worker].put((self.next_game_id, 1))
    self.waiting = None
    self.next_game_id += 1



def SetUp():
  available_workers = multiprocessing.Queue(NUM_THREADS)
  worker_queues = []
  for i in xrange(NUM_THREADS):
    worker_queue = multiprocessing.Queue()
    available_workers.put(i)
    worker_queues.append(worker_queue)

  game_mother_tasks = multiprocessing.Queue()
  match_making_tasks = multiprocessing.Queue()

  game_mother = GameMother(game_mother_tasks, worker_queues)
  game_mother_process = multiprocessing.Process(
      target=game_mother.ServeForever)
  game_mother_process.start()

  match_maker = MatchMaker(match_making_tasks, worker_queues)
  match_maker_process = multiprocessing.Process(
      target=match_maker.ServeForever)
  match_maker_process.start()

  web_server = WebServer(worker_queues, available_workers, game_mother_tasks,
      match_making_tasks)
  web_server.ServeForever()
  

if __name__=="__main__":
  SetUp()
