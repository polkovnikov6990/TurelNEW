import cv2
import time
from ultralytics import YOLO
import torch
import config

def main():
    # Загружаем вашу модель
    model = YOLO('yolov8m.pt')

    # Открываем камеру (0 — стандартная веб-камера)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Не удалось открыть камеру.")
        return

    last_log_time = time.time()
    deviation_text = "Вк"

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Не удалось получить кадр с камеры.")
                break

            # Получаем размеры кадра и центр
            height, width = frame.shape[:2]
            center_x = width // 2
            center_y = height // 2

            # Детекция объектов
            results = model(frame)
            annotated_frame = results[0].plot()  # Кадр с разметкой

            # Поиск самого вероятного объекта (например, дрона)
            max_conf = 0
            drone_center = None
            x1, y1, x2, y2 = None, None, None, None  # Инициализируем переменные

            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf > max_conf:
                        max_conf = conf
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        drone_center = ((x1 + x2) // 2, (y1 + y2) // 2)

            # Обновляем текст только раз в секунду
            current_time = time.time()
            if current_time - last_log_time >= 1.0:
                if drone_center:
                    # X — как раньше, Y — инвертирован
                    deviation = (drone_center[0] - center_x, center_y - drone_center[1])
                    deviation_text = f"Отклонение: X={deviation[0]} px, Y={deviation[1]} px"
                else:
                    deviation_text = "Дрон не найден"
                last_log_time = current_time

            # Рисуем перекрестие
            cv2.drawMarker(frame, (center_x, center_y), config.CROSSHAIR_COLOR, markerType=cv2.MARKER_CROSS, markerSize=config.CROSSHAIR_SIZE, thickness=config.CROSSHAIR_THICKNESS)

            # Рисуем квадрат вокруг цели, если дрон найден
            if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
                cv2.rectangle(frame, (x1, y1), (x2, y2), config.TARGET_BOX_COLOR, config.TARGET_BOX_THICKNESS)

            # Рисуем текст
            cv2.putText(frame, deviation_text, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, config.TEXT_SCALE, config.TEXT_COLOR, config.TEXT_THICKNESS, cv2.LINE_AA)

            # Показываем результат
            cv2.imshow('YOLOv8m Detection', frame)

            # Выход по клавише 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
