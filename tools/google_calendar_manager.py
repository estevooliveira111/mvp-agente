import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "google_calendar_manager",
    "description": "Ferramenta para criar eventos no Google Agenda (Calendar). Utiliza OAuth2 para autenticar usuários reais e injetar compromissos com horário e participantes na agenda.",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "O título ou resumo do evento (ex: 'Reunião de Alinhamento do MVP')."
            },
            "description": {
                "type": "string",
                "description": "Detalhes, laudos ou pauta sobre o evento."
            },
            "start_time": {
                "type": "string",
                "description": "Data e hora de início no formato ISO-8601. Exemplo: '2026-07-10T14:00:00-03:00' (para horário de Brasília)."
            },
            "end_time": {
                "type": "string",
                "description": "Data e hora de fim no formato ISO-8601. Exemplo: '2026-07-10T15:00:00-03:00'."
            },
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "(Opcional) Lista de strings contendo os e-mails dos participantes a serem convidados."
            }
        },
        "required": ["summary", "start_time", "end_time"]
    }
}

# Definimos o escopo mínimo para permitir apenas a criação/edição de eventos (maior segurança)
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    1. Verifica se já existe um token de acesso de usuário (OAuth2).
    2. Se o token expirou, atualiza. Se não existe, pede login interativo e gera o token.
    3. Conecta com a Google Calendar API (v3).
    4. Constrói o JSON do evento estruturado e realiza o POST (insert).
    """
    summary = kwargs.get("summary")
    description = kwargs.get("description", "")
    start_time = kwargs.get("start_time")
    end_time = kwargs.get("end_time")
    attendees_list = kwargs.get("attendees", [])
    
    if not summary or not start_time or not end_time:
        return json.dumps({"status": "error", "message": "Os parâmetros 'summary', 'start_time' e 'end_time' são estritamente obrigatórios."})
        
    try:
        creds = None
        # token.json armazena o access token e refresh token do usuário após o 1º login
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
        # Se não houver credenciais (ou estiverem expiradas), inicia o processo OAuth
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Token venceu? Pega um novo silenciosamente
                creds.refresh(Request())
            else:
                # Primeiro acesso: requer credentials.json (baixado do Google Cloud)
                if not os.path.exists('credentials.json'):
                    return json.dumps({
                        "status": "error",
                        "message": "Falta o arquivo 'credentials.json' do OAuth Client ID. Baixe-o no console do Google Cloud e coloque na raiz do projeto."
                    })
                    
                # Abre aba no navegador para o usuário logar na conta Google e permitir acesso
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Salva credencial recém gerada/atualizada
            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())
                
        # Instancia o serviço da API do Calendário
        service = build('calendar', 'v3', credentials=creds)
        
        # Mapeia os participantes para a estrutura requerida pelo Google
        attendees_formatted = [{'email': email} for email in attendees_list]
        
        # Estruturação final do evento
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
            },
            'end': {
                'dateTime': end_time,
            },
            'attendees': attendees_formatted,
            'reminders': {
                'useDefault': True,
            },
        }
        
        # Executa a requisição síncrona diretamente no calendário primário do usuário autenticado
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        return json.dumps({
            "status": "success",
            "data": {
                "message": "Compromisso sincronizado com a agenda do Google com sucesso.",
                "eventId": created_event.get('id'),
                "link": created_event.get('htmlLink'),
                "status": created_event.get('status'),
                "attendees_invited": len(attendees_list)
            }
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Erro de comunicação com a API do Google Calendar: {str(e)}"
        })
