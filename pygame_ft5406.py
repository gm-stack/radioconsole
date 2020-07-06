import os
import threading

import pygame

class ft5406Events(object):
    ts = None

    def __init__(self):
        try:
            import ft5406
            print("Using FT5406 driver, disabling SDL mouse support")
            os.environ['SDL_NOMOUSE'] = '1'
            os.environ['SDL_MOUSEDEV'] = '/dev/null'

            # pylint: disable=too-few-public-methods
            class TouchscreenDaemonRun(ft5406.Touchscreen):
                def run(self):
                    # pylint: disable=access-member-before-definition
                    # pylint: disable=attribute-defined-outside-init
                    if self._thread is not None:
                        return
                    self._thread = threading.Thread(target=self._run, daemon=True)
                    self._thread.start()

            self.ts = TouchscreenDaemonRun()
        except ImportError:
            print("Not using FT5406 driver, leaving SDL mouse support enabled")

    def start(self):
        if not self.ts:
            return

        pygame.mouse.set_visible(False)

        def touch_handler_press(_, touch):
            pygame.event.post(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                pos=(touch.x, touch.y),
                button=1
            ))
        def touch_handler_release(_, touch):
            pygame.event.post(pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                pos=(touch.x, touch.y),
                button=1
            ))
        def touch_handler_move(_, touch):
            pygame.event.post(pygame.event.Event(
                pygame.MOUSEMOTION,
                pos=(touch.x, touch.y),
                buttons=(1, 0, 0)
            ))

        for touch in self.ts.touches:
            touch.on_press = touch_handler_press
            touch.on_release = touch_handler_release
            touch.on_move = touch_handler_move

        self.ts.run()

    def stop(self):
        if self.ts:
            self.ts.stop()
