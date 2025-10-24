# Multi-Backend OCR Architecture Plan

## 🎯 **Updated Goal**
Support multiple OCR backends (DeepSeek-OCR & Mineru) running simultaneously with:
- **Dedicated GPU isolation** (2x RTX 3090, 24GB VRAM each)
- **Simultaneous model loading** - no switching logic needed
- **Client-specified backend selection** per request
- **Unified web-client** for easy comparison
- **Structured response handling** (JSON raw + markdown processed)

## 🔧 **Hardware Analysis**

### **Available Resources:**
- **GPU**: 2x RTX 3090 (24GB VRAM each)
- **CPU**: 36 cores, 64GB RAM
- **Storage**: Sufficient for multiple model weights

### **Resource Allocation:**
- **DeepSeek OCR**: RTX 3090 #1 (dedicated)
- **Mineru**: RTX 3090 #2 (dedicated)
- **CPU/Memory**: More than adequate for both backends + orchestrator

### **Memory Requirements:**
- **DeepSeek OCR**: ~17GB peak (6.23GB model + ~10GB KV cache)
- **Mineru**: Similar requirements (likely 15-20GB range)
- **Total**: ~35GB VRAM - **FITS PERFECTLY** with 48GB total

## 🏗️ **Architecture Design**

### **Three-Server Structure:**
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

### **Port Allocation:**
- **Orchestrator**: Port 8080 (main entry point)
- **DeepSeek Backend**: Port 5000 (GPU 0)
- **Mineru Backend**: Port 5001 (GPU 1)

## 📁 **Repository Structure**

```
project/
├── backends/
│   ├── deepseek-ocr/
│   │   ├── venv/                    # DeepSeek-specific environment
│   │   ├── server.py                # DeepSeek Flask server (GPU 0)
│   │   ├── requirements.txt         # DeepSeek dependencies
│   │   └── models/                  # DeepSeek model weights
│   ├── mineru/
│   │   ├── venv/                    # Mineru-specific environment
│   │   ├── server.py                # Mineru Flask wrapper (GPU 1)
│   │   ├── requirements.txt         # Mineru dependencies
│   │   └── models/                  # Mineru model weights
├── orchestrator/
│   ├── server.py                    # Main orchestrator
│   ├── requirements.txt             # Orchestrator dependencies
│   └── config.py                    # Backend configuration
├── web-client/                      # Shared frontend
│   ├── src/
│   │   ├── App.jsx                  # Updated with backend selection
│   │   └── config.js                # Updated endpoints
│   └── package.json
├── shared/
│   ├── api_contract.py              # Unified API response format
│   └── utils.py                     # Common utilities
└── deployment/
    ├── deploy.sh                    # Unified deployment script
    └── startup.sh                   # Start all services
```

## 🔄 **API Response Standardization**

### **Unified Response Format:**
```json
{
  "success": true,
  "backend": "deepseek-ocr" | "mineru",
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

### **Backend-Specific Processing:**
- **DeepSeek**: Raw result as text, processed to markdown
- **Mineru**: Raw result as JSON, processed to markdown using native post-processor

## 🚀 **Implementation Phases**

### **Phase 0: Common Interface & Project Structure**
1. **Create Common OOP Interface** - Define abstract base class in `shared/ocr_backend.py`
2. **Define Method Signatures** - Function names and signatures only (no implementation): model initialization, image OCR, PDF OCR, common functionality
3. **Setup Project Structure** - Create all directories and key files with placeholders
4. **API Contract Definition** - Standardize request/response formats in `shared/api_contract.py`

### **Phase 1: Backend Isolation & GPU Assignment**
1. **DeepSeek Backend** - Modify to use GPU 0 exclusively
2. **Mineru Backend** - Create Flask wrapper using GPU 1 exclusively
3. **Environment Setup** - Separate venv for each backend
4. **GPU Configuration** - Set CUDA_VISIBLE_DEVICES for isolation

### **Phase 2: Orchestrator Development**
1. **Request Routing** - Route to specified backend
2. **Backend Selection** - Client specifies backend in request
3. **Health Monitoring** - Monitor both backend status
4. **Error Handling** - Immediate error on backend failure (no fallback)

### **Phase 3: Web Client Enhancement**
1. **Backend Selection UI** - Dropdown to choose OCR backend
2. **Comparison View** - Side-by-side results display
3. **Performance Metrics** - Response time comparison
4. **Unified Response Handling** - Standardized display for both backends

### **Phase 4: Response Processing**
1. **DeepSeek Processing** - Maintain existing text→markdown pipeline
2. **Mineru Processing** - JSON→markdown using native post-processor
3. **Image Handling** - Unified bounding box/image extraction
4. **MathJax Integration** - Consistent equation rendering

## 🔧 **Technical Implementation Details**

### **GPU Isolation:**
```python
# DeepSeek Server (GPU 0)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Mineru Server (GPU 1)
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
```

### **Orchestrator Request Flow:**
```python
# Client request
{
  "image": file,
  "backend": "deepseek-ocr" | "mineru",
  "prompt": "optional custom prompt"
}

# Orchestrator routing
if backend == "deepseek-ocr":
    response = requests.post("http://localhost:5000/ocr/image", ...)
elif backend == "mineru":
    response = requests.post("http://localhost:5001/ocr/image", ...)
```

### **Backend Health Monitoring:**
- Each backend exposes `/health` endpoint
- Orchestrator monitors both backends
- Immediate error if selected backend is unavailable

## 🚨 **Risk Mitigation**

### **High Priority Risks:**
1. **GPU Memory Conflicts** - SOLVED by dedicated GPU assignment
2. **Dependency Conflicts** - SOLVED by separate virtual environments
3. **API Response Differences** - Managed by response normalization
4. **Performance Bottlenecks** - Ample CPU/RAM resources available

### **No Fallback Strategy:**
- **Immediate Error** if selected backend fails
- **No Automatic Switching** - Client must explicitly choose
- **Clear Error Messages** - Indicate which backend failed

## 📊 **Expected Performance**

### **Simultaneous Processing:**
- Both backends can process requests concurrently
- No resource contention due to GPU isolation
- Orchestrator overhead minimal

### **Response Times:**
- **DeepSeek OCR**: ~10-60 seconds (current performance)
- **Mineru**: Similar range expected
- **Orchestrator**: < 100ms routing overhead

## 🎯 **Success Criteria**

- Both backends run simultaneously without interference
- Dedicated GPU assignment working correctly
- Client can specify backend per request
- Unified API responses for frontend consistency
- No dependency conflicts between environments
- Immediate error handling (no fallback)

## 🔄 **Deployment Strategy**

### **Unified Deployment:**
```bash
./deployment/deploy.sh
```

### **Service Startup:**
```bash
./deployment/startup.sh
# Starts: Orchestrator (8080), DeepSeek (5000), Mineru (5001)
```

This architecture leverages your excellent hardware resources to provide a robust, high-performance multi-backend OCR system with complete isolation and simultaneous operation.

## 📚 **Reference Materials**

**Note**: The `deepseekocr-reference/` , `mineru-reference/` and `deployment-reference/` directories contain the original implementation code and are **gitignored**. These serve **only as educational/helper references** for writing the new multi-backend architecture from scratch. The reference code is **not part of the running system**.
