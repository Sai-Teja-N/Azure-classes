#!/bin/sh
set -eu

ollama serve >/tmp/ollama.log 2>&1 &
pid="$!"

until ollama list >/dev/null 2>&1; do
  sleep 1
done

ollama pull llama3.2:3b
wait "$pid"
