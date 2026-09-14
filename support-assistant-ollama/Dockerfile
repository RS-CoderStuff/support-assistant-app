FROM ollama/ollama:latest

ENV OLLAMA_HOST=0.0.0.0:11434

RUN ollama serve >/tmp/ollama.log 2>&1 & \
    server_pid=$!; \
    until ollama list >/dev/null 2>&1; do sleep 1; done; \
    ollama pull qwen2.5:3b; \
    kill "$server_pid"; \
    wait "$server_pid" || true

EXPOSE 11434

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ollama list >/dev/null 2>&1 || exit 1