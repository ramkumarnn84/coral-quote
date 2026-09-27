"""
Utility module for Industrial AI - Quotation Intelligence.
Contains helper functions used across the application.
"""

import os
import uuid
from datetime import datetime
from PIL import Image
import config


def validate_file(filename: str, file_size: int) -> tuple:
    """
    Validate uploaded file.

    Args:
        filename: Original filename
        file_size: File size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "No file selected"

    # Check extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in config.ALLOWED_EXTENSIONS:
        return False, f"File type '.{ext}' not allowed. Supported: {', '.join(config.ALLOWED_EXTENSIONS)}"

    # Check size
    if file_size > config.MAX_FILE_SIZE:
        max_mb = config.MAX_FILE_SIZE / (1024 * 1024)
        return False, f"File size exceeds {max_mb}MB limit"

    return True, ""


def save_upload(file_content: bytes, original_filename: str) -> str:
    """
    Save uploaded file with unique name.

    Args:
        file_content: File content bytes
        original_filename: Original filename

    Returns:
        Path to saved file
    """
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)

    ext = original_filename.rsplit(".", 1)[-1].lower()
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = os.path.join(config.UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return file_path


def optimize_image(file_path: str, max_size: int = 2048) -> str:
    """
    Optimize image for Vision API processing.

    Args:
        file_path: Path to image
        max_size: Maximum dimension

    Returns:
        Path to optimized image (same file, resized if needed)
    """
    try:
        with Image.open(file_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode == "RGBA":
                img = img.convert("RGB")

            # Resize if too large
            width, height = img.size
            if width > max_size or height > max_size:
                ratio = min(max_size / width, max_size / height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                img.save(file_path, quality=90)

    except Exception as e:
        print(f"Image optimization warning: {e}")

    return file_path


def format_currency(amount: float) -> str:
    """Format amount as Indian Rupees."""
    if amount >= 10000000:
        return f"₹ {amount / 10000000:.2f} Cr"
    elif amount >= 100000:
        return f"₹ {amount / 100000:.2f} L"
    else:
        return f"₹ {amount:,.2f}"


def get_current_date() -> str:
    """Get current date formatted."""
    return datetime.utcnow().strftime("%d %B %Y")


def get_file_size_str(size_bytes: int) -> str:
    """Convert bytes to human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
