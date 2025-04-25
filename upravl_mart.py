import cv2
import numpy as np
from ultralytics import YOLO
import threading
from queue import Queue
import time
import math
from PIL import Image, ImageDraw, ImageFont
from config import TARGET, CROSSHAIR, QUADRANTS, ARROW, FRAME_PROCESSING
from turel_control import TurelController

def get_coordinates(frame, point):
    """
    Преобразует координаты точки в координаты относительно центра кадра
    point: tuple (x, y) - координаты точки в пикселях
    Возвращает: tuple (x, y) - координаты относительно центра
    """
    height, width = frame.shape[:2]
    center_x = width // 2
    center_y = height // 2
    
    # Вычисляем смещение от центра
    relative_x = point[0] - center_x
    relative_y = point[1] - center_y
    
    return (relative_x, relative_y)

def draw_crosshair(frame):
    height, width = frame.shape[:2]
    center_x = width // 2
    center_y = height // 2
    
    # Рисуем прямо на входном кадре без создания копии
    cv2.line(frame, 
             (center_x - CROSSHAIR['SIZE'], center_y),
             (center_x + CROSSHAIR['SIZE'], center_y),
             CROSSHAIR['COLOR'],
             CROSSHAIR['THICKNESS'])
    
    cv2.line(frame,
             (center_x, center_y - CROSSHAIR['SIZE']),
             (center_x, center_y + CROSSHAIR['SIZE']),
             CROSSHAIR['COLOR'],
             CROSSHAIR['THICKNESS'])
    
    return frame

def put_russian_text(img, text, org, font_scale, color, thickness=1):
    """Функция для отображения текста с поддержкой кириллицы"""
    # Создаем изображение PIL из массива numpy
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    
    # Загружаем шрифт (укажите правильный путь к шрифту)
    # Можно использовать любой шрифт с поддержкой кириллицы, например Arial.ttf
    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", int(font_scale * 30))
    
    # Рисуем текст
    draw.text(org, text, font=font, fill=(color[2], color[1], color[0]))
    
    # Конвертируем обратно в BGR
    result_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    # Копируем только область с текстом обратно в исходное изображение
    return result_img

def draw_quadrants(frame):
    height, width = frame.shape[:2]
    center_x = width // 2
    center_y = height // 2
    
    # Рисуем пунктирные линии
    for y in range(0, height, QUADRANTS['LINE_SEGMENT']):
        cv2.line(frame, 
                 (center_x, y),
                 (center_x, min(y + QUADRANTS['LINE_SEGMENT']//2, height)),
                 QUADRANTS['COLOR'],
                 QUADRANTS['LINE_THICKNESS'])
    
    for x in range(0, width, QUADRANTS['LINE_SEGMENT']):
        cv2.line(frame,
                 (x, center_y),
                 (min(x + QUADRANTS['LINE_SEGMENT']//2, width), center_y),
                 QUADRANTS['COLOR'],
                 QUADRANTS['LINE_THICKNESS'])
    
    # Добавляем номера четвертей
    for i, pos in enumerate([(1, -1), (1, 1), (-1, -1), (-1, 1)], 1):
        frame = put_russian_text(frame,
                              str(i),
                              (center_x + pos[0] * QUADRANTS['NUMBER_OFFSET'],
                               center_y + pos[1] * QUADRANTS['NUMBER_OFFSET']),
                              font_scale=QUADRANTS['FONT_SCALE'],
                              color=QUADRANTS['COLOR'])
    
    return frame

def draw_target_arrow(frame, start_point, end_point):
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    length = math.sqrt(dx**2 + dy**2)
    
    if length > ARROW['MAX_LENGTH']:
        scale = ARROW['MAX_LENGTH'] / length
        dx *= scale
        dy *= scale
        end_point = (int(start_point[0] + dx), int(start_point[1] + dy))
    
    # Рисуем пунктирную линию
    for i in range(ARROW['NUM_SEGMENTS']):
        if i % 2 == 0:
            segment_start = (
                int(start_point[0] + (dx * i / ARROW['NUM_SEGMENTS'])),
                int(start_point[1] + (dy * i / ARROW['NUM_SEGMENTS']))
            )
            segment_end = (
                int(start_point[0] + (dx * (i + 1) / ARROW['NUM_SEGMENTS'])),
                int(start_point[1] + (dy * (i + 1) / ARROW['NUM_SEGMENTS']))
            )
            cv2.line(frame, segment_start, segment_end, 
                    ARROW['COLOR'], ARROW['THICKNESS'])
    
    # Рисуем наконечник стрелки
    angle = math.atan2(dy, dx)
    arrow_angle = math.radians(ARROW['HEAD_ANGLE'])
    
    p1 = (
        int(end_point[0] - ARROW['HEAD_LENGTH'] * math.cos(angle + arrow_angle)),
        int(end_point[1] - ARROW['HEAD_LENGTH'] * math.sin(angle + arrow_angle))
    )
    p2 = (
        int(end_point[0] - ARROW['HEAD_LENGTH'] * math.cos(angle - arrow_angle)),
        int(end_point[1] - ARROW['HEAD_LENGTH'] * math.sin(angle - arrow_angle))
    )
    
    cv2.line(frame, end_point, p1, ARROW['COLOR'], ARROW['THICKNESS'])
    cv2.line(frame, end_point, p2, ARROW['COLOR'], ARROW['THICKNESS'])
    
    return frame

class VideoStreamThread(threading.Thread):
    def __init__(self, src=0):
        super().__init__()
        self.src = src
        self.frame_queue = Queue(maxsize=1)
        self.stop_flag = False
        self.daemon = True

    def run(self):
        cap = cv2.VideoCapture(self.src)
        
        # Устанавливаем высокое разрешение для лучшей детекции
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # Full HD разрешение
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        if not cap.isOpened():
            print("Ошибка: Не удалось получить доступ к веб-камере")
            return
        
        while not self.stop_flag:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Очищаем очередь перед добавлением нового кадра
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

                # Переменные для отслеживания приоритетной цели
                priority_target = None
                max_confidence = 0

                # Находим цель с максимальной вероятностью
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

                # Если найдена приоритетная цель, отображаем её
                if priority_target:
                    x1, y1, x2, y2 = priority_target['box']
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    deviation = priority_target['deviation']
                    confidence = priority_target['confidence']

                    # Рисуем стрелку от центра к цели
                    height, width = frame.shape[:2]
                    frame_center = (width // 2, height // 2)
                    target_center = (center_x, center_y)
                    frame = draw_target_arrow(frame, frame_center, target_center)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Создаем текст с информацией
                    prob_text = f"Вероятность: {confidence:.2f}"
                    coord_text = f"X: {deviation[0]:.1f} Y: {deviation[1]:.1f}"

                    # Рисуем белый прямоугольник для фона информации
                    cv2.rectangle(frame, 
                                  TARGET['POSITION'],
                                  (TARGET['POSITION'][0] + TARGET['SIZE'][0], 
                                   TARGET['POSITION'][1] + TARGET['SIZE'][1]),
                                  TARGET['BACKGROUND_COLOR'],  # Убедитесь, что этот цвет белый
                                  -1)  # -1 для заполнения прямоугольника

                    # Отображаем информацию с поддержкой кириллицы
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
                # Если цель не найдена, прямоугольник не рисуется
                else:
                    # Здесь можно добавить код для очистки информации, если нужно
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

def capture_video():
    frame_queue = Queue(maxsize=1)
    result_queue = Queue(maxsize=1)
    
    video_thread = VideoStreamThread()
    detection_thread = DetectionThread(frame_queue, result_queue)
    
    video_thread.start()
    detection_thread.start()
    
    try:
        last_time = time.time()
        fps = 0
        frames_count = 0
        
        while True:
            current_time = time.time()
            if current_time - last_time >= 1.0:
                print(f"FPS: {fps}")
                fps = 0
                last_time = current_time
                
            frame = video_thread.get_frame()
            if frame is not None:
                frame_queue.put(frame)
                fps += 1
                
            if not result_queue.empty():
                processed_frame = result_queue.get()
                cv2.imshow('Drone Detection', processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        video_thread.stop()
        detection_thread.stop()
        video_thread.join()
        detection_thread.join()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_video()