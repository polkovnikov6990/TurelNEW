import cv2
import threading
import time
from queue import Queue

class VideoStreamThread(threading.Thread):
    def __init__(self, src=0):
        super().__init__()
        self.src = src
        self.frame_queue = Queue(maxsize=1)
        self.stop_flag = False
        self.daemon = True

    def run(self):
        cap = cv2.VideoCapture(self.src)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        if not cap.isOpened():
            print("Ошибка: Не удалось получить доступ к веб-камере")
            return
        while not self.stop_flag:
            ret, frame = cap.read()
            if not ret:
                break
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except:
                    pass
            self.frame_queue.put(frame)
            time.sleep(0.001)
        cap.release()

    def stop(self):
        self.stop_flag = True

    def get_frame(self):
        try:
            return self.frame_queue.get_nowait()
        except:
            return None