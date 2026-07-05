FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY inventory_management/ ./inventory_management/
COPY data/ ./data/

# Ensure Flask can import local modules like db.py and models
ENV PYTHONPATH=/app/inventory_management
ENV DATABASE_PATH=/app/data/data.db
WORKDIR /app/inventory_management

EXPOSE 5000

CMD ["python", "-m", "flask", "--app", "app.py", "run", "--host=0.0.0.0", "--port=5000"]
