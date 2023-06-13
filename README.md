# Drekar Launch Process

This library contains client utility functions for processes launched using `drekar-launch`, although they may also be used without `drekar-launch`. Currently this package provides a reliable way for processes to receive shutdown signals from a process manager or the user using `ctrl-c`.

See `drekar-launch`: https://github.com/johnwason/drekar-launch

## Installation

```
python -m pip install --user drekar-launch-process
```

On Ubuntu, it may be necessary to replace `python` with `python3`.

## Usage

The module contains three functions:

* `drekar_launch_process.wait_exit()` - Block and wait for exit
* `drekar_launch_process.wait_exit_callback(callback)` - Return immediately and call `callback()` when shutdown signal received
* `drekar_launch_process.wait_exit_stop_loop(loop)` - Call to stop an `asyncio` loop when shutdown signal received

## Example

A simple example of running a Python http server in a background thread, using the blocking `wait_exit()`.

```python
import drekar_launch_process
import threading
from http import server as http_server

server=http_server.ThreadingHTTPServer(('',8085), 
        http_server.SimpleHTTPRequestHandler)
def run_server():
    server.serve_forever()

th = threading.Thread(target=run_server)
th.daemon = True
th.start()

drekar_launch_process.wait_exit()
```

This example uses the callback version to quit the http server:

```python
import drekar_launch_process
import threading
from http import server as http_server

server=http_server.ThreadingHTTPServer(('',8085), 
        http_server.SimpleHTTPRequestHandler)

def shutdown_server():
    server.shutdown()

drekar_launch_process.wait_exit_callback(shutdown_server)

server.serve_forever()
```

## Shutdown Signal Explanation

Reliably sending a shutdown/quit command to a process in a cross-platform manner is surprisingly difficult. On POSIX based systems like Linux and Mac OS X, signals such as `SIGINT` or `SIGTERM` are typically sent. (Ctrl-C sends `SIGINT`). These signals can be caught by the process, and used to gracefully shut down. `SIGKILL` is used to immediately terminate the process.

On Windows, it is significantly more difficult. Windows typically uses "Window Message Queues" to communicate with processes. Even processes like services that do not have a visible window often have a hidden window so messages can be received from the operating system. There is some functionality for sending console signals, but these are not reliable for all cases. Windows also has the concept of `Job Objects` that can be used to group different processes together. The combination of job objects and windows messages provide a reliable way to send and receive graceful shutdown signals.

The `wait_for_exit*` commands either way for Signals on POSIX, or windows close messages and console events on Windows.


