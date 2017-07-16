from picamera.array import PiRGBArray
import time 
import io 
import threading 
import picamera
import cv2
import numpy as np
 
class Camera(object):
    thread = None # background thread that reads frames from camera
    frame = None # current frame is stored here by background thread
    last_access = 0 # time of last client access to the camera
    lower_array_mask = np.array([0,0,0])
    upper_array_mask = np.array([179, 255,255])
    rowlower = 220
    rowupper = 260
    collower =  300
    colupper = 340
    mse = 0
    
    def initialize(self):
        if Camera.thread is None:
            # start background frame thread
            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()
            # wait until frames start to be available            
            while self.frame is None:
                time.sleep(0)
    
    def get_frame(self):
        Camera.last_access = time.time()
        self.initialize()
        return self.frame

    @classmethod
    def setmaskyellow(cls):
        print("Setting mask yellow")
        cls.lower_array_mask = np.array([13,0,0])
        cls.upper_array_mask = np.array([46,255,255])
        
        
    @classmethod
    def setmaskgreen(cls):
        print("Setting mask blue")
        cls.lower_array_mask = np.array([61,0,0])
        cls.upper_array_mask = np.array([98,255,255])
        
    @classmethod
    def removemask(cls):
        print("Setting mask")
        cls.lower_array_mask = np.array([0,0,0])
        cls.upper_array_mask = np.array([179,255,255])
        
    @classmethod
    def _thread(cls):
        with picamera.PiCamera() as camera:
            # camera setup
            camera.resolution = (640, 480)
            
            # let camera warm up            
            time.sleep(2)
            stream = io.BytesIO()
            camera.framerate=40
            cls.setmaskyellow()
            print ('framerate ',camera.framerate)
            rawCapture = PiRGBArray(camera, size=(640, 480))            
            for frame in camera.capture_continuous(rawCapture, 'bgr',
                                                 use_video_port=True):
                # store frame
                image = frame.array
                # Convert BGR to HSV
                hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                
                hsv[220, 300:340,0]=4
                hsv[260, 300:340,0]=4
                hsv[220:260, 300,0]=4
                hsv[220:260, 340,0]=4
                
                hsv[220, 300:340,1]=240
                hsv[260, 300:340,1]=240
                hsv[220:260, 300,1]=240
                hsv[220:260, 340,1]=240

                hsv[220, 300:340,2]=240
                hsv[260, 300:340,2]=240
                hsv[220:260, 300,2]=240
                hsv[220:260, 340,2]=240

                section = np.array(hsv[cls.rowlower:cls.rowupper, cls.collower:cls.colupper, 0:3])
                mask = cv2.inRange(section, cls.lower_array_mask, cls.upper_array_mask)
                
                # Bitwise-AND mask and original image
                res = cv2.bitwise_and(section, section, mask= mask)
                
                # Detection
                cls.mse = (res ** 2).mean(axis=None)
                if cls.mse > 0:
                    print ("Bee detected")
                rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                r, j = cv2.imencode('.jpg', rgb)
                cls.frame = bytearray(j)
                rawCapture.truncate(0)
                
                # if there hasn't been any clients asking for frames in 
                # the last 10 seconds stop the thread
                if time.time() - cls.last_access > 10:
                    break
        cls.thread = None
