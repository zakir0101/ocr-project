"""
API Contract Definition

This module defines the standardized request and response formats
for the multi-backend OCR system.
"""

from typing import Dict, Any, Union, Optional


# Client Request Format
CLIENT_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "image": {
            "type": "file",
            "description": "Input image file for OCR processing"
        },
        "pdf": {
            "type": "file",
            "description": "Input PDF file for OCR processing"
        },
        "backend": {
            "type": "string",
            "enum": ["deepseek-ocr", "mineru"],
            "description": "Specify which OCR backend to use"
        },
        "prompt": {
            "type": "string",
            "description": "Optional custom prompt for OCR processing"
        },
        "pages": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "List of page numbers to process (1-indexed)"
        }
    },
    "required": ["backend"],
    "oneOf": [
        {"required": ["image"]},
        {"required": ["pdf"]}
    ]
}


# Unified Response Format
UNIFIED_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Whether the OCR processing was successful"
        },
        "backend": {
            "type": "string",
            "enum": ["deepseek-ocr", "mineru"],
            "description": "Which backend processed the request"
        },
        "raw_result": {
            "type": "object",
            "description": "Backend-specific raw output format",
            "properties": {
                "deepseek": {
                    "type": ["string", "object"],
                    "description": "DeepSeek raw text output with detection markers or multi-page object"
                },
                "mineru": {
                    "type": "object",
                    "description": "Mineru structured JSON output"
                }
            }
        },
        "markdown": {
            "type": "string",
            "description": "Processed markdown text ready for display"
        },
        "source_markdown": {
            "type": "string",
            "description": "HTML-ready markdown with image references"
        },
        "boxes_image": {
            "type": "string",
            "description": "Base64-encoded image with bounding boxes"
        },
        "processing_time": {
            "type": "number",
            "description": "Time taken for OCR processing in seconds"
        },
        "file_name": {
            "type": "string",
            "description": "Name of the processed file"
        },
        "file_type": {
            "type": "string",
            "enum": ["image", "pdf"],
            "description": "Type of processed file"
        },
        "page_count": {
            "type": "integer",
            "description": "Total number of pages in PDF (for multi-page files)"
        },
        "processed_pages": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "List of processed page numbers (1-indexed)"
        }
    },
    "required": ["success", "backend", "raw_result", "markdown", "processing_time", "file_name"]
}


# Backend-Specific Raw Result Formats
DEEPSEEK_RAW_FORMAT = {
    "description": "DeepSeek OCR raw output format",
    "pattern": r"<\|ref\|>.*?<\|/ref\|><\|det\|>\[\[.*?\]\]<\|/det\|>",
    "example": "<|ref|>Sample text<|/ref|><|det|>[[10,20,100,50]]<|/det|>"
}

MINERU_RAW_FORMAT = {
    "description": "Mineru structured JSON output format",
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "Extracted text content"
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata about the OCR process"
        }
    }
}


# Health Check Response Format
HEALTH_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["healthy", "unhealthy"],
            "description": "Overall health status"
        },
        "model_loaded": {
            "type": "boolean",
            "description": "Whether the model is loaded in GPU memory"
        },
        "gpu_available": {
            "type": "boolean",
            "description": "Whether GPU is available and accessible"
        },
        "backend": {
            "type": "string",
            "enum": ["deepseek-ocr", "mineru"],
            "description": "Which backend this health check is for"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp of the health check"
        }
    },
    "required": ["status", "model_loaded", "gpu_available", "backend"]
}


def validate_request(request_data: Dict[str, Any]) -> bool:
    """
    Validate client request against the expected schema.

    Args:
        request_data: Client request data

    Returns:
        bool: True if request is valid, False otherwise
    """
    # TODO: Implement actual validation logic
    required_fields = ["image", "backend"]
    return all(field in request_data for field in required_fields)


def create_unified_response(
    success: bool,
    backend: str,
    raw_result: Dict[str, Any],
    markdown: str,
    source_markdown: Optional[str] = None,
    boxes_image: Optional[str] = None,
    processing_time: Optional[float] = None,
    image_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a unified response in the standardized format.

    Args:
        success: Whether OCR processing was successful
        backend: Which backend processed the request
        raw_result: Backend-specific raw output
        markdown: Processed markdown text
        source_markdown: HTML-ready markdown with images
        boxes_image: Base64-encoded image with bounding boxes
        processing_time: Processing time in seconds
        image_name: Name of processed image file

    Returns:
        dict: Unified response in standardized format
    """
    return {
        "success": success,
        "backend": backend,
        "raw_result": raw_result,
        "markdown": markdown,
        "source_markdown": source_markdown or markdown,
        "boxes_image": boxes_image or "",
        "processing_time": processing_time or 0.0,
        "image_name": image_name or ""
    }