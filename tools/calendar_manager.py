import json
from datetime import datetime
from database.database import SessionLocal
from database.models import EventDB

tool_metadata = {
    "name": "calendar_manager",
    "description": "Gerencia a agenda do usuário. Permite consultar disponibilidade, criar compromissos, listar eventos e buscar eventos importantes. Sempre utilize esta ferramenta para qualquer assunto relacionado a datas, compromissos ou horários.",
    "parameters": {
        "action": "A ação a ser executada. Obrigatório. Valores permitidos: 'check_availability', 'create_event', 'list_events', 'cancel_event', 'get_important_events'.",
        "user_id": "ID do usuário (int). Se não souber, envie 1 como padrão.",
        "title": "Título do evento (string) - Necessário para 'create_event'.",
        "start_time": "Data e hora de início no formato 'YYYY-MM-DD HH:MM:SS' - Necessário para 'create_event' e 'check_availability'.",
        "end_time": "Data e hora de término no formato 'YYYY-MM-DD HH:MM:SS' - Necessário para 'create_event' e 'check_availability'.",
        "date": "Data no formato 'YYYY-MM-DD' - Necessário para 'list_events'.",
        "event_id": "ID do evento (int) - Necessário para 'cancel_event'."
    }
}

def execute(arguments: dict) -> str:
    """
    Executa a ferramenta da Agenda baseada na ação informada.
    """
    action = arguments.get("action")
    user_id = arguments.get("user_id", 1)  # Mocked user 1 if not provided
    
    if not action:
        return json.dumps({"status": "error", "message": "Parâmetro 'action' é obrigatório."})
        
    db = SessionLocal()
    
    try:
        if action == "list_events":
            date_str = arguments.get("date")
            if not date_str:
                return json.dumps({"status": "error", "message": "Falta o parâmetro 'date'."})
            
            start_of_day = datetime.strptime(f"{date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            end_of_day = datetime.strptime(f"{date_str} 23:59:59", "%Y-%m-%d %H:%M:%S")
            
            events = db.query(EventDB).filter(
                EventDB.user_id == user_id,
                EventDB.start_time >= start_of_day,
                EventDB.start_time <= end_of_day,
                EventDB.status != "cancelled"
            ).all()
            
            if not events:
                return json.dumps({"status": "success", "message": f"Nenhum evento agendado para {date_str}."})
                
            results = []
            for e in events:
                results.append(f"- ID {e.id}: {e.title} das {e.start_time.strftime('%H:%M')} às {e.end_time.strftime('%H:%M')}")
            
            return json.dumps({"status": "success", "events": results})
            
        elif action == "check_availability":
            start_str = arguments.get("start_time")
            end_str = arguments.get("end_time")
            
            if not start_str or not end_str:
                return json.dumps({"status": "error", "message": "Falta 'start_time' ou 'end_time'."})
                
            start = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
            
            conflicts = db.query(EventDB).filter(
                EventDB.user_id == user_id,
                EventDB.status != "cancelled",
                EventDB.start_time < end,
                EventDB.end_time > start
            ).all()
            
            if conflicts:
                return json.dumps({"status": "conflict", "message": "Existem conflitos nesse horário.", "conflicting_events": [c.title for c in conflicts]})
            
            return json.dumps({"status": "available", "message": "Horário livre."})
            
        elif action == "create_event":
            start_str = arguments.get("start_time")
            end_str = arguments.get("end_time")
            title = arguments.get("title")
            
            if not start_str or not end_str or not title:
                return json.dumps({"status": "error", "message": "Falta 'title', 'start_time' ou 'end_time'."})
                
            new_event = EventDB(
                user_id=user_id,
                title=title,
                start_time=datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S"),
                end_time=datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S"),
                status="scheduled"
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            
            return json.dumps({"status": "success", "message": f"Evento '{title}' agendado com sucesso (ID: {new_event.id})."})
            
        elif action == "cancel_event":
            event_id = arguments.get("event_id")
            if not event_id:
                return json.dumps({"status": "error", "message": "Falta 'event_id'."})
                
            ev = db.query(EventDB).filter(EventDB.id == event_id, EventDB.user_id == user_id).first()
            if not ev:
                return json.dumps({"status": "error", "message": "Evento não encontrado."})
                
            ev.status = "cancelled"
            db.commit()
            return json.dumps({"status": "success", "message": "Evento cancelado com sucesso."})
            
        elif action == "get_important_events":
            # Mock de eventos importantes (feriados, etc)
            return json.dumps({
                "status": "success", 
                "important_events": [
                    {"date": "2026-12-25", "title": "Natal"},
                    {"date": "2026-01-01", "title": "Ano Novo"}
                ]
            })
            
        else:
            return json.dumps({"status": "error", "message": f"Ação '{action}' desconhecida na agenda."})
            
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()
