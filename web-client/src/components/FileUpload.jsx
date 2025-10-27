import React from 'react';
import { Upload, File, CheckSquare, Square } from 'lucide-react';

const FileUpload = ({
  selectedFile,
  fileType,
  previewUrl,
  pdfPages,
  selectedPages,
  pdfPageCount,
  isDragOver,
  isGeneratingPreview,
  uploadProgress,
  onFileSelect,
  onDrop,
  onDragOver,
  onDragLeave,
  onFileInput,
  togglePageSelection,
  selectAllPages,
  clearPageSelection,
  processOCR,
  isLoading,
  isComparisonMode
}) => {
  return (
    <div className="upload-section">
      <div
        className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
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
        onChange={onFileInput}
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
              `Processing${isComparisonMode ? ' All Backends...' : '...'}`
            ) : (
              `Extract Text${fileType === 'pdf' ? ` (${selectedPages.length} pages)` : ''}`
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUpload;