# edited by Norbert (mjpeg part) from a file from Copyright Jon Berg , turtlemeat.com,
# MJPEG Server for the webcam

import string, cgi, time
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import cv
import re

capture = cv.CaptureFromCAM(-1)
img = cv.QueryFrame(capture)
cameraQuality = 75


class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global cameraQuality
        try:
            self.path = re.sub('[^.a-zA-Z0-9]', "", str(self.path))
            if self.path == "" or self.path is None or self.path[:1] == ".":
                return

            if self.path.endswith(".html"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return

            if self.path.endswith(".mjpeg"):
                self.send_response(200)
                self.wfile.write("Content-Type: multipart/x-mixed-replace; boundary=--aaboundary")
                self.wfile.write("\r\n\r\n")
                while 1:
                    img = cv.QueryFrame(capture)
                    cv2mat = cv.EncodeImage(".jpeg", img, (cv.CV_IMWRITE_JPEG_QUALITY, cameraQuality))
                    JpegData = cv2mat.tostring()
                    self.wfile.write("--aaboundary\r\n")
                    self.wfile.write("Content-Type: image/jpeg\r\n")
                    self.wfile.write("Content-length: " + str(len(JpegData)) + "\r\n\r\n")
                    self.wfile.write(JpegData)
                    self.wfile.write("\r\n\r\n\r\n")
                    time.sleep(0.05)
                return

            if self.path.endswith(".jpeg"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        global rootnode, cameraQuality
        try:
            query = None

            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query = cgi.parse_multipart(self.rfile, pdict)
            self.send_response(301)

            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            value = int(upfilecontent[0])
            cameraQuality = max(2, min(99, value))
            self.wfile.write("<HTML>POST OK. Camera Set to<BR><BR>")
            self.wfile.write(str(cameraQuality))

        except Exception as e:
            print(e)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    # class ThreadedHTTPServer(HTTPServer):
    """Handle requests in a separate thread."""


def main():
    server = None
    try:
        server = ThreadedHTTPServer(('0.0.0.0', 8080), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()


if __name__ == '__main__':
    main()
