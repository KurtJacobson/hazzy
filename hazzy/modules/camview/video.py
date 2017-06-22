import cv2
import subprocess

# check if opencv3 is used, so we will have to change attribut naming
from pkg_resources import parse_version

OPCV3 = parse_version(cv2.__version__) >= parse_version('3')


class VideoDev:
    def __init__(self, videodevice=0, frame_width=640, frame_height=480):
        # set the selected camera as video device
        self.videodevice = videodevice

        # set the correct camera as video device

        self.cam = cv2.VideoCapture(self.videodevice)

        # set the capture size
        self.frame_width = frame_width
        self.frame_height = frame_height

        self.frame = self.cam.read()[1]

        self.jpeg_frame = cv2.imencode('.jpg', self.frame)[1].tostring()

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
            self.cam.set(cv2.CAP_PROP_FPS, 30)
        else:
            self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.frame_height)

    def run(self):
        running = True
        while running:

            success, frame = self.cam.read()
            if success:
                self.frame = frame

            cv2.waitKey(60)

    def get_jpeg_frame(self):
        self.jpeg_frame = cv2.imencode('.jpg', self.frame)[1].tostring()
        return self.jpeg_frame
