"""
DeepSeek OCR Backend Implementation

This module implements the DeepSeekOCRBackend class that conforms to the
OCRBackend interface from shared/ocr_backend.py.
"""

import os
import time
import base64
import io
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import torch
from PIL import Image, ImageDraw
from flask import Flask, request, jsonify

# Import shared components
from shared.ocr_backend import OCRBackend
from shared.api_contract import create_unified_response


# Set vLLM to use legacy API (compatible with DeepSeek OCR)
os.environ["VLLM_USE_V1"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = '0'

# Configuration
DEEPSEEK_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."
CROP_MODE = True


class DeepSeekOCRBackend(OCRBackend):
    """
    DeepSeek OCR backend implementation using the OCRBackend interface.

    This backend uses GPU 0 exclusively and implements all required
    abstract methods from the OCRBackend interface.
    """

    def __init__(self, model_path: str, device: str = "cuda"):
        """
        Initialize DeepSeek OCR backend with model path and device.

        Args:
            model_path (str): Path to DeepSeek OCR model weights/config
            device (str): Device to run on (default: "cuda")
        """
        self.model_path = Path(model_path)
        self.device = device
        self.engine = None
        self.model_loaded = False
        self.gpu_available = False

        # Set GPU isolation for DeepSeek backend
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"

        print(f"DeepSeekOCRBackend initialized with model_path: {model_path}")
        print(
            f"GPU isolation: CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES')}"
        )

    def load_model(self) -> bool:
        """
        Load DeepSeek model into GPU 0 memory.

        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            print("Loading DeepSeek OCR model into GPU 0 memory...")

            # Check if CUDA is available
            if not torch.cuda.is_available():
                print("✗ CUDA not available - cannot load model")
                self.gpu_available = False
                return False

            self.gpu_available = True

            # Check if model path exists
            if not self.model_path.exists():
                print(f"✗ Model path does not exist: {self.model_path}")
                return False

            # Import required modules (lazy imports to avoid dependency issues)
            try:
                from vllm import LLM, SamplingParams
                from vllm.model_executor.models.registry import ModelRegistry

                from deepseek_ocr import DeepseekOCRForCausalLM
                from process.ngram_norepeat import NoRepeatNGramLogitsProcessor

                # Import processor exactly like reference implementation
                from process.image_process import DeepseekOCRProcessor

                print(
                    "✓ Using DeepseekOCRProcessor from process.image_process"
                )
            except ImportError as e:
                print(f"✗ Required modules not available: {e}")
                return False

            # Register model
            print("✓ Registering DeepseekOCRForCausalLM model...")
            ModelRegistry.register_model(
                "DeepseekOCRForCausalLM", DeepseekOCRForCausalLM
            )
            print("✓ Model registration successful")

            # Initialize vLLM engine - EXACTLY like reference implementation
            print("✓ Initializing vLLM engine...")
            self.engine = LLM(
                model=str(self.model_path),
                hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
                tokenizer=str(self.model_path),
                block_size=256,
                enforce_eager=False,
                trust_remote_code=True,
                max_model_len=8192,
                swap_space=0,
                max_num_seqs=100,  # Like official MAX_CONCURRENCY
                tensor_parallel_size=1,
                gpu_memory_utilization=0.9,  # Official uses 0.9
                disable_mm_preprocessor_cache=True,  # CRITICAL: Official uses this
            )
            print("✓ vLLM engine initialization successful")

            # Test processor creation to catch initialization errors early
            print("✓ Testing processor creation...")
            try:
                # Create a test processor instance to verify it works
                test_processor = DeepseekOCRProcessor()
                print("✓ Processor creation successful")
            except Exception as e:
                print(f"✗ Processor creation failed: {e}")
                raise

            # Processor will be created fresh each time like reference implementation
            print(
                "✓ Processor will be created fresh for each request (like reference)"
            )

            self.model_loaded = True
            print("✓ DeepSeek OCR model loaded successfully into GPU 0")
            return True

        except Exception as e:
            print(f"✗ Failed to load DeepSeek model: {e}")
            self.model_loaded = False
            return False

    def ocr_image(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        Perform OCR on a single image using DeepSeek OCR.

        Args:
            image_path (str): Path to input image
            **kwargs: Additional parameters

        Returns:
            dict: OCR results in unified format
        """
        if not self.model_loaded:
            return create_unified_response(
                success=False,
                backend="deepseek-ocr",
                raw_result="",
                rendered_html="Model not loaded",
                image_name=Path(image_path).name,
            )

        start_time = time.time()

        try:
            print(f"🔍 DEBUG: Starting OCR processing for image: {image_path}")

            # Load and process image - ensure RGB format
            image = Image.open(image_path)
            print(f"🔍 DEBUG: Original image mode: {image.mode}, size: {image.size}")

            # Convert to RGB to ensure 3 channels (remove alpha channel if present)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
                print(f"🔍 DEBUG: Converted image from {image.mode} to RGB")
            elif image.mode != 'RGB':
                image = image.convert('RGB')
                print(f"🔍 DEBUG: Converted image from {image.mode} to RGB")
            else:
                print(f"🔍 DEBUG: Image already in RGB format")

            # Process image through DeepSeek OCR
            raw_output = self._process_image_with_deepseek(image, **kwargs)

            # Extract image references and crop images (like reference implementation)
            matches_ref, matches_images, matches_other = self._re_match(raw_output)
            if matches_images:
                self._crop_and_save_images(image_path, matches_images)

            # Extract rendered HTML and bounding boxes
            rendered_html = self._process_ocr_for_rendering(raw_output)
            boxes_image = self._generate_boxes_image(image, raw_output)

            processing_time = time.time() - start_time

            print(f"🔍 DEBUG: OCR processing completed in {processing_time:.2f}s")
            print(f"🔍 DEBUG: Final rendered HTML length: {len(rendered_html)}")

            return create_unified_response(
                success=True,
                backend="deepseek-ocr",
                raw_result=raw_output,  # Direct DeepSeek output, not combined format
                rendered_html=rendered_html,
                boxes_image=boxes_image,
                processing_time=processing_time,
                image_name=Path(image_path).name,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"✗ OCR processing failed: {e}")

            return create_unified_response(
                success=False,
                backend="deepseek-ocr",
                raw_result="",
                rendered_html=f"OCR processing failed: {str(e)}",
                processing_time=processing_time,
                image_name=Path(image_path).name,
            )

    def ocr_pdf(self, pdf_path: str, **kwargs) -> Dict[str, Any]:
        """
        Perform OCR on a PDF document using DeepSeek OCR with optimized parallel processing.

        Args:
            pdf_path (str): Path to input PDF
            **kwargs: Additional parameters (pages, etc.)

        Returns:
            dict: OCR results in unified format
        """
        if not self.model_loaded:
            return create_unified_response(
                success=False,
                backend="deepseek-ocr",
                raw_result="",
                rendered_html="Model not loaded",
                image_name=Path(pdf_path).name,
            )

        start_time = time.time()

        try:
            # Extract selected pages from kwargs
            selected_pages = kwargs.get("pages", None)

            # Process PDF using optimized DeepSeek approach
            raw_output, markdown_result = self._process_pdf_with_deepseek(
                pdf_path, selected_pages
            )

            # Generate bounding boxes image (placeholder for now)
            boxes_image = (
                ""  # PDF bounding box visualization would be more complex
            )

            # Create proper RENDERED output - use same function as image processing
            rendered_html = self._process_ocr_for_rendering(markdown_result)

            processing_time = time.time() - start_time

            return create_unified_response(
                success=True,
                backend="deepseek-ocr",
                raw_result=raw_output,  # Direct DeepSeek output, not combined format
                rendered_html=rendered_html,
                boxes_image=boxes_image,
                processing_time=processing_time,
                image_name=Path(pdf_path).name,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"✗ PDF processing failed: {e}")

            return create_unified_response(
                success=False,
                backend="deepseek-ocr",
                raw_result="",
                rendered_html=f"PDF processing failed: {str(e)}",
                processing_time=processing_time,
                image_name=Path(pdf_path).name,
            )

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get DeepSeek backend health status.

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
            "backend": "deepseek-ocr",
            "timestamp": time.time(),
        }

    def _process_pdf_with_deepseek(
        self, pdf_path: str, selected_pages: List[int] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Process PDF using optimized DeepSeek approach with parallel page processing.
        Based on official DeepSeek PDF processing implementation.

        Args:
            pdf_path: Path to PDF file
            selected_pages: List of page numbers to process (1-indexed)

        Returns:
            Tuple of (raw_output, markdown_content)
        """
        import fitz
        import io
        from concurrent.futures import ThreadPoolExecutor

        try:
            # Convert PDF to high-quality images (144 DPI like official code)
            images = self._pdf_to_images_high_quality(pdf_path, selected_pages)

            if not images:
                raise ValueError("No valid pages selected for processing")

            # Process images exactly like official code
            batch_inputs = []
            for image in images:
                from process.image_process import DeepseekOCRProcessor

                cache_item = {
                    "prompt": DEEPSEEK_PROMPT,
                    "multi_modal_data": {
                        "image": DeepseekOCRProcessor().tokenize_with_images(
                            images=[image],
                            bos=True,
                            eos=True,
                            cropping=CROP_MODE,
                        )
                    },
                }
                batch_inputs.append(cache_item)

            # Generate OCR results for all pages using official sampling parameters
            from vllm import SamplingParams
            from process.ngram_norepeat import NoRepeatNGramLogitsProcessor

            sampling_params = SamplingParams(
                temperature=0.0,
                max_tokens=8192,  # Official uses 8192
                logits_processors=[NoRepeatNGramLogitsProcessor(
                    ngram_size=20,  # Official uses 20 for PDF
                    window_size=50,  # Official uses 50 for PDF
                    whitelist_token_ids={128821, 128822}
                )],
                skip_special_tokens=False,
                include_stop_str_in_output=True,  # Official includes this
            )

            # Use synchronous generation for PDF processing like official code
            outputs_list = self.engine.generate(
                batch_inputs, sampling_params=sampling_params
            )

            # Process results using official approach
            contents_det = ''
            contents = ''
            raw_outputs = []

            for jdx, (output, img) in enumerate(zip(outputs_list, images)):
                content = output.outputs[0].text

                # Clean up the output like official code
                if '<|endoftext|>' in content:
                    content = content.replace('<|endoftext|>', '')

                # Add page separator like official code
                page_separator = f'\n<--- Page Split --->\n'
                contents_det += content + page_separator

                # Process image references like official code
                matches_ref, matches_images, matches_other = self._re_match(content)

                # Crop and save images from bounding boxes
                if matches_images:
                    # Save the current page image temporarily to crop from it
                    temp_image_path = f"/tmp/pdf_page_{jdx}.png"
                    img.save(temp_image_path)
                    self._crop_and_save_images(temp_image_path, matches_images, image_prefix=f"{jdx}_")

                # Replace image references with direct HTML img tags
                for idx, a_match_image in enumerate(matches_images):
                    img_tag = f'<img src="http://localhost:5000/images/{jdx}_{idx}.jpg" alt="Extracted image" style="max-width: 100%; height: auto;"><br>'
                    content = content.replace(a_match_image, img_tag)

                # Remove other <|ref|> tags and clean up
                for a_match_other in matches_other:
                    content = content.replace(a_match_other, '').replace('\\coloneqq', ':=').replace('\\eqqcolon', '=:').replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')

                contents += content + page_separator
                raw_outputs.append({
                    "page": jdx + 1,
                    "raw_output": content,
                    "matches_ref": matches_ref,
                    "matches_images": matches_images,
                    "matches_other": matches_other
                })

            # Use the cleaned content for markdown
            markdown_content = contents
            raw_output = {
                "pages": raw_outputs,
                "total_pages": len(images),
                "processed_pages": list(range(1, len(images) + 1)),
                "contents_det": contents_det,
            }

            return raw_output, markdown_content

        except Exception as e:
            print(f"Error in PDF processing: {e}")
            raise

    def _pdf_to_images_high_quality(self, pdf_path: str, selected_pages: List[int] = None, dpi: int = 144):
        """
        Convert PDF to high-quality images using official approach.

        Args:
            pdf_path: Path to PDF file
            selected_pages: List of page numbers to process (1-indexed)
            dpi: DPI for conversion (default 144 like official code)

        Returns:
            List of PIL Image objects
        """
        import fitz
        import io

        images = []

        pdf_document = fitz.open(pdf_path)

        # Determine pages to process
        if selected_pages is None:
            pages_to_process = list(range(pdf_document.page_count))
        else:
            # Convert to 0-indexed and validate
            pages_to_process = [
                p - 1 for p in selected_pages if 1 <= p <= pdf_document.page_count
            ]

        if not pages_to_process:
            pdf_document.close()
            return images

        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in pages_to_process:
            page = pdf_document[page_num]

            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            Image.MAX_IMAGE_PIXELS = None

            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Convert to RGB like official code
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            images.append(img)

        pdf_document.close()
        return images

    def cleanup(self):
        """
        Clean up DeepSeek backend resources.
        """
        if self.engine:
            # Clean up vLLM engine resources
            try:
                self.engine.shutdown()
            except Exception as e:
                print(f"Warning: Error during engine cleanup: {e}")

        self.engine = None
        self.model_loaded = False
        print("DeepSeek backend resources cleaned up")

    def _process_image_with_deepseek(
        self, image: Image.Image, **kwargs
    ) -> str:
        """
        Process image through DeepSeek OCR model.

        Args:
            image: PIL Image object
            **kwargs: Additional parameters

        Returns:
            str: Raw OCR output text
        """
        import asyncio
        import re

        async def generate_ocr():
            """Async generation function from reference implementation"""
            from vllm import SamplingParams
            from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
            from process.image_process import DeepseekOCRProcessor

            # Prepare image for processing
            image_path = "/tmp/temp_image.png"
            image.save(image_path)

            # Process image using DeepSeek OCR processor - EXACTLY like reference
            image_features = DeepseekOCRProcessor().tokenize_with_images(
                images=[image], bos=True, eos=True, cropping=CROP_MODE
            )

            # Create request exactly like reference implementation
            request = {
                "prompt": DEEPSEEK_PROMPT,
                "multi_modal_data": {"image": image_features},
            }

            # Prepare sampling parameters
            sampling_params = SamplingParams(
                temperature=0.0,
                top_p=1.0,
                max_tokens=4096,
                logits_processors=[NoRepeatNGramLogitsProcessor(
                    ngram_size=30,
                    window_size=90,
                    whitelist_token_ids={128821, 128822}
                )],
                skip_special_tokens=False
            )

            # Generate OCR output using vLLM engine - EXACTLY like reference
            request_id = f"ocr_{int(time.time())}"

            # Accumulate output like reference implementation
            printed_length = 0
            final_output = ""

            async for request_output in self.engine.generate(
                request, sampling_params=sampling_params, request_id=request_id
            ):
                if request_output.outputs:
                    full_text = request_output.outputs[0].text
                    # Stream the output like official code
                    new_text = full_text[printed_length:]
                    if new_text:
                        print(new_text, end='', flush=True)
                    printed_length = len(full_text)
                    final_output = full_text

            print('\n')  # New line after generation completes
            return final_output

        try:
            print(f"🔍 DEBUG: Starting DeepSeek OCR processing for image: {image.size}")
            print(f"🔍 DEBUG: Using prompt: {DEEPSEEK_PROMPT}")

            # Run async generation with timeout
            final_output = asyncio.run(
                asyncio.wait_for(generate_ocr(), timeout=120.0)
            )

            print(f"🔍 DEBUG: Raw OCR output received, length: {len(final_output) if final_output else 0}")
            if final_output:
                print(f"🔍 DEBUG: First 500 chars of raw output: {final_output[:500]}")
                print(f"🔍 DEBUG: Last 500 chars of raw output: {final_output[-500:]}")
            else:
                print("🔍 DEBUG: Raw OCR output is EMPTY")

            return final_output

        except asyncio.TimeoutError:
            print("DeepSeek OCR generation timed out after 120 seconds")
            return ""
        except Exception as e:
            print(f"Error during DeepSeek OCR generation: {e}")
            return ""

    def _extract_markdown_from_output(self, raw_output: str) -> str:
        """
        Extract markdown text from DeepSeek raw output.
        Matches reference implementation: remove all <|ref|> and <|det|> tags

        Args:
            raw_output: Raw OCR output from DeepSeek

        Returns:
            str: Processed markdown text
        """
        import re

        print(f"🔍 DEBUG: Starting markdown extraction from raw output")
        print(f"🔍 DEBUG: Raw output length: {len(raw_output) if raw_output else 0}")

        if not raw_output:
            print("🔍 DEBUG: Raw output is empty, returning empty string")
            return ""

        # Process OCR output like reference implementation: remove all <|ref|> and <|det|> tags
        processed = re.sub(r'<\|ref\|>.*?<\|/ref\|>', '', raw_output)
        processed = re.sub(r'<\|det\|>.*?<\|/det\|>', '', processed)

        # Clean up extra whitespace
        processed = re.sub(r'\n\s*\n', '\n\n', processed)  # Multiple newlines to double newlines
        processed = processed.strip()

        print(f"🔍 DEBUG: Processed markdown text length: {len(processed)}")
        print(f"🔍 DEBUG: Markdown text preview: '{processed[:200]}...'")

        final_result = (
            processed
            if processed
            else "No text extracted from OCR output"
        )

        print(f"🔍 DEBUG: Final markdown result: '{final_result}'")
        return final_result

    def _re_match(self, text):
        """Extract <|ref|> and <|det|> tags from OCR output (official implementation)"""
        import re

        pattern = r'(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)'
        matches = re.findall(pattern, text, re.DOTALL)

        matches_image = []
        matches_other = []
        for a_match in matches:
            if '<|ref|>image<|/ref|>' in a_match[0]:
                matches_image.append(a_match[0])
            else:
                matches_other.append(a_match[0])
        return matches, matches_image, matches_other

    def _extract_coordinates_and_label(self, ref_text, image_width, image_height):
        """Extract coordinates and label from <|ref|> and <|det|> tags (official implementation)"""
        import re

        try:
            # Extract the pattern: <|ref|>label<|/ref|><|det|>[[x1,y1,x2,y2]]<|/det|>
            pattern = r'<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>'
            match = re.search(pattern, ref_text, re.DOTALL)
            if match:
                label_type = match.group(1)
                coords_text = match.group(2)

                # Extract coordinates from [[x1,y1,x2,y2]]
                if coords_text.startswith('[[') and coords_text.endswith(']]'):
                    coords_list = eval(coords_text)
                    return (label_type, coords_list)
        except Exception as e:
            print(f"Error extracting coordinates: {e}")
            return None

        return None

    def _extract_source_markdown_from_output(self, raw_output: str) -> str:
        """
        Extract source markdown for rendering - preserves HTML tables and formatting
        Matches reference implementation's process_ocr_for_rendering function

        Args:
            raw_output: Raw OCR output from DeepSeek

        Returns:
            str: Processed source markdown with HTML preserved
        """
        import re

        print(f"🔍 DEBUG: Starting source markdown extraction from raw output")
        print(f"🔍 DEBUG: Raw output length: {len(raw_output) if raw_output else 0}")

        if not raw_output:
            print("🔍 DEBUG: Raw output is empty, returning empty string")
            return ""

        # Use reference implementation's process_ocr_for_rendering function logic
        # Extract image references using official implementation
        matches_ref, matches_images, matches_other = self._re_match(raw_output)

        # Start with the raw text
        processed = raw_output

        # Replace image references with proper HTML <img> tags
        for idx, a_match_image in enumerate(matches_images):
            # Extract coordinates from the image reference
            result = self._extract_coordinates_and_label(a_match_image, 1000, 1000)  # Use dummy dimensions for calculation
            if result:
                label_type, coords_list = result
                if label_type == 'image' and coords_list:
                    # Get the first bounding box coordinates
                    x1, y1, x2, y2 = coords_list[0]
                    # Calculate width and height from coordinates
                    width = x2 - x1
                    height = y2 - y1
                    # Create proper HTML img tag with server URL and dimensions
                    img_tag = f'<img src="http://localhost:5000/images/{idx}.jpg" width="{width}" height="{height}" alt="Extracted image">'
                    processed = processed.replace(a_match_image, img_tag)

        # Remove other <|ref|> and <|det|> tags (non-image)
        for a_match_other in matches_other:
            processed = processed.replace(a_match_other, '')

        # Convert markdown image syntax to HTML img tags
        processed = self._convert_markdown_images_to_html(processed)

        # Clean up extra whitespace but PRESERVE newlines for proper markdown rendering
        processed = re.sub(r'\n\s*\n', '\n\n', processed)
        processed = processed.strip()

        print(f"🔍 DEBUG: Processed source markdown text length: {len(processed)}")
        print(f"🔍 DEBUG: Source markdown text preview: '{processed[:200]}...'")

        final_result = (
            processed
            if processed
            else "No text extracted from OCR output"
        )

        print(f"🔍 DEBUG: Final source markdown result: '{final_result}'")
        return final_result

    def _crop_and_save_images(self, image_path, matches_images, image_prefix=""):
        """Crop and save images from bounding boxes (official implementation)"""
        try:
            from pathlib import Path

            image = Image.open(image_path).convert('RGB')
            image_width, image_height = image.size

            # Create images directory
            images_dir = Path("outputs") / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            for idx, match_image in enumerate(matches_images):
                result = self._extract_coordinates_and_label(match_image, image_width, image_height)
                if result:
                    label_type, points_list = result
                    if label_type == 'image':
                        for points in points_list:
                            x1, y1, x2, y2 = points

                            # Normalize coordinates from 0-999 range to actual image dimensions
                            x1 = int(x1 / 999 * image_width)
                            y1 = int(y1 / 999 * image_height)
                            x2 = int(x2 / 999 * image_width)
                            y2 = int(y2 / 999 * image_height)

                            try:
                                cropped = image.crop((x1, y1, x2, y2))
                                image_filename = f"{image_prefix}{idx}.jpg" if image_prefix else f"{idx}.jpg"
                                cropped.save(images_dir / image_filename)
                                print(f"✅ Cropped and saved image {image_filename}")
                            except Exception as e:
                                print(f"Error cropping image {idx}: {e}")
                                continue

            return True
        except Exception as e:
            print(f"Error in crop_and_save_images: {e}")
            return False

    def _generate_boxes_image(
        self, image: Image.Image, raw_output: str
    ) -> str:
        """
        Generate base64-encoded image with bounding boxes.

        Args:
            image: Original PIL Image
            raw_output: Raw OCR output with detection markers

        Returns:
            str: Base64-encoded image with bounding boxes
        """
        import re
        import io
        import numpy as np

        if not raw_output:
            return ""

        try:
            # Extract bounding boxes from <|ref|> and <|det|> tags
            boxes = []
            pattern = r"(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)"
            matches = re.findall(pattern, raw_output, re.DOTALL)

            for match in matches:
                try:
                    ref_text = match[1]  # Content between <|ref|> and <|/ref|>
                    det_text = match[2]  # Content between <|det|> and <|/det|>

                    # Extract coordinates from <|det|>[[x1,y1,x2,y2]]<|/det|>
                    if det_text.startswith("[[") and det_text.endswith("]]"):
                        coords_text = det_text[2:-2]  # Remove [[ and ]]
                        coords = [
                            int(x.strip()) for x in coords_text.split(",")
                        ]
                        if len(coords) == 4:
                            x1, y1, x2, y2 = coords
                            boxes.append(
                                {
                                    "coordinates": [x1, y1, x2, y2],
                                    "label": ref_text if ref_text else "text",
                                }
                            )
                except Exception as e:
                    print(f"Error parsing bounding box: {e}")
                    continue

            if not boxes:
                return ""

            # Create image with bounding boxes
            image_width, image_height = image.size
            img_draw = image.copy()
            draw = ImageDraw.Draw(img_draw)

            # Create semi-transparent overlay
            overlay = Image.new("RGBA", img_draw.size, (0, 0, 0, 0))
            draw2 = ImageDraw.Draw(overlay)

            # Try to load font, fallback to default
            try:
                font = ImageFont.truetype("Arial.ttf", 12)
            except:
                font = ImageFont.load_default()

            for i, box_info in enumerate(boxes):
                try:
                    coordinates = box_info["coordinates"]
                    label = box_info["label"]

                    if len(coordinates) == 4:
                        x1, y1, x2, y2 = coordinates

                        # Normalize coordinates from 0-999 range to actual image dimensions
                        x1 = int(x1 / 999 * image_width)
                        y1 = int(y1 / 999 * image_height)
                        x2 = int(x2 / 999 * image_width)
                        y2 = int(y2 / 999 * image_height)

                        # Generate random color for each box
                        color = (
                            np.random.randint(0, 200),
                            np.random.randint(0, 200),
                            np.random.randint(0, 255),
                        )
                        color_a = color + (20,)  # Semi-transparent version

                        # Draw bounding box with semi-transparent fill
                        draw.rectangle(
                            [x1, y1, x2, y2], outline=color, width=2
                        )
                        draw2.rectangle(
                            [x1, y1, x2, y2],
                            fill=color_a,
                            outline=(0, 0, 0, 0),
                            width=1,
                        )

                        # Add label text with background
                        text_x = x1
                        text_y = max(0, y1 - 15)

                        try:
                            text_bbox = draw.textbbox((0, 0), label, font=font)
                            text_width = text_bbox[2] - text_bbox[0]
                            text_height = text_bbox[3] - text_bbox[1]

                            draw.rectangle(
                                [
                                    text_x,
                                    text_y,
                                    text_x + text_width,
                                    text_y + text_height,
                                ],
                                fill=(255, 255, 255, 30),
                            )
                            draw.text(
                                (text_x, text_y), label, font=font, fill=color
                            )
                        except:
                            # Fallback if font measurement fails
                            draw.text(
                                (text_x, text_y), label, font=font, fill=color
                            )
                except Exception as e:
                    print(f"Error drawing box {i}: {e}")
                    continue

            # Apply the semi-transparent overlay
            img_draw.paste(overlay, (0, 0), overlay)

            # Convert to base64
            buffer = io.BytesIO()
            img_draw.save(buffer, format="PNG")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return image_base64

        except Exception as e:
            print(f"Error generating boxes image: {e}")
            return ""

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

    def _process_ocr_for_rendering(self, raw_text: str) -> str:
        """
        Process OCR output specifically for rendered HTML view
        This version preserves image references with proper <img> tags and handles line breaks
        EXACTLY matches reference implementation from vast_server.py

        Args:
            raw_text: Raw OCR output from DeepSeek

        Returns:
            str: Processed HTML for rendering
        """
        import re

        print(f"🔍 DEBUG: Starting process_ocr_for_rendering")
        print(f"🔍 DEBUG: Raw text length: {len(raw_text) if raw_text else 0}")

        # Extract image references using official implementation
        matches_ref, matches_images, matches_other = self._re_match(raw_text)

        # Start with the raw text
        processed = raw_text

        # Replace image references with proper HTML <img> tags
        for idx, a_match_image in enumerate(matches_images):
            # Extract coordinates from the image reference
            result = self._extract_coordinates_and_label(a_match_image, 1000, 1000)  # Use dummy dimensions for calculation
            if result:
                label_type, coords_list = result
                if label_type == 'image' and coords_list:
                    # Get the first bounding box coordinates
                    x1, y1, x2, y2 = coords_list[0]
                    # Calculate width and height from coordinates
                    width = x2 - x1
                    height = y2 - y1
                    # Create proper HTML img tag with server URL and dimensions
                    img_tag = f'<img src="http://localhost:5000/images/{idx}.jpg" width="{width}" height="{height}" alt="Extracted image"><br>'
                    processed = processed.replace(a_match_image, img_tag)

        # Remove other <|ref|> and <|det|> tags (non-image)
        for a_match_other in matches_other:
            processed = processed.replace(a_match_other, '')

        # Clean up extra whitespace and handle line breaks for HTML rendering
        processed = re.sub(r'\n\s*\n', '\n\n', processed)

        # Convert newlines to <br> tags for proper HTML rendering
        processed = processed.replace('\n', '<br>')

        processed = processed.strip()

        print(f"🔍 DEBUG: Processed HTML length: {len(processed)}")
        print(f"🔍 DEBUG: Processed HTML preview: '{processed[:200]}...'")

        return processed

    def _convert_markdown_images_to_html(self, markdown_content: str) -> str:
        """
        Convert markdown image links to HTML img tags for proper rendering.

        Args:
            markdown_content: Original markdown content with image links

        Returns:
            str: Processed markdown with HTML img tags
        """
        import re

        if not markdown_content:
            return markdown_content

        print(f"🔍 DEBUG: Converting markdown images to HTML")

        # Pattern to match markdown image syntax: ![alt](url)
        pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'

        def replace_image_match(match):
            alt_text = match.group(1)
            image_url = match.group(2)

            print(f"🔍 DEBUG: Found markdown image: alt='{alt_text}', url='{image_url}'")

            # Extract image filename from URL
            import os
            image_filename = os.path.basename(image_url)

            # Create HTML img tag with server URL
            img_tag = f'<img src="http://localhost:5000/images/{image_filename}" alt="{alt_text}" style="max-width: 100%; height: auto;">'
            print(f"🔍 DEBUG: Converted to: {img_tag}")
            return img_tag

        # Replace all markdown image links with HTML img tags
        processed_content = re.sub(pattern, replace_image_match, markdown_content)

        print(f"🔍 DEBUG: Markdown image conversion completed. Original length: {len(markdown_content)}, Processed length: {len(processed_content)}")

        return processed_content


# Flask server for DeepSeek backend
app = Flask(__name__)

# Global backend instance
backend = None


def initialize_backend():
    """Initialize the DeepSeek backend on server startup"""
    global backend

    # Use the model path from the config
    model_path = "../models/deepseek-ocr"
    backend = DeepSeekOCRBackend(model_path=model_path)

    if backend.load_model():
        print("✓ DeepSeek backend initialized successfully")
    else:
        print("✗ Failed to initialize DeepSeek backend")


@app.route("/ocr/image", methods=["POST"])
def ocr_image():
    """Process single image OCR request"""
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files["image"]

    # Save uploaded file temporarily
    temp_path = f"/tmp/{image_file.filename}"
    image_file.save(temp_path)

    try:
        # Process image with backend
        result = backend.ocr_image(temp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"OCR processing failed: {str(e)}"}), 500
    finally:
        # Clean up temporary file
        try:
            os.remove(temp_path)
        except:
            pass


@app.route("/ocr/pdf", methods=["POST"])
def ocr_pdf():
    """Process PDF OCR request"""
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400

    pdf_file = request.files["pdf"]

    # Save uploaded file temporarily
    temp_path = f"/tmp/{pdf_file.filename}"
    pdf_file.save(temp_path)

    try:
        # Process PDF with backend
        result = backend.ocr_pdf(temp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"PDF processing failed: {str(e)}"}), 500
    finally:
        # Clean up temporary file
        try:
            os.remove(temp_path)
        except:
            pass


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    if backend:
        status = backend.get_health_status()
        return jsonify(status)
    else:
        return jsonify(
            {
                "status": "unhealthy",
                "model_loaded": False,
                "gpu_available": False,
                "backend": "deepseek-ocr",
                "timestamp": time.time(),
            }
        )


if __name__ == "__main__":
    # Initialize backend on startup
    initialize_backend()

    # Start Flask server on port 5000
    print("Starting DeepSeek OCR backend server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)

