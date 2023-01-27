from typing import Union
from pydantic import BaseModel

class TodoBase(BaseModel):
    title: str
    body: Union[str, None] = None

class TodoCreate(TodoBase):
    pass

class Todo(TodoBase):
    id: int
    author_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    Todos: list[Todo] = []

    class Config:
        orm_mode = True