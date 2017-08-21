import collections
import errno
import multiprocessing
import os
import signal
import socket

HOST, PORT = '', 8888

Environment = collections.namedtuple('Environment', ['args', 'method', 'body'])

class Server(object):

  address_family = socket.AF_INET
  socket_type = socket.SOCK_STREAM
  request_queue_size = 100

  def __init__(self, server_address, callback):
    self.callback = callback

    self.listen_socket = socket.socket(self.address_family, self.socket_type)
    self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.listen_socket.bind(server_address)
    self.listen_socket.listen(self.request_queue_size)

    # Get server host name and port
    host, port = self.listen_socket.getsockname()[:2]
    self.server_name = socket.getfqdn(host)
    self.server_port = port

  def ServeForever(self, verbose=False):
    while True:
      client_connection, client_address = self.listen_socket.accept()
      process = multiprocessing.Process(target=_Handle, args=(
        self.listen_socket, client_connection, self.callback, verbose))
      process.start()
      client_connection.close()

def _Handle(listen_socket, client_connection, callback, verbose):
  listen_socket.close()
  handler = Handler(client_connection, callback, verbose)
  handler.Handle()

class Handler(object):

  def __init__(self, client_connection, callback, verbose=False):
    self.client_connection = client_connection
    self.callback = callback
    self.verbose = verbose
    self.handled = False
    self.set_headers = False

  def Handle(self):
    if self.handled:
      return

    self.request = self.client_connection.recv(1024)
    if self.verbose:
      print PrefixLinesWith(self.request, '(%d) >' % os.getpid())

    self._ParseRequest()

    env = Environment(args=self.args, method=self.method, body=self.body)
    
    self.data = self.callback(self.path, env, self._StartResponse)
    self._Finish()

  def _StartResponse(self, status, response_headers):
    self.set_headers = True
    server_headers = []
    self.headers = server_headers + response_headers
    self.status = status

  def _ParseRequest(self):
    lines = [line.rstrip('\r\n') for line in self.request.splitlines()]
    self.method, path_and_args, self.version = lines[0].split()
    self._ParsePathAndArgs(path_and_args)

    empty = lines.index('')
    self.body = '\n'.join(lines[(empty+1):])


  def _ParsePathAndArgs(self, path_and_args):
    path_and_args_str = path_and_args.split('?', 1)
    self.path = path_and_args_str[0]
    if len(path_and_args_str) == 1:
      self.args = {}
      return
    args_str = path_and_args_str[1]
    args_and_values = args_str.split('&')
    self.args = dict(_ParseArgAndValue(arg_value)
                     for arg_value in args_and_values)

  def _Finish(self):
    contents = ''.join(data_part for data_part in self.data)

    if not self.set_headers:
      raise ValueError('Must call start_response before returning.')

    response = 'HTTP/1.1 {status}\r\n'.format(status=self.status)
    for header in self.headers:
      response += '{0}: {1}\r\n'.format(*header)
    response += '\r\n'
    response += contents

    if self.verbose:
      content = response
      if self.path.endswith(".png"):
        content = "BINARY FILE: %s" % self.path
      print PrefixLinesWith(content, '(%d) <' % os.getpid())

    try:
      self.client_connection.sendall(response)
    finally:
      self.client_connection.close()

def _ParseArgAndValue(arg_value):
  parts = arg_value.split('=', 1)
  if len(parts) == 1:
    return [arg_value, 'True']
  return parts

def PrefixLinesWith(text, prefix):
  return ''.join('{prefix} {line}\n'.format(prefix=prefix, line=line)
                 for line in text.splitlines())

def DoResponse(path, args, start_response):
  start_response(200, [])
  yield 'Path: %s\n' % path
  for arg, value in args.iteritems():
    yield '%s=%s\n' % (arg, value)

if __name__ == '__main__':
  server = Server(('', 8888), DoResponse)
  server.ServeForever()
