FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 5000

CMD ["flask", "run"]
# WORKDIR /app

# # Install dependencies first for better layer caching
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy application source
# COPY . .
# COPY data/ ./data/

# # Ensure Flask can import local modules like db.py and models
# ENV PYTHONPATH=/app/inventory_management
# ENV DATABASE_PATH=/app/data/data.db
# ENV FLASK_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0
# WORKDIR /app/inventory_management

# EXPOSE 5000

# CMD ["python", "app.py"]