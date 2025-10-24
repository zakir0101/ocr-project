from abc import ABC, abstractmethod


class OCRBackend(ABC):
    """
    Abstract base class for OCR backends.

    This interface defines the common methods that all OCR backends
    (DeepSeek-OCR, Mineru, etc.) must implement.
    """

    @abstractmethod
    def __init__(self, model_path: str, device: str = "cuda"):
        """
        Initialize OCR backend with model path and device.

        Args:
            model_path (str): Path to model weights/config
            device (str): Device to run on (default: "cuda")
        """
        pass

    @abstractmethod
    def load_model(self) -> bool:
        """
        Load model into GPU memory.

        This method should handle the actual model loading into GPU memory.
        It should be called separately from __init__ to allow for lazy loading.

        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def ocr_image(self, image_path: str, **kwargs) -> dict:
        """
        Perform OCR on a single image.

        Args:
            image_path (str): Path to input image
            **kwargs: Additional parameters

        Returns:
            dict: OCR results in unified format
        """
        pass

    @abstractmethod
    def ocr_pdf(self, pdf_path: str, **kwargs) -> dict:
        """
        Perform OCR on a PDF document.

        Args:
            pdf_path (str): Path to input PDF
            **kwargs: Additional parameters

        Returns:
            dict: OCR results in unified format
        """
        pass

    @abstractmethod
    def get_health_status(self) -> dict:
        """
        Get backend health status.

        Returns:
            dict: Health information including model_loaded, gpu_available, etc.
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Clean up backend resources.

        This method should release GPU memory and other resources.
        """
        pass