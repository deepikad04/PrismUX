from __future__ import annotations

import base64
import io
import logging

from PIL import Image, ImageDraw, ImageFont

from schemas.navigation import BoundingBox, DetectedElement

logger = logging.getLogger(__name__)

# Color map for element types
ELEMENT_COLORS = {
    "button": (59, 130, 246, 128),     # blue
    "input": (34, 197, 94, 128),       # green
    "link": (168, 85, 247, 128),       # purple
    "image": (251, 146, 60, 128),      # orange
    "navigation": (14, 165, 233, 128), # sky blue
    "modal": (239, 68, 68, 128),       # red
    "form": (234, 179, 8, 128),        # yellow
    "dropdown": (20, 184, 166, 128),   # teal
}

DEFAULT_COLOR = (148, 163, 184, 128)   # slate


class OverlayRenderer:
    """Renders bounding box overlays on screenshots using Pillow."""

    def render_overlay(
        self,
        screenshot_b64: str,
        elements: list[DetectedElement],
        highlight_bbox: BoundingBox | None = None,
    ) -> str:
        """Draw bounding boxes on screenshot, return as base64 PNG."""
        img_bytes = base64.b64decode(screenshot_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for element in elements:
            bbox = element.bbox
            color = ELEMENT_COLORS.get(element.element_type, DEFAULT_COLOR)

            # Draw filled semi-transparent rectangle
            draw.rectangle(
                [bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height],
                fill=(*color[:3], 40),
                outline=(*color[:3], 200),
                width=2,
            )

            # Draw label
            label = f"{element.label} ({element.confidence:.2f})"
            label_y = max(bbox.y - 16, 0)
            draw.rectangle(
                [bbox.x, label_y, bbox.x + len(label) * 7, label_y + 14],
                fill=(*color[:3], 180),
            )
            draw.text((bbox.x + 2, label_y + 1), label, fill=(255, 255, 255, 255))

        # Highlight the action target
        if highlight_bbox:
            draw.rectangle(
                [
                    highlight_bbox.x - 3,
                    highlight_bbox.y - 3,
                    highlight_bbox.x + highlight_bbox.width + 3,
                    highlight_bbox.y + highlight_bbox.height + 3,
                ],
                outline=(255, 0, 0, 255),
                width=4,
            )

        result = Image.alpha_composite(img, overlay)
        result = result.convert("RGB")

        buffer = io.BytesIO()
        result.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
