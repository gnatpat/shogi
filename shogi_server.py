import json
import multiprocessing
import os
import server
import shogi
import random

NUM_THREADS = 10

def _NumToPlayer(num):
  if num == 0: return shogi._PLAYER1
  return shogi._PLAYER2

class WebServer(object):

  def __init__(self, worker_queues, available_workers, board_mother_tasks, 
      match_making_tasks):
    self.worker_queues = worker_queues
    self.available_workers = available_workers
    self.board_mother_tasks = board_mother_tasks
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
    print "Getting status", game_id, player_id
    self.board_mother_tasks.put(("get_state", self.worker_index, game_id, player_id))
    board, whos_turn = self.queue.get()
    payload = {}
    payload['board'] = board
    payload['my_turn'] = player_id == whos_turn
    if payload['my_turn']:
      payload['moves'] = shogi.PossibleMoves(board, _NumToPlayer(player_id))
    return json.dumps(payload)

  def Move(self, game_id, player_id, move_from, move_to):
    self.board_mother_tasks.put(("get_state", self.worker_index, game_id, player_id))
    board, whos_turn = self.queue.get()
    if player_id != whos_turn:
      return self.GetStatus(game_id, player_id)
    boards = shogi.PossibleMoves(board, _NumToPlayer(player_id))
    if move_to not in boards[move_from]:
      return self.GetStatus(game_id, player_id)
    next_board = boards[move_from][move_to]
    self.board_mother_tasks.put(("put_board", self.worker_index, game_id, next_board, player_id))
    ack = self.queue.get()
    return self.GetStatus(game_id, player_id)

  def WaitForTurn(self, game_id, player_id):
    self.board_mother_tasks.put(("wake_at_my_turn", self.worker_index, game_id, player_id))
    # TODO(npat): timeout in ~30 seconds and clear the waking.
    ack = self.queue.get()
    return self.GetStatus(game_id, player_id)


class BoardMother(object):

  def __init__(self, tasks, worker_queues):
    self.tasks = tasks
    self.worker_queues = worker_queues
    # TODO(npat): store boards as named tuple (board, player)
    self.boards = {}
    self.waiting = {}
    self.next_board = 0

  def ServeForever(self):
    while True:
      task = self.tasks.get()
      task_type = task[0]
      from_worker = task[1]
      args = task[2:]
      print task
      if task_type == "get_state":
        game_id, player_id = args
        if not game_id in self.boards:
          self.boards[game_id] = (shogi.StartingBoard(), random.randint(0, 1))
        self.worker_queues[from_worker].put(self.boards[game_id])
        continue
      elif task_type == "put_board":
        game_id, next_board, by_player = args
        self.boards[game_id] = (next_board, 1-by_player)
        self.worker_queues[from_worker].put(True)
        waiter = self.waiting[game_id]
        if waiter:
          self.worker_queues[waiter].put(True)
          del self.waiting[game_id]
        continue
      elif task_type == "wake_at_my_turn":
        game_id, player_id = args
        if self.boards[game_id][1] == player_id:
          self.worker_queues[from_worker].put(True)
          continue
        if game_id in self.waiting:
          self.worker_queues[self.waiting[game_id]].put(True)
        self.waiting[game_id] = from_worker
        continue

class MatchMaker(object):

  def __init__(self, tasks, worker_queues):
    self.tasks = tasks
    self.worker_queues = worker_queues
    self.next_game_id = 0
    self.waiting = None

  def ServeForever(self):
    while True:
      task = self.tasks.get()
      task_type = task[0]
      from_worker = task[1]
      args = task[2:]
      if task_type == "match":
        if self.waiting == None:
          self.waiting = from_worker
          continue
        self.worker_queues[self.waiting].put((self.next_game_id, 0))
        self.worker_queues[from_worker].put((self.next_game_id, 1))
        self.waiting = None
        self.next_game_id += 1
        continue



def SetUp():
  available_workers = multiprocessing.Queue(NUM_THREADS)
  worker_queues = []
  for i in xrange(NUM_THREADS):
    worker_queue = multiprocessing.Queue()
    available_workers.put(i)
    worker_queues.append(worker_queue)

  board_mother_tasks = multiprocessing.Queue()
  match_making_tasks = multiprocessing.Queue()

  board_mother = BoardMother(board_mother_tasks, worker_queues)
  board_mother_process = multiprocessing.Process(
      target=board_mother.ServeForever)
  board_mother_process.start()

  match_maker = MatchMaker(match_making_tasks, worker_queues)
  match_maker_process = multiprocessing.Process(
      target=match_maker.ServeForever)
  match_maker_process.start()

  web_server = WebServer(worker_queues, available_workers, board_mother_tasks,
      match_making_tasks)
  web_server.ServeForever()
  

if __name__=="__main__":
  SetUp()
