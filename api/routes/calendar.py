from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import EventDB, User
from database.user_repository import get_or_create_user

router = APIRouter(prefix="/api/v1/calendar", tags=["Calendar"])


# Schemas Pydantic
class EventCreate(BaseModel):
    external_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    participants: List[str] = []
    priority: str = "medium"
    reminders: List[int] = []
    # String RRULE-like (ex: "FREQ=WEEKLY;INTERVAL=1"), o front-end é responsável
    # por traduzir isso para/de opções simples como "toda semana".
    recurrence: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    participants: Optional[List[str]] = None
    priority: Optional[str] = None
    reminders: Optional[List[int]] = None
    recurrence: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    participants: List[str] = []
    priority: str
    reminders: List[int] = []
    recurrence: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


@router.post("/events", response_model=EventResponse)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    user = get_or_create_user(db, event.external_id)

    db_event = EventDB(
        user_id=user.id,
        title=event.title,
        description=event.description,
        category=event.category,
        start_time=event.start_time,
        end_time=event.end_time,
        location=event.location,
        meeting_link=event.meeting_link,
        participants=event.participants,
        priority=event.priority,
        reminders=event.reminders,
        recurrence=event.recurrence,
        status="scheduled",
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.get("/events", response_model=List[EventResponse])
def get_events(external_id: str, date: Optional[str] = None, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    user = db.query(User).filter(User.external_id == external_id).first()
    if not user:
        return []

    query = db.query(EventDB).filter(EventDB.user_id == user.id)
    if date:
        # Simplificação para filtrar por dia
        start_of_day = datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_of_day = datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S")
        query = query.filter(EventDB.start_time >= start_of_day, EventDB.start_time <= end_of_day)

    return query.order_by(EventDB.start_time.asc()).all()


@router.put("/events/{event_id}", response_model=EventResponse)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    db_event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)
    return db_event


@router.delete("/events/{event_id}")
def cancel_event(event_id: int, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    db_event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    db_event.status = "cancelled"
    db.commit()
    return {"message": "Evento cancelado com sucesso."}
