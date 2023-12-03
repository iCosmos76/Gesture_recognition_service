from abc import ABC, abstractmethod
import threading
import socket
import struct
from typing import Optional, Callable


class Service(ABC):
    """
    Абстрактный базовый класс, представляющий собой общий сервис.
    
    :Параметры:
    - `ip_ (str)` — IP-адрес для привязки сервиса. 
    - `port_ (int)` — Номер порта для привязки сервиса.
    - `n_conn_ (int, необязательно)` — Максимальное количество разрешенных подключений (по умолчанию - 10).
    
    :Атрибуты:
    - `ip (str)` — IP-адрес сервиса.
    - `port (int)` — Номер порта сервиса.
    - `n_conn (int)` — Максимальное количество разрешенных подключений.
    - `timeout (int)` — Значение времени ожидания для операций сокета (по умолчанию - 3 секунды).
    - `need_job_break (bool)` — Флаг, указывающий, нужно ли сервису прекратить обработку задач.
    - `need_job_pause (bool)` — Флаг, указывающий, нужно ли сервису приостановить обработку задач.
    - `server_is_open (bool)` — Флаг, указывающий, открыт ли сервер.
    - `need_restart (bool)` — Флаг, указывающий, нужно ли сервису перезапуститься.
    - `server (socket.socket)` — Объект сокета для взаимодействия.
    - `connected_clients (list)` — Список подключенных сокетов клиентов.
    
    :Методы:
    - `__init__(self, ip_, port_, n_conn_)` — Конструктор класса.
    - `__recvall(self, sock, n) -> bytearray` — Приватный метод для приема определенного количества байтов из сокета.
    - `__recv_msg(self, sock) -> bytearray` — Приватный метод для приема сообщения из сокета.
    - `__send_msg(self, sock, msg) -> None` — Приватный метод для отправки сообщения в сокет.
    - `__manage_clients(self) -> None` — Приватный метод для управления подключенными клиентами.
    - `_do_job(self)` — Абстрактный метод для выполнения конкретной задачи сервиса. Должен быть переопределен.
    - `_request_handler(self, request)` — Абстрактный метод для обработки запросов от клиентов.
    - `_run_client(self, ip, port, request, response_handler) -> None` — Метод для запуска клиента и отправки запроса на сервер.
    - `run_client(self, ip, port, request, response_handler) -> None` — Метод для запуска клиента в отдельном потоке.
    - `start(self) -> None` — Метод для запуска сервера.
    - `stop(self) -> None` — Метод для остановки сервера.
    - `pause(self) -> None` — Метод для приостановки выполнения работы.
    - `unpause(self) -> None` — Метод для возобновления выполнения работы.
    - `restart(self) -> None` — Метод для перезапуска сервера.
    :Примечание:
    Этот класс служит абстрактным базовым классом и должен быть унаследован для реализации конкретной функциональности сервиса.
    """


    def __init__(self, ip_: str, port_: int, n_conn_=10):
        """
        Конструктор класса.

        """
        self.ip = ip_
        self.port = port_
        self.n_conn = n_conn_
        self.timeout = 3
        self.need_job_break = False
        self.need_job_pause = True
        self.server_is_open = True
        self.need_restart = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_clients = []

    def __recvall(self, sock, n: int) -> bytearray:
        """
        Приватный метод для полного приема данных из сокета.

        :Параметры:
        - `sock (socket)` — Сокет, из которого происходит прием данных.
        - `n (int)` — Количество байтов, которое необходимо принять.

        Внутренний цикл продолжается, пока не будет принято указанное количество байтов.
        Каждый полученный пакет данных добавляется к общему массиву данных.

        Возвращает массив байтов, представляющий полностью принятые данные.

        """
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                break
            data.extend(packet)
        return data


    def __recv_msg(self, sock) -> bytearray:
        """
        Приватный метод для приема сообщения из сокета.

        :Параметры:
        - `sock (socket)` — Сокет, из которого происходит прием сообщения.

        Получает длину сообщения из первых 4 байтов, затем вызывает `__recvall` для полного приема сообщения.

        Возвращает массив байтов, представляющий принятое сообщение.

        """

        raw_msglen = self.__recvall(sock, 4)
        if not raw_msglen:
            return bytearray()
        msglen = struct.unpack('>I', raw_msglen)[0]
        return self.__recvall(sock, msglen)

    def __send_msg(self, sock, msg: bytes) -> None:
        """
        Приватный метод для отправки сообщения в сокет.

        :Параметры:
        - `sock (socket)` — Сокет, в который происходит отправка сообщения.
        - `msg (bytes) — Сообщение для отправки.

        Упаковывает длину сообщения в 4 байта, добавляет сообщение и отправляет все данные в сокет.

        """
        msg = struct.pack('>I', len(msg)) + msg
        sock.sendall(msg)


    def __manage_clients(self) -> None:
        """
        Приватный метод для управления подключенными клиентами.

        Внутренний цикл обрабатывает запросы от клиентов, основываясь на полученных данных.
        Если нет подключенных клиентов и сервер закрыт, цикл завершается.
        Если нет подключенных клиентов, происходит продолжение цикла.
        Для каждого подключенного клиента извлекается запрос и обрабатывается в соответствии с логикой:\n
        - `disable` — приостанавливает сервис и отправляет подтверждение клиенту. \n
        - `enable` — возобновляет сервис и отправляет подтверждение клиенту. \n
        - `close` или `restart` — останавливает сервис, добавляет соответствующую команду в список, отправляет подтверждение клиенту.
        В остальных случаях вызывается метод обработки запроса `_request_handler` и результат отправляется клиенту.
        
        При возникновении исключения выводится сообщение об ошибке, и клиентский сокет закрывается.

        Если в списке команд закрытия есть "restart", устанавливается флаг `need_restart`.

        """
        service_closing_commands = []
        while True:
            if len(self.connected_clients) == 0 and not self.server_is_open:
                break
            if len(self.connected_clients) == 0:
                continue
            while len(self.connected_clients) > 0:
                client_socket = self.connected_clients[0]
                self.connected_clients.pop(0)
                try:
                    request = self.__recv_msg(client_socket)
                    request = request.decode("utf-8")
                    print(f"Received: {request}")
                    if request.lower() == "disable":
                        self.pause()
                        self.__send_msg(client_socket, "disable success".encode("utf-8"))
                    elif request.lower() == "enable":
                        self.unpause()
                        self.__send_msg(client_socket, "enable success".encode("utf-8"))
                    elif request.lower() == "close" or request.lower() == "restart":
                        self.stop()
                        service_closing_commands.append(request.lower())
                        self.__send_msg(client_socket, ("beginning " + request.lower()).encode("utf-8"))
                    else:
                        result = self._request_handler(request)
                        self.__send_msg(client_socket, result.encode("utf-8"))
                except Exception as e:
                    print(f"Server error when handling client: {e}")
                finally:
                    client_socket.close()
        if len(service_closing_commands) > 0:
            if service_closing_commands[0] == "restart":
                self.need_restart = True


    # protected:
    @abstractmethod
    def _do_job(self):
        """
        Абстрактный метод для выполнения конкретной задачи сервиса. Должен быть переопределен.

        Реализация этого метода должна содержать логику выполнения работы сервиса.

        """
        pass

    @abstractmethod
    def _request_handler(self, request):
        """
        Абстрактный метод для обработки запросов от клиентов.

        :Параметры:
        - `request` — Запрос, полученный от клиента.

        Возвращает результат обработки запроса.

        """
        pass

    def _run_client(self, ip: str, port: int, request: str,
                    response_handler: Optional[Callable[[str], None]] = None) -> None:
        
        """
        Метод для запуска клиента и отправки запроса на сервер.
        :Параметры:
        - `ip (str)` — IP-адрес сервера.
        - `port (int)` — Порт сервера.
        - `request (str)` — Запрос для отправки на сервер.
        - `response_handler (Callable[[str], None], необязательно)` — Обработчик ответа от сервера.
        Создает сокет клиента, подключается к серверу, отправляет запрос и ожидает ответа.
        Если предоставлен обработчик ответа, вызывает его с полученным ответом.
        """

        global client
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, port))
            self.__send_msg(client, request.encode("utf-8"))
            response = self.__recv_msg(client)
            response = response.decode("utf-8")
            print(f"Received: {response}")
            if response_handler is not None:
                response_handler(response)
        except Exception as e:
            print(f"Client error when handling client: {e}")
        finally:
            client.close()
            print("Connection to server closed")


    # public:
    def run_client(self, ip: str, port: int, request: str, response_handler: Optional[Callable] = None) -> None:
        """
        Метод для запуска клиента в отдельном потоке.

        :Параметры:
        - `ip (str)` — IP-адрес сервера.
        - `port (int)` — Порт сервера.
        - `request (str)` — Запрос для отправки на сервер.
        - `response_handler (Callable, необязательно)` — Обработчик ответа от сервера.

        Создает новый поток для выполнения `_run_client` с указанными параметрами.

        """
        
        client_thread = threading.Thread(target=self._run_client, args=(ip, port, request, response_handler,))
        client_thread.start()

    def start(self) -> None:
        """
        Метод для запуска сервера.

        Инициализирует все необходимые параметры, создает сокет сервера и запускает потоки
        для выполнения работы сервиса, управления клиентами и прослушивания новых подключений.

        """
        self.need_job_break = False
        self.need_job_pause = True
        self.server_is_open = True
        self.need_restart = False
        self.connected_clients = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.settimeout(self.timeout)
        self.server.bind((self.ip, self.port))
        self.server.listen(self.n_conn)
        print(f"Listening on {self.ip}:{self.port}")

        job_thread = threading.Thread(target=self._do_job, args=())
        job_thread.start()

        client_managing_thread = threading.Thread(target=self.__manage_clients, args=())
        client_managing_thread.start()

        while self.server_is_open:
            try:
                client_socket, client_address = self.server.accept()
                print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
                self.connected_clients.append(client_socket)
            except socket.timeout:
                pass

        client_managing_thread.join()
        self.server.close()

        if self.need_restart:
            self.restart()


    def stop(self) -> None:
        """
        Метод для остановки сервера.

        Устанавливает флаги `server_is_open` и `need_job_break` в False для завершения циклов,
        управляющих сервером и выполнением работы.

        """
        self.server_is_open = False
        self.need_job_break = True

    def pause(self) -> None:
        """
        Метод для приостановки выполнения работы.

        Устанавливает флаг `need_job_pause` в False.

        """
        self.need_job_pause = False

    def unpause(self) -> None:
        """
        Метод для возобновления выполнения работы.

        Устанавливает флаг `need_job_pause` в True.

        """
        self.need_job_pause = True

    def restart(self) -> None:
        """
        Метод для перезапуска сервера.

        Инициализирует параметры для нового запуска, затем вызывает метод `start` для запуска сервера.

        """
        self.need_job_break = False
        self.need_job_pause = True
        self.server_is_open = True
        self.need_restart = False
        self.connected_clients = []
        self.start()
