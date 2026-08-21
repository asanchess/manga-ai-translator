---
name: sota_manga_pipeline_setup
description: Workflow for configuring a 100% local, SOTA AI manga translation service and integrating an AI web assistant.
---

# SOTA Manga Pipeline Setup Workflow

When asked to setup the full-stack SOTA manga translation pipeline, follow these steps:

1. **Environment Initialization:**
   - Ensure `manga-ocr`, `simple-lama-inpainting`, and `easyocr` are installed via pip.
   - Verify `ollama` is running on `http://localhost:11434`.

2. **Architecture Constraints:**
   - Isolate Cleaning from Typesetting. Cleaners must return an empty background (LaMa) and a JSON mask of bubbles.
   - The Typesetter (Renderer) dynamically applies translations onto the cached clean background.

3. **AI Assistant Integration (100+ Sources):**
   - The web frontend must include a chat interface connected to the AI Assistant.
   - The Assistant uses a local LLM to navigate known manga sources (e.g., Dex, Asura, Reaper) and trigger the backend scraper + pipeline to automatically deploy chapters to the UI.

4. **Version Control:**
   - Always commit and push intermediate working states to GitHub (using GitHub MCP) to prevent loss of progress during massive refactors.
