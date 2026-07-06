.PHONY: install api cli up down ngrok

# Instala as dependências do projeto
install:
	venv/bin/python -m pip install --upgrade pip
	venv/bin/python -m pip install -r requeires.txt

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

# Expõe a porta 8080 da API para a internet
ngrok:
	ngrok http 8080
