import React from 'react';
import { File, ImageIcon, FileText } from 'lucide-react';
import ResultCard from './ResultCard';

const ResultDisplay = ({
  result,
  previewUrl,
  onReset,
  getBackendLabel
}) => {
  if (!result) return null;

  return (
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
        <ResultCard
          result={result}
          backend={result.backend}
          getBackendLabel={getBackendLabel}
          isComparisonMode={false}
        />

        <div style={{ textAlign: 'center', marginTop: '20px' }}>
          <button className="button" onClick={onReset}>
            Process Another File
          </button>
        </div>
      </div>
    </>
  );
};

export default ResultDisplay;