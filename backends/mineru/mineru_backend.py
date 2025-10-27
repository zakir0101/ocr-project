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
MINERU_PROMPT = (
    "Extract text from this document and convert to markdown format."
)
formula_enable = True
table_enable = True


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
        print(
            f"GPU isolation: CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES')}"
        )

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
                from mineru.backend.pipeline.pipeline_analyze import (
                    doc_analyze as pipeline_doc_analyze,
                )
                from mineru.backend.pipeline.pipeline_middle_json_mkcontent import (
                    union_make as pipeline_union_make,
                )
                from mineru.backend.pipeline.model_json_to_middle_json import (
                    result_to_middle_json as pipeline_result_to_middle_json,
                )
                from mineru.data.data_reader_writer import FileBasedDataWriter
                from mineru.cli.common import (
                    prepare_env,
                    read_fn,
                    convert_pdf_bytes_to_bytes_by_pypdfium2,
                )
                from mineru.utils.enum_class import MakeMode

                # Store the imported functions for later use
                self.pipeline_doc_analyze = pipeline_doc_analyze
                self.pipeline_union_make = pipeline_union_make
                self.pipeline_result_to_middle_json = (
                    pipeline_result_to_middle_json
                )
                self.FileBasedDataWriter = FileBasedDataWriter
                self.prepare_env = prepare_env
                self.read_fn = read_fn
                self.convert_pdf_bytes_to_bytes_by_pypdfium2 = (
                    convert_pdf_bytes_to_bytes_by_pypdfium2
                )
                self.MakeMode = MakeMode

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
                raw_result={},
                rendered_html="Model not loaded",
                image_name=Path(image_path).name,
            )

        start_time = time.time()

        try:
            # Process image through Mineru using pipeline backend
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir) / "output"
                output_dir.mkdir(exist_ok=True)

                # Process the image using Mineru pipeline
                raw_output, markdown_result = (
                    self._process_with_mineru_pipeline(
                        image_path, output_dir, **kwargs
                    )
                )

                # Generate bounding boxes image (placeholder for now)
                boxes_image = self._generate_boxes_image(
                    Image.open(image_path), raw_output
                )

                processing_time = time.time() - start_time

                return create_unified_response(
                    success=True,
                    backend="mineru",
                    raw_result=raw_output,
                    rendered_html=markdown_result,
                    boxes_image=boxes_image,
                    processing_time=processing_time,
                    image_name=Path(image_path).name,
                )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"✗ OCR processing failed: {e}")

            return create_unified_response(
                success=False,
                backend="mineru",
                raw_result={},
                rendered_html=f"OCR processing failed: {str(e)}",
                processing_time=processing_time,
                image_name=Path(image_path).name,
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
                raw_result={},
                rendered_html="Model not loaded",
                image_name=Path(pdf_path).name,
            )

        start_time = time.time()

        try:
            # Process PDF through Mineru using pipeline backend
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir) / "output"
                output_dir.mkdir(exist_ok=True)

                # Process the PDF using Mineru pipeline
                raw_output, markdown_result = (
                    self._process_with_mineru_pipeline(
                        pdf_path, output_dir, **kwargs
                    )
                )

                # Generate bounding boxes image (placeholder for now)
                boxes_image = (
                    ""  # PDF bounding box visualization would be more complex
                )

                processing_time = time.time() - start_time

                return create_unified_response(
                    success=True,
                    backend="mineru",
                    raw_result=raw_output,
                    rendered_html=markdown_result,
                    boxes_image=boxes_image,
                    processing_time=processing_time,
                    image_name=Path(pdf_path).name,
                )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"✗ PDF processing failed: {e}")

            return create_unified_response(
                success=False,
                backend="mineru",
                raw_result={},
                rendered_html=f"PDF processing failed: {str(e)}",
                processing_time=processing_time,
                image_name=Path(pdf_path).name,
            )

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get Mineru backend health status.

        Returns:
            dict: Health information including model_loaded, gpu_available, etc.
        """
        return {
            "status": (
                "healthy"
                if self.model_loaded and self.gpu_available
                else "unhealthy"
            ),
            "model_loaded": self.model_loaded,
            "gpu_available": self.gpu_available,
            "backend": "mineru",
            "timestamp": time.time(),
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

    def _process_with_mineru_pipeline(
        self, file_path: str, output_dir: Path, **kwargs
    ) -> tuple[Dict[str, Any], str]:
        """
        Process file (image or PDF) using Mineru pipeline backend.

        Args:
            file_path: Path to input file
            output_dir: Output directory for Mineru results
            **kwargs: Additional parameters (pages, etc.)

        Returns:
            tuple: (raw_output_dict, markdown_content)
        """
        try:
            # Prepare environment for Mineru processing
            file_name = Path(file_path).stem
            print(
                f"🔍 DEBUG: Calling prepare_env with output_dir={output_dir}, file_name={file_name}"
            )
            local_image_dir, local_md_dir = self.prepare_env(
                output_dir, file_name, "auto"
            )
            print(
                f"🔍 DEBUG: prepare_env returned local_image_dir={local_image_dir} (type: {type(local_image_dir)})"
            )
            print(
                f"🔍 DEBUG: prepare_env returned local_md_dir={local_md_dir} (type: {type(local_md_dir)})"
            )
            image_writer, md_writer = self.FileBasedDataWriter(
                local_image_dir
            ), self.FileBasedDataWriter(local_md_dir)

            # Read file bytes
            file_bytes = self.read_fn(file_path)

            # Handle page selection for PDFs
            selected_pages = kwargs.get("pages", None)
            start_page_id = 0
            end_page_id = None

            if selected_pages and len(selected_pages) > 0:
                # Convert to 0-indexed for Mineru
                start_page_id = min(selected_pages) - 1
                end_page_id = max(selected_pages) - 1

            # Apply page selection if specified
            if start_page_id > 0 or end_page_id is not None:
                file_bytes = self.convert_pdf_bytes_to_bytes_by_pypdfium2(
                    file_bytes, start_page_id, end_page_id
                )

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
                formula_enable=formula_enable,
                table_enable=table_enable,
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
                    formula_enable,
                )

                # Generate markdown content
                print(
                    f"🔍 DEBUG: Before image_dir assignment, local_image_dir={local_image_dir} (type: {type(local_image_dir)})"
                )
                # FIX: local_image_dir is already a string path, no need for .name
                image_dir = str(local_image_dir)
                print(f"🔍 DEBUG: Using image_dir={image_dir}")
                markdown_content = self.pipeline_union_make(
                    middle_json["pdf_info"], self.MakeMode.MM_MD, image_dir
                )

                # Process markdown to convert image links to HTML img tags
                markdown_content = self._convert_markdown_images_to_html(markdown_content, image_dir)

                # Fix line breaks - ensure proper paragraph spacing
                markdown_content = self._fix_line_breaks(markdown_content)

                # Add HTML line breaks for rendered output
                markdown_content = self._add_line_breaks_to_html(markdown_content)

                # Copy images to permanent location for serving
                self._copy_images_to_serving_location(image_dir)

                # Prepare raw output
                raw_output = {
                    "middle_json": middle_json,
                    "model_output": model_list,
                    "metadata": {
                        "language": _lang,
                        "ocr_enabled": _ocr_enable,
                        "formula_enabled": True,
                        "table_enabled": True,
                    },
                }

                return raw_output, markdown_content

            else:
                raise Exception("No inference results from Mineru")

        except Exception as e:
            print(f"✗ Mineru pipeline processing failed: {e}")
            raise

    def _generate_boxes_image(
        self, image: Image.Image, raw_output: Dict[str, Any]
    ) -> str:
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

    def _convert_markdown_images_to_html(self, markdown_content: str, image_dir: str) -> str:
        """
        Convert markdown image links to HTML img tags for proper rendering.

        Args:
            markdown_content: Original markdown content with image links
            image_dir: Directory where images are stored

        Returns:
            str: Processed markdown with HTML img tags
        """
        import re
        import os
        from pathlib import Path

        if not markdown_content:
            return markdown_content

        print(f"🔍 DEBUG: Converting markdown images to HTML, image_dir: {image_dir}")

        # Pattern to match markdown image syntax: ![alt](url)
        pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'

        def replace_image_match(match):
            alt_text = match.group(1)
            image_url = match.group(2)

            print(f"🔍 DEBUG: Found image: alt='{alt_text}', url='{image_url}'")

            # Extract image filename from URL
            image_filename = os.path.basename(image_url)

            # Check if image file exists in the image directory
            image_path = Path(image_dir) / image_filename
            if image_path.exists():
                # Create HTML img tag with server URL
                img_tag = f'<img src="http://localhost:5001/images/{image_filename}" alt="{alt_text}" style="max-width: 100%; height: auto;">'
                print(f"🔍 DEBUG: Converted to: {img_tag}")
                return img_tag
            else:
                print(f"🔍 DEBUG: Image file not found: {image_path}")
                return match.group(0)  # Return original if image not found

        # Replace all markdown image links with HTML img tags
        processed_content = re.sub(pattern, replace_image_match, markdown_content)

        print(f"🔍 DEBUG: Image conversion completed. Original length: {len(markdown_content)}, Processed length: {len(processed_content)}")

        return processed_content

    def _fix_line_breaks(self, markdown_content: str) -> str:
        """
        Fix line breaks in markdown content to ensure proper paragraph spacing.

        Args:
            markdown_content: Original markdown content

        Returns:
            str: Markdown content with proper line breaks
        """
        import re

        if not markdown_content:
            return markdown_content

        # Ensure proper spacing between paragraphs
        # Replace multiple newlines with exactly two newlines (standard markdown paragraph separation)
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

        # Ensure single newlines at the end of paragraphs are preserved
        # This helps maintain the structure while preventing excessive spacing
        markdown_content = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', markdown_content)

        # Clean up any remaining spacing issues
        markdown_content = markdown_content.strip()

        return markdown_content

    def _copy_images_to_serving_location(self, image_dir: str):
        """
        Copy images from temporary processing directory to permanent serving location.

        Args:
            image_dir: Temporary directory where Mineru processed images are stored
        """
        import shutil
        import os
        from pathlib import Path

        try:
            # Create permanent serving directory
            serving_dir = Path("outputs") / "images"
            serving_dir.mkdir(parents=True, exist_ok=True)

            print(f"🔍 DEBUG: Copying images from {image_dir} to {serving_dir}")

            # Copy all image files from temporary directory to serving directory
            temp_dir = Path(image_dir)
            if temp_dir.exists():
                for image_file in temp_dir.glob("*.*"):
                    if image_file.is_file():
                        dest_path = serving_dir / image_file.name
                        shutil.copy2(image_file, dest_path)
                        print(f"🔍 DEBUG: Copied {image_file.name} to serving location")
            else:
                print(f"🔍 DEBUG: Temporary image directory {image_dir} does not exist")

        except Exception as e:
            print(f"🔍 DEBUG: Error copying images to serving location: {e}")

    def _add_line_breaks_to_html(self, html_content: str) -> str:
        """
        Add line breaks to HTML content for proper spacing.
        Converts newlines to <br> tags while preserving existing HTML structure.

        Args:
            html_content: HTML content with newlines

        Returns:
            str: HTML content with <br> tags
        """
        import re

        if not html_content:
            return html_content

        # Convert double newlines to <br><br> (paragraph breaks)
        html_content = re.sub(r'\n\s*\n', '<br><br>', html_content)
        # Convert single newlines to <br> (line breaks)
        html_content = re.sub(r'\n', '<br>', html_content)

        return html_content
