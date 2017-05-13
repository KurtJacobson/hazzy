
import threading
import time

from video import VideoDev
from stream import HttpServer
from camview import CamViewWindow


class ControlThread(threading.Thread):
    def __init__(self, thread_id, name, counter, callback, args=None):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.counter = counter
        self.callback = callback
        self.args = args

    def run(self):
        print("Starting {0}".format(self.name))

        if self.args is None:
            self.callback()
        else:
            self.callback(self.args)

        print("Exiting {0}".format(self.name))


def main():

    video_device = VideoDev(videodevice=0, frame_width=640, frame_height=480)
    video_streamer = HttpServer("HAZZY stream", '0.0.0.0', 8080, video_device.get_jpeg_frame)
    video_gui = CamViewWindow(video_device)

    stream_thread = ControlThread(1, "StreamThread", 1, video_streamer.run)
    gui_thread = ControlThread(1, "GuiThread", 1, video_gui.run)

    stream_thread.start()
    gui_thread.start()

if __name__ == '__main__':
    main()
