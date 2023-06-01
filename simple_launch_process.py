import sys
import atexit
import traceback
import threading

def wait_exit():

    #Wait for shutdown signal if running in service mode
    #print("Press Ctrl-C to quit...")
    if sys.platform == "win32":
        _win32_wait_exit()
    else:
        import signal
        signal.sigwait([signal.SIGTERM,signal.SIGINT])
    
def wait_exit_callback(callback):
    if sys.platform != "win32":
        evt = threading.Event()
    def t_func():
        try:
            
            #Wait for shutdown signal if running in service mode
            #print("Press Ctrl-C to quit...")
            if sys.platform == "win32":
                hwnd = _win32_create_message_hwnd()
                def _stop_loop():
                    _win32_post_hwnd_close(hwnd)
                try:
                    atexit.register(_stop_loop)
                    _win32_wait_message_hwnd(hwnd)
                finally:
                    try:
                        atexit.unregister(_stop_loop)
                    except Exception: pass
            else:
                evt.wait()
        except Exception:
            traceback.print_exc()
        callback()
    
    t = threading.Thread(target=t_func)
    t.setDaemon(True)
    t.start()

    # Block signals in main thread
    if sys.platform != "win32":
        import signal
        # Send signals to noop handler in main thread
        def noop_handler(signum, frame):
            evt.set()
        signal.signal(signal.SIGTERM, noop_handler)
        signal.signal(signal.SIGINT, noop_handler)

def wait_exit_stop_loop(loop): 
    wait_exit_callback(lambda: loop.call_soon_threadsafe(loop.stop))

if sys.platform == "win32":
    # https://gist.github.com/mouseroot/6128651
    import ctypes
    import ctypes.wintypes

    WNDPROCTYPE = ctypes.WINFUNCTYPE(ctypes.wintypes.LPARAM, ctypes.wintypes.HWND, ctypes.wintypes.UINT, 
                                     ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
    CtrlCHandlerRoutine = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.DWORD)
    WM_DESTROY = 2
    WM_CLOSE = 16
    HWND_MESSAGE = ctypes.wintypes.HWND(-3)

    class WNDCLASSEX(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint),
                    ("style", ctypes.c_uint),
                    ("lpfnWndProc", WNDPROCTYPE),
                    ("cbClsExtra", ctypes.c_int),
                    ("cbWndExtra", ctypes.c_int),
                    ("hInstance", ctypes.wintypes.HANDLE),
                    ("hIcon", ctypes.wintypes.HANDLE),
                    ("hCursor", ctypes.wintypes.HANDLE),
                    ("hBrush", ctypes.wintypes.HANDLE),
                    ("lpszMenuName", ctypes.wintypes.LPCWSTR),
                    ("lpszClassName", ctypes.wintypes.LPCWSTR),
                    ("hIconSm", ctypes.wintypes.HANDLE)]

    def _PyWndProcedure(hWnd, Msg, wParam, lParam):
        if Msg == WM_DESTROY:
            ctypes.windll.user32.PostQuitMessage(0)
        elif Msg == WM_CLOSE:
            ctypes.windll.user32.DestroyWindow(hWnd)
        else:
            return ctypes.windll.user32.DefWindowProcW(hWnd, Msg, ctypes.wintypes.WPARAM(wParam),
                                                                ctypes.wintypes.LPARAM(lParam))
        return 0

    WndProc = WNDPROCTYPE(_PyWndProcedure)

    def _ctrl_c_empty_handler(code):
        return True

    _ctrl_c_empty_handler_ptr = CtrlCHandlerRoutine(_ctrl_c_empty_handler)

    def _win32_wait_exit():
        hwnd = _win32_create_message_hwnd()
        _win32_wait_message_hwnd(hwnd)

    def _win32_create_message_hwnd():
        
        hInst = ctypes.windll.kernel32.GetModuleHandleW(0)
        wclassName = 'pyri_message_window'
        wname = 'pyri_hidden_window'
        
        wndClass = WNDCLASSEX()
        wndClass.cbSize = ctypes.sizeof(WNDCLASSEX)
        wndClass.lpfnWndProc = WndProc
        wndClass.lpszClassName = wclassName
        wndClass.hInstance = hInst

        regRes = ctypes.windll.user32.RegisterClassExW(ctypes.byref(wndClass))
        assert regRes, "Could not create win32 message wnd class"

        hWnd = ctypes.windll.user32.CreateWindowExW( 0, wclassName, wname, 0, 0, 0, 0, 0, HWND_MESSAGE, None, None, None )
        assert hWnd, "Could not create win32 message hwnd"
        return hWnd

    def _win32_wait_message_hwnd(hWnd):


        # Install a ctrl-c handler to send WM_QUIT

        def ctrl_c_handler(code):
            _win32_post_hwnd_close(hWnd)
            return True

        ctrl_c_handler_ptr = CtrlCHandlerRoutine(ctrl_c_handler)
        
        ctypes.windll.kernel32.SetConsoleCtrlHandler(ctrl_c_handler_ptr, 1)
        
        msg = ctypes.wintypes.MSG()
        lpmsg = ctypes.pointer(msg)
        while ctypes.windll.user32.GetMessageA(lpmsg, 0, 0, 0) != 0:
            ctypes.windll.user32.TranslateMessage(lpmsg)
            ctypes.windll.user32.DispatchMessageA(lpmsg)

        ctypes.windll.kernel32.SetConsoleCtrlHandler(_ctrl_c_empty_handler_ptr, 1)

    def _win32_post_hwnd_close(hWnd):
        ctypes.windll.user32.PostMessageW(hWnd,WM_CLOSE,0,0)

__all__ = ["wait_exit","wait_exit_callback","wait_exit_stop_loop"]