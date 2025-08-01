FROM python:3.10-slim

WORKDIR /app

# Ensure our modules can be imported when running CLI tools like Alembic
ENV PYTHONPATH=/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
