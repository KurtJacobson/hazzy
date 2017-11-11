#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   TBA

import os
import re
import time
import cgi
import socket

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn


class HttpServerHandler(BaseHTTPRequestHandler):

    def do_PUT(self):
        print "----- SOMETHING WAS PUT!! ------"
        print self.headers
        length = int(self.headers['Content-Length'])
        content = self.rfile.read(length)
        self.send_response(200)

        print content

    def do_GET(self):
        self.path = re.sub('[^.a-zA-Z0-9]', "", str(self.path))

        if self.path == "" or self.path.endswith("index.html"):
            self.send_response(200)
            file_path = os.path.join(os.curdir, self.path)
            print(file_path)
            with open(file_path) as f:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
            return
        return

    def do_POST(self):
        try:
            query = None

            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query = cgi.parse_multipart(self.rfile, pdict)

            self.send_response(301)

            self.end_headers()
            upfilecontent = query.get('upfile')
            print("filecontent {0}".format(upfilecontent[0]))
            value = int(upfilecontent[0])
            camera_quality = max(2, min(99, value))
            self.wfile.write("<HTML>POST OK. Camera Set to<BR><BR>")
            self.wfile.write(str(camera_quality))

        except IOError:
            return

    def finish(self):
        try:
            BaseHTTPRequestHandler.finish(self)
        except socket.error:
            pass

    def handle(self):
        try:
            BaseHTTPRequestHandler.handle(self)
        except socket.error:
            pass


class StreamHTTPServer(ThreadingMixIn, HTTPServer):
    """this class is necessary to allow passing custom request handler into
       the RequestHandlerClass"""

    def __init__(self, server_address, request_handler_class):
        HTTPServer.__init__(self, server_address, request_handler_class)
        self.stop = False

    def serve_forever(self, poll_interval=0.5):
        while not self.stop:
            self.handle_request()
        self.stop = False

    def serve_stop(self):
        self.server_close()
        self.stop = True


class VideoHttpServer:
    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port
        self.server = None

    def start(self):
        print("starting HTTP server")
        self.server = StreamHTTPServer((self.host, self.port), HttpServerHandler)
        self.server.serve_forever()

    def stop(self):
        print("stoping HTTP server")
        self.server.serve_stop()
