# Deployment

This app is deployed with [npd](https://github.com/gnatpat/npd).

- `npd.toml` at the repo root is the whole deploy config: the start command and
  the route it is served under.
- Unlike the other apps, this one has **no deploy workflow**: it is deployed by
  running `npd update shogi` on the server by hand.
- The server must listen on `127.0.0.1` on the port in `$PORT`, and it runs
  under a systemd sandbox (`sandbox = true`) that hides everything outside its
  own directory. Keep it that way.
- It is Python 2.7. Tests: `python2.7 shogi_test.py` and
  `python2.7 shogi_server_test.py`.
- Please do not add a second deploy mechanism (Dockerfile, deploy script, CI
  deploy step) without asking.
