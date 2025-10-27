import React, { useState, useCallback, useEffect } from 'react'
import { Upload, FileText, Image as ImageIcon, Loader, Server, Wifi, WifiOff, GitCompare, File, CheckSquare, Square } from 'lucide-react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import config, {
  getApiUrl,
  getBackendOptions,
  getDefaultBackend,
  getBackendLabel,
  getBackendDescription,
  isComparisonMode,
  getComparisonBackends
} from './config'

// Import modular components
import FileUpload from './components/FileUpload'
import ResultDisplay from './components/ResultDisplay'
import ComparisonDisplay from './components/ComparisonDisplay'

// PDF.js imports
import * as pdfjsLib from 'pdfjs-dist'

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

function App() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileType, setFileType] = useState('image') // 'image' or 'pdf'
  const [previewUrl, setPreviewUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [comparisonResults, setComparisonResults] = useState({})
  const [error, setError] = useState('')
  const [isDragOver, setIsDragOver] = useState(false)
  const [serverStatus, setServerStatus] = useState('checking')
  const [selectedBackend, setSelectedBackend] = useState(getDefaultBackend())
  const [backendInfo, setBackendInfo] = useState({})
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false)

  // PDF-specific state
  const [pdfPages, setPdfPages] = useState([]) // Array of page preview URLs
  const [selectedPages, setSelectedPages] = useState([]) // Array of selected page numbers
  const [pdfPageCount, setPdfPageCount] = useState(0) // Total number of pages in PDF

  // Function to generate PDF previews
  const generatePdfPreviews = useCallback(async (file) => {
    try {
      setIsGeneratingPreview(true)
      setUploadProgress(0)

      const arrayBuffer = await file.arrayBuffer()
      setUploadProgress(20)

      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
      setUploadProgress(40)

      const pageCount = pdf.numPages
      setPdfPageCount(pageCount)

      // Select all pages by default
      const allPages = Array.from({ length: pageCount }, (_, i) => i + 1)
      setSelectedPages(allPages)
      setUploadProgress(60)

      // Generate previews for first few pages (limit to 5 for performance)
      const previewLimit = Math.min(pageCount, 5)
      const previewPromises = []

      for (let i = 1; i <= previewLimit; i++) {
        previewPromises.push(
          pdf.getPage(i).then(async (page) => {
            const viewport = page.getViewport({ scale: 0.5 })
            const canvas = document.createElement('canvas')
            const context = canvas.getContext('2d')
            canvas.height = viewport.height
            canvas.width = viewport.width

            await page.render({
              canvasContext: context,
              viewport: viewport
            }).promise

            // Update progress for each page rendered
            setUploadProgress(60 + ((i / previewLimit) * 30))

            return {
              pageNumber: i,
              previewUrl: canvas.toDataURL('image/jpeg', 0.8)
            }
          })
        )
      }

      const previews = await Promise.all(previewPromises)
      setPdfPages(previews)
      setUploadProgress(100)

      // Reset progress after a short delay
      setTimeout(() => setUploadProgress(0), 1000)

    } catch (error) {
      console.error('Error generating PDF previews:', error)
      setError('Failed to load PDF preview. The file might be corrupted.')
      setUploadProgress(0)
    } finally {
      setIsGeneratingPreview(false)
    }
  }, [])

  // Page selection helper functions
  const togglePageSelection = useCallback((pageNumber) => {
    setSelectedPages(prev => {
      if (prev.includes(pageNumber)) {
        return prev.filter(p => p !== pageNumber)
      } else {
        return [...prev, pageNumber].sort((a, b) => a - b)
      }
    })
  }, [])

  const selectAllPages = useCallback(() => {
    const allPages = Array.from({ length: pdfPageCount }, (_, i) => i + 1)
    setSelectedPages(allPages)
  }, [pdfPageCount])

  const clearPageSelection = useCallback(() => {
    setSelectedPages([])
  }, [])

  const selectPageRange = useCallback((start, end) => {
    const range = Array.from({ length: end - start + 1 }, (_, i) => start + i)
    setSelectedPages(range)
  }, [])

  const handleFileSelect = useCallback((file) => {
    if (!file) {
      setError('Please select a file')
      return
    }

    // File size validation
    const maxFileSize = config.app.upload.maxFileSize
    if (file.size > maxFileSize) {
      setError(`File size must be less than ${maxFileSize / (1024 * 1024)}MB`)
      return
    }

    const isImage = file.type.startsWith('image/')
    const isPDF = file.type === 'application/pdf'

    if (isImage || isPDF) {
      setSelectedFile(file)
      setFileType(isImage ? 'image' : 'pdf')
      setError('')

      // Create preview URL for images
      if (isImage) {
        const url = URL.createObjectURL(file)
        setPreviewUrl(url)
        // Reset PDF state
        setPdfPages([])
        setSelectedPages([])
        setPdfPageCount(0)
      } else {
        // For PDFs, generate previews
        setPreviewUrl('')
        generatePdfPreviews(file)
      }
    } else {
      setError('Please select a valid image (JPEG, PNG, etc.) or PDF file')
    }
  }, [generatePdfPreviews])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }, [handleFileSelect])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleFileInput = useCallback((e) => {
    const file = e.target.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }, [handleFileSelect])

  // Check server status on component mount
  useEffect(() => {
    checkServerStatus()
  }, [])

  // Process MathJax equations when result changes
  useEffect(() => {
    if (result && window.MathJax) {
      // Give the DOM time to update, then process MathJax
      setTimeout(() => {
        window.MathJax.typesetPromise && window.MathJax.typesetPromise();
      }, 100)
    }
  }, [result])

  const checkServerStatus = async () => {
    try {
      const healthUrl = getApiUrl('health')
      const backendsUrl = getApiUrl('backends')
      console.log('Checking orchestrator status at:', healthUrl)

      const [healthResponse, backendsResponse] = await Promise.all([
        axios.get(healthUrl, {
          timeout: 10000,
          validateStatus: (status) => status < 500
        }),
        axios.get(backendsUrl, {
          timeout: 10000,
          validateStatus: (status) => status < 500
        })
      ])

      console.log('Orchestrator health response:', healthResponse.data)
      console.log('Backends response:', backendsResponse.data)

      if (healthResponse.data.status === 'healthy' || healthResponse.data.status === 'degraded') {
        setServerStatus('connected')
        setBackendInfo(backendsResponse.data.backends || {})
      } else {
        setServerStatus('error')
      }
    } catch (err) {
      console.error('Orchestrator connection failed:', err.message)
      console.error('Error details:', err.response?.data || err.code)
      setServerStatus('disconnected')
    }
  }

  const processOCR = async () => {
    if (!selectedFile) {
      setError('Please select an image first')
      return
    }

    if (serverStatus !== 'connected') {
      setError('Cannot connect to OCR server. Please check server status.')
      return
    }

    setIsLoading(true)
    setError('')
    setResult(null)
    setComparisonResults({})

    try {
      if (isComparisonMode(selectedBackend)) {
        // Process with all backends for comparison
        const backends = getComparisonBackends()
        const results = {}

        // Use correct field name and endpoint based on file type
        const isPDF = fileType === 'pdf'
        const fieldName = isPDF ? 'pdf' : 'image'
        const endpoint = isPDF ? 'ocrPdf' : 'ocrImage'

        for (const backend of backends) {
          try {
            const formData = new FormData()
            formData.append(fieldName, selectedFile)
            formData.append('backend', backend)

            // Add page selection for PDFs
            if (isPDF && selectedPages.length > 0) {
              formData.append('pages', JSON.stringify(selectedPages))
            }

            const response = await axios.post(getApiUrl(endpoint), formData, {
              headers: {
                'Content-Type': 'multipart/form-data'
              },
              timeout: 120000 // 120 second timeout for OCR processing
            })

            if (response.data.success) {
              results[backend] = response.data
            } else {
              results[backend] = { error: response.data.error || 'OCR processing failed' }
            }
          } catch (err) {
            results[backend] = {
              error: err.response?.data?.error || `Failed to process ${isPDF ? 'PDF' : 'image'}`
            }
          }
        }

        setComparisonResults(results)
      } else {
        // Process with single backend
        const formData = new FormData()

        // Use correct field name and endpoint based on file type
        const isPDF = fileType === 'pdf'
        const fieldName = isPDF ? 'pdf' : 'image'
        const endpoint = isPDF ? 'ocrPdf' : 'ocrImage'

        formData.append(fieldName, selectedFile)
        formData.append('backend', selectedBackend)

        // Add page selection for PDFs
        if (isPDF && selectedPages.length > 0) {
          formData.append('pages', JSON.stringify(selectedPages))
        }

        const response = await axios.post(getApiUrl(endpoint), formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 120000 // 120 second timeout for OCR processing
        })

        if (response.data.success) {
          setResult(response.data)
        } else {
          setError(response.data.error || 'OCR processing failed')
        }
      }
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError('Request timeout. The server might be processing a large image.')
      } else {
        setError(err.response?.data?.error || 'Failed to process image. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const resetForm = () => {
    setSelectedFile(null)
    setFileType('image')
    setPreviewUrl('')
    setResult(null)
    setComparisonResults({})
    setError('')
    setSelectedBackend(getDefaultBackend())
    setUploadProgress(0)
    setIsGeneratingPreview(false)

    // Reset PDF state
    setPdfPages([])
    setSelectedPages([])
    setPdfPageCount(0)

    // Clean up preview URL
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>{config.app.name}</h1>
        <p>{config.app.description}</p>

        {/* Backend Selection */}
        <div className="backend-selector">
          <label htmlFor="backend-select">Select OCR Backend:</label>
          <select
            id="backend-select"
            value={selectedBackend}
            onChange={(e) => setSelectedBackend(e.target.value)}
            disabled={isLoading}
          >
            {getBackendOptions().map((backend) => (
              <option key={backend.value} value={backend.value}>
                {backend.label}
              </option>
            ))}
            <option value="comparison">
              <GitCompare size={16} style={{ marginRight: '8px' }} />
              Compare All Backends
            </option>
          </select>
          {backendInfo[selectedBackend] && (
            <div className="backend-info">
              <span className={`status ${backendInfo[selectedBackend].healthy ? 'healthy' : 'unhealthy'}`}>
                {backendInfo[selectedBackend].healthy ? '✓ Healthy' : '✗ Unhealthy'}
              </span>
              {backendInfo[selectedBackend].description && (
                <span className="description">
                  {backendInfo[selectedBackend].description}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Server Status Indicator */}
        <div className="server-status">
          <div className={`status-indicator ${serverStatus}`}>
            {serverStatus === 'connected' && <Wifi size={16} />}
            {serverStatus === 'disconnected' && <WifiOff size={16} />}
            {serverStatus === 'checking' && <Loader size={16} />}
            <span>
              Server: {serverStatus === 'connected' ? 'Connected' :
                serverStatus === 'disconnected' ? 'Disconnected' :
                  'Checking...'}
            </span>
            <button
              onClick={checkServerStatus}
              style={{
                marginLeft: '10px',
                padding: '2px 8px',
                fontSize: '12px',
                background: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              Refresh
            </button>
          </div>

          {result?.demo_mode && (
            <div className="demo-notice">
              ⚠ Running in demo mode - install vLLM for full functionality
            </div>
          )}
        </div>

      </div>

      {/* File Upload Section */}
      {!result && Object.keys(comparisonResults).length === 0 && (
        <FileUpload
          selectedFile={selectedFile}
          fileType={fileType}
          previewUrl={previewUrl}
          pdfPages={pdfPages}
          selectedPages={selectedPages}
          pdfPageCount={pdfPageCount}
          isDragOver={isDragOver}
          isGeneratingPreview={isGeneratingPreview}
          uploadProgress={uploadProgress}
          onFileSelect={handleFileSelect}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onFileInput={handleFileInput}
          togglePageSelection={togglePageSelection}
          selectAllPages={selectAllPages}
          clearPageSelection={clearPageSelection}
          processOCR={processOCR}
          isLoading={isLoading}
          isComparisonMode={isComparisonMode(selectedBackend)}
        />
      )}

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Single Backend Result Display */}
      {result && (
        <ResultDisplay
          result={result}
          previewUrl={previewUrl}
          onReset={resetForm}
          getBackendLabel={getBackendLabel}
        />
      )}

      {/* Comparison Mode Display */}
      {Object.keys(comparisonResults).length > 0 && (
        <ComparisonDisplay
          comparisonResults={comparisonResults}
          fileType={fileType}
          previewUrl={previewUrl}
          selectedFile={selectedFile}
          pdfPageCount={pdfPageCount}
          selectedPages={selectedPages}
          onReset={resetForm}
          getBackendLabel={getBackendLabel}
          getComparisonBackends={getComparisonBackends}
        />
      )}

      {isLoading && (
        <div className="loading">
          <Loader size={48} style={{ marginBottom: '15px' }} />
          <p>
            Processing image with {
              isComparisonMode(selectedBackend)
                ? 'all backends...'
                : `${getBackendLabel(selectedBackend)}...`
            }
          </p>
          <p style={{ fontSize: '14px', color: '#666' }}>
            This may take a few moments depending on image size and complexity.
          </p>
        </div>
      )}
    </div>
  )
}

export default App