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
  const [activeTab, setActiveTab] = useState('rendered')
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
    if (result && activeTab === 'rendered' && window.MathJax) {
      // Give the DOM time to update, then process MathJax
      setTimeout(() => {
        window.MathJax.typesetPromise && window.MathJax.typesetPromise();
      }, 100)
    }
  }, [result, activeTab])

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
    setActiveTab('rendered')
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

      {!result && (
        <div className="upload-section">
          <div
            className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => document.getElementById('file-input').click()}
          >
            <Upload className="upload-icon" />
            <h3>Drag & Drop Image or PDF Here</h3>
            <p>or click to select a file</p>
            <p style={{ fontSize: '14px', color: '#666', marginTop: '10px' }}>
              Supported formats: JPEG, PNG, WebP, PDF (up to 50MB)
            </p>

            {/* Progress indicator for PDF preview generation */}
            {isGeneratingPreview && (
              <div className="preview-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                  Generating PDF preview... {uploadProgress}%
                </p>
              </div>
            )}
          </div>

          <input
            id="file-input"
            type="file"
            accept="image/*,.pdf"
            onChange={handleFileInput}
            style={{ display: 'none' }}
          />

          {selectedFile && (
            <div className="preview-container">
              {/* File info header */}
              <div className="file-info">
                <div className="file-type-badge">
                  {fileType === 'image' ? '📷 Image' : '📄 PDF'}
                </div>
                <div className="file-name">{selectedFile.name}</div>
                <div className="file-size">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </div>
              </div>

              {fileType === 'image' && previewUrl ? (
                <>
                  <h4>Image Preview:</h4>
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="preview-image-upload"
                  />
                </>
              ) : fileType === 'pdf' && pdfPages.length > 0 ? (
                <>
                  <h4>
                    <File size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                    PDF Preview ({pdfPageCount} pages)
                  </h4>

                  {/* Page Selection Controls */}
                  <div className="page-selection-controls">
                    <div className="selection-summary">
                      <strong>Selected:</strong> {selectedPages.length} of {pdfPageCount} pages
                      {selectedPages.length > 0 && (
                        <span className="selected-pages">
                          ({selectedPages.join(', ')})
                        </span>
                      )}
                    </div>
                    <div className="selection-buttons">
                      <button
                        className="button small"
                        onClick={selectAllPages}
                        disabled={selectedPages.length === pdfPageCount}
                      >
                        Select All
                      </button>
                      <button
                        className="button small"
                        onClick={clearPageSelection}
                        disabled={selectedPages.length === 0}
                      >
                        Clear All
                      </button>
                    </div>
                  </div>

                  {/* Page Previews */}
                  <div className="pdf-preview-grid">
                    {pdfPages.map((page) => (
                      <div
                        key={page.pageNumber}
                        className={`pdf-page-preview ${selectedPages.includes(page.pageNumber) ? 'selected' : ''}`}
                        onClick={() => togglePageSelection(page.pageNumber)}
                      >
                        <div className="page-checkbox">
                          {selectedPages.includes(page.pageNumber) ? (
                            <CheckSquare size={16} />
                          ) : (
                            <Square size={16} />
                          )}
                        </div>
                        <img
                          src={page.previewUrl}
                          alt={`Page ${page.pageNumber}`}
                          className="pdf-preview-image"
                        />
                        <div className="page-number">Page {page.pageNumber}</div>
                      </div>
                    ))}
                    {pdfPageCount > 5 && (
                      <div className="pdf-page-preview more-pages">
                        <div className="more-pages-text">
                          +{pdfPageCount - 5} more pages
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : null}

              <button
                className="button"
                onClick={processOCR}
                disabled={isLoading || (fileType === 'pdf' && selectedPages.length === 0)}
              >
                {isLoading ? (
                  <>
                    <Loader size={16} style={{ marginRight: '8px' }} />
                    Processing...
                  </>
                ) : (
                  `Extract Text${fileType === 'pdf' ? ` (${selectedPages.length} pages)` : ''}`
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <>
          <div className="preview-section">
            <div className="preview-image">
              <h3>
                {result.file_type === 'pdf' ? (
                  <File size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                ) : (
                  <ImageIcon size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                )}
                {result.file_type === 'pdf' ? 'PDF Document' : 'Original Image'}
              </h3>
              {result.file_type === 'pdf' ? (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <File size={48} style={{ color: '#007bff', marginBottom: '10px' }} />
                  <div style={{ fontSize: '14px', color: '#666' }}>
                    <div><strong>File:</strong> {result.file_name}</div>
                    <div><strong>Pages:</strong> {result.page_count || 'N/A'}</div>
                    {result.processed_pages && (
                      <div><strong>Processed:</strong> {result.processed_pages.join(', ')}</div>
                    )}
                  </div>
                </div>
              ) : (
                <img src={previewUrl} alt="Original" />
              )}
            </div>

            {result.boxes_image && (
              <div className="preview-image">
                <h3>
                  <FileText size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                  Image with Bounding Boxes
                </h3>
                <img src={`data:image/jpeg;base64,${result.boxes_image}`} alt="With bounding boxes" />
              </div>
            )}
          </div>

          <div className="result-section">
            <div className="result-tabs">
              <button
                className={`tab ${activeTab === 'rendered' ? 'active' : ''}`}
                onClick={() => setActiveTab('rendered')}
              >
                Rendered Markdown
              </button>
              <button
                className={`tab ${activeTab === 'source' ? 'active' : ''}`}
                onClick={() => setActiveTab('source')}
              >
                Source Markdown
              </button>
              <button
                className={`tab ${activeTab === 'raw' ? 'active' : ''}`}
                onClick={() => setActiveTab('raw')}
              >
                Raw OCR Output
              </button>
            </div>

            {activeTab === 'rendered' ? (
              <div
                className="markdown-content"
                dangerouslySetInnerHTML={{ __html: result.source_markdown }}
              />
            ) : activeTab === 'source' ? (
              <div className="markdown-source">
                {result.markdown}
              </div>
            ) : (
              <div className="markdown-raw">
                <pre>{JSON.stringify(result.raw_result, null, 2)}</pre>
              </div>
            )}

            <div className="result-metrics">
              <div className="metric">
                <strong>Backend:</strong> {getBackendLabel(result.backend)}
              </div>
              <div className={`metric ${result.processing_time < 5 ? 'success' : result.processing_time < 15 ? 'warning' : 'error'}`}>
                <strong>Processing Time:</strong> {result.processing_time?.toFixed(2)}s
              </div>
              {result.markdown && (
                <div className="metric">
                  <strong>Text Length:</strong> {result.markdown.length} chars
                </div>
              )}
              {result.file_type && (
                <div className="metric">
                  <strong>File Type:</strong> {result.file_type.toUpperCase()}
                </div>
              )}
              {result.page_count && (
                <div className="metric">
                  <strong>Total Pages:</strong> {result.page_count}
                </div>
              )}
              {result.processed_pages && (
                <div className="metric success">
                  <strong>Processed Pages:</strong> {result.processed_pages.length}
                </div>
              )}
              {result.boxes_image && (
                <div className="metric success">
                  <strong>Bounding Boxes:</strong> ✓ Detected
                </div>
              )}
            </div>

            <div style={{ textAlign: 'center', marginTop: '20px' }}>
              <button className="button" onClick={resetForm}>
                Process Another File
              </button>
            </div>
          </div>
        </>
      )}

      {Object.keys(comparisonResults).length > 0 && (
        <>
          <div className="preview-section">
            <div className="preview-image">
              <h3>
                {fileType === 'pdf' ? (
                  <File size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                ) : (
                  <ImageIcon size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                )}
                {fileType === 'pdf' ? 'PDF Document' : 'Original Image'}
              </h3>
              {fileType === 'pdf' ? (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <File size={48} style={{ color: '#007bff', marginBottom: '10px' }} />
                  <div style={{ fontSize: '14px', color: '#666' }}>
                    <div><strong>File:</strong> {fileName}</div>
                    <div><strong>Pages:</strong> {pdfPageCount || 'N/A'}</div>
                    {selectedPages.length > 0 && (
                      <div><strong>Selected:</strong> {selectedPages.join(', ')}</div>
                    )}
                  </div>
                </div>
              ) : (
                <img src={previewUrl} alt="Original" />
              )}
            </div>
          </div>

          <div className="comparison-section">
            <h2 style={{ textAlign: 'center', marginBottom: '30px' }}>
              <GitCompare size={24} style={{ marginRight: '10px', verticalAlign: 'middle' }} />
              Backend Comparison Results
            </h2>

            <div className="comparison-grid">
              {getComparisonBackends().map((backend) => (
                <div key={backend} className="comparison-card">
                  <div className="comparison-header">
                    <h3>{getBackendLabel(backend)}</h3>
                    <div className={`status ${comparisonResults[backend]?.success ? 'success' : 'error'}`}>
                      {comparisonResults[backend]?.success ? '✓ Success' : '✗ Failed'}
                    </div>
                  </div>

                  {comparisonResults[backend]?.success ? (
                    <>
                      <div className="comparison-tabs">
                        <button
                          className={`tab ${activeTab === 'rendered' ? 'active' : ''}`}
                          onClick={() => setActiveTab('rendered')}
                        >
                          Rendered
                        </button>
                        <button
                          className={`tab ${activeTab === 'source' ? 'active' : ''}`}
                          onClick={() => setActiveTab('source')}
                        >
                          Source
                        </button>
                        <button
                          className={`tab ${activeTab === 'raw' ? 'active' : ''}`}
                          onClick={() => setActiveTab('raw')}
                        >
                          Raw
                        </button>
                      </div>

                      {activeTab === 'rendered' ? (
                        <div
                          className="markdown-content comparison-content"
                          dangerouslySetInnerHTML={{ __html: comparisonResults[backend].source_markdown }}
                        />
                      ) : activeTab === 'source' ? (
                        <div className="markdown-source comparison-content">
                          {comparisonResults[backend].markdown}
                        </div>
                      ) : (
                        <div className="markdown-raw comparison-content">
                          <pre>{JSON.stringify(comparisonResults[backend].raw_result, null, 2)}</pre>
                        </div>
                      )}

                      <div className="comparison-metrics">
                        <div className={`metric ${comparisonResults[backend].processing_time < 5 ? 'success' : comparisonResults[backend].processing_time < 15 ? 'warning' : 'error'}`}>
                          <strong>Processing Time:</strong> {comparisonResults[backend].processing_time?.toFixed(2)}s
                        </div>
                        {comparisonResults[backend].markdown && (
                          <div className="metric">
                            <strong>Text Length:</strong> {comparisonResults[backend].markdown.length} chars
                          </div>
                        )}
                        {comparisonResults[backend].file_type && (
                          <div className="metric">
                            <strong>File Type:</strong> {comparisonResults[backend].file_type.toUpperCase()}
                          </div>
                        )}
                        {comparisonResults[backend].page_count && (
                          <div className="metric">
                            <strong>Total Pages:</strong> {comparisonResults[backend].page_count}
                          </div>
                        )}
                        {comparisonResults[backend].processed_pages && (
                          <div className="metric success">
                            <strong>Processed Pages:</strong> {comparisonResults[backend].processed_pages.length}
                          </div>
                        )}
                        {comparisonResults[backend].boxes_image && (
                          <div className="metric success">
                            <strong>Bounding Boxes:</strong> ✓ Detected
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="comparison-error">
                      <strong>Error:</strong> {comparisonResults[backend]?.error || 'Unknown error'}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="comparison-summary">
              <h3>Performance Summary</h3>
              <div className="summary-grid">
                {(() => {
                  // Determine fastest and slowest backends
                  const successfulBackends = getComparisonBackends().filter(
                    backend => comparisonResults[backend]?.success
                  );

                  if (successfulBackends.length === 0) return null;

                  const processingTimes = successfulBackends.map(
                    backend => comparisonResults[backend].processing_time
                  );
                  const fastestTime = Math.min(...processingTimes);
                  const slowestTime = Math.max(...processingTimes);

                  return getComparisonBackends().map((backend) => {
                    const isFastest = comparisonResults[backend]?.success &&
                                     comparisonResults[backend].processing_time === fastestTime;
                    const isSlowest = comparisonResults[backend]?.success &&
                                     comparisonResults[backend].processing_time === slowestTime;

                    return (
                      <div
                        key={backend}
                        className={`summary-item ${isFastest ? 'fastest' : ''} ${isSlowest ? 'slowest' : ''}`}
                      >
                        <div className="summary-backend">{getBackendLabel(backend)}</div>
                        <div className="summary-time">
                          {comparisonResults[backend]?.success
                            ? `${comparisonResults[backend].processing_time?.toFixed(2)}s`
                            : 'Failed'
                          }
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '30px' }}>
              <button className="button" onClick={resetForm}>
                Process Another File
              </button>
            </div>
          </div>
        </>
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