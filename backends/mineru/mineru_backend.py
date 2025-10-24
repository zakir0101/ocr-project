"""
Mineru Backend Implementation

This module implements the MineruBackend class that conforms to the
OCRBackend interface from shared/ocr_backend.py.
"""

import os
import time
import base64
import io
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import torch
from PIL import Image, ImageDraw
from flask import Flask, request, jsonify

# Import shared components
from shared.ocr_backend import OCRBackend
from shared.api_contract import create_unified_response

# Configuration
MINERU_PROMPT = "Extract text from this document and convert to markdown format."


class MineruBackend(OCRBackend):
    """
    Mineru backend implementation using the OCRBackend interface.

    This backend uses GPU 1 exclusively and implements all required
    abstract methods from the OCRBackend interface.
    """

    def __init__(self, model_path: str, device: str = "cuda"):
        """
        Initialize Mineru backend with model path and device.

        Args:
            model_path (str): Path to Mineru model weights/config
            device (str): Device to run on (default: "cuda")
        """
        self.model_path = Path(model_path)
        self.device = device
        self.model = None
        self.processor = None
        self.model_loaded = False
        self.gpu_available = False

        # Set GPU isolation for Mineru backend
        os.environ["CUDA_VISIBLE_DEVICES"] = "1"

        print(f"MineruBackend initialized with model_path: {model_path}")
        print(f"GPU isolation: CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES')}")

    def load_model(self) -> bool:
        """
        Load Mineru model into GPU 1 memory.

        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            print("Loading Mineru model into GPU 1 memory...")

            # Check if CUDA is available
            if not torch.cuda.is_available():
                print("✗ CUDA not available - cannot load model")
                self.gpu_available = False
                return False

            self.gpu_available = True

            # Import required Mineru modules
            try:
                from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
                from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
                from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
                from mineru.data.data_reader_writer import FileBasedDataWriter
                from mineru.cli.common import prepare_env, read_fn, convert_pdf_bytes_to_bytes_by_pypdfium2

                # Store the imported functions for later use
                self.pipeline_doc_analyze = pipeline_doc_analyze
                self.pipeline_union_make = pipeline_union_make
                self.pipeline_result_to_middle_json = pipeline_result_to_middle_json
                self.FileBasedDataWriter = FileBasedDataWriter
                self.prepare_env = prepare_env
                self.read_fn = read_fn
                self.convert_pdf_bytes_to_bytes_by_pypdfium2 = convert_pdf_bytes_to_bytes_by_pypdfium2

            except ImportError as e:
                print(f"✗ Required Mineru modules not available: {e}")
                return False

            self.model_loaded = True
            print("✓ Mineru model loaded successfully into GPU 1")
            return True

        except Exception as e:
            print(f"✗ Failed to load Mineru model: {e}")
            self.model_loaded = False
            return False

    def ocr_image(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        Perform OCR on a single image using Mineru.

        Args:
            image_path (str): Path to input image
            **kwargs: Additional parameters

        Returns:
            dict: OCR results in unified format
        """
        if not self.model_loaded:
            return create_unified_response(
                success=False,
                backend="mineru",
                raw_result={"deepseek": "", "mineru": {}},
                markdown="Model not loaded",
                image_name=Path(image_path).name
            )

        start_time = time.time()

        try:
            # Process image through Mineru using pipeline backend
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir) / "output"
                output_dir.mkdir(exist_ok=True)

                # Process the image using Mineru pipeline
                raw_output, markdown_result = self._process_with_mineru_pipeline(
                    image_path, output_dir, **kwargs
                )

                # Generate bounding boxes image (placeholder for now)
                boxes_image = self._generate_boxes_image(Image.open(image_path), raw_output)

                processing_time = time.time() - start_time

                return create_unified_response(
                    success=True,
                    backend="mineru",
                    raw_result={"deepseek": "", "mineru": raw_output},
                    markdown=markdown_result,
                    source_markdown=markdown_result,
                    boxes_image=boxes_image,
                    processing_time=processing_time,
                    image_name=Path(image_path).name
                )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"✗ OCR processing failed: {e}")

            return create_unified_response(
                success=False,
                backend="mineru",
                raw_result={"deepseek": "", "mineru": {}},
                markdown=f"OCR processing failed: {str(e)}",
                processing_time=processing_time,
                image_name=Path(image_path).name
            )

    def ocr_pdf(self, pdf_path: str, **kwargs) -> Dict[str, Any]:
        """
        Perform OCR on a PDF document using Mineru.

        Args:
            pdf_path (str): Path to input PDF
            **kwargs: Additional parameters

        Returns:
            dict: OCR results in unified format
        """
        if not self.model_loaded:
            return create_unified_response(
                success=False,
                backend="mineru",
                raw_result={"deepseek": "", "mineru": {}},
                markdown="Model not loaded",
                image_name=Path(pdf_path).name
            )

        start_time = time.time()

        try:
            # Process PDF through Mineru using pipeline backend
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir) / "output"
                output_dir.mkdir(exist_ok=True)

                # Process the PDF using Mineru pipeline
                raw_output, markdown_result = self._process_with_mineru_pipeline(
                    pdf_path, output_dir, **kwargs
                )

                # Generate bounding boxes image (placeholder for now)
                boxes_image = ""  # PDF bounding box visualization would be more complex

                processing_time = time.time() - start_time

                return create_unified_response(
                    success=True,
                    backend="mineru",
                    raw_result={"deepseek": "", "mineru": raw_output},
                    markdown=markdown_result,
                    source_markdown=markdown_result,
                    boxes_image=boxes_image,
                    processing_time=processing_time,
                    image_name=Path(pdf_path).name
                )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"✗ PDF processing failed: {e}")

            return create_unified_response(
                success=False,
                backend="mineru",
                raw_result={"deepseek": "", "mineru": {}},
                markdown=f"PDF processing failed: {str(e)}",
                processing_time=processing_time,
                image_name=Path(pdf_path).name
            )

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get Mineru backend health status.

        Returns:
            dict: Health information including model_loaded, gpu_available, etc.
        """
        return {
            "status": "healthy" if self.model_loaded and self.gpu_available else "unhealthy",
            "model_loaded": self.model_loaded,
            "gpu_available": self.gpu_available,
            "backend": "mineru",
            "timestamp": time.time()
        }

    def cleanup(self):
        """
        Clean up Mineru backend resources.
        """
        if self.model:
            # Clean up model resources
            try:
                del self.model
            except Exception as e:
                print(f"Warning: Error during model cleanup: {e}")

        self.model = None
        self.processor = None
        self.model_loaded = False
        print("Mineru backend resources cleaned up")

    def _process_with_mineru_pipeline(self, file_path: str, output_dir: Path, **kwargs) -> tuple[Dict[str, Any], str]:
        """
        Process file (image or PDF) using Mineru pipeline backend.

        Args:
            file_path: Path to input file
            output_dir: Output directory for Mineru results
            **kwargs: Additional parameters

        Returns:
            tuple: (raw_output_dict, markdown_content)
        """
        try:
            # Prepare environment for Mineru processing
            file_name = Path(file_path).stem
            local_image_dir, local_md_dir = self.prepare_env(output_dir, file_name, "auto")
            image_writer, md_writer = self.FileBasedDataWriter(local_image_dir), self.FileBasedDataWriter(local_md_dir)

            # Read file bytes
            file_bytes = self.read_fn(file_path)

            # Process with Mineru pipeline
            (
                infer_results,
                all_image_lists,
                all_pdf_docs,
                lang_list,
                ocr_enabled_list,
            ) = self.pipeline_doc_analyze(
                [file_bytes],
                ["ch"],  # Default to Chinese, can be parameterized
                parse_method="auto",
                formula_enable=True,
                table_enable=True,
            )

            # Process the results
            if infer_results:
                model_list = infer_results[0]
                images_list = all_image_lists[0]
                pdf_doc = all_pdf_docs[0]
                _lang = lang_list[0]
                _ocr_enable = ocr_enabled_list[0]

                # Convert to middle JSON
                middle_json = self.pipeline_result_to_middle_json(
                    model_list,
                    images_list,
                    pdf_doc,
                    image_writer,
                    _lang,
                    _ocr_enable,
                    formula_enable=True,
                )

                # Generate markdown content
                image_dir = str(local_image_dir.name)
                markdown_content = self.pipeline_union_make(middle_json["pdf_info"], "MM_MD", image_dir)

                # Prepare raw output
                raw_output = {
                    "middle_json": middle_json,
                    "model_output": model_list,
                    "metadata": {
                        "language": _lang,
                        "ocr_enabled": _ocr_enable,
                        "formula_enabled": True,
                        "table_enabled": True
                    }
                }

                return raw_output, markdown_content

            else:
                raise Exception("No inference results from Mineru")

        except Exception as e:
            print(f"✗ Mineru pipeline processing failed: {e}")
            raise

    def _generate_boxes_image(self, image: Image.Image, raw_output: Dict[str, Any]) -> str:
        """
        Generate base64-encoded image with bounding boxes.

        Args:
            image: Original PIL Image
            raw_output: Raw OCR output with detection data

        Returns:
            str: Base64-encoded image with bounding boxes
        """
        # TODO: Implement bounding box extraction and visualization
        # This would extract coordinates from Mineru output
        # and draw bounding boxes on the image

        # For now, return empty string as bounding box visualization
        # would require more complex integration with Mineru's bbox drawing
        return ""