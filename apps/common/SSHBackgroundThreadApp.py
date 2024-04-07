import math
import html
import threading
import time
import socket
import select
import ctypes

import pygame
import pygame_gui
import paramiko

import crash_handler
from AppManager.app import app
from config_reader import cfg

class SSHBackgroundThreadApp(app):

    def __init__(self, bounds, config, display, name):
        self.backend_threads = {}
        super().__init__(bounds, config, display, name)

    def run_ssh_func_persistent(self, host, thread_name, func, *args, **kwargs):
        # run a function persistently in a SSH session which shouldn't exit

        # use dirty hack to stop previous thread if one exists with same id
        if thread_name in self.backend_threads:
            print(f"stopping backend thread {thread_name}")
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.backend_threads[thread_name].ident), 
                ctypes.py_object(SystemExit)
            )
        
        # define a function to run the thread
        # wrap in crash_handler.monitor_thread to
        # bring everything down if it exits uncommanded
        def _run_command_in_loop(self):
            self._command_backend_thread(host, func, False, *args, **kwargs)

        # start the thread
        self.backend_threads[thread_name] = threading.Thread(
            target=crash_handler.monitor_thread(_run_command_in_loop),
            args=[self],
            daemon=True
        )
        self.backend_threads[thread_name].start()
    
    def run_ssh_func_single(self, host, func, *args, **kwargs):
        # run a function once in a SSH session which should run once an dexit

        # monitors for an exception and raises it on main thread
        # but does not bring everything down if thread exits
        def _run_single_func(self):
            self._command_backend_thread(host, func, onceonly=True, *args, **kwargs)

        th = threading.Thread(
            target=crash_handler.monitor_thread_exception(_run_single_func),
            args=[self],
            daemon=True
        )
        th.start()

    def run_command(self, ts, cmd):
        ch = ts.open_session()
        ch.set_combine_stderr(True)
        stdout = ch.makefile('rb', -1)
        ch.exec_command(cmd)
        res = bytes()
        while True:
            out = stdout.channel.recv(1024)
            if not out:
                break
            else:
                res += out
        return res.decode('UTF-8').rstrip(' \t\r\n\x00')

    def _command_backend_thread(self, host, func, onceonly, *args, **kwargs):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        while True:
            try:
                ssh.connect(
                    host.host,
                    username=host.username,
                    port=host.port,
                    timeout=5,
                    banner_timeout=10
                )
                ts = ssh.get_transport()

                while True:
                    func(ts, *args, **kwargs)
                    if onceonly:
                        break
                    time.sleep(self.config.retry_seconds)

            except OSError as e:
                self.error_message(f"Connection error: {str(e)}")
                self.data_updated = True

            except paramiko.SSHException as e:
                self.error_message(f"SSH error: {str(e)}")
                self.data_updated = True
            
            if onceonly:
                break
            else:
                time.sleep(1)


    def update(self, dt):
        return super().update(dt)

    def draw(self, screen):
        return super().draw(screen)

    def process_events(self, e):
        super().process_events(e)