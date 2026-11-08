# Task List API

Небольшой REST API для списка задач на FastAPI и SQLite. Подходит как стартовый пример CRUD-сервиса и интеграции с API.

## Возможности

- создать задачу;
- получить список всех задач или отфильтровать по статусу;
- изменить название или статус выполнения;
- удалить задачу;
- интерактивная документация Swagger UI.

## Запуск на Windows, macOS или Linux

```bash
python -m venv .venv
```

Активируйте окружение (`.venv\\Scripts\\activate` в Windows или `source .venv/bin/activate` в macOS/Linux), затем:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Откройте `http://127.0.0.1:8000/docs`. База `tasks.db` создаётся автоматически рядом с приложением при запуске.

## Примеры запросов

Создать задачу:

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Разобрать CSV-файл"}'
```

Получить только незавершённые задачи: `GET /tasks?done=false`  
Отметить задачу выполненной: `PATCH /tasks/1` с JSON `{"done":true}`  
Удалить задачу: `DELETE /tasks/1`

> Демонстрационный проект для портфолио. Для публичного развёртывания потребуется добавить аутентификацию и настроить резервное копирование базы.
