import traceback
import threading
import sys
import ctypes
import inspect

import pygame

screen = None
safe_exit = None

def register(scr, ex):
    global screen, safe_exit
    screen = scr
    safe_exit = ex

# pylint: disable=broad-except
def monitor_thread(func):
    def wrapper(self):
        funcdesc = f"Thread exited: \n  File \"{inspect.getfile(func)}\"," \
            f" line {func.__code__.co_firstlineno}, in {func.__name__}"
        try:
            func(self)
            crash(None, is_thread=True, threadmsg=funcdesc)
        except Exception as e:
            crash(e, is_thread=True)
    return wrapper

def monitor_thread_exception(func):
    def wrapper(self):
        try:
            func(self)
        except Exception as e:
            crash(e, is_thread=True)
    return wrapper

class SubThreadExitedException(RuntimeError):
    pass

do_exit = False
subthread_tb = None
subthread_name = None
subthread_msg = None
def crash(exc, is_thread=False, threadmsg=None):
    global subthread_tb, subthread_name, subthread_msg

    if is_thread:
        subthread_tb = traceback.format_exc()
        subthread_name = threading.currentThread().getName()
        subthread_msg = threadmsg
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(threading.main_thread().ident),
            ctypes.py_object(SubThreadExitedException)
        )
        return

    if isinstance(exc, SubThreadExitedException):
        tb = subthread_tb
        thread_name = subthread_name
        threadmsg = subthread_msg
    else:
        tb = traceback.format_exc()
        thread_name = threading.currentThread().getName()

    screen.fill((0, 0, 0))

    font = pygame.font.Font("ttf/FiraCode-Regular.ttf", 14)
    header = "*"*80

    if threadmsg:
        msg = f"Error: Thread \'{thread_name}\' \n"
        msg += f"{header}\n{threadmsg}\n"
    else:
        msg = f"Thread {thread_name} crashed: \n"
        msg += f"{header}\n{tb}\n"
    msg += f"{header}\n>>> Click/tap or press any key to exit... <<<"

    print(msg, file=sys.stderr)
    lineheight = font.get_linesize()
    for i, line in enumerate(msg.splitlines()):
        text = font.render(line, True, (255, 0, 0))
        screen.blit(text, (8, 8+(i*lineheight)))

    pygame.display.update()

    while True:
        for e in pygame.event.get():
            if e.type in (pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                safe_exit()
