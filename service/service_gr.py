# Импортируем класс, от которого будем наследоваться
import os, sys

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f"{dir_path}/..")

from service import Service

# Ниже импорты специфичные для задачи
from ultralytics import YOLO
import cv2

# Импорт класса для работы с камерой
from cam import Camera

# Определения сервиса для детекции лиц
# Пример как определить свой сервис
class ServiceGR(Service):

    # Функция, которую НЕОБХОДИМО переопределить
    def _do_job(self):
        try:
            # Подключение к RTSP потоку камеры
            #url = 'rtsp://0.0.0.0:8554/mystream'  # rtsp-стрим
            url = 0  # webcam
            cap = Camera(url)        

            # Инициализация переменных
            self.__init_vars()

            # "Бесконечный цикл", который выполняют работу, для которой создан сервис:
            # 1) Обработка кадров
            # 2) Обработка звука
            # 3) Обработка сигналов (с лидаров/сонаров)
            while True:
                # ДАННЫЙ БЛОК НЕОБХОДИМО ВКЛЮЧИТЬ В СВОЙ БЕСКОНЕЧНЫЙ ЦИКЛ
                # Начало
                if self.need_job_break:
                    return
                if not self.need_job_pause:
                    continue
                # Конец

                # Получение кадров из потока
                frame_raw = cap.getFrame()
                # Проверка, что кадр непустой
                if frame_raw is None:
                    continue

                # На текущий момент фрейм - это две картинки с RGB-сенсора и со стереопары (Depth) w=1280px, h=480px
                # RGB фрейм слева, т.е. его координаты (x=0, y=0, w=640, h=480)
                # Depth фрейм слева, т.е. его координаты (x=0, y=0, w=640, h=480)
                h, w, ch = frame_raw.shape
                w = w//2
                self.frame = frame_raw[0:h, 0:w]  # получение RGB
                # frame = frame_raw[0:h, w:2*w]  # получение Depth

                # Обработка кадра (или иная работа сервиса)
                # В данном примере работа - это определение лица и его идентификация между кадрами
                result = self.__specific_work()

                # Пример коммуникации с другим Сервисом Б
                # 1) Сервис Б должен прослушивать server_ip:server_port
                # 2) Сервис Б должен уметь обрабатывать команду req и возвращать какой-либо результат
                # чтобы обработать результат следует использовать функцию, которая принимает ответ сервиса (str)
                server_ip_speach_recognition = '0.0.0.0'
                server_port_speach_recognition = 0000

                server_ip_doing_movements = '0.0.0.0'
                server_port_doing_movements = 0000

                if result == "Class wasn't recognised":
                    continue
                elif result == "Hello" or result == "Goodbye":
                    # взаимодействие с сервисом Анализа и синтеза речи
                    self.run_client(ip=server_ip_speach_recognition, port=serverserver_port_speach_recognition_port, \
                                    request=result, response_handler=self.__resp_hand)
                else:
                    # взаимодействие с сервисом Выполнения движения робота
                    self.run_client(ip=server_ip_doing_movements, port=server_port_doing_movements,\
                                    request=result, response_handler=self.__resp_hand)
                         
                # Пример реализации небольшой задержки и корректного выхода их бесконечного цикла
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        finally:    
            cv2.destroyAllWindows()
            # close job + server
            self.stop()


    # Вспомогательная функция
    def __init_vars(self):
        self._classNames = ['Forward', 'Left', 'Right', 'Stop', 'Goodbye', 'Back', 'Hello']
        self._model = YOLO("best.onnx")

    # Вспомогательная функция
    def __specific_work(self):
        
        results = self._model(self.frame)
        recognition_class = ""

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                recognition_class = self._classNames[cls]

        annotated_frame = results[0].plot()
        
        cv2.imshow("Gesture recognition", annotated_frame)

        #print(recognition_class)

        if recognition_class == "":
            return "Class wasn't recognised"
        else:
            return recognition_class


    def __resp_hand(self, response):
        print(f"Message was receiced from ip {server_ip_speach_recognition}: {response}")

    def _request_handler(request: str) -> str:
    # Завести набор команд, которые может обрабатывать сервер
    # Предварительно обозначены следующие команды, которые есть у КАЖДОГО сервиса
    # 1) disable (ставим на паузу)
    # 2) enable (снимаем с паузы)
    # 3) close (закрываем сервис)
    # 4) restart (перезапускаем сервис)

    # остальной набор команд специфичен для каждого сервиса
    # данная функция ВСЕГДА должна что-то возвращать либо результат, либо статус (OK, FAILED, etc)

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