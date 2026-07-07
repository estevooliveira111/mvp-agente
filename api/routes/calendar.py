from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from database.database import get_db
from database.models import EventDB
from sqlalchemy.orm import Session
import json

router = APIRouter(prefix="/api/v1/calendar", tags=["Calendar"])

# Schemas Pydantic
class EventCreate(BaseModel):
    user_id: int
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

class EventResponse(EventCreate):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True

@router.post("/events", response_model=EventResponse)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = EventDB(
        user_id=event.user_id,
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
        status="scheduled"
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/events", response_model=List[EventResponse])
def get_events(user_id: int, date: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(EventDB).filter(EventDB.user_id == user_id)
    if date:
        # Simplificação para filtrar por dia
        start_of_day = datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_of_day = datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S")
        query = query.filter(EventDB.start_time >= start_of_day, EventDB.start_time <= end_of_day)
        
    return query.all()

@router.delete("/events/{event_id}")
def cancel_event(event_id: int, db: Session = Depends(get_db)):
    db_event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    db_event.status = "cancelled"
    db.commit()
    return {"message": "Event cancelled successfully"}
