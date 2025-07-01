# agent_service/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY agent_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application and the shared ingestor module
COPY agent_service /app/agent_service
COPY ingestor /app/ingestor

# Set PYTHONPATH
ENV PYTHONPATH="/app"

CMD ["uvicorn", "agent_service.main:app", "--host", "0.0.0.0", "--port", "80"]