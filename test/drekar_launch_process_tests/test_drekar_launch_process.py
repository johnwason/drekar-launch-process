import subprocess
from pathlib import Path
import sys
import time
import drekar_launch_process
from multiprocessing import Process
import os
import threading

if sys.platform == "win32":
    import win32gui
    import win32con
    import win32process

def _send_shutdown_signal(proc):
    if sys.platform == "win32":
        # proc.send_signal(subprocess.signal.CTRL_C_EVENT)
        # Send WM_CLOSE to the window

        # Find all windows for process proc using pywin32
        

        windows = []
        print(proc.pid)
        # Use FindWindowsEx to find all WM_MESSAGE windows for the process
        hwnd_child_after = 0
        while True:
            hWnd = win32gui.FindWindowEx(win32con.HWND_MESSAGE, hwnd_child_after, None, None)
            if hWnd == 0:
                break
            pid = win32process.GetWindowThreadProcessId(hWnd)[1]
            if pid == proc.pid:
                windows.append(hWnd)
            hwnd_child_after = hWnd

        # Send WM_CLOSE to all windows
        print(windows)
        for hwnd in windows:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    
        # os.kill(proc.pid, subprocess.signal.CTRL_C_EVENT)
    else:
        os.kill(proc.pid, subprocess.signal.SIGINT)

def _wait_proc_exit(proc):
    try:
        proc.join(timeout=10)
    except subprocess.TimeoutExpired:
        assert False, "Process did not exit in time"
        

def _sub_launch_wait_exit():
    drekar_launch_process.wait_exit()

def _run_wait_exit_proc():

    proc = Process(target=_sub_launch_wait_exit)
    proc.start()
    return proc

def test_drekar_launch_process_wait_exit():
    
    launch_proc = _run_wait_exit_proc()

    # TODO: check servers status

    time.sleep(5)

    _send_shutdown_signal(launch_proc)
    print("Sent shutdown")
    _wait_proc_exit(launch_proc)
    print("Process exited")

def _sub_launch_callback_exit():
    evt = threading.Event()
    drekar_launch_process.wait_exit_callback(lambda: evt.set())
    evt.wait()

def _run_callback_exit_proc():

    proc = Process(target=_sub_launch_callback_exit)
    proc.start()
    return proc

def test_drekar_launch_process_callback_exit():
    
    launch_proc = _run_callback_exit_proc()

    # TODO: check servers status

    time.sleep(5)

    _send_shutdown_signal(launch_proc)
    print("Sent shutdown")
    _wait_proc_exit(launch_proc)
    print("Process exited")