import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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
    """
    Рисует прицел (крестик) в центре кадра
    """
    height, width = frame.shape[:2]
    center_x = width // 2
    center_y = height // 2
    
    cv2.line(frame, 
             (center_x - 20, center_y),
             (center_x + 20, center_y),
             (255, 0, 0), 2)
    
    cv2.line(frame,
             (center_x, center_y - 20),
             (center_x, center_y + 20),
             (255, 0, 0), 2)
    
    return frame

def put_russian_text(img, text, org, font_scale, color, thickness=1):
    """Функция для отображения текста с поддержкой кириллицы"""
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    
    try:
        font = ImageFont.truetype(font_path, int(font_scale * 30))
    except IOError:
        font = ImageFont.load_default()

    draw.text(org, text, font=font, fill=(color[2], color[1], color[0]))

    result_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return result_img

def draw_target_arrow(frame, start_point, end_point):
    """
    Рисует стрелку от start_point к end_point
    """
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    length = np.sqrt(dx**2 + dy**2)
    
    if length > 50:
        scale = 50 / length
        dx *= scale
        dy *= scale
        end_point = (int(start_point[0] + dx), int(start_point[1] + dy))
    
    for i in range(10):
        if i % 2 == 0:
            segment_start = (int(start_point[0] + (dx * i / 10)), int(start_point[1] + (dy * i / 10)))
            segment_end = (int(start_point[0] + (dx * (i + 1) / 10)), int(start_point[1] + (dy * (i + 1) / 10)))
            cv2.line(frame, segment_start, segment_end, (0, 0, 255), 2)
    
    return frame

def draw_quadrants(frame):
    """
    Рисует квадранты на кадре, разделяя его на 4 части.
    """
    height, width = frame.shape[:2]
    center_x = width // 2
    center_y = height // 2
    
    # Рисуем вертикальные и горизонтальные линии для создания 4 квадрантов
    cv2.line(frame, (center_x, 0), (center_x, height), (255, 0, 0), 2)
    cv2.line(frame, (0, center_y), (width, center_y), (255, 0, 0), 2)

    # Добавление номеров для квадрантов (1, 2, 3, 4)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, '1', (center_x + 10, center_y - 30), font, 1, (255, 0, 0), 2)
    cv2.putText(frame, '2', (center_x + 10, center_y + 30), font, 1, (255, 0, 0), 2)
    cv2.putText(frame, '3', (center_x - 30, center_y - 30), font, 1, (255, 0, 0), 2)
    cv2.putText(frame, '4', (center_x - 30, center_y + 30), font, 1, (255, 0, 0), 2)

    return frame
