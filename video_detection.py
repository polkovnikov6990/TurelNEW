# detection.py

import cv2
import time
from ultralytics import YOLO
from queue import Queue
import threading
from config import TARGET, QUADRANTS, CROSSHAIR, FRAME_PROCESSING
from turel_control import TurelController
from utils import draw_crosshair, draw_quadrants, get_coordinates, put_russian_text, draw_target_arrow

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

                priority_target = None
                max_confidence = 0

                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        confidence = float(box.conf[0])
                        if confidence > max_confidence:
                            max_confidence = confidence
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            deviation = get_coordinates(frame, (center_x, center_y))

                            priority_target = {
                                'box': (x1, y1, x2, y2),
                                'center': (center_x, center_y),
                                'deviation': deviation,
                                'confidence': confidence
                            }

                if priority_target:
                    x1, y1, x2, y2 = priority_target['box']
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    deviation = priority_target['deviation']
                    confidence = priority_target['confidence']

                    height, width = frame.shape[:2]
                    frame_center = (width // 2, height // 2)
                    target_center = (center_x, center_y)
                    frame = draw_target_arrow(frame, frame_center, target_center)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    prob_text = f"Вероятность: {confidence:.2f}"
                    coord_text = f"X: {deviation[0]:.1f} Y: {deviation[1]:.1f}"

                    cv2.rectangle(frame, 
                                  TARGET['POSITION'],
                                  (TARGET['POSITION'][0] + TARGET['SIZE'][0], 
                                   TARGET['POSITION'][1] + TARGET['SIZE'][1]),
                                  TARGET['BACKGROUND_COLOR'],  
                                  -1)  

                    frame = put_russian_text(
                        frame,
                        prob_text,
                        (TARGET['POSITION'][0] + TARGET['PADDING'],
                         TARGET['POSITION'][1] + TARGET['TEXT_OFFSET_Y1'] - 10),
                        TARGET['INFO_FONT_SCALE'],
                        TARGET['TEXT_COLOR']
                    )

                    frame = put_russian_text(
                        frame,
                        coord_text,
                        (TARGET['POSITION'][0] + TARGET['PADDING'],
                         TARGET['POSITION'][1] + TARGET['TEXT_OFFSET_Y2'] - 10),
                        TARGET['INFO_FONT_SCALE'],
                        TARGET['TEXT_COLOR']
                    )
                else:
                    pass

                self.last_detection_time = current_time
            
            while not self.result_queue.empty():
                try:
                    self.result_queue.get_nowait()
                except:
                    pass
                    
            self.result_queue.put(frame)

    def stop(self):
        self.turel.cleanup()
        self.stop_flag = True
