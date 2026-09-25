.PHONY: install api cli up down ngrok dev

# Instala as dependências do projeto
install:
	venv/bin/python -m pip install --upgrade pip
	venv/bin/python -m pip install -r requirements.txt

# Roda o servidor Webhook (FastAPI) para o Telegram/WhatsApp
api:
	venv/bin/python app.py

# Roda o Agente em modo interativo direto no Terminal
cli:
	venv/bin/python main.py

# Sobe os bancos de dados auxiliares (Memcached, Postgres, etc)
up:
	docker-compose up -d

# Desliga os bancos de dados
down:
	docker-compose down

# Porta da API (mesmo valor de API_PORT no .env) e domínio fixo opcional do ngrok
# (ex: make dev NGROK_DOMAIN=meu-app.ngrok-free.app)
API_PORT ?= 8080
NGROK_DOMAIN ?=

# Expõe a porta da API para a internet
ngrok:
	ngrok http $(API_PORT) $(if $(NGROK_DOMAIN),--url=$(NGROK_DOMAIN))

# Sobe o ngrok em segundo plano e a API em seguida. A API descobre a URL do túnel e
# registra o webhook do Telegram sozinha (com WEBHOOK_URL vazia no .env).
# Ctrl+C encerra os dois. O log do ngrok fica em logs/ngrok.log.
dev:
	@mkdir -p logs
	@ngrok http $(API_PORT) $(if $(NGROK_DOMAIN),--url=$(NGROK_DOMAIN)) --log=stdout > logs/ngrok.log 2>&1 & \
	NGROK_PID=$$!; \
	trap 'kill $$NGROK_PID 2>/dev/null' EXIT INT TERM; \
	echo "ngrok rodando (PID $$NGROK_PID). Painel: http://localhost:4040"; \
	venv/bin/python app.py
