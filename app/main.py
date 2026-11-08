from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator


DATABASE = Path(__file__).with_name("tasks.db")


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
            )
            """
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Task List API",
    description="Небольшой REST API списка задач на FastAPI и SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Название не должно быть пустым.")
        return value


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    done: bool | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Название не может быть null.")
        value = value.strip()
        if not value:
            raise ValueError("Название не должно быть пустым.")
        return value


def serialize(row: sqlite3.Row) -> dict[str, object]:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks(
    done: Annotated[bool | None, Query(description="Фильтр по статусу выполнения")] = None,
) -> list[dict[str, object]]:
    query = "SELECT id, title, done FROM tasks"
    parameters: tuple[object, ...] = ()
    if done is not None:
        query += " WHERE done = ?"
        parameters = (int(done),)
    query += " ORDER BY id"
    with connect() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [serialize(row) for row in rows]


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate) -> dict[str, object]:
    with connect() as connection:
        cursor = connection.execute("INSERT INTO tasks (title) VALUES (?)", (task.title.strip(),))
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    assert row is not None
    return serialize(row)


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, changes: TaskUpdate) -> dict[str, object]:
    updates = changes.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Укажите хотя бы одно поле для изменения.")
    if "done" in updates and updates["done"] is None:
        raise HTTPException(status_code=422, detail="Поле done не может быть null.")
    if "done" in updates and updates["done"] is not None:
        updates["done"] = int(updates["done"])

    allowed_columns = {"title", "done"}
    assignments = ", ".join(f"{column} = ?" for column in updates if column in allowed_columns)
    values = tuple(updates.values()) + (task_id,)
    with connect() as connection:
        cursor = connection.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", values)
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Задача не найдена.")
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    assert row is not None
    return serialize(row)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> Response:
    with connect() as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Задача не найдена.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
