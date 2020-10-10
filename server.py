#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import time
import random
import signal


class TicTimer():
    """
        A simple timer
    """
    start_time = 0
    tic_time = 0
    completed = False

    def __init__(self, tic=0):
        self.tic_time = tic

    def start(self, tic):
        if tic != 0:
            self.tic = tic
            self.start_time = time.perf_counter()

    def is_finished(self):
        if((time.perf_counter() - self.start_time) >= self.tic):
            return True
        return False


class GetData():
    """
        Foo function returning random data for the server
        Replace it with a function that grabs actual data
    """
    def __init__(self):
        self.data = 0

    def get_value(self):
        self.data = str(random.randint(0, 1023)).encode("utf-8")
        return self.data


# ------------------------------------------
class ThreadForClient(threading.Thread):
    """ Thread for managing a client """
    data = GetData()

    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn

    def run(self):
        while True:
            try:
                value = self.conn.recv(1024)
                value = value.decode("utf-8")
                if value == "close":
                    break
                elif value == "send":
                    self.conn.sendall(self.data.get_value())
                else:
                    print(">>> Bad command!")
            except (ConnectionResetError, BrokenPipeError) as e:
                print(">>> ", e, " exiting...")
                break
        self.conn.close()
# ------------------------------------------


host, port = ('localhost', 5500)

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((host, port))
print(">>> [STARTING] server is starting...")

try:
    while True:
        socket.listen(5)
        print(f">>> [LISTENING] server is listening on {host} (CTL+C to exit)")
        conn, address = socket.accept()
        print(f">>> [CONNECTING] new client from {address}")
        my_thread = ThreadForClient(conn)
        my_thread.start()
        print(">>> Number of connected clients: " +
            str(threading.active_count() - 1) + "\n")
except KeyboardInterrupt:
    print(">>> Keyboard interrupt caught!")
    socket.close()
finally:
    print(">>> [STOPING] server stoping...")
