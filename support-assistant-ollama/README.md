# Support Assistant Ollama Image

This image runs the Ollama API with `qwen2.5:3b` preloaded.

## Build

```bash
docker build -t support-assistant-ollama:qwen2.5-3b .
```

## Run

```bash
docker run --rm -p 11434:11434 --name support-assistant-ollama support-assistant-ollama:qwen2.5-3b
```

## Verify

```bash
curl http://localhost:11434/api/tags
```