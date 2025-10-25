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
os.environ['VLLM_USE_V1'] = '0'

# Configuration
DEEPSEEK_PROMPT = '<image>\n<|grounding|>Convert the document to markdown.'
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
        self.processor = None
        self.model_loaded = False
        self.gpu_available = False

        # Set GPU isolation for DeepSeek backend
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"

        print(f"DeepSeekOCRBackend initialized with model_path: {model_path}")
        print(f"GPU isolation: CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES')}")

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
                from vllm import AsyncLLMEngine, SamplingParams
                from vllm.engine.arg_utils import AsyncEngineArgs
                from vllm.model_executor.models.registry import ModelRegistry
                from deepseek_ocr import DeepseekOCRForCausalLM
                from process.ngram_norepeat import NoRepeatNGramLogitsProcessor

                # Import processor exactly like reference implementation
                from process.image_process import DeepseekOCRProcessor
                print("✓ Using DeepseekOCRProcessor from process.image_process")
            except ImportError as e:
                print(f"✗ Required modules not available: {e}")
                return False

            # Register model
            ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

            # Initialize vLLM engine
            engine_args = AsyncEngineArgs(
                model=str(self.model_path),
                tokenizer=str(self.model_path),
                tensor_parallel_size=1,
                dtype="bfloat16",
                gpu_memory_utilization=0.9,
                max_model_len=8192,
                enable_chunked_prefill=True,
                max_num_batched_tokens=8192,
                max_num_seqs=16,
                trust_remote_code=True,
                disable_custom_all_reduce=True,
            )

            self.engine = AsyncLLMEngine.from_engine_args(engine_args)

            # Initialize processor with error handling
            try:
                self.processor = DeepseekOCRProcessor()
                if self.processor is None:
                    print("✗ DeepseekOCRProcessor() returned None - CRITICAL ERROR")
                    raise Exception("DeepseekOCRProcessor() returned None")

                # Test if processor has required attributes
                if not hasattr(self.processor, 'padding_side'):
                    print("✗ DeepseekOCRProcessor missing 'padding_side' attribute - CRITICAL ERROR")
                    raise Exception("DeepseekOCRProcessor missing 'padding_side' attribute")

            except Exception as e:
                print(f"✗ Failed to initialize DeepseekOCRProcessor: {e}")
                raise

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
                raw_result={"deepseek": "", "mineru": {}},
                markdown="Model not loaded",
                image_name=Path(image_path).name
            )

        start_time = time.time()

        try:
            # Load and process image
            image = Image.open(image_path)

            # Process image through DeepSeek OCR
            raw_output = self._process_image_with_deepseek(image, **kwargs)

            # Extract markdown and bounding boxes
            markdown_result = self._extract_markdown_from_output(raw_output)
            boxes_image = self._generate_boxes_image(image, raw_output)

            processing_time = time.time() - start_time

            return create_unified_response(
                success=True,
                backend="deepseek-ocr",
                raw_result={"deepseek": raw_output, "mineru": {}},
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
                backend="deepseek-ocr",
                raw_result={"deepseek": "", "mineru": {}},
                markdown=f"OCR processing failed: {str(e)}",
                processing_time=processing_time,
                image_name=Path(image_path).name
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
                raw_result={"deepseek": "", "mineru": {}},
                markdown="Model not loaded",
                image_name=Path(pdf_path).name
            )

        start_time = time.time()

        try:
            # Extract selected pages from kwargs
            selected_pages = kwargs.get('pages', None)

            # Process PDF using optimized DeepSeek approach
            raw_output, markdown_result = self._process_pdf_with_deepseek(pdf_path, selected_pages)

            # Generate bounding boxes image (placeholder for now)
            boxes_image = ""  # PDF bounding box visualization would be more complex

            processing_time = time.time() - start_time

            return create_unified_response(
                success=True,
                backend="deepseek-ocr",
                raw_result={"deepseek": raw_output, "mineru": {}},
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
                backend="deepseek-ocr",
                raw_result={"deepseek": "", "mineru": {}},
                markdown=f"PDF processing failed: {str(e)}",
                processing_time=processing_time,
                image_name=Path(pdf_path).name
            )

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get DeepSeek backend health status.

        Returns:
            dict: Health information including model_loaded, gpu_available, etc.
        """
        return {
            "status": "healthy" if self.model_loaded and self.gpu_available else "unhealthy",
            "model_loaded": self.model_loaded,
            "gpu_available": self.gpu_available,
            "backend": "deepseek-ocr",
            "timestamp": time.time()
        }

    def _process_pdf_with_deepseek(self, pdf_path: str, selected_pages: List[int] = None) -> Tuple[Dict[str, Any], str]:
        """
        Process PDF using optimized DeepSeek approach with parallel page processing.

        Args:
            pdf_path: Path to PDF file
            selected_pages: List of page numbers to process (1-indexed)

        Returns:
            Tuple of (raw_output, markdown_content)
        """
        import fitz
        import io
        from concurrent.futures import ThreadPoolExecutor
        from tqdm import tqdm

        try:
            # Open PDF document
            doc = fitz.open(pdf_path)

            # Determine pages to process
            if selected_pages is None:
                pages_to_process = list(range(len(doc)))
            else:
                # Convert to 0-indexed and validate
                pages_to_process = [p-1 for p in selected_pages if 1 <= p <= len(doc)]

            if not pages_to_process:
                raise ValueError("No valid pages selected for processing")

            # Convert PDF pages to high-quality images
            images = []
            zoom = 144 / 72.0  # 144 DPI
            matrix = fitz.Matrix(zoom, zoom)

            for page_idx in pages_to_process:
                page = doc[page_idx]
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                img_data = pixmap.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)

            doc.close()

            # Process images in parallel using ThreadPoolExecutor
            batch_inputs = []
            with ThreadPoolExecutor(max_workers=min(len(images), 4)) as executor:
                # Prepare batch inputs
                for image in images:
                    cache_item = {
                        "prompt": DEEPSEEK_PROMPT,
                        "multi_modal_data": {
                            "image": self.processor.tokenize_with_images(
                                images=[image], bos=True, eos=True, cropping=CROP_MODE
                            )
                        },
                    }
                    batch_inputs.append(cache_item)

            # Generate OCR results for all pages
            outputs_list = self.engine.generate(
                batch_inputs,
                sampling_params=self.sampling_params
            )

            # Combine results from all pages
            all_contents = []
            raw_outputs = []

            for output, page_num in zip(outputs_list, pages_to_process):
                content = output.outputs[0].text

                # Clean up the output
                if '<|endoftext|>' in content:
                    content = content.replace('<|endoftext|>', '')

                # Add page separator
                page_separator = f'\n<--- Page {page_num + 1} --->\n'
                all_contents.append(content + page_separator)
                raw_outputs.append({
                    "page": page_num + 1,
                    "raw_output": content
                })

            # Combine all page results
            markdown_content = "\n".join(all_contents)
            raw_output = {
                "pages": raw_outputs,
                "total_pages": len(pages_to_process),
                "processed_pages": [p + 1 for p in pages_to_process]
            }

            return raw_output, markdown_content

        except Exception as e:
            print(f"Error in PDF processing: {e}")
            raise

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
        self.processor = None
        self.model_loaded = False
        print("DeepSeek backend resources cleaned up")

    def _process_image_with_deepseek(self, image: Image.Image, **kwargs) -> str:
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

            # Prepare image for processing
            image_path = "/tmp/temp_image.png"
            image.save(image_path)

            # Process image using DeepSeek OCR processor
            processed_inputs = self.processor(
                prompt=DEEPSEEK_PROMPT,
                images=[image_path],
                return_tensors="pt",
                cropping=CROP_MODE
            )

            # Prepare sampling parameters
            sampling_params = SamplingParams(
                temperature=0.1,
                top_p=0.9,
                max_tokens=4096,
                stop_token_ids=[self.processor.tokenizer.eos_token_id],
                logits_processors=[NoRepeatNGramLogitsProcessor(ngram_size=3)]
            )

            # Generate OCR output using vLLM engine
            request_id = f"ocr_{int(time.time())}"

            async for request_output in self.engine.generate(
                prompt=DEEPSEEK_PROMPT,
                sampling_params=sampling_params,
                request_id=request_id,
                **processed_inputs
            ):
                if request_output.outputs:
                    full_text = request_output.outputs[0].text
                    return full_text

            return ""

        try:
            # Run async generation with timeout
            final_output = asyncio.run(asyncio.wait_for(generate_ocr(), timeout=120.0))
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

        Args:
            raw_output: Raw OCR output from DeepSeek

        Returns:
            str: Processed markdown text
        """
        import re

        if not raw_output:
            return ""

        # Extract text between <|ref|> and <|/ref|> markers (excluding image references)
        pattern = r'<\|ref\|>(?!image)(.*?)<\|/ref\|>'
        matches = re.findall(pattern, raw_output, re.DOTALL)

        # Combine all text matches
        markdown_text = "\n\n".join([match.strip() for match in matches if match.strip()])

        # Clean up extra whitespace
        markdown_text = re.sub(r'\n\s*\n', '\n\n', markdown_text)
        markdown_text = markdown_text.strip()

        return markdown_text if markdown_text else "No text extracted from OCR output"

    def _generate_boxes_image(self, image: Image.Image, raw_output: str) -> str:
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
            pattern = r'(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)'
            matches = re.findall(pattern, raw_output, re.DOTALL)

            for match in matches:
                try:
                    ref_text = match[1]  # Content between <|ref|> and <|/ref|>
                    det_text = match[2]  # Content between <|det|> and <|/det|>

                    # Extract coordinates from <|det|>[[x1,y1,x2,y2]]<|/det|>
                    if det_text.startswith('[[') and det_text.endswith(']]'):
                        coords_text = det_text[2:-2]  # Remove [[ and ]]
                        coords = [int(x.strip()) for x in coords_text.split(',')]
                        if len(coords) == 4:
                            x1, y1, x2, y2 = coords
                            boxes.append({
                                'coordinates': [x1, y1, x2, y2],
                                'label': ref_text if ref_text else 'text'
                            })
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
            overlay = Image.new('RGBA', img_draw.size, (0, 0, 0, 0))
            draw2 = ImageDraw.Draw(overlay)

            # Try to load font, fallback to default
            try:
                font = ImageFont.truetype("Arial.ttf", 12)
            except:
                font = ImageFont.load_default()

            for i, box_info in enumerate(boxes):
                try:
                    coordinates = box_info['coordinates']
                    label = box_info['label']

                    if len(coordinates) == 4:
                        x1, y1, x2, y2 = coordinates

                        # Normalize coordinates from 0-999 range to actual image dimensions
                        x1 = int(x1 / 999 * image_width)
                        y1 = int(y1 / 999 * image_height)
                        x2 = int(x2 / 999 * image_width)
                        y2 = int(y2 / 999 * image_height)

                        # Generate random color for each box
                        color = (np.random.randint(0, 200), np.random.randint(0, 200), np.random.randint(0, 255))
                        color_a = color + (20,)  # Semi-transparent version

                        # Draw bounding box with semi-transparent fill
                        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                        draw2.rectangle([x1, y1, x2, y2], fill=color_a, outline=(0, 0, 0, 0), width=1)

                        # Add label text with background
                        text_x = x1
                        text_y = max(0, y1 - 15)

                        try:
                            text_bbox = draw.textbbox((0, 0), label, font=font)
                            text_width = text_bbox[2] - text_bbox[0]
                            text_height = text_bbox[3] - text_bbox[1]

                            draw.rectangle([text_x, text_y, text_x + text_width, text_y + text_height],
                                        fill=(255, 255, 255, 30))
                            draw.text((text_x, text_y), label, font=font, fill=color)
                        except:
                            # Fallback if font measurement fails
                            draw.text((text_x, text_y), label, font=font, fill=color)
                except Exception as e:
                    print(f"Error drawing box {i}: {e}")
                    continue

            # Apply the semi-transparent overlay
            img_draw.paste(overlay, (0, 0), overlay)

            # Convert to base64
            buffer = io.BytesIO()
            img_draw.save(buffer, format='PNG')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return image_base64

        except Exception as e:
            print(f"Error generating boxes image: {e}")
            return ""


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


@app.route('/ocr/image', methods=['POST'])
def ocr_image():
    """Process single image OCR request"""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']

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


@app.route('/ocr/pdf', methods=['POST'])
def ocr_pdf():
    """Process PDF OCR request"""
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400

    pdf_file = request.files['pdf']

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


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if backend:
        status = backend.get_health_status()
        return jsonify(status)
    else:
        return jsonify({
            "status": "unhealthy",
            "model_loaded": False,
            "gpu_available": False,
            "backend": "deepseek-ocr",
            "timestamp": time.time()
        })


if __name__ == '__main__':
    # Initialize backend on startup
    initialize_backend()

    # Start Flask server on port 5000
    print("Starting DeepSeek OCR backend server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)