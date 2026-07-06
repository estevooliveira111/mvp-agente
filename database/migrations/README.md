# Migrações (Alembic)

A pasta `migrations/` é reservada para armazenar o versionamento e evolução da estrutura do seu banco de dados PostgreSQL.
Recomendamos o uso do **Alembic** acoplado ao SQLAlchemy para gerar as migrações automaticamente lendo seus arquivos de `models.py`.

## Guia Rápido

1. **Inicializar o ambiente (se necessário):**
   ```bash
   alembic init migrations
   ```

2. **Gerar uma nova versão do banco (após criar ou alterar tabelas no `models.py`):**
   ```bash
   alembic revision --autogenerate -m "criando_tabelas_iniciais"
   ```

3. **Aplicar as migrações (criar de fato as tabelas no PostgreSQL):**
   ```bash
   alembic upgrade head
   ```
