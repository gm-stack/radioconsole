import traceback
import threading
import sys

import pygame

def crash(screen, safe_exit):
    screen.fill((0,0,0))

    font = pygame.font.Font(None, 24)
    header = "*"*80
    thread_name = threading.currentThread().getName()
    stacktrace = traceback.format_exc()
    msg = f"Thread {thread_name} crashed: \n{header}\n{stacktrace}\n{header}\n>>> Click or press any key to exit... <<<"
    print(msg, file=sys.stderr)
    lineheight = font.get_linesize()
    for i, line in enumerate(msg.splitlines()):
        text = font.render(line, True, (255,0,0))
        screen.blit(text, (0,i*lineheight))

    pygame.display.update()

    while True:
        for e in pygame.event.get():
            if e.type in (pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                safe_exit()