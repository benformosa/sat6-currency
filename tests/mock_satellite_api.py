#!/usr/bin/env python2
"""
Mocks the Satellite 6 API
"""

import SimpleHTTPServer
import SocketServer
import os
import socket
import threading


class MockSatelliteAPIRequestHandler(
        SimpleHTTPServer.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override log_message to avoid logging to console
        pass


def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


def serve_api(hostname='localhost', port=8000):
    FILE_PATH = 'www'
    directory = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        FILE_PATH
    )
    os.chdir(directory)
    mock_server = SocketServer.TCPServer(
        (hostname, port),
        MockSatelliteAPIRequestHandler
    )
    mock_server_thread = threading.Thread(
        target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()
