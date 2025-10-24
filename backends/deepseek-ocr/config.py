# DeepSeek OCR Configuration
# Configuration for DeepSeek OCR backend

# Image processing settings
BASE_SIZE = 1024
IMAGE_SIZE = 640
CROP_MODE = True
MIN_CROPS = 2
MAX_CROPS = 6  # max:9; If your GPU memory is small, it is recommended to set it to 6.
MAX_CONCURRENCY = 100  # If you have limited GPU memory, lower the concurrency count.
NUM_WORKERS = 64  # image pre-process (resize/padding) workers
PRINT_NUM_VIS_TOKENS = False
SKIP_REPEAT = True

# Model path - default path relative to backend directory
MODEL_PATH = '../models/deepseek-ocr'

# Input/Output paths (not used in server mode)
INPUT_PATH = ''
OUTPUT_PATH = ''

# OCR prompt
PROMPT = '<image>\n<|grounding|>Convert the document to markdown.'

# Tokenizer - will be initialized when model path is available
TOKENIZER = None

# Function to initialize tokenizer when model path is available
def initialize_tokenizer(model_path=None):
    """Initialize the tokenizer with the given model path"""
    global TOKENIZER
    try:
        from transformers import AutoTokenizer
        path = model_path or MODEL_PATH
        TOKENIZER = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        return TOKENIZER
    except Exception as e:
        print(f"Warning: Failed to initialize tokenizer: {e}")
        return None
