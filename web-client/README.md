# Multi-Backend OCR Web Client

A modern React application for interacting with the Multi-Backend OCR System. Supports DeepSeek-OCR and Mineru backends with comparison capabilities.

## Features

- **Multi-Backend Support**: Choose between DeepSeek-OCR, Mineru, or automatic selection
- **Comparison View**: Side-by-side comparison of results from different backends
- **Drag & Drop Interface**: Easy image and PDF upload with drag and drop support
- **Real-time Preview**: Preview files before processing
- **Markdown Rendering**: View OCR results as rendered markdown
- **Source View**: Toggle between rendered markdown and source text
- **Bounding Box Visualization**: See detected regions with bounding boxes
- **PDF Support**: Multi-page PDF upload and processing
- **Responsive Design**: Works on desktop and mobile devices

## Setup

### Prerequisites

- Node.js 16+ and npm
- Multi-Backend OCR System running with:
  - Orchestrator on `http://localhost:8080`
  - DeepSeek backend on `http://localhost:5000`
  - Mineru backend on `http://localhost:5001`

### Installation

1. **Navigate to the web-client directory:**
   ```bash
   cd ocr-project/web-client
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser to:**
   ```
   http://localhost:3000
   ```

## Usage

1. **Select Backend**: Choose between DeepSeek-OCR, Mineru, or "Auto" (orchestrator decides)
2. **Upload File**: Drag and drop an image or PDF file, or click to select
3. **Preview**: See the uploaded file before processing
4. **Process**: Click "Extract Text" to send to the selected backend
5. **View Results**:
   - See the original file and file with bounding boxes (images)
   - Toggle between rendered markdown and source view
   - Browse extracted sub-images
   - Compare results side-by-side if using comparison mode
6. **Process Another**: Click "Process Another File" to start over

## API Integration

The client communicates with the Orchestrator server (port 8080) which routes requests to the appropriate backend:

- **POST /ocr/image**: Send image for OCR processing (with backend parameter)
- **POST /ocr/pdf**: Send PDF for OCR processing (with backend parameter)
- **GET /health**: Check orchestrator and backend health
- **GET /backends**: Get information about available backends
- **Proxy Configuration**: Vite dev server proxies API calls to Orchestrator

## Project Structure

```
web-client/
├── src/
│   ├── App.jsx              # Main application component with backend selection
│   ├── main.jsx             # React entry point
│   ├── index.css            # Global styles
│   ├── config.js            # Configuration and constants
│   └── components/          # Reusable components
│       ├── BackendSelector/ # Backend selection component
│       ├── FileUpload/      # File upload component
│       ├── ResultView/      # Result display component
│       └── ComparisonView/  # Side-by-side comparison component
├── package.json             # Dependencies and scripts
├── vite.config.js           # Vite configuration
└── index.html              # HTML template
```

## Dependencies

### Core Dependencies
- **React 18**: UI framework
- **React DOM**: DOM rendering
- **React Markdown**: Markdown rendering
- **Axios**: HTTP client for API calls
- **Lucide React**: Icon library
- **React Dropzone**: File upload with drag and drop

### Development Dependencies
- **Vite**: Build tool and dev server
- **@vitejs/plugin-react**: React plugin for Vite

## Customization

### Styling
- CSS is organized in `index.css`
- Uses a clean, modern design with responsive layout
- Easy to customize colors, fonts, and layout

### Components
- Main application logic is in `App.jsx`
- Can be extended with additional components in `src/components/`

### API Configuration
- Server URL is configured in `vite.config.js` (proxies to orchestrator on port 8080)
- Backend selection is handled through the `backend` parameter in API requests
- Change the proxy target if orchestrator runs on different port

## Build for Production

```bash
npm run build
```

This creates a `dist` folder with optimized production files.

## Troubleshooting

1. **Connection Errors**: Ensure Orchestrator server is running on port 8080 and backends on 5000/5001
2. **CORS Issues**: Orchestrator handles CORS; check orchestrator configuration
3. **Build Errors**: Clear node_modules and reinstall dependencies
4. **File Upload Issues**: Verify file format and size (images and PDFs supported)
5. **Backend Selection Issues**: Check backend health via `/health` endpoints
6. **PDF Processing Issues**: Ensure PDF backend support is properly configured

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

Part of the Multi-Backend OCR System project. See main project for license details.