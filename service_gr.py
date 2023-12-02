import os, sys

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f"{dir_path}/..")

from service import Service
from ultralytics import YOLO
import cv2
from cam import Camera

class ServiceGR(Service):
    """
    Этот класс расширяет базовый класс Service и реализует конкретную логику обработки задач,
    связанных с распознаванием жестов с использованием видеопотока с камеры.

    :Атрибуты:
    - `_classNames` —  Список названий классов жестов.
    - `_model` —  Модель YOLO для распознавания жестов.

    :Методы:
    - `_do_job(self)` — Реализует основной цикл работы, захватывая кадры с камеры, выполняя распознавание жестов и взаимодействуя с внешними серверами на основе распознанных жестов.
    - `__init_vars(self)` — Инициализирует внутренние переменные, такие как названия классов жестов и модель YOLO.
    - `__specific_work(self)` — Выполняет конкретную работу по распознаванию жестов с использованием модели YOLO.
    - `__resp_hand(self, response)` — Обрабатывает ответы от внешних серверов.
    - `_request_handler(request: str) -> str` — Обрабатывает запросы на включение, отключение, закрытие или перезапуск службы.

    :Примечание:
    - Метод `_do_job` содержит цикл, который непрерывно захватывает кадры, выполняет
      распознавание жестов и взаимодействует с внешними серверами. Цикл может быть прерван
      установкой `need_job_break` в True или приостановлен установкой `need_job_pause` в False.
    - Ожидается, что файл модели YOLO "best.onnx" находится в том же каталоге, что и скрипт.
    - Результаты распознавания жестов отображаются с использованием OpenCV в окне с заголовком "Gesture recognition".
    - Класс поддерживает обработку конкретных жестов, таких как "Hello" и "Goodbye",
      взаимодействуя с серверами распознавания речи.

    Использование:
    ```python
    service = ServiceGR()
    service.start()  # Запустить службу, инициируя цикл распознавания жестов.
    ```

    """
    def _do_job(self):
        """
        Реализует основной цикл работы сервиса по распознаванию жестов.

        Метод начинает выполнение, захватывая кадры с камеры и инициализируя необходимые переменные.
        Далее запускается бесконечный цикл, в котором происходит следующее:
        
        1. Проверяется флаг `need_job_break`. Если он установлен в True, цикл прерывается, и выполнение метода завершается.
        
        2. Проверяется флаг `need_job_pause`. Если он установлен в False, цикл останавливается, и выполнение метода
           приостанавливается, ожидая изменения значения флага.

        3. Захватывается кадр с камеры, проверяется его корректность, и обрабатывается для дальнейшего использования.

        4. Выполняется распознавание жестов с использованием метода `__specific_work`, который использует модель YOLO.

        5. В зависимости от распознанного жеста, инициируется взаимодействие с внешними серверами:
           - Если жест распознан как "Hello" или "Goodbye", выполняется запрос к серверу распознавания речи.
           - В противном случае, выполняется запрос к серверу управления движениями.

        6. В окне с заголовком "Gesture recognition" с использованием OpenCV отображаются результаты распознавания.

        7. Если нажата клавиша 'q', цикл прерывается, и метод завершает выполнение.

        Наконец, в блоке `finally` закрываются окна OpenCV, и вызывается метод `stop` для завершения работы сервиса.

        """
        try:
            url = 0
            cap = Camera(url)        
            self.__init_vars()
            while True:
                if self.need_job_break:
                    return
                if not self.need_job_pause:
                    continue

                frame_raw = cap.getFrame()
                if frame_raw is None:
                    continue

                h, w, ch = frame_raw.shape
                w = w//2
                self.frame = frame_raw[0:h, 0:w]

                result = self.__specific_work()

                server_ip_speach_recognition = '0.0.0.0'
                server_port_speach_recognition = 0000
                server_ip_doing_movements = '0.0.0.0'
                server_port_doing_movements = 0000

                if result == "Class wasn't recognised":
                    continue
                elif result == "Hello" or result == "Goodbye":
                    self.run_client(ip=server_ip_speach_recognition, port=server_port_speach_recognition_port, \
                                    request=result, response_handler=self.__resp_hand)
                else:
                    self.run_client(ip=server_ip_doing_movements, port=server_port_doing_movements,\
                                    request=result, response_handler=self.__resp_hand)
                         
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        finally:    
            cv2.destroyAllWindows()
            self.stop()

    def __init_vars(self):
        """
        Инициализирует внутренние переменные класса ServiceGR.

        Устанавливает список `_classNames` с названиями классов жестов и загружает модель YOLO из файла "best.onnx".

        """
        self._classNames = ['Forward', 'Left', 'Right', 'Stop', 'Goodbye', 'Back', 'Hello']
        self._model = YOLO("best.onnx")

    def __specific_work(self) -> str:
        """
        Выполняет конкретную работу по распознаванию жестов с использованием модели YOLO.

        Метод передает текущий кадр в модель YOLO и обрабатывает результаты распознавания.
        Если распознан какой-либо жест, то отображает аннотированный кадр с результатами и возвращает
        строку с названием распознанного класса жеста. В случае, если жест не распознан, возвращает
        строку "Class wasn't recognised".

        """
        results = self._model(self.frame)
        recognition_class = ""

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                recognition_class = self._classNames[cls]

        annotated_frame = results[0].plot()

        cv2.imshow("Gesture recognition", annotated_frame)

        if recognition_class == "":
            return "Class wasn't recognised"
        else:
            return recognition_class

    def __resp_hand(self, response):
        """
        Обрабатывает ответ от внешних сервисов.

        Выводит в консоль сообщение о полученном ответе и IP-адресе сервера.

        """
        print(f"Message was received from ip {server_ip_speech_recognition}: {response}")

    def _request_handler(request: str) -> str:
        """
        Обрабатывает запросы, поступающие от внешних источников.

        В зависимости от значения запроса, возвращает соответствующий ответ.

        Аргументы:
        - `request` — Строка с запросом.

        Возвращает:
        Строка с ответом на запрос.

        """
        if request == "disable":
            return "disabled"
        elif request == "enable":
            return "enabled"
        elif request == "close":
            return "closed"
        elif request == "restart":
            return "restarted"
        else:
            return "nothing"
