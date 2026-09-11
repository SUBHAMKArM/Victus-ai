# Victus AI Assistant v7.1

A robust, locally-running AI voice assistant optimized for HP Victus laptops. It features multi-language support (English, Hindi, Bengali), intelligent routing to local AI models, system control, a floating GUI HUD with an Alexa-style animated ring, and live weather integrations!

## Features
- **Voice Activation:** Reliable wake word detection ("Hey Victus", "Hello Victus").
- **Local AI Brain:** Seamless integration with LM Studio or Ollama for full privacy.
- **Smart Routing:** Auto-detects language and routes queries to appropriate local models (e.g., Gemma for Hindi/Bengali, Llama/Qwen for English).
- **GUI HUD:** Floating, transparent ring that pulses based on AI state (Listening, Thinking, Speaking) with an image upload button for Vision AI.
- **System Control:** Control volume, brightness, open/close applications, and optimize RAM.
- **Weather Integration:** Live weather reporting via OpenWeatherMap API.

## Setup Instructions

### 1. Requirements
Ensure you have Python 3.11 installed. You also need an AI backend running locally:
- [LM Studio](https://lmstudio.ai/) (Runs on Port `1234`)
- [Ollama](https://ollama.com/) (Runs on Port `11434`)

### 2. Secure Configuration (`.env`)
To protect your private API keys, do not commit them directly to GitHub.
Instead, copy the example template to create your own environment file:

```bash
cp .env.example .env
```
Then, open the `.env` file and insert your actual `OPENWEATHER_API_KEY`.

### 3. Install & Run
Simply double-click the `Start_Victus_AI.bat` file.
This script will automatically:
- Verify and resolve any missing Python packages.
- Upgrade tools and suppress noisy pip warnings.
- Launch the assistant and spawn the visual HUD ring on your desktop.

## Security Notice
This repository contains a strict `.gitignore` designed to prevent the accidental upload of:
- Your `.env` files and API keys
- The `memory.json` file (your private chat logs)
- Gigabyte-sized vision models (`vosk-model/` or `.pt`/`.gguf` files)
- Python cache files (`__pycache__`)
