# Multi-Backend OCR System - Claude Assistant Documentation

This document provides essential information for Claude assistants to effectively work with the multi-backend OCR system.

## 🚨 CRITICAL REMINDERS

- **NEVER run code locally** - Always use deployment scripts for testing
- **ALWAYS use `deployment/deploy.sh`** for any code changes
- **NEVER install dependencies locally** - All dependencies are handled on server
- **ALWAYS sleep 30+ seconds** when reading Bash output from long-running processes
- **NEVER modify reference directories** - `deepseekocr-reference/`, `mineru-reference/`, `deployment-reference/` are READ-ONLY

## 🏗️ Current Architecture Overview

### **Three-Server System:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   Orchestrator  │    │  Backend Servers │
│  (localhost:3000) │◄──►│  (localhost:8080) │◄──►│                 │
└─────────────────┘    └─────────────────┘    ├─────────────────┤
                                              │ DeepSeek Server │
                                              │  (localhost:5000) │
                                              │  GPU: RTX 3090 #1 │
                                              ├─────────────────┤
                                              │   Mineru Server  │
                                              │  (localhost:5001) │
                                              │  GPU: RTX 3090 #2 │
                                              └─────────────────┘
```

### **Current Implementation Status:**
- **Phase 0: COMPLETED** - Common interface & project structure
- **Phase 1: ALMOST DONE** - Backend isolation & GPU assignment
- **Phase 2: TODO** - Orchestrator development
- **Phase 3: TODO** - Web client enhancement
- **Phase 4: TODO** - Response processing

## 🚀 Quick Deployment Commands

### Standard Deployment
```bash
./deployment/deploy.sh -m "Your descriptive commit message"
```

### Manual Deployment (if script fails)
```bash
# Commit and push
git add .
git commit -m "Your changes"
git push origin master

# SSH to server
ssh -p 40032 zakir@223.166.245.194 -L 8080:localhost:8080 -L 5000:localhost:5000 -L 5001:localhost:5001

# Deploy on server
pkill -9 python3
cd /home/zakir/ocr-project
git fetch origin && git reset --hard origin/master
cd deployment
./setup.sh
./startup.sh
```

## 📁 Current Project Structure

```
ocr-project/
├── backends/
│   ├── deepseek-ocr/           # DeepSeek backend (GPU 0)
│   │   ├── deepseek_ocr_backend.py  # OCRBackend implementation
│   │   ├── server.py           # Flask server (port 5000)
│   │   ├── requirements.txt    # DeepSeek-specific dependencies
│   │   ├── process/            # DeepSeek OCR processing modules
│   │   ├── deepencoder/        # DeepSeek vision encoder modules
│   │   └── venv/               # DeepSeek virtual environment
│   └── mineru/                 # Mineru backend (GPU 1)
│       ├── mineru_backend.py   # OCRBackend implementation
│       ├── server.py           # Flask server (port 5001)
│       ├── requirements.txt    # Mineru-specific dependencies
│       └── venv/               # Mineru virtual environment
├── orchestrator/
│   ├── server.py               # Main orchestrator (port 8080)
│   ├── requirements.txt        # Orchestrator dependencies
│   └── config.py               # Backend configuration
├── shared/
│   ├── ocr_backend.py          # Abstract OCRBackend interface
│   ├── api_contract.py         # Unified API response format
│   └── utils.py                # Common utilities
├── deployment/
│   ├── deploy.sh               # Main deployment script
│   ├── setup.sh                # Main setup orchestrator
│   ├── setup_deepseek.sh       # DeepSeek backend setup
│   ├── setup_mineru.sh         # Mineru backend setup
│   ├── setup_orchestrator.sh   # Orchestrator setup
│   ├── startup.sh              # Service startup script
│   └── test_*.sh               # Various test scripts
└── web-client/                 # Shared frontend (TODO)
```

## 🔧 Current Development Tasks

### **Immediate Tasks (Phase 1 Completion):**
1. Fix DeepSeek backend configuration issues
2. Complete Mineru backend implementation
3. Implement orchestrator server
4. Test multi-backend deployment

### **Testing Commands:**
```bash
# Test individual backends
curl http://localhost:5000/health  # DeepSeek
curl http://localhost:5001/health  # Mineru

# Test orchestrator (when implemented)
curl http://localhost:8080/health
```

## 🛠️ Development Guidelines

### **When Working on Backends:**
- Each backend MUST implement the `OCRBackend` abstract class
- Backends use dedicated GPUs via `CUDA_VISIBLE_DEVICES`
- Backends should NOT have CORS - orchestrator handles frontend communication
- Backend servers run on specific ports (5000 for DeepSeek, 5001 for Mineru)

### **When Working on Orchestrator:**
- Orchestrator handles CORS for frontend communication
- Routes requests to appropriate backend based on `backend` parameter
- Provides unified health monitoring for all backends
- Runs on port 8080

### **When Working on Deployment:**
- Use `deployment/deploy.sh` for all deployments
- Never modify reference directories directly
- Test deployment scripts after any changes
- Verify all three services start correctly

## 📊 Expected Health Responses

### **DeepSeek Backend (port 5000):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true,
  "backend": "deepseek-ocr",
  "timestamp": 1730064000
}
```

### **Mineru Backend (port 5001):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true,
  "backend": "mineru",
  "timestamp": 1730064000
}
```

### **Orchestrator (port 8080):**
```json
{
  "status": "healthy",
  "deepseek_status": "healthy",
  "mineru_status": "healthy",
  "timestamp": 1730064000
}
```

## 🔍 Common Issues & Solutions

### **GPU Memory Issues:**
- **Symptom**: Model loading fails with CUDA out of memory
- **Solution**: Ensure `CUDA_VISIBLE_DEVICES` is set correctly (0 for DeepSeek, 1 for Mineru)

### **Import Errors:**
- **Symptom**: Missing modules when starting servers
- **Solution**: Run `deployment/setup.sh` to install all dependencies

### **Port Conflicts:**
- **Symptom**: "Address already in use" errors
- **Solution**: Kill existing processes with `pkill -9 python3`

### **Model Loading Failures:**
- **Symptom**: `model_loaded: false` in health response
- **Solution**: Check model files exist in `models/deepseek-ocr/` and `models/mineru/`

## 🚨 Emergency Procedures

### **Server Crash Recovery:**
1. SSH to server: `ssh -p 40032 zakir@223.166.245.194`
2. Kill old processes: `pkill -9 python3`
3. Navigate to project: `cd /home/zakir/ocr-project`
4. Start services: `cd deployment && ./startup.sh`

### **Deployment Issues:**
1. Check git status: `git status`
2. Pull latest changes: `git fetch origin && git reset --hard origin/master`
3. Re-run setup: `cd deployment && ./setup.sh`
4. Restart services: `./startup.sh`

## 📝 Documentation Updates

When making significant changes:
1. Update this CLAUDE.md file
2. Update PLAN.md with current progress
3. Test deployment scripts still work
4. Verify all services start correctly

---

**Last Updated**: 2025-10-24
**Current Status**: 🟡 Phase 1 (Backend Isolation) - Almost Complete
**Known Issues**: Configuration issues in DeepSeek backend
**Deployment Method**: `./deployment/deploy.sh`
**Next Phase**: Phase 2 (Orchestrator Development)
- never ever run this code locally .. later on we will test and run it on the server
- never ever run this code locally .. later on we will test and run it on the server
do you understand me !!
