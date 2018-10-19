#!/usr/bin/env python2
"""
Mocks the Satellite 6 API
"""

import BaseHTTPServer
import SocketServer
import os
import threading
import socket

class MockSatelliteAPIRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    FILE_PATH = 'api'

    def do_get(self, content):
        self.send_response(200, self.responses[200])
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(content)

    def do_notFound(self):
        self.send_response(404, self.responses[404])
        self.end_headers()

    def do_get_file(self, filename):
        directory = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            self.FILE_PATH
        )
        with open(os.path.join(directory, filename), 'r') as f:
            self.do_get('\n'.join(f.readlines()))
        pass

    def do_GET(self):
        if self.path == '/foo':
            self.do_get(
                '[\n'
                '  {\n'
                '    "foo": "bar"\n'
                '  }\n'
                ']'
            )
        elif self.path == '/baz':
            self.do_get_file('baz.json')
        else:
            self.do_notFound()


def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port

def serve_api(hostname='localhost', port=8000):
    mock_server = SocketServer.TCPServer(
        (hostname, port),
        MockSatelliteAPIRequestHandler
    )
    mock_server_thread = threading.Thread(
        target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()
