import os
import tempfile
import time
from typing import Tuple, Optional
from PIL import Image

class ImageOptimizer:
    """Pre-processes full resolution screenshots to drastically reduce multimodal token consumption

    while preserving UI sharpness and aspect ratio.
    """

    def __init__(self, max_dimension: int = 1280, quality: int = 85):
        self.max_dimension = max_dimension
        self.quality = quality

    def optimize_for_vision(self, input_path: str, output_path: Optional[str] = None) -> Tuple[str, float, float]:
        """Resizes the screenshot if it exceeds max_dimension.

        Returns:
            Tuple of (optimized_path, scale_factor_x, scale_factor_y)
        """
        if not output_path:
            output_path = os.path.join(tempfile.gettempdir(), f"clicky_opt_{int(time.time()*1000)}.jpg")

        with Image.open(input_path) as img:
            orig_w, orig_h = img.size

            # If within bounds, convert to compressed JPEG for token savings
            if orig_w <= self.max_dimension and orig_h <= self.max_dimension:
                rgb_img = img.convert("RGB")
                rgb_img.save(output_path, "JPEG", quality=self.quality, optimize=True)
                return output_path, 1.0, 1.0

            # Compute scaling factor
            scale = min(self.max_dimension / orig_w, self.max_dimension / orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)

            # High-quality Lanczos resampling
            resized = img.convert("RGB").resize((new_w, new_h), Image.Resampling.LANCZOS)
            resized.save(output_path, "JPEG", quality=self.quality, optimize=True)

            scale_x = orig_w / float(new_w)
            scale_y = orig_h / float(new_h)

            return output_path, scale_x, scale_y
