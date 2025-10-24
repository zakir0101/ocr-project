// Configuration for Multi-Backend OCR Client
// This file allows easy configuration for different deployment environments

const config = {
  // Server configuration
  server: {
    // Orchestrator URL - main entry point for all OCR requests
    baseUrl: 'http://localhost:8080',

    // API endpoints
    endpoints: {
      ocrImage: '/ocr/image',
      ocrPdf: '/ocr/pdf',
      health: '/health',
      backends: '/backends'
    }
  },

  // Backend options
  backends: {
    options: [
      { value: 'deepseek-ocr', label: 'DeepSeek OCR', description: 'DeepSeek OCR Backend' },
      { value: 'mineru', label: 'Mineru', description: 'Mineru Backend' }
    ],
    default: 'deepseek-ocr'
  },

  // Application settings
  app: {
    name: 'Multi-Backend OCR',
    version: '2.0.0',
    description: 'OCR with multiple AI backends (DeepSeek & Mineru)',

    // File upload settings
    upload: {
      maxFileSize: 50 * 1024 * 1024, // 50MB (increased for PDFs)
      allowedTypes: ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'application/pdf'],

      // Validation messages
      messages: {
        fileTooLarge: 'File size must be less than 50MB',
        invalidType: 'Please upload a valid image (JPEG, PNG, WebP, GIF) or PDF file',
        uploadError: 'Failed to upload file. Please try again.'
      }
    },

    // OCR processing settings
    processing: {
      timeout: 120000, // 120 seconds (matches orchestrator timeout)
      retryAttempts: 3,

      // Default prompts (passed to backends)
      prompts: {
        document: 'Extract text from this document and convert to markdown format.',
        freeOcr: 'Perform OCR on this image.',
        parseFigure: 'Parse the figure and extract information.',
        describe: 'Describe this image in detail.'
      }
    }
  },

  // UI settings
  ui: {
    theme: {
      primary: '#007bff',
      secondary: '#6c757d',
      success: '#28a745',
      danger: '#dc3545',
      warning: '#ffc107',
      info: '#17a2b8'
    },

    layout: {
      maxWidth: '1200px',
      sidebarWidth: '300px',
      headerHeight: '80px'
    }
  }
};

// Server URL helper
export const getServerUrl = () => {
  // Always use the static server URL
  return config.server.baseUrl;
};

// API URL helper
export const getApiUrl = (endpoint) => {
  const baseUrl = getServerUrl();
  const fullEndpoint = config.server.endpoints[endpoint] || endpoint;

  // If we have a base URL, prepend it
  if (baseUrl) {
    return `${baseUrl}${fullEndpoint}`;
  }

  // Otherwise use relative URL (will be proxied in dev)
  return fullEndpoint;
};

// Development mode check
export const isDevelopment = () => {
  return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
};

// Backend selection helpers
export const getBackendOptions = () => {
  return config.backends.options;
};

export const getDefaultBackend = () => {
  return config.backends.default;
};

export const getBackendLabel = (backendValue) => {
  const backend = config.backends.options.find(b => b.value === backendValue);
  return backend ? backend.label : backendValue;
};

export const getBackendDescription = (backendValue) => {
  const backend = config.backends.options.find(b => b.value === backendValue);
  return backend ? backend.description : backendValue;
};

// Comparison mode helpers
export const isComparisonMode = (selectedBackend) => {
  return selectedBackend === 'comparison';
};

export const getComparisonBackends = () => {
  return config.backends.options.map(b => b.value);
};

export default config;
