# !/usr/bin/env python

import os
import re
import time
import cgi

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


class HttpServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            self.path = re.sub('[^.a-zA-Z0-9]', "", str(self.path))
            if self.path == "" or self.path is None or self.path[:1] == ".":
                return

            if self.path.endswith("index.html"):
                file_path = os.path.join(os.curdir, self.path)
                with open(file_path) as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(f.read())
                return

            if self.path.endswith("stream.mjpeg"):
                self.send_response(200)
                self.wfile.write("Content-Type: multipart/x-mixed-replace; boundary=--aaboundary")
                self.wfile.write("\r\n\r\n")

                running = True
                while running:

                        img = self.server.handler()
                        self.wfile.write("--aaboundary\r\n")
                        self.wfile.write("Content-Type: image/jpeg\r\n")
                        self.wfile.write("Content-length: {0}\r\n\r\n".format(len(img)))
                        self.wfile.write(img)
                        self.wfile.write("\r\n\r\n\r\n")
                        time.sleep(0.1)

                return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

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

        except Exception as e:
            print(e)


class MyHTTPServer(HTTPServer):
    """this class is necessary to allow passing custom request handler into
       the RequestHandlerClass"""

    def __init__(self, server_address, RequestHandlerClass, handler):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.handler = handler


class HttpServer:
    def __init__(self, name, host, port, handler):
        self.name = name
        self.host = host
        self.port = port
        self.handler = handler
        self.server = None

    def run(self):
        self.server = MyHTTPServer((self.host, self.port), HttpServerHandler,
                                   self.handler)
        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()

