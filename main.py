from fastapi import FastAPI, HTTPException, Depends, Response
from typing import List, Optional, Dict, Annotated
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    uname:str
    name:str
    password:str
    email:str
    role:str
class User(UserCreate):
    id:int
class ClubCreate(BaseModel):
    name:str
    description:str
class Club(ClubCreate):
    id:int
class EventCreate(BaseModel):
    club_id:int
    title:str
    date:str
class Event(EventCreate):
    id:int



#WORK WITH DATABASE

from sqlalchemy import select, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


engine = create_async_engine('sqlite+aiosqlite:///campus.db')
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
    role: Mapped[str]
class ClubModel(Base):
    __tablename__ = "clubs"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str]
class EventModel(Base):
    __tablename__ = "events"
    id: Mapped[int]=mapped_column(primary_key=True)
    club_id: Mapped[int]=mapped_column(ForeignKey('clubs.id'))
    title: Mapped[str]
    date: Mapped[str]
class RegistrationModel(Base):
    __tablename__ = "registrations"
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey('users.id'))
    event_id: Mapped[int]=mapped_column(ForeignKey('events.id'))

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
        email=user.email,
        role=user.role
    )
    session.add(new_user)
    await session.commit()
    return {"ok":True, "data":new_user}
@app.get("/users")
async def user_get(session:SessionDep):
    query = select(UserModel)
    result = await session.execute(query)
    return result.scalars().all()
@app.post("/clubs/add")
async def club_add(club: ClubCreate, session:SessionDep):
    new_club=ClubModel(
        name=club.name,
        description=club.description,
    )
    session.add(new_club)
    await session.commit()
    return {"ok":True, "data":new_club}
@app.get("/clubs")
async def clubs_get(session:SessionDep):
    query = select(ClubModel)
    result = await session.execute(query)
    return result.scalars().all()
@app.post("/events/add")
async def event_add(event: EventCreate, session:SessionDep):
    new_event=EventModel(
        club_id=event.club_id,
        title=event.title,
        date=event.date,
    )
    session.add(new_event)
    await session.commit()
    return {"ok":True, "data":new_event}
@app.get("/events")
async def events_get(session:SessionDep):
    query = select(EventModel)
    result = await session.execute(query)
    return result.scalars().all()
@app.post("/event/{event_id}/register/{user_id}")
async def event_register(event_id: int, user_id: int, session:SessionDep):
    event = await session.get(EventModel, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    new_reg=RegistrationModel(
        user_id=user_id,
        event_id=event_id
    )
    session.add(new_reg)
    await session.commit()
    return {"ok":True, "data":new_reg}

#AUTHORIZATION (LOGIN)

from authx import AuthX, AuthXConfig
from dotenv import load_dotenv
import os

config = AuthXConfig()
load_dotenv()
config.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
config.JWT_ACCESS_COOKIE_NAME="access_token"
config.JWT_TOKEN_LOCATION=["cookies"]

security=AuthX(config=config)

class UserLogin(BaseModel):
    username: str
    password: str
@app.post("/login")
async def user_login(creds: UserLogin, session:SessionDep, response:Response):
    query = select(UserModel).where(UserModel.uname == creds.username)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username")
    if user.password != creds.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    token=security.create_access_token(uid=str(user.id))
    response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
    return {"access_token": token}

#SWAGGER AUTH
#from fastapi.security import OAuth2PasswordBearer

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

#sessiondep2=Annotated[str, Depends(oauth2_scheme)]

#@app.post("/login")
#async def user_login():
   #return {"access_token": "supersecrettoken", "token_type": "bearer"}

#@app.get("/login")
#async def user_login(token: sessiondep2):
    #return {"token": token}



