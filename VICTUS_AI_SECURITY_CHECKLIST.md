# 🛡️ Victus AI Assistant — Security & Environment Checklist

> **Version:** v7.1 (Production & Git-Ready)  
> **Repository:** [SUBHAMKArM/Victus-ai](https://github.com/SUBHAMKArM/Victus-ai)  
> **Target:** HP Victus & Local AI Assistants  

---

## 1. Security & Environment Architecture

### 🔑 Environment Variables (`.env`)
All private keys, tokens, and local ports are managed through `.env`. 
Never commit `.env` to Git. Use `.env.example` as a template.

| Variable | Description | Default / Example | Required |
| :--- | :--- | :--- | :--- |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | `YOUR_API_KEY_HERE` | Optional (Weather) |
| `DEFAULT_CITY` | Default city for weather queries | `Kolkata` | Optional |
| `LMSTUDIO_URL` | Local LM Studio server endpoint | `http://127.0.0.1:1234` | Default |
| `OLLAMA_URL` | Local Ollama fallback server endpoint | `http://127.0.0.1:11434` | Default |
| `PHONE_SERVER_PORT` | Port for phone remote control server | `5000` | Optional |
| `PHONE_AUTH_TOKEN` | Optional security token for phone commands | *(Empty = Open LAN)* | Recommended |

---

## 2. Git & Repository Protection (`.gitignore`)

The project uses a strict `.gitignore` to prevent secret leaks, private user logs, and model bloat:

- **Secrets & Credentials:** `.env`, `.env.*`, `!.env.example`, `*.pem`, `*.key`
- **User Privacy & Memory:** `memory.json`, `failed_commands.json`, `data.xlsx`
- **Heavy Model Weights:** `vosk-model/`, `*.gguf`, `*.bin`, `*.pt`, `*.onnx`
- **Cache & Temp:** `__pycache__/`, `*.pyc`, `*.mp3`, `*.wav`, `temp_*`

---

## 3. Security Checklist for New Version Releases

- [x] **No Hardcoded Secrets in Code:** Verify `config.py` loads from `os.getenv()`.
- [x] **Git Ignore Verification:** Confirm `.env` and `memory.json` are never tracked by Git.
- [x] **Phone Server Auth:** Enable `PHONE_AUTH_TOKEN` if accessing from public or shared networks.
- [x] **Dependency Check:** `requirements.txt` includes `python-dotenv`.
- [x] **Clean Launch:** Verified with `Start_Victus_AI.bat` and `test_all.py`.
