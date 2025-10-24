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
- **Phase 1: COMPLETED** - Backend isolation & GPU assignment
- **Phase 2: COMPLETED** - Orchestrator development
- **Phase 3: COMPLETED** - Web client enhancement
- **Phase 4: COMPLETED** - Response processing

### **🎉 PROJECT COMPLETE - All phases successfully implemented!**

## 🚀 Deployment & Testing Guide

### **Standard Deployment Process**

#### **1. Full Deployment (Recommended)**

CURRENT_SSH_SERVER_ADDRESS="root@115.231.176.132" 
CURRENT_SSH_SERVER_PORT="51498"

```bash
# Deploy all changes to server with configurable parameters
./deployment/deploy.sh -m "Your descriptive commit message" -s server_address -p ssh_port -d project_directory

# Examples:
./deployment/deploy.sh -m "Update OCR system" -s zakir@192.168.1.100 -p 40032
./deployment/deploy.sh -m "Quick update" -s root@10.0.1.50 -d /opt/ocr-project
./deployment/deploy.sh -m "Standard deployment"  # Uses defaults
```

#### **2. Manual Deployment (if script fails)**
```bash
# Commit and push changes
git add .
git commit -m "Your changes"
git push origin master

# SSH to server with port forwarding (replace with your server details)
ssh -p SSH_PORT SERVER_ADDRESS -L 8080:localhost:8080 -L 5000:localhost:5000 -L 5001:localhost:5001

# Deploy on server
pkill -9 python3
cd PROJECT_DIRECTORY
git fetch origin && git reset --hard origin/master
cd deployment
./setup.sh
./startup.sh
```

#### **3. Quick Restart (if services already running)**
```bash
# SSH to server (replace with your server details)
ssh -p SSH_PORT SERVER_ADDRESS

# Restart services only
pkill -9 python3
cd PROJECT_DIRECTORY/deployment
./startup.sh [optional_project_root]
```

### **Comprehensive Testing Procedures**

#### **1. Health & Model Loading Test**
```bash
# Test all servers and model loading
./deployment/test_server_health.sh
```
**Expected Output:**
- All servers responding (✅)
- Models loaded into GPU memory (✅)
- GPU resources available (✅)

#### **2. Image OCR Endpoint Test**
```bash
# Test image processing for both backends
./deployment/test_image_endpoints.sh
```
**Tests:**
- Direct backend endpoints (5000, 5001)
- Orchestrator routing (8080)
- Backend selection functionality
- Unified response format

#### **3. PDF OCR Endpoint Test**
```bash
# Test PDF processing for both backends
./deployment/test_pdf_endpoints.sh
```
**Tests:**
- Multi-page PDF processing
- Backend-specific PDF handling
- Orchestrator routing with PDFs
- Unified response format

#### **4. System Integration Test**
```bash
# Run comprehensive system test
./deployment/test_system.sh
```
**Tests:**
- All endpoints and routing
- Health monitoring
- Error handling
- Performance metrics

#### **5. Web Client Test**
```bash
# Test web client functionality
./deployment/test_phase3_web_client.sh
```
**Tests:**
- Frontend backend selection
- Comparison view
- File upload and preview
- Real-time status updates

### **Individual Component Testing**

#### **Quick Health Checks**
```bash
# Orchestrator health
curl http://localhost:8080/health

# DeepSeek backend health
curl http://localhost:5000/health

# Mineru backend health
curl http://localhost:5001/health
```

#### **Backend Information**
```bash
# List available backends with status
curl http://localhost:8080/backends
```

#### **Manual OCR Testing**
```bash
# Test image OCR with DeepSeek
curl -X POST -F "image=@test_image.png" -F "backend=deepseek-ocr" http://localhost:8080/ocr/image

# Test PDF OCR with Mineru
curl -X POST -F "pdf=@test_document.pdf" -F "backend=mineru" http://localhost:8080/ocr/pdf

# Test with page selection (PDF only)
curl -X POST -F "pdf=@test_document.pdf" -F "backend=deepseek-ocr" -F "pages=[1,2]" http://localhost:8080/ocr/pdf
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

## 🔧 Project Status

### **🎉 PROJECT COMPLETE - All Development Tasks Completed!**

### **Completed Features:**
1. ✅ **DeepSeek Backend** - Running on GPU 0 (port 5000)
2. ✅ **Mineru Backend** - Running on GPU 1 (port 5001)
3. ✅ **Orchestrator Server** - Complete implementation (port 8080)
4. ✅ **Web Client** - Enhanced with backend selection and comparison
5. ✅ **PDF Support** - Multi-page PDF upload and processing
6. ✅ **Response Processing** - Unified markdown generation
7. ✅ **Health Monitoring** - Real-time backend status tracking
8. ✅ **Deployment System** - Complete automation scripts

### **Quick Testing Commands:**
```bash
# Basic health checks
curl http://localhost:8080/health    # Orchestrator
curl http://localhost:5000/health    # DeepSeek
curl http://localhost:5001/health    # Mineru

# Backend information
curl http://localhost:8080/backends  # All backend status

# Comprehensive testing
./deployment/test_server_health.sh    # Health & models
./deployment/test_image_endpoints.sh  # Image OCR
./deployment/test_pdf_endpoints.sh    # PDF OCR
./deployment/test_system.sh           # Full system
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

## 🔍 Deployment Issues & Solutions

### **Setup & Installation Issues**

#### **DeepSeek Model Download Failures:**
- **Symptom**: HuggingFace download fails or times out
- **Solution**:
  ```bash
  # Manual download with retry
  cd deployment
  ./setup_deepseek.sh
  # If fails, run individual commands from the script
  ```

#### **Mineru Package Installation Issues:**
- **Symptom**: `uv pip install` fails or hangs
- **Solution**:
  ```bash
  # Use standard pip instead
  pip install mineru[core]
  # Or install individual components
  pip install mineru flask flask-cors Pillow
  ```

#### **Virtual Environment Issues:**
- **Symptom**: Python packages not found in venv
- **Solution**:
  ```bash
  # Recreate virtual environments
  cd deployment
  rm -rf ../backends/deepseek-ocr/venv
  rm -rf ../backends/mineru/venv
  rm -rf ../orchestrator/venv
  ./setup.sh
  ```

### **Runtime Issues**

#### **GPU Memory Issues:**
- **Symptom**: Model loading fails with CUDA out of memory
- **Solution**: Ensure `CUDA_VISIBLE_DEVICES` is set correctly (0 for DeepSeek, 1 for Mineru)

#### **Import Errors:**
- **Symptom**: Missing modules when starting servers
- **Solution**: Run `deployment/setup.sh` to install all dependencies

#### **Port Conflicts:**
- **Symptom**: "Address already in use" errors
- **Solution**: Kill existing processes with `pkill -9 python3`

#### **Model Loading Failures:**
- **Symptom**: `model_loaded: false` in health response
- **Solution**: Check model files exist in `models/deepseek-ocr/` and `models/mineru/`

### **Deployment Script Issues**

#### **SSH Connection Failures:**
- **Symptom**: `deploy.sh` fails at SSH step
- **Solution**:
  ```bash
  # Manual deployment with correct server parameters
  git add . && git commit -m "fix" && git push
  ssh -p SSH_PORT SERVER_ADDRESS -L 8080:localhost:8080 -L 5000:localhost:5000 -L 5001:localhost:5001
  # Then run manual deployment commands
  ```

#### **Git Reset Issues:**
- **Symptom**: `git reset --hard` fails
- **Solution**:
  ```bash
  # Force reset
  git fetch origin
  git reset --hard origin/master --force
  ```

#### **Service Startup Order:**
- **Symptom**: Backends start before dependencies are ready
- **Solution**:
  ```bash
  # Add delays in startup.sh
  sleep 10  # Wait for orchestrator
  # Start backends sequentially
  ```

## 🚨 Emergency Procedures

### **Server Crash Recovery:**
1. SSH to server: `ssh -p SSH_PORT SERVER_ADDRESS`
2. Kill old processes: `pkill -9 python3`
3. Navigate to project: `cd PROJECT_DIRECTORY`
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

**Last Updated**: 2025-10-25
**Current Status**: ✅ **PROJECT COMPLETE** - All phases successfully implemented
**Known Issues**: None - All components implemented and tested
**Deployment Method**: `./deployment/deploy.sh` (configurable server parameters)
**Testing Methods**: Comprehensive test scripts for health, images, PDFs, and system integration
**Ready for Production**: Yes - Complete multi-backend OCR system with flexible deployment

### **Deployment System Summary**

#### **Key Deployment Scripts:**
- `deploy.sh` - Full automated deployment with git commit/push and SSH tunneling
- `setup.sh` - Main setup orchestrator for all components
- `startup.sh` - Service startup script for all three servers
- `setup_*.sh` - Individual backend setup scripts
- `test_*.sh` - Comprehensive testing scripts

#### **Configurable Deployment Parameters:**
- **Server Address** (`-s`): Configurable server address (e.g., `zakir@192.168.1.100`)
- **SSH Port** (`-p`): Configurable SSH port (default: `22`)
- **Project Directory** (`-d`): Configurable project directory (default: `/home/zakir/ocr-project`)
- **Commit Message** (`-m`): Optional commit message for git
- **SSH Tunneling**: Automatic port forwarding for 8080, 5000, 5001

#### **Usage Examples:**
```bash
# Full deployment with custom server
./deploy.sh -m "Update OCR system" -s zakir@192.168.1.100 -p 40032

# Deployment with custom project directory
./deploy.sh -s root@10.0.1.50 -d /opt/ocr-project

# Quick deployment (uses defaults)
./deploy.sh -m "Quick update"

# Start services with custom project root
./startup.sh /home/custom/ocr-project
```

#### **Service Architecture:**
- **Orchestrator**: Port 8080 (main entry point)
- **DeepSeek**: Port 5000 (GPU 0)
- **Mineru**: Port 5001 (GPU 1)

#### **Testing Coverage:**
- ✅ Server health and model loading
- ✅ Image OCR endpoints
- ✅ PDF OCR endpoints (multi-page)
- ✅ System integration
- ✅ Web client functionality
- ✅ Backend selection and routing

- never ever run this code locally .. later on we will test and run it on the server
- never ever run this code locally .. later on we will test and run it on the server
do you understand me !!





CURRENT_SSH_SERVER_ADDRESS="root@115.231.176.132" 
CURRENT_SSH_SERVER_PORT="51498"
- use sleep to wait for long runnign task