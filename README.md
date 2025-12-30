# Multi-Backend OCR System

A high-performance, multi-backend OCR system that runs DeepSeek-OCR and Mineru simultaneously on dedicated GPUs with complete isolation.

## 🎯 Project Overview

This system provides a unified OCR solution that can leverage multiple OCR backends simultaneously, allowing users to choose the best backend for their specific use case or compare results between different OCR engines.

### Key Features
- **Multi-Backend Support**: Run DeepSeek-OCR and Mineru simultaneously
- **GPU Isolation**: Dedicated GPU assignment (RTX 3090 #1 for DeepSeek, RTX 3090 #2 for Mineru)
- **Client Selection**: Users can specify which backend to use per request
- **Unified API**: Standardized response format across all backends
- **Performance Comparison**: Built-in tools to compare accuracy and speed

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

### Implementation Progress
- **Phase 0**: ✅ **Completed** - Common interface & project structure
- **Phase 1**: 🟡 **Almost Complete** - Backend isolation & GPU assignment
- **Phase 2**: ⚪ **Todo** - Orchestrator development
- **Phase 3**: ⚪ **Todo** - Web client enhancement
- **Phase 4**: ⚪ **Todo** - Response processing

### Current Components
| Component | Status | Port | GPU | Notes |
|-----------|--------|------|-----|--------|
| DeepSeek Backend | 🟡 Mostly Complete | 5000 | 0 | Needs configuration fixes |
| Mineru Backend | ⚪ Basic Structure | 5001 | 1 | Needs implementation |
| Orchestrator | ⚪ Placeholder | 8080 | - | Needs development |
| Web Client | ⚪ Todo | 3000 | - | Needs enhancement |

## 🚀 Quick Start

### Prerequisites
- Access to Vast.ai server with 2x RTX 3090 GPUs
- Git repository access
- SSH access to deployment server

### Deployment
```bash
# Deploy the entire system
./deployment/deploy.sh -m "Initial deployment"

# Or manually
./deployment/setup.sh    # Setup all components
./deployment/startup.sh  # Start all services
```

### Testing
```bash
# Test individual backends
curl http://localhost:5000/health  # DeepSeek
curl http://localhost:5001/health  # Mineru

# Test orchestrator (when implemented)
curl http://localhost:8080/health
```

## 📁 Project Structure

```
deepseek-ocr-vastai/
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

## 🔧 API Usage

### Client Request Format
```json
{
  "image": "file_data",
  "backend": "deepseek-ocr" | "mineru",
  "prompt": "optional custom prompt"
}
```

### Unified Response Format
```json
{
  "success": true,
  "backend": "deepseek-ocr",
  "raw_result": {
    "deepseek": "<|ref|>text<|/ref|><|det|>[[...]]<|/det|>...",
    "mineru": {
      "content": "structured json output",
      "metadata": {...}
    }
  },
  "markdown": "processed markdown text",
  "source_markdown": "HTML-ready markdown with images",
  "boxes_image": "base64_encoded_image_with_boxes",
  "processing_time": 12.5,
  "image_name": "upload_12345.jpg"
}
```

## 🛠️ Development

### Backend Development
Each backend must implement the `OCRBackend` abstract class:
- `load_model()` - Load model into GPU memory
- `ocr_image()` - Process single image
- `ocr_pdf()` - Process PDF document
- `get_health_status()` - Return health information
- `cleanup()` - Release resources

### GPU Isolation
```python
# DeepSeek Server (GPU 0)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Mineru Server (GPU 1)
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
```

### Deployment
- Use `deployment/deploy.sh` for all deployments
- Backends should NOT have CORS (orchestrator handles frontend communication)
- Test deployment scripts after any changes
- Verify all three services start correctly

## 📊 Performance

### Expected Resource Usage
- **DeepSeek OCR**: ~17GB VRAM peak
- **Mineru**: ~15-20GB VRAM expected
- **Total VRAM**: ~35GB (fits perfectly in 48GB total)

### Expected Response Times
- **DeepSeek OCR**: 10-60 seconds
- **Mineru**: Similar range expected
- **Orchestrator**: < 100ms routing overhead

## 🔍 Troubleshooting

### Common Issues
1. **GPU Memory Conflicts**: Ensure `CUDA_VISIBLE_DEVICES` is set correctly
2. **Import Errors**: Run `deployment/setup.sh` to install dependencies
3. **Port Conflicts**: Kill existing processes with `pkill -9 python3`
4. **Model Loading Failures**: Check model files exist in respective model directories

### Health Check Responses
```bash
# DeepSeek Backend
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true,
  "backend": "deepseek-ocr",
  "timestamp": 1730064000
}
```

## 🚨 Emergency Procedures

### Server Crash Recovery
```bash
ssh -p 40032 zakir@223.166.245.194
pkill -9 python3
cd /home/zakir/deepseek-ocr-kaggle
cd deployment && ./startup.sh
```

### Deployment Issues
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

## 📝 Documentation

- **CLAUDE.md**: Detailed instructions for AI assistants
- **PLAN.md**: Implementation plan and progress tracking
- **README.md**: Human-readable project overview (this file)

## 🤝 Contributing

1. Follow the established project structure
2. Use the abstract `OCRBackend` interface for new backends
3. Test deployment scripts after changes
4. Update documentation when making significant changes

## 📄 License

This project is part of a private OCR system deployment.

---

**Last Updated**: 2025-10-24
**Current Status**: Phase 1 (Backend Isolation) - Almost Complete
**Deployment Method**: `./deployment/deploy.sh`
**Next Phase**: Phase 2 (Orchestrator Development)
