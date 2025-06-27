# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy FastAPI app
COPY . /app/agent_service

# Run the app
CMD ["uvicorn", "agent_service.main:app", "--host", "0.0.0.0", "--port", "80"]
