# fastapi-base

This service demonstrates a minimal, **portable** core with a simple public endpoint.

## 1) Setup

### 1.1. Python & venv
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
```
### 1.2. Install dependencies

```bash
pip install -r requirements.txt
```
### 1.3. Environment
Copy .env.example to .env and edit values as needed:

```bash
cp .env.example .env
```
For PostgreSQL set:

DB=postgresql, DB_PORT=5432

For MySQL set:

DB=mysql, DB_PORT=3306

The app only needs a reachable database; migrations are optional for this sample.

2) Run
```bash
uvicorn app.main:app --reload
```
Root health: http://127.0.0.1:8000/health

Docs (Swagger): http://127.0.0.1:8000/docs