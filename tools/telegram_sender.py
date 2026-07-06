import json
import os
import requests
from dotenv import load_dotenv

# Carrega variáveis de ambiente (como o Bot Token) do arquivo .env
load_dotenv()

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "telegram_sender",
    "description": "Envia notificações e mensagens formatadas em tempo real usando a API HTTP oficial do Telegram Bot.",
    "parameters": {
        "type": "object",
        "properties": {
            "chat_id": {
                "type": "string",
                "description": "O ID (ou @username de canal) do chat ou usuário destino no Telegram."
            },
            "text": {
                "type": "string",
                "description": "O texto da mensagem a ser enviada."
            },
            "parse_mode": {
                "type": "string",
                "description": "(Opcional) Formato de estilo do texto, geralmente 'Markdown' (padrão) ou 'HTML'."
            }
        },
        "required": ["chat_id", "text"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    Recebe um destinatário e envia a mensagem realizando um POST HTTP
    contra o endpoint do Telegram Bot, usando a biblioteca 'requests'.
    """
    chat_id = kwargs.get("chat_id")
    text = kwargs.get("text")
    parse_mode = kwargs.get("parse_mode", "Markdown")
    
    if not chat_id or not text:
        return json.dumps({"status": "error", "message": "Os parâmetros 'chat_id' e 'text' são obrigatórios para enviar a notificação."})
        
    try:
        # Recupera o token oficial do Bot gerado pelo @BotFather
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            return json.dumps({
                "status": "error", 
                "message": "Token do Bot não encontrado. Configure 'TELEGRAM_BOT_TOKEN' no arquivo .env."
            })
            
        # URL oficial do endpoint sendMessage
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Payload JSON estruturado conforme documentação do Telegram
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        # Envio HTTP e suporte à notificação em tempo real (tempo de timeout curto = 10s)
        response = requests.post(api_url, json=payload, timeout=10)
        
        # Lê a resposta para indicar o status da entrega
        data = response.json()
        
        if data.get("ok"):
            return json.dumps({
                "status": "success",
                "data": {
                    "message": "Notificação em tempo real enviada e confirmada pelo Telegram.",
                    "message_id": data["result"]["message_id"],
                    "recipient_chat_id": data["result"]["chat"]["id"]
                }
            })
        else:
            # Caso o chat_id esteja errado, o bot foi bloqueado, etc.
            return json.dumps({
                "status": "error",
                "message": f"O Telegram rejeitou o envio da mensagem. Detalhes: {data.get('description', 'Erro Desconhecido')}"
            })
            
    except requests.exceptions.RequestException as req_err:
        return json.dumps({"status": "error", "message": f"Erro de rede ao comunicar com a API do Telegram: {str(req_err)}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Falha interna ao preparar o envio do Telegram: {str(e)}"})
