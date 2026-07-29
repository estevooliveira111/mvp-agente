from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy.orm import Session

from core.auth import get_current_user
from database.database import get_db
from database.models import EventDB, User

router = APIRouter(prefix="/api/v1/calendar", tags=["Calendar"])


# Schemas Pydantic
class EventCreate(BaseModel):
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

    @model_validator(mode="after")
    def check_end_after_start(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time deve ser posterior a start_time.")
        return self


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

    @model_validator(mode="after")
    def check_end_after_start(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time deve ser posterior a start_time.")
        return self


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

    model_config = ConfigDict(from_attributes=True)


@router.post("/events", response_model=EventResponse)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    db_event = EventDB(
        user_id=current_user.id,
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
def get_events(
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    query = db.query(EventDB).filter(EventDB.user_id == current_user.id)
    if date:
        # Simplificação para filtrar por dia
        try:
            start_of_day = datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S")
            end_of_day = datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Parâmetro 'date' inválido. Use o formato 'YYYY-MM-DD'.",
            )
        query = query.filter(EventDB.start_time >= start_of_day, EventDB.start_time <= end_of_day)

    return query.order_by(EventDB.start_time.asc()).all()


@router.put("/events/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    db_event = (
        db.query(EventDB)
        .filter(EventDB.id == event_id, EventDB.user_id == current_user.id)
        .first()
    )
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)
    return db_event


@router.delete("/events/{event_id}")
def cancel_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    db_event = (
        db.query(EventDB)
        .filter(EventDB.id == event_id, EventDB.user_id == current_user.id)
        .first()
    )
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    db_event.status = "cancelled"
    db.commit()
    return {"message": "Evento cancelado com sucesso."}
