#!/usr/bin/env python3
import cv2, os, time, queue, base64, threading, logging
import numpy as np

class extract_Thread(threading.Thread):
    def __init__(self, fileName, extract_queue):
        threading.Thread.__init__(self)
        self.file = fileName
        self.Q = extract_queue
    
    def run(self):
        print("Extract_Thread")
        # Initialize frame count 
        count = 0
        # open video file
        vidcap = cv2.VideoCapture(self.file)
        # read first image
        success,image = vidcap.read()
        print("Reading frame {} {} ".format(count, success))
        while success:
            # get a jpg encoded frame
            success, jpgImage = cv2.imencode('.jpg', image)
            #encode the frame as base 64 to make debugging easier
            jpgAsText = base64.b64encode(jpgImage)
            # add the frame to the buffer
            self.Q.put(jpgAsText)
            success,image = vidcap.read()
            print('Reading frame {} {}'.format(count, success))
            count += 1

        print("Frame extraction complete")

class convert_Thread(threading.Thread):
    def __init__(self, extract_queue, display_queue):
        threading.Thread.__init__(self)
        self.extract_Q = extract_queue
        self.display_Q = display_queue

    def run(self):
        print("Convert_Thread")
        # initialize frame count
        count = 0
        # get the next frame file name
        inFrame = self.extract_Q.get()
        # load the next file
        inputFrame = cv2.imread(inFrame, cv2.IMREAD_COLOR)
        while inputFrame is not None:
            print("Converting frame {}".format(count))
            # convert the image to grayscale
            grayscaleFrame = cv2.cvtColor(inputFrame, cv2.COLOR_BGR2GRAY)
            self.display_Q.put(grayscaleFrame)
            count += 1
            # load the next frame
            inputFrame = cv2.imread(inFrame, cv2.IMREAD_COLOR)

class display_Thread(threading.Thread):
    def __init__(self, display_queue):
        threading.Thread.__init__(self)
        self.Q = display_queue
    
    def run(self):
        print("Display_Thread")
        # initialize frame count
        count = 0
        # go through each frame in the buffer until the buffer is empty
        while not self.Q.empty():
            # get the next frame
            frameAsText = self.Q.get()
            # decode the frame 
            jpgRawImage = base64.b64decode(frameAsText)
            # convert the raw frame to a numpy array
            jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)
            # get a jpg encoded frame
            img = cv2.imdecode( jpgImage ,cv2.IMREAD_UNCHANGED)
            print("Displaying frame {}".format(count))        
            # display the image in a window called "video" and wait 42ms
            # before displaying the next frame
            cv2.imshow("Video", img)
            if cv2.waitKey(42) and 0xFF == ord("q"):
                break
            count += 1

        print("Finished displaying all frames")
        # cleanup the windows
        cv2.destroyAllWindows()

class my_Queue(queue.Queue):
    def __init__(self):
        self.sem_full = threading.Semaphore(0)
        self.sem_empty = threading.Semaphore(10)
        self.q_lock = threading.Lock()
    
    def put(self, v):
        print("Putting in QUEUE")
        # Acquire rights to 1 empty queue
        self.sem_empty.acquire()
        # Insert into queue
        self.q_lock.acquire()
        self.put(v)
        self.q_lock.release()
        # Release rights to 1 full queue
        self.sem_full.release()

    def get(self):
        # Acquire rights to 1 full queue
        self.sem_full.acquire()
        # Delete from queue
        self.q_lock.acquire()
        val = self.get()
        self.q_lock.release()
        # Release rights to 1 empty queue
        self.sem_empty.release()
        return val

file = "clip.mp4"
extract_queue = my_Queue()
display_queue = my_Queue()

extract_Thread(file, extract_queue).start()
convert_Thread(extract_queue, display_queue).start()
display_Thread(display_queue).start()
