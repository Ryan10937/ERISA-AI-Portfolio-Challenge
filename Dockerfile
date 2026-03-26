FROM ryan10937/erisa-agent-base

WORKDIR /app

# Copy your files
COPY scripts/ ./scripts/
COPY models/ ./models/
COPY install/ ./install/
COPY docs/ ./docs/
COPY database/ ./database/
COPY data/ ./data/

# Install Python deps
RUN pip install --no-cache-dir -r install/requirements.txt

# Copy startup script
COPY scripts/ollama_start.sh .
RUN chmod +x scripts/ollama_start.sh
RUN export OLLAMA_HOST=127.0.0.1:11434

RUN apt-get update && apt-get install -y clinfo nvidia-utils-535 

# Expose Ollama port
EXPOSE 11434

ENTRYPOINT ["./scripts/ollama_start.sh"]
