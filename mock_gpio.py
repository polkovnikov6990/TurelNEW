class GPIO:
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0

    # Словарь для хранения назначения пинов
    PIN_NAMES = {
        17: "HORIZONTAL_STEP",
        18: "HORIZONTAL_DIR",
        22: "VERTICAL_STEP",
        27: "VERTICAL_DIR",
        23: "HORIZONTAL_ENABLE",
        24: "VERTICAL_ENABLE"
    }

    # Счетчики шагов
    horizontal_steps = 0
    vertical_steps = 0
    
    # Направления движения
    horizontal_direction = "NONE"
    vertical_direction = "NONE"

    @staticmethod
    def setmode(mode):
        print(f"Инициализация GPIO в режиме {mode}")

    @staticmethod
    def setup(pin, mode):
        pin_name = GPIO.PIN_NAMES.get(pin, f"UNKNOWN_PIN_{pin}")
        print(f"Настройка пина {pin_name} ({pin}) в режим {mode}")

    @staticmethod
    def output(pin, value):
        pin_name = GPIO.PIN_NAMES.get(pin, f"UNKNOWN_PIN_{pin}")
        
        # Отслеживание шагов горизонтального двигателя
        if pin == 17:  # HORIZONTAL_STEP
            if value == 1:  # Передний фронт импульса
                GPIO.horizontal_steps += 1
                direction = "вправо" if GPIO.horizontal_direction == "RIGHT" else "влево"
                print(f"Горизонтальный шаг #{GPIO.horizontal_steps} ({direction})")
        
        # Отслеживание направления горизонтального двигателя
        elif pin == 18:  # HORIZONTAL_DIR
            GPIO.horizontal_direction = "RIGHT" if value == 1 else "LEFT"
            print(f"Установка направления горизонтального движения: {'вправо' if value == 1 else 'влево'}")
        
        # Отслеживание шагов вертикального двигателя
        elif pin == 22:  # VERTICAL_STEP
            if value == 1:  # Передний фронт импульса
                GPIO.vertical_steps += 1
                direction = "вверх" if GPIO.vertical_direction == "UP" else "вниз"
                print(f"Вертикальный шаг #{GPIO.vertical_steps} ({direction})")
        
        # Отслеживание направления вертикального двигателя
        elif pin == 27:  # VERTICAL_DIR
            GPIO.vertical_direction = "UP" if value == 1 else "DOWN"
            print(f"Установка направления вертикального движения: {'вверх' if value == 1 else 'вниз'}")

    @staticmethod
    def cleanup():
        print("\nИтоговая статистика движения:")
        print(f"Сделано {GPIO.horizontal_steps} шагов по горизонтали")
        print(f"Сделано {GPIO.vertical_steps} шагов по вертикали")
        print("GPIO cleanup выполнен")
