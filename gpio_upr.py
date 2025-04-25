import time
import cv2
import numpy as np

# Эмуляция пинов (для тестирования на Mac)
X_DIR_PIN = 17  # Эмуляция пина для оси X
X_STEP_PIN = 27  # Эмуляция пина для шага по оси X
Y_DIR_PIN = 22  # Эмуляция пина для оси Y
Y_STEP_PIN = 23  # Эмуляция пина для шага по оси Y

# Константы
STEP_DELAY = 0.002  # задержка между шагами

# Создаем пустое изображение для отображения
frame = np.zeros((480, 640, 3), dtype=np.uint8)

# Функция для эмуляции работы шагового мотора
def step_motor(direction, steps, axis="", frame=None):
    # Эмуляция направления мотора
    direction_str = "vpravo" if direction > 0 else "влево"
    print(f"dvig motor  {axis} v napr {direction_str} на {abs(steps)} шагов.")

    # Добавляем текст на экран (в правый нижний угол)
    text = f"emul SHD po osi {axis}: {abs(steps)} шагов"
    cv2.putText(frame, text, (frame.shape[1] - 400, frame.shape[0] - 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    # Эмуляция шага
    for _ in range(abs(steps)):
        # Отображаем шаги на экране
        print(f"Шаг: включен шаг {axis}...")  # Эмуляция шага
        time.sleep(STEP_DELAY)
        print(f"Шаг: выключен шаг {axis}...")  # Эмуляция выключения
        time.sleep(STEP_DELAY)

        # Обновляем изображение
        cv2.imshow('emul SHD', frame)

def move_by_deviation(x_dev, y_dev, threshold=10, step_scale=0.1):
    # Преобразуем пиксели в шаги
    x_steps = int(x_dev * step_scale)
    y_steps = int(y_dev * step_scale)

    if abs(x_steps) > threshold:
        step_motor(direction=1 if x_steps > 0 else -1, steps=abs(x_steps), axis="X", frame=frame)
    if abs(y_steps) > threshold:
        step_motor(direction=1 if y_steps > 0 else -1, steps=abs(y_steps), axis="Y", frame=frame)

    # Закрываем окно после завершения
    cv2.waitKey(1)
    cv2.destroyAllWindows()

# Пример вызова с эмуляцией отклонения
move_by_deviation(5, -3)
