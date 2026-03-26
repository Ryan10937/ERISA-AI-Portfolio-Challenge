#!/bin/bash
set -e

# Start Ollama server in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
echo "Waiting for Ollama to start..."
for i in {1..30}; do
  if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama ready!"
    break
  fi
  sleep 1
done

# Run main.py with all passed args (e.g., 'workup --claim-id ...')
echo "Running main.py with args: $@"
python scripts/main.py "$@"
