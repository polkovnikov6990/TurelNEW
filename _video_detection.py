from ultralytics import YOLO
import threading
import time
from _turel_control import TurelController
from _utils import draw_quadrants, draw_crosshair, draw_target_arrow, put_russian_text, get_coordinates
from _config import TARGET, FRAME_PROCESSING

class DetectionThread(threading.Thread):
    def __init__(self, frame_queue, result_queue, model_path='yolov8m.pt'):
        super().__init__()
        self.frame_queue = frame_queue
        self.result_queue = result_queue
        self.model = YOLO(model_path)
        self.stop_flag = False
        self.daemon = True
        self.last_detection_time = 0
        self.turel = TurelController()

    def run(self):
        while not self.stop_flag:
            if self.frame_queue.empty():
                time.sleep(0.001)
                continue
            frame = self.frame_queue.get()
            current_time = time.time()
            if current_time - self.last_detection_time >= FRAME_PROCESSING['DETECTION_INTERVAL']:
                frame = draw_quadrants(frame)
                frame = draw_crosshair(frame)
                results = self.model(frame, conf=TARGET['CONFIDENCE_THRESHOLD'])
                # ... (оставь остальную логику как есть)
                # Вынеси вспомогательные функции в utils.py
            while not self.result_queue.empty():
                try:
                    self.result_queue.get_nowait()
                except:
                    pass
            self.result_queue.put(frame)

    def stop(self):
        self.turel.cleanup()
        self.stop_flag = True
