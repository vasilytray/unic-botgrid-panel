# Создание собственного API на Python (FastAPI) 
(повторение туториалов от [Yakovenko Oleksii](https://github.com/Yakvenalex))
1. [Создание собственного API на Python (FastAPI): Знакомство и первые функции](https://habr.com/ru/companies/amvera/articles/826196/)
2. [Создание собственного API на Python (FastAPI): Гайд по POST, PUT, DELETE запросам и моделям Pydantic](https://habr.com/ru/articles/827134/)

## Знакомство и первые функции
### Установка зависимостей

```
pip install -r requirements.txt
```
Файл **app/auth/utils.py** - 
Пишем 2 простые функции. Первая **принимает список питоновских словарей**, создавая JSON файл. А вторая – **трансформирует JSON файл в список питоновских словарей**. 
Далее мы просто импортируем эту функцию в приложение FastApi

Пишем приложение (файл **app/main.py**):
- пропишем путь к JSON файлу и сохраним в переменной
- Создадим наше первое приложение:
```
app = FastAPI()
```
- Напишем функцию для главной страницы, ```@app.get("/") def home_page()```
- Напишем функцию, которая будет возвращать список из всех наших студентов ```@app.get("/students") def get_all_students()```
- Напишем функцию с параметрами пути для вывода студентов по курсу ```@app.get("/students/{course}") def get_all_students_course()```
- Добавим функцию с параметрами пути (path parameters) для идентификации ресурса (id студента) ```@app.get("/student/{student_id}") def get_all_students_course()```
- Добавим функцию с комбинированием параметров пути (курса) и запросов (специальность (major) и год 
поступления (enrollment_year)) ```@app.get("/students/{course}") def get_all_students_course()```

## Гайд по POST, PUT, DELETE запросам и моделям Pydantic

Во второй статье в качестве исходных данных создадим новый файл **students.json**
и перепишем в него из GitHub-а новые записи студентов с скорректированными параметрами. 
Для этого откроем коммиты проекта Туториала Алексея с коммитом "обновленный код под вторую статью".

Создадим  файл **app/auth/models.py**
- *Импорты*:

```python
from enum import Enum # для создания перечислений (enums).
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError # Pydantic используется для создания моделей данных и валидации.
from datetime import date, datetime # для работы с датами.
from typing import Optional # для указания необязательных полей.
import re # для использования регулярных выражений.
```
- Создадим класс перечисления валидных курсов ```class Major(str, Enum)```
- Создадим класс - модель **SStudent()** с описанием полей(field) и внутренними валидаторами.

```python
class SStudent(BaseModel): # Pydantic-схема, SS - дополнительная S говорит о том что добавил схему(модель)
```
### Внтуренние валидаторы полей в Pydantic

**ge:** Это сокращение от "greater than or equal" (больше или равно). Используется для установки минимального допустимого значения для числового поля. Если значение поля меньше указанного, будет вызвано исключение валидации.

**le:** Это сокращение от "less than or equal" (меньше или равно). Используется для установки максимального допустимого значения для числового поля. Если значение поля больше указанного, также будет вызвано исключение валидации.

**min_lenght**: описываем минимальную длину строки

**max_lenght**: описываем максимальную длину строки

**gt, ge, lt, le**: Ограничения для числовых значений (больше, больше или равно, меньше, меньше или равно).

**multiple_of**: Число, на которое значение должно быть кратно.

**max_digits, decimal_places**: Ограничения для чисел с плавающей точкой (максимальное количество цифр, количество десятичных знаков)

**title**: Заголовок поля. Используется для документации или автоматической генерации API.

**examples**: Примеры значений для поля. Используются для документации и обучения.

Подробнее в документации [Pydantic](https://docs.pydantic.dev/).

Добавим внутренний валидатор для номера телефона: ```@field_validator("phone_number") @classmethod def validate_phone_number(cls, values: str)```

Добавим валидатор для даты рождения: ``` @field_validator("date_of_birth") @classmethod def validate_date_of_birth(cls, values: date)```

### Pydantic модель и GET эндпоинт

Передалем модель ответа ```@app.get("/student")``` в **app/main.py** используя в качестве *response_model* (модель ответа) схему **SStudent**

```python
@app.get("/student")
def get_student_from_param_id(student_id: int) -> SStudent:
    students = json_to_dict_list(path_to_json)
    for student in students:
        if student["student_id"] == student_id:
            return student
```
Теперь, если информация о студенте, представленная в students.json не будет проходить валидацию,
мы получим ошибку сервера с расшифровкой ошибки (ожидалось - получили).

Изменим модель ответа ```@app.get("/students/{course}")``` в **app/main.py**  для списка студентов. Из модуля typing передаем List  и далее модель, говоря тем самым , что этот метод должен вернуть список студентов. и добавим ```request_body``` в обработчик параметров **course, major, enrollment_year**

```py
def get_all_students_course(course: int, major: Optional[str] = None, enrollment_year: Optional[int] = None) -> List[
    SStudent]
    ...
```

Оптимизируем передачу запросов аргументов (фильтров ) в адресе ссылки через создание класса с определением наших фильтров:

```py
class RBStudent:
    def __init__(self, course: int, major: Optional[str] = None, enrollment_year: Optional[int] = None):
        self.course: int = course
        self.major: Optional[str] = major
        self.enrollment_year: Optional[int] = enrollment_year
```

и передадим этот класс в наш эндпоинт, где выводим список студентов воспользоваться функцией Depends для обхода ошибки валидации поля ответа нашего класса ```app.main.RBStudent```:
```py
def get_all_students_course(request_body: RBStudent = Depends()) -> List[SStudent]:
    students = json_to_dict_list(path_to_json)
    ...
```

### POST метод в FastApi

Для дальнейшего изучения установим библиотеку json_db_lite и трансформируем наш JSON-файл со списком студентов в мини-базу.
```sh
pip install --upgrade json_db_lite
```
Смысл **POST** методов в том, чтоб отправить данные от клиента на сервер (базу данных). В качестве примера добавим нового студента в базу данных.

Для начала напишем функции, которые позволят нам имитировать работу с базой данных, изменим файл **app/auth/utils.py** (предыдущий файл utils.py переименуем в utils_ch1.py - мы его использовали в первой части, оставим для информации)

подробное описание каждого метода этой библиотеки описаны в статье [Новая библиотека для работы с JSON: json_db_lite](https://habr.com/ru/articles/826434/).

Теперь правильно напишем **POST** запрос, который будет принимать данные о студенте для добавления, после будет выполнять проверку их валидности, а затем, если все данные валидные, мы будем добавлять новое значение в нашу мини базу данных (add_student).
```py
@app.post("/add_student")
def add_student_handler(student: SStudent):
    student_dict = student.model_dump() # поскольку dict - depricated, используем madel_dump
    check = add_student(student_dict)
    if check:
        return {"message": "Студент успешно добавлен!"}
    else:
        return {"message": "Ошибка при добавлении студента"}
```
добавим  запрос вместе с импортом ```add_student``` в файл **model.py**
```py
from app.auth.utils import json_to_dict_list, add_student
```
и попробуем добавить нового студента, запустив FastAPI
```json
  {
    "student_id": 11,
    "phone_number": "+7016789",
    "first_name": "Ольга",
    "last_name": "Никитина",
    "date_of_birth": "1999-06-20",
    "email": "olga.nikitina@example.com",
    "address": "г. Томск, ул. Ленина, д. 60, кв. 18",
    "enrollment_year": 2018,
    "major": "Экология",
    "course": 3,
    "special_notes": "Без особых примет"
  }
```
1. первая попытка вернула ошибку с невалидным форматом телефонного номера.
2. сделаем номер валидным и повтрорим попытку добавить пользователя.
Действительно такой пользователь добавился, НО! уже есть такой с таким же ID, **нам необходимо сделать проверку на пользователя!**
Добавим проверку по существующему email:

1. Получаем текущий список студентов с помощью json_to_dict_list()
2. Проходим по всем существующим записям и сравниваем email (с приведением к нижнему регистру)
3. При обнаружении дубликата сразу возвращаем ошибку 400
4. Если дубликатов нет, вызываем add_student() и обрабатываем результат

```py
@app.post("/add_student")
def add_student_handler(student: SStudent):
    # Получаем список всех студентов для проверки на совпадение email
    students = json_to_dict_list()

    # Проверяем наличие дубликата email
    for existing_student in students:
        if existing_student["email"] == student.email: # .lower() - не используем потому что в Pydantic-схеме
            raise HTTPException(                       # уже автоматически приводится e-mail к нижнему регистру 
                status_code=400,                       # посредством email: EmailStr
                detail="Студент с таким email уже существует"
            )
    # Добавляем студента, если проверка пройдена
    student_dict = student.model_dump()
    check = add_student(student_dict)
    if check:
        return {"message": "Студент успешно добавлен!"}
    else:
        raise HTTPException(
            status_code=400, 
            detail="Ошибка при добавлении студента"
        )
```
проверка по e-mail теперь возвращает ошибку! Поменяем e-mail нового студента и повторим попытку:
в результате получаем ответ:
```json
{
  "message": "Студент успешно добавлен!"
}
```

### Обработка PUT методов в FastAPI

Обратимся в файле app/auth/utils.py к функции обновления данных ```def upd_student(upd_filter: dict, new_data: dict)```

И добавим в файл app/auth/model.py две модели:
```py
# Определение модели для фильтрации данных студента
class SUpdateFilter(BaseModel):
    student_id: int


# Определение модели для новых данных студента
class SStudentUpdate(BaseModel):
    course: int = Field(..., ge=1, le=5, description="Курс должен быть в диапазоне от 1 до 5")
    major: Optional[Major] = Field(..., description="Специальность студента")
```

Теперь добавим в main.py метод ```@app.put("/update_student") def update_student_handler(filter_student: SUpdateFilter, new_data: SStudentUpdate)```
и импортируем из **utils.py** ```upd_student``` и из **models.py** ```SUpdateFilter, SStudentUpdate```

Данный метод будет обновлять данные по конкретному студенту, принимая его ID. 

В новых данных мы должны будем передать курс и специальность студента.

```json
{
  "message": "Информация о студенте успешно обновлена!"
}
```

### Обработка DELETE запросов в FastAPI

В **utils.py** мы записали функцию удаления записи студента ```def dell_student(key: str, value: str)```

Добавим в  **models.py** модель не забыв импортировать из **typing** ```, Any```

```py
class SDeleteFilter(BaseModel):
    key: str
    value: Any
```

И теперь добавим функцию для удаления студента из списка не забыв импортировать ```SDeleteFilter``` из **models.py**
и ```dell_student``` из **utils.py**

```py
@app.delete("/delete_student")
def delete_student_handler(filter_student: SDeleteFilter)
...
```
запускаем и пробуем удалить студента.
обработчик возвращает успех, НО смотрим в JSON и видим, что запись на самом деле не удалена!
Проведем корректировку:


## Структура проекта, SQLAlchemy PostgreSQL, миграции и первые модели таблиц

Создадим новый проект под новую главу, дабы не терять того, что наработано и куда можно подсмотреть

Назову приложение app3 - т.к. это изучаю третью статью цикла
3. [Создание собственного API на Python (FastAPI): Структура проекта, SQLAlchemy PostgreSQL, миграции и первые модели таблиц](https://habr.com/ru/articles/827222/)

Структурируем наш проект:

### Зависимости проекта

- `fastapi[all]==0.115.0` - высокопроизводительный веб-фреймворк
- `pydantic==2.9.2` - валидация данных
- `pydantic-settings==2.8.0` - библиотека для хранения настроек
- `uvicorn==0.34.0` - ASGI-сервер
- `jinja2==3.1.4` - шаблонизатор
- `SQLAlchemy==2.0.35` - ORM для работы с базами данных
- `asyncpg==0.30.0` - асинхронная поддержка для PostgreSQL
- `alembic==1.13.3` - управление миграциями базы данных
- `loguru==0.7.2` - красивое и удобное логирование

### Структура проекта

Проект построен с учётом модульной архитектуры, что позволяет легко расширять приложение и упрощает его поддержку.
Каждый модуль отвечает за отдельные задачи, такие как авторизация или управление данными.

### Основная структура проекта

```
my_fastapi_project/
├── tests/
│   └── test.py                 # тут мы будем добавлять функции для Pytest
├── app/
│   ├── students/               # Модуль отвечающий за работу с данными студентов
│   │   ├── dao.py              # Data Access Object для работы с БД
│   │   ├── models.py           # Модели данных для авторизации
│   │   ├── router.py           # Роутеры FastAPI для маршрутизации
│   │   └── utils.py            # Вспомогательные функции для авторизации   
│   ├── migration/              # Миграции базы данных
│   │   ├── versions/           # Файлы миграций Alembic
│   │   ├── env.py              # Настройки среды для Alembic
│   │   ├── README              # Документация по миграциям
│   │   └── script.py.mako      # Шаблон для генерации миграций
│   ├── database.py             # Подключение к базе данных и управление сессиями    
│   ├── config.py               # Конфигурация приложения
│   └── main.py                 # Основной файл для запуска приложения
├── .venv/
│   └── .env                    # Конфигурация окружения
├── alembic.ini                 # Конфигурация Alembic
├── README.md                   # Документация проекта
└── requirements.txt            # Зависимости проекта
```

### Подготовка
1. Развернем базу данных в PostgreSQL локально в Docker - контейнере.
1.1. Поставим [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2.2. Создадим в корне проекта  файл docker-compose.yml 

```yml
version: '3.9'

services:
  postgres:
    image: postgres:latest
    container_name: postgres_container
    environment:
      POSTGRES_USER: amin
      POSTGRES_PASSWORD: my_super_password
      POSTGRES_DB: fast_api
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5430:5432"
    volumes:
      - ./pgdata:/var/lib/postgresql/data/pgdata
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    command: >
      postgres -c max_connections=1000
               -c shared_buffers=256MB
               -c effective_cache_size=768MB
               -c maintenance_work_mem=64MB
               -c checkpoint_completion_target=0.7
               -c wal_buffers=16MB
               -c default_statistics_target=100
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U postgres_user -d postgres_db" ]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
    tty: true
    stdin_open: true

volumes:
  pgdata:
    driver: local
```
#### Краткий обзор Docker Compose файла

1. services/postgres:

**image**: используемая Docker-образ PostgreSQL, в данном случае postgres:latest.

**container_name**: имя контейнера, в котором будет запущен PostgreSQL.

**environment**: переменные окружения для настройки PostgreSQL (пользователь, пароль, имя базы данных - не забудьте указать свои).

**ports**: проброс портов, где "5430:5432" означает, что порт PostgreSQL внутри контейнера (5432) проброшен на порт хоста (5430). Это значит что для подключения к постгрес нужно будет прописывать порт 5430.

**volumes**: монтируем локальный каталог ``./pgdata`` внутрь контейнера для сохранения данных PostgreSQL.

**deploy**: определяет ресурсы и стратегию развертывания для Docker Swarm (необязательно для стандартного использования Docker Compose).

**command**: дополнительные параметры командной строки PostgreSQL для настройки параметров производительности.

**healthcheck**: проверка состояния PostgreSQL с использованием pg_isready.

***restart, tty, stdin_open***: настройки перезапуска контейнера и взаимодействия с ним через терминал.

2. volumes/pgdata:

Определяет том **pgdata**, который используется для постоянного хранения данных PostgreSQL.

#### Запуск PostgreSQL

- Запустим Docker Desktop

- Выполняем команду 

```sh
docker-compose up -d
```

Эта команда запустит контейнер PostgreSQL в фоновом режиме **(-d)** на основе настроек, указанных в файле ``docker-compose.yml``

```sh
docker-compose up -d
time="2025-02-26T19:24:11+07:00" level=warning msg="C:\\www\\pyfapi\\unic\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
[+] Running 15/15
 ✔ postgres Pulled                                                                                                                          27.6s 
[+] Running 3/3
 ✔ Network unic_default         Created                                                                                                      0.2s 
 ✔ Volume "unic_pgdata"         Created                                                                                                      0.0s 
 ✔ Container postgres_fast_api  Started
```

Контейнер запущен и работает, подключемся к нему клиентом PgAdmin4 или DBeaver
указав данные базы и порт 5433 (мы выбрали его в настройках docker-compose.yml) в качестве порта для подключения к контейнеру

Установим необходимые зависимости:
```
pip install -r requirements.txt
```
### Описание моделей таблиц 

Создадим файл ``app/database.py`` nподключения к БД PostgreSQL

Для понимания коментарии к коду файла:

**create_async_engine**: создаёт асинхронное подключение к базе данных PostgreSQL, используя драйвер asyncpg.

**async_sessionmaker**: создаёт фабрику асинхронных сессий, используя созданный движок. Сессии используются для выполнения транзакций в базе данных.

**Base**: абстрактный класс, от которого наследуются все модели. Он используется для миграций и аккумулирует информацию обо всех моделях, чтобы ``Alembic`` мог создавать миграции для синхронизации структуры базы данных с моделями на бэкенде.· 

**@declared_attr.directive**: определяет имя таблицы для модели на основе имени класса, преобразуя его в нижний регистр и добавляя букву 's' в конце (например, класс User будет иметь таблицу users).

Дополнительно добавим настройку анотаций колонок

```py
int_pk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_true = Annotated[str, mapped_column(nullable=True)]
```
Данные аннотации колонок позволяют создавать кастомные шаблоны для описания колонок в SQLAlchemy. 

Этот механизм значительно сокращает дублирование кода, упрощая создание и поддержку моделей данных.

Кроме того дополним класс **Base**, добавив в него:

created_at: Mapped[created_at]
updated_at: Mapped[updated_at]
Теперь, в каждой создаваемой вами таблице будут появляться две колонки:

**created_at** — Дата и время создания записи. Описанная аннотация сделает так, чтоб на стороне базы данных вытягивалась дата с сервера, на котором база данных размещена: server_default=func.now().

**updated_at** — колонка, в которой будет фиксироваться текущая дата и время после обновления.

Теперь подготовим файл **app/config.py**, который опишет значения подключения к БД, передадим путь к .env файлу.
сгенерируем ссылку к БД.

Будем помещать отдельные сущности нашего API, такие как студенты или преподаватели, в отдельные папки. А внутри уже создавать файлы и папки, которые будут иметь отношение к конкретной сущности.

Теперь создадим папку и внутри нее файл **students/models.py** :

Создадим модель таблицы students и опишем колонки при этом в первой колонке значение id - это целое число, первичный ключ, да ещё и Autoincrement 
(передали не явно, так как в алхимии целое число, которое первичный ключ автоматически помечается автоинкрементным) 
и будет автоматически генерироваться и увеличиваться на единицу.

Bмя таблицы у нас генерируется автоматически и берется оно от названия класса

Обратим внимание на использование внешнего ключа:

```py
major_id: Mapped[int] = mapped_column(ForeignKey("majors.id"), nullable=False)
```
Данная запись в SQLAlchemy описывает колонку **major_id**, сообщая алхимии, что **major_id** является внешним ключом (**ForeignKey**) и ссылается на колонку id в таблице majors. Таким образом, **major_id** может хранить значения, которые существуют в колонке id таблицы **majors**

**class Major(Base):** Создает модель таблицы Major, которая наследуется от Base.
Обратим внимание на **count_students:** строка в которой будет храниться количество студентов. 

Запись ```server_default=text('0')``` в SQLAlchemy используется для установки значения по умолчанию для колонки на уровне базы данных с помощью SQL-выражения '0'.
 
__str__ и __repr__: Методы для удобного представления объектов модели в виде строки.

### Миграция в базу данных PostgreSQL

При помощи **Alembic** каждая из созданных моделей таблиц трансформируется в полноценную таблицу PostgreSQL со всеми данными и зависимостями, которые мы в них заложили.

Для создания миграций в дирректории «app» через консоль выполнить команду:
```sh
alembic init -t async migration
```
После выполнения данной команды будет сгенерирован файл **migrations/alembic.ini**. Для предложенной структуры проекта FastApi, необходимо выполнить следующее:

1. Перемещаем файл **alembic.ini** с папки **app** в корень проекта

2. В файле **alembic.ini** заменяем строку ```script_location=migration``` на ```script_location = app/migration```

Заходим в папку **migration**, которая появилась в дирректории app и там находим файл **env.py**.

Правим файл **env.py** следующим образом.

Добавляем в файл новые импорты:
```py
import sys
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(abspath(__file__))))

from app.database import DATABASE_URL, Base
from app.students.models import Student, Major
```
Далее нам необходимо добавить строку:

```config.set_main_option("sqlalchemy.url", DATABASE_URL)```
config: Это объект конфигурации Alembic (alembic.config.Config), который используется для управления параметрами и настройками миграций.

**set_main_option("sqlalchemy.url", DATABASE_URL):** Этот метод устанавливает основную опцию sqlalchemy.url в конфигурации Alembic. Он используется для указания URL, по которому Alembic будет подключаться к базе данных SQLAlchemy.

Заменим ``target_metadata = None`` на ``target_metadata = Base.metadata``

**Base.metadata:** Это атрибут metadata вашего базового класса SQLAlchemy (Base), который содержит информацию о структуре вашей базы данных.

Выполним свою первую миграцию (**revision**). Для этого необходимо в консоли вернуться в корень проекта. 
Далее вводим команду:
```sh
alembic revision --autogenerate -m "Initial revision"
```
Эта команда используется для автоматической генерации миграции базы данных с помощью **Alembic**.

#### Зачем используется флаг --autogenerate
- Автоматическое создание миграций:

   - Флаг ``--autogenerate`` позволяет **Alembic** анализировать текущее состояние базы данных и сравнивать его с определениями моделей SQLAlchemy. На основе этих сравнений Alembic генерирует код миграции, который включает изменения структуры базы данных (такие как создание новых таблиц, изменение существующих столбцов и т.д.).

- Упрощение процесса:

   -Автоматическая генерация миграций с флагом ``--autogenerate`` упрощает процесс управления изменениями в базе данных, особенно когда ваши модели данных SQLAlchemy изменяются. Это позволяет избежать ручного написания сложных SQL-запросов для каждого изменения.

- Как это работает:
1. Сравнение текущего состояния с моделями: Alembic анализирует текущую структуру базы данных и сравнивает её с определениями моделей SQLAlchemy, которые хранятся в ``target_metadata`` (как мы рассмотрели ранее).

2. Генерация миграционного скрипта: На основе выявленных различий Alembic автоматически генерирует код Python, который описывает необходимые изменения структуры базы данных.

3. Применение и откат миграций: Сгенерированный миграционный скрипт можно применить к базе данных с помощью команды ``alembic upgrade head``, а при необходимости выполнить откат изменений с помощью ``alembic downgrade``.

![автоматическая генерация миграции базы данных с помощью Alembic](/images/image.png)

В нижней строке описывается путь к сгенерированной версии миграции.

Тут стоит обратить внимание на важный момент. Функция upgrade не выполнится автоматически. Alembic, в данном случае, просто сгенерировал его, а для того чтоб ее запустить нам необходимо выполнить следующую команду:

```sh
alembic upgrade 07a1c361e3c2
```

Либо можно вместо ``revision_id`` выполнить команду:
```sh
alembic upgrade head
```
В таком случае подтянется самое последнее обновление и выполнится функция **upgrade**.

Теперь, если подключимся к базе данных, то увидим наши таблицы и таблицу alembic_version, в которой будут храниться ID миграций.

- Для отмены последнего изменения достаточно выполнить команду:

```sh
alembic downgrade -1
```

## Router и асинхронные запросы в PostgreSQL (SQLAlchemy)

Теперь немного дополним его следующим образом.

В каждую нашу отдельную сущность (к примеру это студенты, под которых мы выделили отдельную папку) нужно будет добавить файл router.py, schemas.py, rb.py и dao.py

### Router в FastApi

В FastAPI, Router — это инструмент, который помогает организовывать и группировать маршруты (пути) вашего веб-приложения. Представьте себе, что у вас есть несколько функций, каждая из которых отвечает за разные URL-адреса. Router позволяет вам собрать эти функции в одно место и затем добавить их в ваше основное приложение.

распишем новые файлы:

- В ``schemas.py`` разместим модели **Pydantic**
- В ``rb,py`` разместим классы, описывающие тело запроса
- В ``dao.py`` будем вносить индивидуальные функции, относящиеся к конкретной сущности. К примеру такой сущностью может выступить наши студенты и функции базы данных, которые относятся исключительно к студентам. DAO в контексте баз данных расшифровывается как «Data Access Object» (объект доступа к данным).

Также создадим папку **dao** в корне дирректории **app**, а внутрь мы положим файл **base.py**. В данном файле опишем класс с универсальными методами по работе с базой данных.

*Примеры такого метода:* получение записи по её id, получение всех записей, получение записей по определенному фильтру, удаление записи по определенному фильтру. 

После изменений наш проект будет выглядеть так:
my_fastapi_project/
├── tests/
│   └── (тут мы будем добавлять функции для Pytest)
├── .venv/
│   └── .env                    # Конфигурация окружения
├── app/
│   ├── database.py
│   ├── config.py
│   ├── main.py
│   ├── students/
│   |  ├── router.py
│   |  ├── schemas.py
│   |  ├── dao.py
│   |  └── rb.py
│   ├── dao/
│   |   └── base.py
│   └── migration/
│       └── (файлы миграций Alembic)
├── alembic.ini
├── README.md
└── requirements.txt

Теперь добавим в нашу базу первый факультет и первого студента. А после оформим наш первый простой Router со студентами, добавив в него один эндпоинт для получения данных с базы данных о всех студентах.

Логика:
1. Настраиваем роутер
2. Пишем простой эндпоинт для получения с базы данных информаци о студенте

Для начала импортируем нужные модули и настроим Router

#### Импорты:

```py
from fastapi import APIRouter 
from sqlalchemy import select 
from app.database import async_session_maker 
from app.students.models import Student
```
#### Настраиваем Router

```py
router = APIRouter(prefix='/students', tags=['Работа со студентами'])
```

router = APIRouter(...): Создает экземпляр APIRouter.

prefix='/students': Устанавливает префикс для всех маршрутов, определенных в этом роутере. Это означает, что все маршруты, добавленные к этому роутеру, будут начинаться с /students.

tags=['Работа со студентами']: Добавляет тег к роутеру, который будет использоваться в документации Swagger для группировки и описания маршрутов.

Напишем наш первый эндпоинт Router
```py
@router.get("/", summary="Получить всех студентов")
async def get_all_students():
    async with async_session_maker() as session: 
        query = select(Student)
        result = await session.execute(query)
        students = result.scalars().all()
        return students
```

Давайте разберем функцию get_all_students простыми словами, шаг за шагом.

Маршрут для получения всех студентов
@router.get("/", summary="Получить всех студентов")
Эта строка говорит FastAPI, что когда кто-то делает GET-запрос на адрес /students/, нужно выполнить функцию get_all_students(). Описание «Получить всех студентов» будет показано в документации.
Асинхронная функция
async def get_all_students():
Это начало асинхронной функции. Асинхронность позволяет обрабатывать несколько запросов одновременно, не блокируя другие операции.

Создание сессии
async with async_session_maker() as session:
Здесь создается асинхронная сессия для работы с базой данных. Эта сессия автоматически закроется после выполнения всех операций внутри блока with.

Создание запроса
``query = select(Student)``
Создается запрос для выбора всех записей из таблицы Student.

Выполнение запроса
``result = await session.execute(query)``
Запрос отправляется в базу данных, и результат сохраняется в переменной result.

Извлечение результатов
``students = result.scalars().all()``
Все строки результата запроса извлекаются и собираются в список. Каждый элемент этого списка представляет собой объект Student.

Возвращение результата
``return students``
Список студентов возвращается в виде JSON-ответа. FastAPI автоматически преобразует его в формат JSON.

Итог
Функция get_all_students делает следующее:
1. При получении GET-запроса на /students/ она открывает сессию с базой данных.
2. Создает запрос для получения всех студентов из базы данных.
3. Выполняет запрос и получает все записи.
4. Преобразует полученные записи в список объектов Student.
5. Возвращает этот список как JSON-ответ.

Таким образом, когда кто-то обращается к вашему API по адресу ``/students/``, он получает полный список всех студентов, зарегистрированных в системе.

#### Подключим Router

Для того чтобы созданный Router заработал, его необходимо подключить в файле **main.py**. Подключение выглядит следующим образом:

```py
from fastapi import FastAPI
from app.students.router import router as router_students


app = FastAPI()


@app.get("/") # эндпоинт главной страницы
def home_page():
    return {"message": "Привет, Все!"}


app.include_router(router_students) # подключить (включить) роутер
```

Теперь можно запустить наше FastAPI приложение (не забудьте подготовить данные в таблицах). Из корня проекта выполняем команду:

```sh
uvicorn app.main:app --reload --port 8005
```

Зайдем в документацию по адресу http://127.0.0.1:8000/docs и видим следующее:

![Получить список всех студентов](/images/students.png)

выполним функцию и получим  ответ и базы в формате JSON.

Но в эндпоинтах никто не пишет прямые запросы к базе данных, да и сам запрос было бы неплохо «прокачать», чтоб он ещё и фильтрованные значения возвращал.
Вынесем код взаимодействия с БД пока в файл dao.py
А в роутере ипортируем класс StudentDAO, указанный в dao.py с использованием @classmetod. Мы сможем теперь импортировать класс и обращаться через точку, не объявляя каждый раз объект класса.

Добавим модель ответа (response_model) в файл schemas.py с возможностями Pydantic/

Функцию для получения всех студентов было бы неплохо вынести в общий класс, так как большой разницы нет, хотим мы получить всех студентов, всех преподавателей или полные данные с любой другой таблицы.

Так мы и сделаем. Тем более мы уже подготовили под это дело специальный файл dao/base.py,
но для того, чтобы класс был универсальным, как минимум, нужно добавить возможность указания модели, с которой должен работать класс и нужно изменить название метода и переменных.

 После изменений код получил такой вид: 
 ```py
from sqlalchemy.future import select
from app.database import async_session_maker


class BaseDAO:
    model = None
    
    @classmethod
    async def find_all(cls):
        async with async_session_maker() as session:
            query = select(cls.model)
            result = await session.execute(query)
            return result.scalars().all()
```

Тут мы вынесли указание модели на уровень класса. Тем самым мы добавили возможность наследоваться от данного класса, передавая нужную модель (на примере далее это будет понятнее).

Далее мы дали более универсальное название методу и переменным.

Теперь классу StudentDAO необходимо наследоваться от созданного класса BaseDao.

Внесем небольшие изменения в класс BaseDao.
```py
class BaseDAO:
    model = None
    
    @classmethod
    async def find_all(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()
```

В этом коде:

Метод find_all класса BaseDAO теперь принимает неограниченное количество именованных аргументов через **filter_by.

Внутри метода проверяется наличие переданных фильтров. Если filter_by содержит какие-то аргументы (например, course=4 и enrollment_year=2018), то создается запрос select(cls.model).filter_by(**filter_by), который фильтрует записи по этим аргументам.

Если filter_by пуст или не указан, выполняется базовый запрос select(cls.model), который выбирает все записи без фильтрации.

Запрос выполняется в асинхронной сессии async_session_maker(), результат извлекается и возвращается в виде списка объектов.

Теперь метод find_all может использоваться с различными комбинациями фильтров, передаваемых в виде именованных аргументов или распакованных из словаря. 

Теперь немного изменим наш эндпоинт, передав в него тело запроса. Для начала напишем код в файл rb.py
```py
class RBStudent:
    def __init__(self, student_id: int | None = None,
                 course: int | None = None,
                 major_id: int | None = None,
                 enrollment_year: int | None = None):
        self.id = student_id
        self.course = course
        self.major_id = major_id
        self.enrollment_year = enrollment_year

        
    def to_dict(self) -> dict:
        data = {'id': self.id, 'course': self.course, 'major_id': self.major_id,
                'enrollment_year': self.enrollment_year}
        # Создаем копию словаря, чтобы избежать изменения словаря во время итерации
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
```

>Внимание. Все параметры тела запроса у нас не обязательные. 
Так-же, в данном классе вы можете увидеть метод, который возвращает данные в виде питоновского словаря. Это нам будет полезно, когда мы будем формировать наш SELECT запрос с фильтрами.

Метод организован таким образом, что если значение у любого поля будет None, то в финальный словарь оно не попадет.

Теперь было бы неплохо написать универсальную функцию, которая будет возвращать запись по id либо пускай она возвращает None если записи с таким id нет. В dao/base.py

```py
@classmethod
async def find_one_or_none_by_id(cls, data_id: int):
    async with async_session_maker() as session:
        query = select(cls.model).filter_by(id=data_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
```

тут подойдет интеграция в эндпоинт с параметром пути. Добавим в роутер
```py
@router.get("/{id}", summary="Получить одного студента по id")
async def get_student_by_id(student_id: int) -> SStudent | None:
    return await StudentDAO.find_one_or_none_by_id(student_id)
```

Отлично. Теперь давайте добавим метод, похожий на find_one_or_none_by_id, но пусть он принимает случайное значение (любой фильтр) и возвращает или одного студента или информацию о том, что студент с такими параметрами не найден.

```py
@classmethod
async def find_one_or_none(cls, **filter_by):
    async with async_session_maker() as session:
        query = select(cls.model).filter_by(**filter_by)
        result = await session.execute(query)
        return result.scalar_one_or_none()
```
Напишем эндпонит.

```py
@router.get("/by_filter", summary="Получить одного студента по фильтру")
async def get_student_by_filter(request_body: RBStudent = Depends()) -> SStudent | dict:
    rez = await StudentDAO.find_one_or_none(**request_body.to_dict())
    if rez is None:
        return {'message': f'Студент с указанными вами параметрами не найден!'}
    return rez
```

Это все круто, но что там с факультетами. Мы же не будем запоминать ID каждого факультета, а просто хотим получить такой расклад «Василий Петров — студент 2 курса факультета Информатики».

Перед тем как начать писать функции давайте немного изменим наши модели таблиц. Предлагаю добавить специальный метод в models.py (в ``class Student(Base)``), который будет превращать объект алхимии, который мы получаем при SELECT запросе в питоновский словарь.

Сделаем это по причине того, что, зачастую, удобнее работать со словарями, чем с объектами алхимии. К примеру, у словаря есть методы по добавлению, обновлению и удалению ключей. 

```py
    def to_dict(self):
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth,
            "email": self.email,
            "address": self.address,
            "enrollment_year": self.enrollment_year,
            "course": self.course,
            "special_notes": self.special_notes,
            "major_id": self.major_id
        }
```

Мы добавили метод to_dict, который просто будет трансформировать все полученные данные в простой словарь. В модель Major можем метод не добавлять.

Добавление метода to_dict() в класс Student не оказывает никакого влияния на структуру таблицы в базе данных. Этот метод представляет собой чисто программистский удобный интерфейс для преобразования объекта Student в формат словаря, что упрощает его использование в различных частях вашего приложения, таких как сериализация в JSON для API или вывод в консоль для отладки.

Теперь давайте добавим эксклюзивный метод в файл dao.py, который будет возвращать полную информацию о студенте с названием факультета.

 Файл students/dao.py:
```py
class StudentDAO(BaseDAO):
    model = Student

    @classmethod
    async def find_full_data(cls, student_id: int):
        async with async_session_maker() as session:
            # Первый запрос для получения информации о студенте
            query_student = select(cls.model).filter_by(id=student_id)
            result_student = await session.execute(query_student)
            student_info = result_student.scalar_one_or_none()

            # Если студент не найден, возвращаем None
            if not student_info:
                return None

            # Второй запрос для получения информации о специальности
            query_major = select(Major).filter_by(id=student_info.major_id)
            result_major = await session.execute(query_major)
            major_info = result_major.scalar_one()

            student_data = student_info.to_dict()
            student_data['major'] = major_info.major_name

            return student_data
```
Обратите внимание. Тут мы, сначала, проверили есть ли у нас студент с указанным id. Если его нет, то сценарий сразу остановится.

В случае же если студент есть, то мы автоматически тянем информацию по его факультету. Мы можем это делать с уверенностью, так как в таблице со студентами есть прямая связь с таблицей факультетов (ForeignKey)

Так как у нас добавилось новое поле — давайте изменим Pydantic модель Sstudent (``/students/schemas.py``). В нее нам необходимо добавить описание всего одного поля:
```py
major: Optional[str] = Field(..., description="Название факультета")
```
Напоминаю, что данное описание говорит, что поле major обязательное.

Теперь внесем правки в эндпоинт.
```py
@router.get("/{id}", summary="Получить одного студента по id")
async def get_student_by_id(student_id: int) -> SStudent | dict:
    rez = await StudentDAO.find_full_data(student_id)
    if rez is None:
        return {'message': f'Студент с ID {student_id} не найден!'}
    return rez
```
Запускаем и проверяем.

my_fastapi_project/

├── tests/
│   └── (тут мы будем добавлять функции для Pytest)
├── app/
│   ├── database.py
│   ├── config.py
│   ├── main.py
│   ├── majors/
│   │  ├── router.py
│   │  ├── schemas.py
│   │  ├── dao.py
│   │  └── rb.py
│   ├── students/
│   │  ├── router.py
│   │  ├── schemas.py
│   │  ├── dao.py
│   │  └── rb.py
│   ├── dao/
│   │   └── base.py
│   └── migration/
│       └── (файлы миграций Alembic)
├── alembic.ini
├── .env
└── requirements.txt

### Добавление данных (POST)

Напоминаю, что в нашей базе данных пока 2 таблицы: students и majors. При чем студента мы не сможем добавить с несуществующим факультетом. Это говорит о том, что нужно сначала добавить факультет, а после добавлять студента.

Технически, и добавление факультета и добавление студента — это не более чем одинаковые действия (за исключением обновления счетчика студентов в таблице факультетов, но об этом чуть далее):

принимаем данные

записываем их в таблицу

Но сущностей у нас, по сути, две. Следовательно, для чистоты кода мы можем разделить факультеты и студентов на две папки.

После изменений структура проекта будет следующей:


 удалил таблицы с базы данных и все файлы с папки migration/versions

Теперь выполняем команду из корня проекта:

alembic revision --autogenerate -m "Initial revision"
Теперь выполним upgrade:

alembic upgrade head
После этого мы получили новые файлы, а вы теперь знаете как легко и просто расширять проект. В дальнейшем, при появлении новых папок, делайте следующее:

Создаете папку

Наполняете ее файлами

Описываете модели

В файле migration/env.py добавляете корректные импорты моделей как на примере выше

Добавляете миграцию (ревизию)

Обновляете

Придерживайтесь такого алгоритма и у вас не будет никаких проблем, как с расширением проекта, так и с миграциями через Alembic.

Мы можем сделать универсальный метод для добавления данных в таблицу.

В файл dao/base.py добавим следующее:
```py
@classmethod
async def add(cls, **values):
    async with async_session_maker() as session:
        async with session.begin():
            new_instance = cls.model(**values)
            session.add(new_instance)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                raise e
            return new_instance

```

Короткие комментарии:

- Создаем асинхронную сессию.
- Начинаем транзакцию.
- Создаем новый экземпляр модели с переданными значениями.
- Добавляем новый экземпляр в сессию.
- Пытаемся зафиксировать изменения в базе данных.
- В случае ошибки откатываем транзакцию и пробрасываем исключение дальше.
- Возвращаем созданный экземпляр.

Тут важно понять, что если мы не будем выполнять commit, то изменения в базе данных не сохраняться.

Сам метод будет принимать некий массив данных (словарь), который мы после распакуем и добавим.

Метод add будет работать и без блока ``async with session.begin()``, но он добавляет важное преимущество, обеспечивая управление транзакциями.

Управление транзакциями:

- Блок async with session.begin() автоматически начинает транзакцию и завершает её после выхода из блока, что гарантирует целостность данных.
- Без этого блока вам нужно вручную начинать и завершать транзакцию.
- Если вы хотите упростить метод и отказаться от использования блока async with session.begin(), вам нужно будет явно управлять транзакциями.

Для простоты опишем Router из папки majors на добавление факультетов. Но, для начала, опишем модель Pydantic для добавления.

Тут сразу хочу обратить внимание на один момент. Обычно отдельно описываются модели для добавления данных и для их получения, что, в целом, логично.

Мы будем делать так-же. В своих проектах я обычно добавляю в название схемы пометку Add и Get. Удобно.

Напишем модель (файл majors/schemas.py):
```py
from pydantic import BaseModel, Field


class SMajorsAdd(BaseModel):
    major_name: str = Field(..., description="Название факультета")
    major_description: str = Field(None, description="Описание факультета")
    count_students: int = Field(0, description="Количество студентов"
```

Тут мы не указывали id, так как наша база данных его и так сформирует.

Теперь напишем Router для обработки POST запроса (файл majors/router.py)
```py
from fastapi import APIRouter
from app.majors.dao import MajorsDAO
from app.majors.schemas import SMajorsAdd


router = APIRouter(prefix='/majors', tags=['Работа с факультетами'])


@router.post("/add/")
async def register_user(major: SMajorsAdd) -> dict:
    check = await MajorsDAO.add(**major.dict())
    if check:
        return {"message": "Факультет успешно добавлен!", "major": major}
    else:
        return {"message": "Ошибка при добавлении факультета!"}
```

Подключим новый роутер в файл app/main.py:
```py
from fastapi import FastAPI
from app.students.router import router as router_students
from app.majors.router import router as router_majors

app = FastAPI()


@app.get("/")
def home_page():
    return {"message": "Привет, Хабр!"}


app.include_router(router_students)
app.include_router(router_majors)

```
Тестируем

Загрузим файл .json со списком студентов 
```sh
curl -X 'POST' \
  'http://127.0.0.1:8005/majors/add/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -F "file=@students_1part.json"
  ```


Загружем несколько факультетов черех bash
```bash
curl -X 'POST' \
  'http://127.0.0.1:8005/majors/add/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "majors": [
    {
      "major_name": "История",
      "major_description": "Здесь учат опыту",
      "count_students": 0
    },
    {
      "major_name": "Биология",
      "major_description": "Здесь учат на биологов",
      "count_students": 0
    },
    {
      "major_name": "Психология",
      "major_description": "Здесь учат понимать себя и людей",
      "count_students": 0
    },
    {
      "major_name": "Экология",
      "major_description": "Здесь учат береч людей",
      "count_students": 0
    }
  ]
}'
```