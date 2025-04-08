FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./app ../../services

EXPOSE 8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.event_manager.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
