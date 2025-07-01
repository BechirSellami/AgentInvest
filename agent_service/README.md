# AgentInvest

This repository contains a FastAPI service (`agent_service`) and an ingestion utility (`ingestor`).

## Building the FastAPI Docker image

The FastAPI `Dockerfile` expects both the `agent_service` and `ingestor` packages to be available in the build context. Build the image from the repository root so that both directories are included:

```bash
docker build -t agent-invest-api -f agent_service/Dockerfile .
```

Then run the container:

```bash
docker run -d \
  --name agent-service \
  --env-file .env \
  --network agentnet \
  -p 8000:80 \
  agent-invest-api