#!/bin/bash
echo "Stopping Studia..."
kill $(cat .backend.pid 2>/dev/null) 2>/dev/null
kill $(cat .ollama.pid 2>/dev/null) 2>/dev/null
rm -f .backend.pid .ollama.pid
echo "Stopped."
