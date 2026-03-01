# LDA Reuniones - Hospital Alma Máter

Sistema web para gestión de reuniones y control de asistencia y despliegue.

## Arquitectura

- Frontend: Angular
- Backend: FastAPI (Python)
- Base de datos: SQL Server

## Estructura del Proyecto

lda-reuniones/
│
├── backend/
│   └── app/
│       ├── core/
│       ├── modules/
│       └── main.py
│
├── frontend/
│   └── lda-reuniones-frontend/

---

## Backend

### Requisitos
- Python 3.10+
- Virtualenv

### Instalación

cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

### Ejecución

uvicorn app.main:app --reload

Swagger:
http://localhost:8000/docs

---

## Frontend

### Requisitos
- Node 18+
- Angular CLI

### Instalación y ejecución

cd frontend/lda-reuniones-frontend
npm install
ng serve

App:
http://localhost:4200