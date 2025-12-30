# Multi-Backend OCR System

A complete, production-ready multi-backend OCR system that runs DeepSeek-OCR and Mineru simultaneously on dedicated GPUs with complete isolation. This system provides a unified interface for OCR processing with backend selection, comparison capabilities, and comprehensive testing.

## 🎯 Project Overview

This system provides a unified OCR solution that leverages multiple OCR backends simultaneously, allowing users to choose the best backend for their specific use case or compare results between different OCR engines. The system is fully implemented and ready for production deployment.

### 🎉 **PROJECT STATUS: COMPLETE** - All phases successfully implemented!

### Key Features
- **Multi-Backend Support**: Run DeepSeek-OCR and Mineru simultaneously with dedicated GPU isolation
- **Orchestrator Server**: Intelligent request routing and unified API responses
- **Enhanced Web Client**: Modern React interface with backend selection and comparison view
- **PDF Support**: Multi-page PDF processing with page selection
- **Unified Response Format**: Standardized JSON responses with markdown rendering
- **Comprehensive Testing**: Complete test suite for health, images, PDFs, and system integration
- **Configurable Deployment**: Flexible deployment with configurable server parameters

## 🏗️ Architecture

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

## 📊 Current Status

### ✅ **Implementation Progress (All Phases Complete)**
- **Phase 0**: ✅ **Completed** - Common interface & project structure
- **Phase 1**: ✅ **Completed** - Backend isolation & GPU assignment
- **Phase 2**: ✅ **Completed** - Orchestrator development
- **Phase 3**: ✅ **Completed** - Web client enhancement
- **Phase 4**: ✅ **Completed** - Response processing

### **Current Components (All Operational)**
| Component | Status | Port | GPU | Notes |
|-----------|--------|------|-----|--------|
| DeepSeek Backend | ✅ **Operational** | 5000 | 0 | Full OCR implementation with image/PDF support |
| Mineru Backend | ✅ **Operational** | 5001 | 1 | Full OCR implementation with image/PDF support |
| Orchestrator | ✅ **Operational** | 8080 | - | Complete routing, health monitoring, unified API |
| Web Client | ✅ **Operational** | 3000 | - | Enhanced React app with backend selection & comparison |

### **Deployment System**
- **Automated Deployment**: `deployment/deploy.sh` with configurable server parameters
- **Comprehensive Testing**: Full test suite for health, images, PDFs, and system integration
- **Service Management**: Complete startup/shutdown scripts for all components

## 🚀 Quick Start

### Prerequisites
- Access to server with 2x RTX 3090 GPUs (or compatible GPUs with sufficient VRAM)
- Git repository access
- SSH access to deployment server

### Standard Deployment (Recommended)
```bash
# Deploy all changes to server with configurable parameters
./deployment/deploy.sh -m "Your descriptive commit message" -s server_address -p ssh_port -d project_directory

# Examples:
./deployment/deploy.sh -m "Update OCR system" -s zakir@192.168.1.100 -p 40032
./deployment/deploy.sh -m "Quick update" -s root@10.0.1.50 -d /opt/ocr-project
./deployment/deploy.sh -m "Standard deployment"  # Uses defaults
```

### Manual Deployment (if script fails)
```bash
# Commit and push changes
git add .
git commit -m "Your changes"
git push origin master

# SSH to server with port forwarding
ssh -p SSH_PORT SERVER_ADDRESS -L 8080:localhost:8080 -L 5000:localhost:5000 -L 5001:localhost:5001

# Deploy on server
pkill -9 python3
cd PROJECT_DIRECTORY
git fetch origin && git reset --hard origin/master
cd deployment
./setup.sh
./startup.sh
```

### Quick Restart (if services already running)
```bash
# SSH to server
ssh -p SSH_PORT SERVER_ADDRESS

# Restart services only
pkill -9 python3
cd PROJECT_DIRECTORY/deployment
./startup.sh [optional_project_root]
```

### Comprehensive Testing
```bash
# Test all servers and model loading
./deployment/test_server_health.sh

# Test image processing for both backends
./deployment/test_image_endpoints.sh

# Test PDF processing for both backends
./deployment/test_pdf_endpoints.sh

# Run comprehensive system test
./deployment/test_system.sh

# Test web client functionality
./deployment/test_phase3_web_client.sh
```

## 📁 Project Structure

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
│   ├── deploy.sh               # Main deployment script (configurable parameters)
│   ├── setup.sh                # Main setup orchestrator
│   ├── setup_deepseek.sh       # DeepSeek backend setup
│   ├── setup_mineru.sh         # Mineru backend setup
│   ├── setup_orchestrator.sh   # Orchestrator setup
│   ├── startup.sh              # Service startup script
│   ├── startup_deepseek.sh     # DeepSeek startup script
│   ├── startup_mineru.sh       # Mineru startup script
│   └── test_*.sh               # Comprehensive test scripts
├── web-client/                 # Enhanced React frontend
│   ├── src/                    # React source code
│   │   ├── App.jsx            # Main application with backend selection
│   │   ├── components/        # Reusable components
│   │   └── config.js          # Configuration
│   ├── package.json           # Dependencies
│   └── vite.config.js         # Build configuration
├── deepseekocr-reference/      # Reference implementation (read-only)
├── mineru-reference/           # Reference implementation (read-only)
├── deployment-reference/       # Reference deployment scripts (read-only)
├── CLAUDE.md                   # AI assistant documentation
├── PLAN.md                     # Implementation plan
└── README.md                   # Project documentation (this file)
```

## 🔧 API Usage

### **Primary Endpoints (Orchestrator - Port 8080)**

#### **Health & Status**
```bash
# Orchestrator health
curl http://localhost:8080/health

# Backend information
curl http://localhost:8080/backends

# Individual backend health
curl http://localhost:5000/health  # DeepSeek
curl http://localhost:5001/health  # Mineru
```

#### **Image OCR**
```bash
# Process image with specific backend
curl -X POST -F "image=@test_image.png" -F "backend=deepseek-ocr" http://localhost:8080/ocr/image
curl -X POST -F "image=@test_image.png" -F "backend=mineru" http://localhost:8080/ocr/image

# Process image with auto-selection (orchestrator chooses)
curl -X POST -F "image=@test_image.png" http://localhost:8080/ocr/image
```

#### **PDF OCR**
```bash
# Process PDF with specific backend
curl -X POST -F "pdf=@test_document.pdf" -F "backend=deepseek-ocr" http://localhost:8080/ocr/pdf
curl -X POST -F "pdf=@test_document.pdf" -F "backend=mineru" http://localhost:8080/ocr/pdf

# Process PDF with page selection
curl -X POST -F "pdf=@test_document.pdf" -F "backend=deepseek-ocr" -F "pages=[1,2]" http://localhost:8080/ocr/pdf
```

### **Direct Backend Access (Advanced Use)**
```bash
# DeepSeek backend directly
curl -X POST -F "image=@test_image.png" http://localhost:5000/ocr/image

# Mineru backend directly
curl -X POST -F "image=@test_image.png" http://localhost:5001/ocr/image
```

### **Unified Response Format**
```json
{
  "success": true,
  "backend": "deepseek-ocr",
  "raw_result": {
    "text": "extracted text content",
    "boxes": [[x1, y1, x2, y2, text], ...],
    "metadata": {...}
  },
  "markdown": "processed markdown text",
  "source_markdown": "HTML-ready markdown with images",
  "boxes_image": "base64_encoded_image_with_boxes",
  "processing_time": 12.5,
  "image_name": "upload_12345.jpg"
}
```

## 🛠️ Development

### **Backend Development**
Each backend implements the `OCRBackend` abstract class (`shared/ocr_backend.py`):
- `load_model()` - Load model into GPU memory
- `ocr_image()` - Process single image
- `ocr_pdf()` - Process PDF document (multi-page support)
- `get_health_status()` - Return health information
- `cleanup()` - Release resources

### **GPU Isolation**
```python
# DeepSeek Server (GPU 0)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Mineru Server (GPU 1)
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
```

### **Orchestrator Development**
The orchestrator (`orchestrator/server.py`) provides:
- Request routing to appropriate backend
- Health monitoring and status tracking
- Unified API response formatting
- CORS handling for web client
- Error handling and fallback mechanisms

### **Web Client Development**
The React web client (`web-client/`) features:
- Backend selection (DeepSeek, Mineru, or auto)
- Comparison view for side-by-side results
- Image and PDF upload with preview
- Real-time processing status
- Markdown rendering with source view

### **Deployment Guidelines**
- Use `deployment/deploy.sh` for all deployments (configurable parameters)
- Backends should NOT have CORS (orchestrator handles frontend communication)
- Test deployment scripts after any changes
- Verify all three services start correctly
- Use comprehensive test scripts to validate functionality

## 📊 Performance

### **Resource Usage**
- **DeepSeek OCR**: ~17GB VRAM peak (6.23GB model + ~10GB KV cache)
- **Mineru**: ~15-20GB VRAM expected
- **Total VRAM**: ~35GB (fits perfectly in 48GB total with 2x RTX 3090)

### **Response Times**
- **DeepSeek OCR**: 10-60 seconds depending on image complexity
- **Mineru**: Similar range expected
- **Orchestrator**: < 100ms routing overhead
- **PDF Processing**: Additional time per page (parallel processing available)

### **System Requirements**
- **GPU**: 2x RTX 3090 (24GB VRAM each) or equivalent
- **CPU**: 8+ cores recommended
- **RAM**: 32GB+ system memory
- **Storage**: 50GB+ for models and temporary files

## 🔍 Troubleshooting

### **Common Issues**
1. **GPU Memory Conflicts**: Ensure `CUDA_VISIBLE_DEVICES` is set correctly (0 for DeepSeek, 1 for Mineru)
2. **Import Errors**: Run `deployment/setup.sh` to install all dependencies
3. **Port Conflicts**: Kill existing processes with `pkill -9 python3`
4. **Model Loading Failures**: Check model files exist in respective model directories
5. **CORS Issues**: Orchestrator handles CORS; backends should NOT have CORS enabled
6. **Service Startup Order**: Use `deployment/startup.sh` to ensure proper startup sequence

### **Health Check Responses**

#### **Orchestrator Health**
```bash
curl http://localhost:8080/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "deepseek_status": "healthy",
  "mineru_status": "healthy",
  "timestamp": 1730064000
}
```

#### **Backend Information**
```bash
curl http://localhost:8080/backends
```
**Expected Response:**
```json
{
  "backends": [
    {
      "name": "deepseek-ocr",
      "healthy": true,
      "port": 5000,
      "gpu": 0
    },
    {
      "name": "mineru",
      "healthy": true,
      "port": 5001,
      "gpu": 1
    }
  ]
}
```

#### **Individual Backend Health**
```bash
# DeepSeek Backend
curl http://localhost:5000/health

# Mineru Backend
curl http://localhost:5001/health
```
**Expected Response (both backends):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true,
  "backend": "backend-name",
  "timestamp": 1730064000
}
```

## 🚨 Emergency Procedures

### **Server Crash Recovery**
```bash
# SSH to server (replace with your server details)
ssh -p SSH_PORT SERVER_ADDRESS

# Kill existing processes
pkill -9 python3

# Navigate to project directory
cd PROJECT_DIRECTORY

# Start services
cd deployment && ./startup.sh
```

### **Deployment Issues**
```bash
# Check git status
git status

# Pull latest changes
git fetch origin && git reset --hard origin/master

# Re-run setup
cd deployment && ./setup.sh

# Restart services
./startup.sh
```

### **Service Startup Issues**
```bash
# Start services individually
cd deployment
./startup_deepseek.sh    # Start DeepSeek backend
./startup_mineru.sh      # Start Mineru backend
# Orchestrator starts automatically with startup.sh
```

### **Model Loading Issues**
```bash
# Check model directories
ls -la models/deepseek-ocr/
ls -la models/mineru/

# Re-run specific setup scripts
./setup_deepseek.sh
./setup_mineru.sh
```

## 📝 Documentation

### **Primary Documentation**
- **CLAUDE.md**: Detailed instructions for AI assistants (critical for development)
- **PLAN.md**: Implementation plan and architecture design
- **README.md**: Human-readable project overview (this file)

### **Code Documentation**
- **Backend Interfaces**: `shared/ocr_backend.py` (abstract base class)
- **API Contracts**: `shared/api_contract.py` (unified response format)
- **Configuration**: `orchestrator/config.py` (backend configuration)

### **Deployment Documentation**
- **Deployment Scripts**: `deployment/` directory with comprehensive scripts
- **Test Scripts**: Complete test suite for validation
- **Setup Scripts**: Individual component setup scripts

## 🤝 Contributing

### **Guidelines**
1. Follow the established project structure and patterns
2. Use the abstract `OCRBackend` interface for new backends
3. Test deployment scripts after any changes
4. Update documentation when making significant changes
5. Use the comprehensive test suite to validate functionality

### **Development Workflow**
1. Make changes locally (never run code locally - see CLAUDE.md)
2. Test deployment scripts if modified
3. Update documentation as needed
4. Deploy using `deployment/deploy.sh` with appropriate parameters
5. Verify all services start correctly and pass health checks

## 📄 License

This project is part of a private OCR system deployment.

---

**Last Updated**: 2025-12-30
**Current Status**: ✅ **PROJECT COMPLETE** - All phases successfully implemented
**Deployment Method**: `./deployment/deploy.sh` (configurable server parameters)
**Testing Coverage**: Comprehensive test suite for health, images, PDFs, and system integration
**Ready for Production**: Yes - Complete multi-backend OCR system with flexible deployment

### **Key Achievements**
- ✅ **Multi-Backend Support**: DeepSeek-OCR and Mineru running simultaneously
- ✅ **GPU Isolation**: Dedicated GPU assignment with complete isolation
- ✅ **Orchestrator**: Intelligent routing and unified API responses
- ✅ **Enhanced Web Client**: Modern interface with backend selection and comparison
- ✅ **PDF Support**: Multi-page PDF processing with page selection
- ✅ **Comprehensive Testing**: Full test suite for all components
- ✅ **Configurable Deployment**: Flexible deployment with configurable parameters
