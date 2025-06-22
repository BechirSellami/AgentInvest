FROM python:3.11-slim
WORKDIR /app
#COPY requirements.txt .
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
#COPY data/sample_companies.csv ./data/sample_companies.csv
CMD ["python", "ingest.py"]
