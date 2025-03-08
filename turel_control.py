try:
    import RPi.GPIO as GPIO
    print("Используется реальный GPIO")
except ImportError:
    print("RPi.GPIO не доступен")
    from mock_gpio import GPIO

import time
from config import TARGET
import math

class TurelController:
    def __init__(self):
        # Пины для горизонтального двигателя
        self.HORIZONTAL_STEP_PIN = 17
        self.HORIZONTAL_DIR_PIN = 18
        self.HORIZONTAL_ENABLE_PIN = 23

        # Пины для вертикального двигателя
        self.VERTICAL_STEP_PIN = 22
        self.VERTICAL_DIR_PIN = 27
        self.VERTICAL_ENABLE_PIN = 24

        # Параметры двигателей
        self.STEPS_PER_REV = 200  # Количество шагов на оборот (для Nema 17)
        self.MICROSTEPS = 16      # Микрошаги (зависит от драйвера)
        self.GEAR_RATIO = 1       # Передаточное отношение (если используется редуктор)
        
        # Параметры точности
        self.TOLERANCE = 5        # Допустимое отклонение в пикселях
        self.STEPS_PER_PIXEL = 0.5  # Количество шагов на один пиксель

        # Инициализация GPIO
        self.setup_gpio()

    def setup_gpio(self):
        """Инициализация пинов GPIO"""
        GPIO.setmode(GPIO.BCM)
        
        # Настройка пинов горизонтального двигателя
        GPIO.setup(self.HORIZONTAL_STEP_PIN, GPIO.OUT)
        GPIO.setup(self.HORIZONTAL_DIR_PIN, GPIO.OUT)
        GPIO.setup(self.HORIZONTAL_ENABLE_PIN, GPIO.OUT)
        
        # Настройка пинов вертикального двигателя
        GPIO.setup(self.VERTICAL_STEP_PIN, GPIO.OUT)
        GPIO.setup(self.VERTICAL_DIR_PIN, GPIO.OUT)
        GPIO.setup(self.VERTICAL_ENABLE_PIN, GPIO.OUT)
        
        # Включаем двигатели
        GPIO.output(self.HORIZONTAL_ENABLE_PIN, GPIO.LOW)
        GPIO.output(self.VERTICAL_ENABLE_PIN, GPIO.LOW)

    def make_step(self, step_pin, direction_pin, direction):
        """Выполнение одного шага"""
        GPIO.output(direction_pin, direction)
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(0.001)  # Задержка между шагами
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(0.001)

    def move_to_target(self, target_x, target_y):
        """
        Перемещение турели к цели
        target_x, target_y: координаты цели относительно центра кадра
        """
        # Определяем направление движения по горизонтали
        horizontal_direction = GPIO.HIGH if target_x > 0 else GPIO.LOW
        horizontal_steps = abs(int(target_x * self.STEPS_PER_PIXEL))

        # Определяем направление движения по вертикали
        vertical_direction = GPIO.HIGH if target_y > 0 else GPIO.LOW
        vertical_steps = abs(int(target_y * self.STEPS_PER_PIXEL))

        # Двигаемся к цели
        for _ in range(max(horizontal_steps, vertical_steps)):
            if horizontal_steps > 0:
                self.make_step(self.HORIZONTAL_STEP_PIN, self.HORIZONTAL_DIR_PIN, horizontal_direction)
                horizontal_steps -= 1
            
            if vertical_steps > 0:
                self.make_step(self.VERTICAL_STEP_PIN, self.VERTICAL_DIR_PIN, vertical_direction)
                vertical_steps -= 1

    def is_on_target(self, target_x, target_y):
        """Проверка, находится ли цель в пределах допуска"""
        return abs(target_x) <= self.TOLERANCE and abs(target_y) <= self.TOLERANCE

    def cleanup(self):
        """Очистка GPIO при завершении работы"""
        GPIO.cleanup()

if __name__ == '__main__':
    # Тестовый код
    controller = TurelController()
    
    # Пример движения
    controller.move_to_target(50, 30)  # Движение вправо и вверх
