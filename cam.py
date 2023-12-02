import threading
from threading import Lock
import cv2

class Camera:
    """
    Класс для работы с камерой и получения изображений.

    :Атрибуты:
    - `last_frame` — Последний захваченный кадр с камеры.
    - `last_ready` — Флаг, указывающий, что последний кадр готов для использования.
    - `lock` — Объект блокировки для обеспечения безопасности многопоточного доступа.

    :Методы:
    - `__init__(self, rtsp_link)` — Конструктор класса, инициализирует объект камеры и запускает поток для чтения RTSP-потока.
    - `rtsp_cam_buffer(self, capture)` — Приватный метод для буферизации кадров из RTSP-потока.
    - `getFrame(self)` — Метод для получения последнего готового кадра из камеры.

    """
    last_frame = None
    last_ready = None
    lock = Lock()

    def __init__(self, rtsp_link):
        """
        Конструктор класса.

        Параметры:
        - `rtsp_link` (str) — Ссылка на RTSP-поток.

        Инициализирует объект камеры, создает объект захвата кадров и запускает поток чтения RTSP-потока.

        """
        capture = cv2.VideoCapture(rtsp_link)
        thread = threading.Thread(target=self.rtsp_cam_buffer, args=(capture,), name="rtsp_read_thread")
        thread.daemon = True
        thread.start()

    def rtsp_cam_buffer(self, capture):
        """
        Приватный метод для буферизации кадров из RTSP-потока.

        Параметры:
        - `capture` (cv2.VideoCapture) — Объект захвата кадров.

        В бесконечном цикле с использованием блокировки обновляет последний готовый кадр и последний кадр с камеры.

        """
        while True:
            with self.lock:
                self.last_ready, self.last_frame = capture.read()

    def getFrame(self):
        """
        Метод для получения последнего готового кадра из камеры.

        Возвращает копию последнего готового кадра, если он доступен, иначе возвращает None.

        """
        if (self.last_ready is not None) and (self.last_frame is not None):
            return self.last_frame.copy()
        else:
            return None



        