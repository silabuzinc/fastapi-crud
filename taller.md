# Taller

En este taller crearemos una ToDo API con FastAPI.

Lo primero que haremos será crear un entorno virtual.

```console
python -m venv venv

venv/Scripts/activate
```

Instalamos FastAPI y uvicorn

```console
pip install fastapi
pip install uvicorn
```

Entonces, procederemos a crear nuestra ruta raíz, creamos el archivo `app.py`, el cual contendrá lo siguiente:

```py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello":"World"}
```

Ahora para ejecutar nuestra aplicación, dentro de la consola ejecutamos:

```console
uvicorn app:app --reload
```

Con esto tenemos el servidor que se actualiza acorde a los cambios.

## Creando modelo

Para poder crear nuestro modelo ToDo, primero mostraremos el resultado final:

```py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Text
from datetime import datetime

app = FastAPI()

class Todo(BaseModel):
    id: int
    title: str
    author: str
    body: Text
    completed: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime

# get route
```

Lo primer que hacemos es importar Pydantic, Text (que es un tipo de dato) y datetime. Nuestro modelo es muy similar a los desarrollados en flask, con la diferencia que en este caso unicamente definimos los tipos de datos que es cada campo.

¿Cómo añadimos campos opcionales? El body no siempre va a estar presente, entonces como le indicamos al modelo que este es un campo opcional, para esto importaremos `Optional` desde `typing`.

```py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Text, Optional
from datetime import datetime

app = FastAPI()

class Todo(BaseModel):
    id: int
    title: Optional[str]
    author: str
    body: Text
    completed: bool = False
    created_at: datetime = datetime.now()
    updated_at: Optional[datetime]

# get route
```

## Creando rutas

Primero añadiremos la ruta de tipo post, la ruta será la siguiente:

```py
@app.post('/create_todo')
def create_todo(todo: Todo):
    print(todo)
    return "recieved"
```

Con esto, podemos probar nuestra primera ruta, utilizaremos el siguiente JSON.

```json
{
  "id": 0,
  "title": "Todo 1",
  "author": "Author 1",
  "body": "Body",
  "completed": false,
  "created_at": "2023-01-27T00:24:58.143951",
  "updated_at": "2023-01-27T05:25:46.399Z"
}
```

> Realizar la prueba mediante un API Client

Si nos damos cuenta el parámetro de la función es el body que enviamos con los tipos que definimos.

## Conectando a una base de datos

Para hacer la conexión, lo realizaremos mediante SQLAlchemy, por lo que primero debemos instalarla.

```console
pip install sqlalchemy
```

Ahora, en la ruta raíz, crearemos el archivo `database.py` el cual contendrá lo siguiente:

```py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

Por temas prácticos haremos uso de SQlite.

### Nuevos modelos

Ahora como tenemos conectada nuestra base de datos, no podemos tener nuestros modelos unicamente con tipos. Por lo que, tendremos que actualizarlas acorde a SQLAlchemy. Para este caso, añadiremos el modelo `User`.

Primero, creamos el archivo `models.py`, el cual contendrá lo siguiente:

```py
from typing import Text, Optional
from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    todos = relationship("Todo", back_populates="author")

class Todo(Base):
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False )
    body = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    author_id = Column(Integer, ForeignKey("users.id"))
    
    author = relationship("User", back_populates="todos")
```

Con `author_id` realizamos la referencia de nuestra llave foránea.

### Creando Schemas

Crearemos el archivo `schemas.py`, el cual contednrá el siguiente código:

```py
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
```

* `TodoBase` y `UserBase`, son netamente para definir atributos que compartirán todas las opciones del CRUD.

* `class Config` define configuración adicional para Pydantic.

* `orm_mode` indica a Pydantic que debe leer los dato, incluso si no son un diccionario.

* `Todos: list[Todo] = []` define la lista de Todos con los que cuenta el usuario

### CRUD utilities

Creamos el archivo `crud.py`, el cual contendrá lo siguiente:

```py
from sqlalchemy.orm import Session
import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_todos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Todo).offset(skip).limit(limit).all()

def create_user_todo(db: Session, todo: schemas.TodoCreate, user_id: int):
    db_todo = models.Todo(**todo.dict(), author_id=user_id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo
```

### Creación de tablas

Es muy simple hacer la creación de tablas dentro de nuestra base de datos, `app.py` debe quedar de la siguiente forma:

```py
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import crud, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

La creación de tabla se da con la siguiente línea:

```py
models.Base.metadata.create_all(bind=engine)
```

Necesitamos tener una sesión/conexión de base de datos independiente (SessionLocal) por solicitud, usar la misma sesión en todas las solicitudes y luego cerrarla después de que finalice la solicitud.

### Rutas del CRUD

Añadiremos al final de `app.py` las rutas de nuestro CRUD.

```py
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/todos/", response_model=schemas.Todo)
def create_todo_for_user(
    user_id: int, todo: schemas.TodoCreate, db: Session = Depends(get_db)
):
    return crud.create_user_todo(db=db, todo=todo, user_id=user_id)


@app.get("/todos/", response_model=list[schemas.Todo])
def read_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    todos = crud.get_todos(db, skip=skip, limit=limit)
    return todos
```

## Tarea

* Probar todas las rutas del CRUD, en caso no les haya funciona aquí el repositorio del proyecto:

  * [CRUD FastAPI]()

* Pasar de SQLite a PosgreSQL de Docker

* Revisar documentación acerca de FastAPI: [documentación](https://fastapi.tiangolo.com/)
