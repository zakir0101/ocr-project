import React from 'react';
import { File, ImageIcon, GitCompare } from 'lucide-react';
import ResultCard from './ResultCard';

const ComparisonDisplay = ({
  comparisonResults,
  fileType,
  previewUrl,
  selectedFile,
  pdfPageCount,
  selectedPages,
  onReset,
  getBackendLabel,
  getComparisonBackends
}) => {
  if (Object.keys(comparisonResults).length === 0) return null;

  return (
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
                <div><strong>File:</strong> {selectedFile?.name}</div>
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
            <ResultCard
              key={backend}
              result={comparisonResults[backend]}
              backend={backend}
              getBackendLabel={getBackendLabel}
              isComparisonMode={true}
            />
          ))}
        </div>

        <ComparisonSummary
          comparisonResults={comparisonResults}
          getBackendLabel={getBackendLabel}
          getComparisonBackends={getComparisonBackends}
        />

        <div style={{ textAlign: 'center', marginTop: '30px' }}>
          <button className="button" onClick={onReset}>
            Process Another File
          </button>
        </div>
      </div>
    </>
  );
};

const ComparisonSummary = ({ comparisonResults, getBackendLabel, getComparisonBackends }) => {
  const successfulBackends = getComparisonBackends().filter(
    backend => comparisonResults[backend]?.success
  );

  if (successfulBackends.length === 0) return null;

  const processingTimes = successfulBackends.map(
    backend => comparisonResults[backend].processing_time
  );
  const fastestTime = Math.min(...processingTimes);
  const slowestTime = Math.max(...processingTimes);

  return (
    <div className="comparison-summary">
      <h3>Performance Summary</h3>
      <div className="summary-grid">
        {getComparisonBackends().map((backend) => {
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
        })}
      </div>
    </div>
  );
};

export default ComparisonDisplay;