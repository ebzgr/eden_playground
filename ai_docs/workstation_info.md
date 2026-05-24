# mk4bt-workstation

## Overview

`mk4bt-workstation` is a shared, high-performance Linux workstation designed for:

- Multi-user research and experimentation  
- GPU-accelerated AI and machine learning workloads  
- Local, containerized services (LLMs, automation pipelines)  
- Secure remote access without exposing the system to the public internet  

The system prioritizes **stability, isolation, and scalability**.

---

## System Identity

- **Hostname:** `mk4bt`  
- **OS:** Ubuntu Server 24.04 LTS  
- **Desktop:** XFCE (lightweight GUI)  
- **Access Model:** SSH-first  
- **Network:** Tailscale (private overlay network)  

---

## Hardware Configuration

### Machine
- Dell Precision 7960  
- Intel Xeon w9-3475X (36 cores / 72 threads)  
- 124 GB RAM  

### GPU
- 2 × NVIDIA RTX A4000 (16GB VRAM each)  
- NVIDIA Driver 590  
- CUDA enabled (host + containers)  
- Both GPUs available to all services (shared, no hard assignment)  

---

## Storage Architecture

### SSD (1 TB NVMe) — System & Services

Used for:
- Operating system  
- Docker engine and images  
- Service state  

Example paths:
```
/var/lib/services/ollama
/var/lib/services/open-webui
/var/lib/services/searxng
/var/lib/services/n8n
/var/lib/services/comfyui
/var/lib/services/filebrowser
```

---

### HDD (7 TB) — User Data Only

Used for:
- User home directories  
- Research data  
- Experiment outputs  

Mapping:
```
/home/<user> → /data/<user>
```

**Design rule:**
- No system or service data on HDD  
- No research data on SSD  

---

## User Management

### Create a User

```bash
sudo adduser-datahome <username>
```

### Set Password

```bash
sudo passwd <username>
```

### Force Password Change on First Login

```bash
sudo chage -d 0 <username>
```

---

## Access & Connectivity

### Network Model

Client → Tailscale → mk4bt

- No port forwarding  
- No public exposure  
- Works behind CGNAT / 5G networks  

---

### SSH (Primary Access)

```bash
ssh <username>@mk4bt
```

---

### Remote Desktop (Optional)

- Protocol: RDP  
- Service: xrdp  
- Desktop: XFCE  

---

## Tailscale Setup

### On Workstation

```bash
sudo tailscale up --ssh
```

---

## Container Layer

- Docker (primary runtime)  
- Docker Compose  
- NVIDIA Container Toolkit  

---

## Core Services

| Service | Description | URL |
|---------|-------------|-----|
| Ollama | Local LLM runtime | `http://mk4bt:11434` |
| Open WebUI | Web UI for Ollama | `http://mk4bt:3000` |
| SearXNG | Self-hosted search engine (internal only) | — |
| n8n | Workflow automation | `http://mk4bt:5678` |
| ComfyUI | Image generation UI | `http://mk4bt:8188` |
| Filebrowser | Web-based file manager (ComfyUI models) | `http://mk4bt:8080` |

---

## Docker Compose

### Location

```
/opt/services/foundation/docker-compose.yml
```

### Managing Services

```bash
cd /opt/services/foundation

# Start all services
docker compose up -d

# Restart a specific service
docker compose restart <service>

# Stop all services
docker compose down

# View logs
docker logs <container_name>
```

### Full docker-compose.yml

```yaml
networks:
  ai_net:
    driver: bridge

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    volumes:
      - /var/lib/services/ollama:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - ai_net

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: unless-stopped
    ports:
      - "3000:8080"
    volumes:
      - /var/lib/services/open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    extra_hosts:
      - host.docker.internal:host-gateway
    networks:
      - ai_net

  searxng:
    image: docker.io/searxng/searxng:latest
    container_name: searxng
    restart: unless-stopped
    volumes:
      - /var/lib/services/searxng:/etc/searxng:rw
    networks:
      - ai_net

  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=r@hEn00r!
      - N8N_SECURE_COOKIE=false
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
      - N8N_RESTRICT_FILE_ACCESS_TO=/data
      - NODES_EXCLUDE=["n8n-nodes-base.localFileTrigger"]
    volumes:
      - /var/lib/services/n8n:/home/node/.n8n
      - /data:/data
    ports:
      - "5678:5678"
    networks:
      - ai_net

  comfyui:
    image: ghcr.io/ai-dock/comfyui:latest-cuda
    container_name: comfyui
    restart: unless-stopped
    ports:
      - "8188:18188"
    volumes:
      - /var/lib/services/comfyui:/opt/ComfyUI
    environment:
      - COMFYUI_ARGS=--listen 0.0.0.0
      - WEB_ENABLE_AUTH=false
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    networks:
      - ai_net

  filebrowser:
    image: filebrowser/filebrowser:latest
    container_name: filebrowser
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - /var/lib/services/comfyui/models:/srv
      - /var/lib/services/filebrowser:/database
    environment:
      - FB_NOAUTH=false
    networks:
      - ai_net
```

---

## Service Configuration

### Ollama

- Runs as a Docker container with access to all GPUs  
- Data stored at `/var/lib/services/ollama`  
- Accessible to other containers via `http://host.docker.internal:11434`  
- Accessible from host via `http://192.168.1.3:11434`
- Supports multi-GPU for large models (e.g. 70B+)

#### Installed Models

| Model | Size |
|-------|------|
| qwen2.5:14b | 14.8B Q4_K_M |
| qwen2.5:7b | 7.6B Q4_K_M |
| deepseek-r1:7b-qwen-distill-q4_K_M | 7.6B Q4_K_M |
| llama3.1:8b-instruct-q4_K_M | 8.0B Q4_K_M |

### Open WebUI

- URL: `http://mk4bt:3000`  
- Data stored at `/var/lib/services/open-webui`  
- First account created becomes admin  
- Supports multiple user accounts (no SMTP required; admin creates accounts and shares invite links manually)

### SearXNG

- Internal service only — not exposed outside Docker network  
- Accessible to Open WebUI at `http://searxng:8080`  
- Accessible from host at `http://192.168.1.3:8080`
- Config stored at `/var/lib/services/searxng/settings.yml`  
- JSON format must be enabled in `settings.yml` for Open WebUI integration

#### settings.yml

```yaml
use_default_settings: true
server:
  secret_key: "your_random_secret_key"
  limiter: false
search:
  formats:
    - html
    - json
```

### Open WebUI Web Search Settings

Configured via Admin Panel → Settings → Web Search:

- Engine: `searxng`  
- URL: `http://searxng:8080/search?q=<query>`  
- Result count: `5`  
- Concurrent requests: `10`  

Web search must be toggled on per chat session via the **+** button next to the message input.

### n8n

- URL: `http://mk4bt:5678`  
- Data stored at `/var/lib/services/n8n`  
- Notable config:
  - `N8N_SECURE_COOKIE=false` — required for HTTP access via Tailscale  
  - User management enabled; invite links shared manually without SMTP  

### ComfyUI

- URL: `http://mk4bt:8188`  
- Node-based image generation UI  
- Entire ComfyUI installation stored at `/var/lib/services/comfyui` (persists across container restarts)  
- Models stored at `/var/lib/services/comfyui/models`  
- Has access to all GPUs  
- No restart required when adding new models — they appear automatically after download
- Uses `ai-dock/comfyui` image; internal port is 18188 mapped to host 8188
- `WEB_ENABLE_AUTH=false` disables the portal login

#### Installing Models

Models can be downloaded via the ComfyUI Model Manager UI, or manually via wget:

```bash
# Example: download a checkpoint model
sudo wget -P /var/lib/services/comfyui/models/checkpoints <model_url>
```

Common model subfolders:
```
/var/lib/services/comfyui/models/checkpoints
/var/lib/services/comfyui/models/vae
/var/lib/services/comfyui/models/text_encoders
/var/lib/services/comfyui/models/loras
/var/lib/services/comfyui/models/controlnet
```

#### Updating ComfyUI

```bash
docker exec -it comfyui git -C /opt/ComfyUI checkout -f <version_tag>
docker exec -it comfyui /opt/environments/python/comfyui/bin/python -m pip install -r /opt/ComfyUI/requirements.txt
cd /opt/services/foundation
docker compose restart comfyui
```

### Filebrowser

- URL: `http://mk4bt:8080`  
- Web-based file manager scoped to ComfyUI models directory  
- Data stored at `/var/lib/services/filebrowser`  
- Root directory mapped to `/var/lib/services/comfyui/models` — users cannot access anything outside this path  
- Authentication enabled (`FB_NOAUTH=false`)  

#### Setup Notes

```bash
# Fix permissions if container fails to start
sudo chown -R 1000:1000 /var/lib/services/filebrowser
```

#### Reset Admin Password

```bash
cd /opt/services/foundation
docker compose stop filebrowser
docker run --rm -v /var/lib/services/filebrowser:/database filebrowser/filebrowser \
  -d /database/filebrowser.db users update admin --password <newpassword>
docker compose start filebrowser
```

Note: Password minimum length is 12 characters.

---

## GPU Strategy

Both GPUs are shared across all services with no hard assignment. This allows:
- Ollama to use both GPUs for large models (70B+)
- ComfyUI to use both GPUs for faster image generation
- Automatic load balancing when services are idle

---

## OpenClaw (Personal AI Assistant)

OpenClaw is a personal AI assistant for ebrahim only. It is **not part of the shared services stack** and runs separately from the main docker-compose.yml.

- **Location:** `~/openclaw`
- **Config:** `~/.openclaw`
- **Workspace:** `~/.openclaw/workspace`
- **Web dashboard:** `http://mk4bt:18789` (requires gateway token)
- **Interface:** Telegram bot (personal, private)
- **Model:** `qwen2.5:14b` via local Ollama (`http://192.168.1.3:11434`)
- **Search:** SearXNG (`http://192.168.1.3:8080`)

### Managing OpenClaw

```bash
cd ~/openclaw

# Start
docker compose up -d openclaw-gateway

# Stop
docker compose down

# View logs
docker compose logs -f openclaw-gateway

# Run CLI commands
docker compose run --rm openclaw-cli <command>
```

### Adding Telegram Users

When a new user messages the bot they receive a pairing code. Approve it with:

```bash
cd ~/openclaw
docker compose run --rm openclaw-cli pairing approve telegram <CODE>
```

### Installed Skills

blogwatcher, clawhub, gh-issues, gifgrep, github, goplaces, himalaya, nano-pdf, 1password, openai-whisper, oracle, session-logs, songsee, summarize, tmux, trello, video-frames

### Installed Hooks

boot-md, command-logger, session-memory

### Security Note

OpenClaw has full access to shell commands and the workspace directory. Only approve trusted Telegram users. Never expose port 18789 publicly.

---

## Security Model

- No public exposure  
- Access via Tailscale only  
- User-level isolation  
- OpenClaw is private to ebrahim only  

---

## System Architecture

```
Users → Tailscale → OS → Docker → Storage
```

---

## Design Principles

- Stability first  
- Clear separation of concerns  
- Minimal host pollution  
- Multi-user ready  

---

## Notes

- Tailscale is required for all access  
- RDP sessions are independent  
- Web search in Open WebUI must be toggled on per chat session  
- ComfyUI models do not require a container restart to take effect  
- OpenClaw updates ~1-2x per month; run `docker compose pull` in `~/openclaw` to update