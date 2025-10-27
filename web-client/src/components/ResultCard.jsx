import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

const ResultCard = ({
  result,
  backend,
  getBackendLabel,
  isComparisonMode = false
}) => {
  const [activeTab, setActiveTab] = useState('rendered');

  if (!result) return null;

  return (
    <div className={`result-card ${isComparisonMode ? 'comparison-card' : ''}`}>
      {isComparisonMode && (
        <div className="comparison-header">
          <h3>{getBackendLabel(backend)}</h3>
          <div className={`status ${result?.success ? 'success' : 'error'}`}>
            {result?.success ? '✓ Success' : '✗ Failed'}
          </div>
        </div>
      )}

      {result?.success ? (
        <>
          <div className={isComparisonMode ? "comparison-tabs" : "result-tabs"}>
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

          <div className="result-content">
            {activeTab === 'rendered' ? (
              <div
                className="markdown-content"
                dangerouslySetInnerHTML={{ __html: result.source_markdown || result.markdown }}
              />
            ) : activeTab === 'source' ? (
              <div className="markdown-source">
                <ReactMarkdown>{result.markdown}</ReactMarkdown>
              </div>
            ) : (
              <div className="markdown-raw">
                <pre>{JSON.stringify(result.raw_result, null, 2)}</pre>
              </div>
            )}
          </div>

          <ResultMetrics result={result} getBackendLabel={getBackendLabel} isComparisonMode={isComparisonMode} />
        </>
      ) : (
        <div className="result-error">
          <strong>Error:</strong> {result?.error || 'Unknown error'}
        </div>
      )}
    </div>
  );
};

const ResultMetrics = ({ result, getBackendLabel, isComparisonMode }) => (
  <div className={`result-metrics ${isComparisonMode ? 'comparison-metrics' : ''}`}>
    {!isComparisonMode && (
      <div className="metric">
        <strong>Backend:</strong> {getBackendLabel(result.backend)}
      </div>
    )}
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
);

export default ResultCard;