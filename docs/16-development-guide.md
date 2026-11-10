# 16 — Local Development Guide

## 1. Prerequisites
- Python 3.12+ (tested on Python 3.13)
- Node.js 18+ & npm 10+
- Redis (or Docker container)
- PostgreSQL (or set `USE_SQLITE=True` in `.env` for local standalone development)

---

## 2. Backend Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Configure environment
cp backend/.env.example backend/.env

# 4. Run migrations
python backend/manage.py migrate

# 5. Seed demonstration data
python backend/manage.py seed_data

# 6. Run test suite
pytest backend/tests

# 7. Start Django API server
python backend/manage.py runserver 0.0.0.0:8000
```

---

## 3. Background Services Setup

In separate terminal tabs:

```bash
# Start Celery delivery worker
celery -A config worker -l info --workdir backend

# Start Transactional Outbox Publisher
python backend/manage.py publish_outbox --poll-interval 1.0

# Start Celery Beat maintenance heartbeat
celery -A config beat -l info --workdir backend
```

---

## 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev

# Or build production bundle
npm run build
```
Dashboard will be available at [http://localhost:5173](http://localhost:5173).
