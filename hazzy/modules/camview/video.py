import cv2
import threading
import subprocess

# check if opencv3 is used, so we will have to change attribut naming
from pkg_resources import parse_version

from stream import HttpServer

OPCV3 = parse_version(cv2.__version__) >= parse_version('3')


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


class VideoDev:
    def __init__(self, videodevice=0, frame_width=640, frame_height=480):
        # set the selected camera as video device
        self.videodevice = videodevice

        # set the capture size
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame = None

        # set other default values or initialize them
        self.color = (0, 0, 255)
        self.radius = 150
        self.radius_difference = 10
        self.circles = 5
        self.autosize = False
        self.full_info = False
        self.linewidth = 1
        # self.frame = None
        self.img_gtk = None
        self.paused = False
        self.thrd = None
        self.initialized = False

        self.img_width = self.frame_width
        self.img_height = self.frame_height
        self.img_ratio = float(self.img_width) / float(self.img_height)

        self.colorseldlg = None
        self.old_frames = 0

        # set the correct camera as video device
        self.cam = cv2.VideoCapture(self.videodevice)

        # 0  = CAP_PROP_POS_MSEC        Current position of the video file in milliseconds.
        # 1  = CAP_PROP_POS_FRAMES      0-based index of the frame to be decoded/captured next.
        # 2  = CAP_PROP_POS_AVI_RATIO   Relative position of the video file
        # 3  = CAP_PROP_FRAME_WIDTH     Width of the frames in the video stream.
        # 4  = CAP_PROP_FRAME_HEIGHT    Height of the frames in the video stream.
        # 5  = CAP_PROP_FPS             Frame rate.
        # 6  = CAP_PROP_FOURCC          4-character code of codec.
        # 7  = CAP_PROP_FRAME_COUNT     Number of frames in the video file.
        # 8  = CAP_PROP_FORMAT          Format of the Mat objects returned by retrieve() .
        # 9  = CAP_PROP_MODE            Backend-specific value indicating the current capture mode.
        # 10 = CAP_PROP_BRIGHTNESS      Brightness of the image (only for cameras).
        # 11 = CAP_PROP_CONTRAST        Contrast of the image (only for cameras).
        # 12 = CAP_PROP_SATURATION      Saturation of the image (only for cameras).
        # 13 = CAP_PROP_HUE             Hue of the image (only for cameras).
        # 14 = CAP_PROP_GAIN            Gain of the image (only for cameras).
        # 15 = CAP_PROP_EXPOSURE        Exposure (only for cameras).
        # 16 = CAP_PROP_CONVERT_RGB     Boolean flags indicating whether images should be converted to RGB.
        # 17 = CAP_PROP_WHITE_BALANCE   Currently unsupported
        # 18 = CAP_PROP_RECTIFICATION   Rectification flag for stereo cameras
        #                               (note: only supported by DC1394 v 2.x backend currently)

        if OPCV3:
            self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        else:
            self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.frame_height)

        self.cam_properties = CamProperties()
        self.cam_properties.get_devices()
        # self.cam_properties.get_resolution(self.videodevice)

    def run(self):
        cv2.namedWindow('RGB')
        running = True
        try:
            while running:
                result, frame = self.cam.read()
                if result:
                    cv2.imshow('RGB', frame)
                    cv2.waitKey(60)
                    self.frame = frame
        except Exception as e:
            print(e)

    def get_jpeg_frame(self):
        jpeg_data = cv2.imencode('.jpg', self.frame)[1].tostring()
        return jpeg_data

class CamProperties():
    def __init__(self):
        # get all availible devices
        self.devices = []
        self.resolutions = []

    def get_devices(self):
        result = subprocess.Popen(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE).communicate()[0]
        result = str(result)
        infos = result.split('\n')
        for item, info in enumerate(infos):
            if info == "":
                continue
            info = info.strip(' \t\n\r')
            if "/dev/video" in info:
                device = str(info + " = " + infos[item - 1])
                self.devices.append(device)

        return self.devices

    #    def get_resolution(self, videodevice=0):
    #        self.resolutions = []
    #
    #        # get all availible resolutions
    #        result = subprocess.Popen(['v4l2-ctl', '-d' + str(videodevice), '--list-formats-ext'], stdout=subprocess.PIPE)#.communicate()[0]
    #        line = ""
    #        res =""
    #        rate = ""
    #        for letter in result.stdout.read():
    #            if letter == "\n":
    #                #print line.strip(" \t\n\r")
    #                info = line.split(":")
    #                if "Size" in info[0]:
    #                    res = info[1].split()
    #                    #width,height = res[1].split("x")
    ##                if "Interval" in info[0]:
    ##                    rate = info[1].split("(")
    ##                    rate = rate[1]
    ##                    rate = rate.strip(" fps)")
    #                    self.resolutions.append(str(res[1]))
    #                line = ""
    #            else:
    #                line += letter
    #
    ##        # check for doble entries, not order preserving
    #        checked = []
    #        for element in self.resolutions:
    #            if element not in checked:
    #                checked.append(element)
    #
    #        self.resolutions = sorted(checked)
    #        return self.resolutions

    def set_powerline_frequeny(self, videodevice, value):
        command = 'v4l2-ctl -d' + str(videodevice) + ' --set-ctrl=power_line_frequency=' + str(value)
        self._run_command(command)

    def open_settings(self, videodevice=0):
        command = "v4l2ucp /dev/video" + str(videodevice)
        self._run_command(command)

    def _run_command(self, command):
        if command:
            result = subprocess.Popen(command, stderr=None, shell=True)


def main():

    video_device = VideoDev(videodevice=0, frame_width=640, frame_height=480)
    video_server = HttpServer("test server", '0.0.0.0', 8080, video_device.get_jpeg_frame)

    video_thread = ControlThread(1, "VideoThread", 1, video_device.run)
    stream_thread = ControlThread(1, "StreamThread", 1, video_server.run)

    video_thread.start()
    stream_thread.start()


if __name__ == '__main__':
    main()
