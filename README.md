## 🛠 Installation & Setup

Follow these steps in order to set up your local development environment.

### 1. Environment Setup
Create a virtual environment and install the necessary dependencies.
```bash
# Create virtual environment
python -m venv .venv

# Activate the environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Infrastructure (Databases & Brokers)
Start the required services (PostgreSQL and Redis) using Docker.
```bash
docker compose up -d
```

---

## 🚀 Running the Application

You will need to open **three separate terminals** (ensure the virtual environment is activated in each).

### Terminal 1: ASGI Server
Runs the main web application.
```bash
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Celery Worker
Handles background task processing.
```bash
celery -A config worker -P gevent -c 50 -l info
```

### Terminal 3: Celery Beat
Handles scheduled/periodic tasks.
```bash
celery -A config beat -l info
```
