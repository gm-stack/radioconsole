import traceback
import threading
import sys
import ctypes
import time
import inspect

import pygame

screen = None
safe_exit = None

def register(scr, ex):
    global screen, safe_exit
    screen = scr
    safe_exit = ex

def monitor_thread(func):
    def wrapper(self):
        funcdesc = f"Thread exited: \n  File \"{inspect.getfile(func)}\", line {func.__code__.co_firstlineno}, in {func.__name__}"
        try:
            func(self)
            crash(None, is_thread=True, threadmsg=funcdesc)
        except Exception as e:
            crash(e, is_thread=True)
    return wrapper

class SubThreadExitedException(RuntimeError):
    pass

do_exit = False
def crash(exc, is_thread=False, threadmsg=None):
    global do_exit

    if isinstance(exc, SubThreadExitedException):
        while True:
            time.sleep(0.1)
            if do_exit:
                safe_exit()
                while True:
                    time.sleep(0.1)

    if is_thread:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            threading.main_thread().ident, 
            ctypes.py_object(SubThreadExitedException)
        )

    screen.fill((0,0,0))

    font = pygame.font.Font(None, 24)
    header = "*"*80
    thread_name = threading.currentThread().getName()
    
    if threadmsg:
        msg = f"Error: Thread \'{thread_name}\' \n"
        msg += f"{header}\n{threadmsg}\n"
    else:
        msg = f"Thread {thread_name} crashed: \n"
        msg += f"{header}\n{traceback.format_exc()}\n"
    msg += f"{header}\n>>> Click/tap or press any key to exit... <<<"
    
    print(msg, file=sys.stderr)
    lineheight = font.get_linesize()
    for i, line in enumerate(msg.splitlines()):
        text = font.render(line, True, (255,0,0))
        screen.blit(text, (0,i*lineheight))

    pygame.display.update()

    while True:
        for e in pygame.event.get():
            if e.type in (pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                do_exit = True
                safe_exit()