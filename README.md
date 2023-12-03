## Сервис распознавания жестов
В рамках курса Современные интеллектуальные сетевые сервисы был разработан сервис, осуществляющий распознавание жестов и их отправку другим сервисам.

#### Настройка

1. Открыть командную строку в папке сервиса
2. Создать виртуальное окружение: python -m venv путь_до_окружения (пример пути: c:\path\to\myenv)
3. Активировать окружение: путь_до_окружения\Scripts\activate
4. Выполнить команду: pip install -r requirements.txt
5. Загрузить веса модели в папку сервиса по ссылке: https://disk.yandex.ru/d/zBgwPO1SKkC_0A 

#### Работа с сервисом

1. Запустить файл service\run.py
2. Включить камеру
3. Начать показывать жесты. Пример жестов находится в папке images

#### Дополнительно

Методы для работы с сервисом приведены в файле list_of_methods.txt

Документация по модулям: https://gesture-recognition-service.readthedocs.io/ru/latest/index.html
