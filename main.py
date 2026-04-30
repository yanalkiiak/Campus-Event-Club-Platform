from fastapi import FastAPI, HTTPException, Depends
from typing import List, Optional, Dict, Annotated
from pydantic import BaseModel

#WORK WITH CRUD
app = FastAPI()

class UserCreate(BaseModel):
    uname:str
    name:str
    password:str
    email:str
class User(UserCreate):
    id:int

@app.get("/")
async def home() -> dict[str, str]:
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

users=[{"id":1,"uname":"yana18","name":"Yana","password":"1234","email":"y@ukd"},
       {"id":2,"uname":"oleg18","name":"Oleg","password":"1234gg","email":"ol@ukd"},
       {"id":3,"uname":"roma2007","name":"Roma","password":"1g200j","email":"roma@ukd.com"}]
@app.get("/users")
async def user()->List[User]:
    return(User(**i) for i in users)

@app.get("/users/{id}")
async def user(id: int) -> User:
    for i in users:
        if i['id'] == id:
            return User(**i)
    raise HTTPException(status_code=404, detail="User not found")

@app.get('/search')
async def search(user_id: Optional[str]=None) -> Dict[str, Optional[User]]:
    if user_id:
        for i in users:
            if i['id'] == user_id:
                return {"data":User(**i)}
        raise HTTPException(status_code=404, detail="User not found")
    else:
        return {"info": None}

@app.post("/users/add")
async def users_add(user: UserCreate) -> User:
    new_user_id=len(users)+1
    new_user={"id":new_user_id,"uname":user.uname, "name":user.name, "password":user.password, "email":user.email}
    users.append(new_user)
    return User(**new_user)
@app.put("/users/update/{id}")
async def users_update(id: int, user: UserCreate):
    users[id]=user
    return {"Message":f"User {id} updated"}

@app.delete("/users/delete/{id}")
async def users_delete(id: int):
    users.pop(id)
    return {"Message":f"User with id {id} deleted"}

#WORK WITH DATABASE

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

engine = create_async_engine('sqlite+aiosqlite:///users.db')
new_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_session():
    async with new_session() as session:
        yield session

SessionDep=Annotated[AsyncSession, Depends(get_session)]

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int]=mapped_column(primary_key=True)
    uname: Mapped[str]
    name: Mapped[str]
    password: Mapped[str]
    email: Mapped[str]

@app.post("/setup_db")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return {"ok": True}
@app.post("/user/add")
async def user_add(user: UserCreate, session:SessionDep):
    new_user=UserModel(
        uname=user.uname,
        name=user.name,
        password=user.password,
        email=user.email
    )
    session.add(new_user)
    await session.commit()
    return {"ok":True, "data":new_user}
@app.get("/added_users")
async def user_get(session:SessionDep):
    query = select(UserModel)
    result = await session.execute(query)
    return result.scalars().all()

#AUTHORIZATION (LOGIN)

from authx import AuthX, AuthXConfig

config = AuthXConfig()
config.JWT_SECRET_KEY="SECRET_KEY"
config.JWT_ACCESS_COOKIE_NAME="access_token"
config.JWT_TOKEN_LOCATION=["cookies"]

security=AuthX(config=config)

class UserLogin(BaseModel):
    username: str
    password: str

#SWAGGER AUTH
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

sessiondep2=Annotated[str, Depends(oauth2_scheme)]

@app.post("/login")
async def user_login():
   return {"access_token": "supersecrettoken", "token_type": "bearer"}

@app.get("/login")
async def user_login(token: sessiondep2):
    return {"token": token}



