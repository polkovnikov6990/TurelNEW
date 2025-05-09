from queue import Queue
from video_detection import DetectionThread  # Импортируем класс для обработки видео
from turel_control import TurelControlThread  # Импортируем класс для управления шаговыми двигателями
import cv2
import time
import queue


def capture_video():
    # Очереди для передачи кадров между потоками
    frame_queue = Queue(maxsize=1)
    result_queue = Queue(maxsize=1)
    
    # Создание потоков для детекции и управления
    video_thread = DetectionThread(frame_queue, result_queue)  # Поток обработки видео
    control_thread = TurelControlThread(result_queue)  # Поток управления Turel

    # Запуск потоков
    video_thread.start()
    control_thread.start()
    
    last_time = time.time()
    fps = 0
    
    try:
        while True:
            current_time = time.time()
            
            # Рассчитываем FPS
            if current_time - last_time >= 1.0:
                print(f"FPS: {fps}")
                fps = 0
                last_time = current_time

            # Получаем кадр из видеопотока
            frame = video_thread.frame_queue.get()
            if frame is not None:
                frame_queue.put(frame)  # Помещаем кадр в очередь для детекции
                fps += 1
                
            # Если есть обработанный кадр, показываем его
            try:
                if not result_queue.empty():
                    processed_frame = result_queue.get_nowait()
                    cv2.imshow('Drone Detection', processed_frame)
            except queue.Empty:
                pass  # Если очередь пустая, просто пропускаем этот шаг
            
            # Если нажата клавиша 'q', выходим из цикла
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("Capture video interrupted.")
    finally:
        # Останавливаем потоки
        video_thread.stop()  
        control_thread.stop()
        
        # Ждем завершения потоков
        video_thread.join()
        control_thread.join()
        
        # Закрываем окна OpenCV
        cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_video()
