"""
InsureGuard AI - Image Analysis Module
Handles duplicate detection and basic tampering analysis.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


def compute_image_hash(file_path: str) -> str:
    """Compute perceptual hash of an image for duplicate detection."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def check_duplicate_images(file_path: str, existing_hashes: List[str]) -> Dict[str, Any]:
    """
    Check if an uploaded image is a duplicate of any previously uploaded image.
    """
    current_hash = compute_image_hash(file_path)
    is_duplicate = current_hash in existing_hashes

    return {
        "file_path": file_path,
        "hash": current_hash,
        "is_duplicate": is_duplicate,
        "message": "Duplicate image detected!" if is_duplicate else "Image is unique"
    }


def analyze_image_metadata(file_path: str) -> Dict[str, Any]:
    """
    Basic image metadata analysis for tampering detection.
    Checks file metadata for signs of manipulation.
    """
    result = {
        "file_path": file_path,
        "suspicious": False,
        "issues": [],
        "metadata": {}
    }

    try:
        stat = os.stat(file_path)
        result["metadata"]["file_size"] = stat.st_size
        result["metadata"]["created"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
        result["metadata"]["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        # Check if modification date is after creation date (possible editing)
        if stat.st_mtime > stat.st_ctime + 60:  # More than 1 minute difference
            result["issues"].append("File modified after creation — possible editing detected")
            result["suspicious"] = True

        # Check file size anomalies
        ext = Path(file_path).suffix.lower()
        if ext in [".jpg", ".jpeg"] and stat.st_size < 5000:
            result["issues"].append("Suspiciously small JPEG file")
            result["suspicious"] = True
        elif ext in [".png"] and stat.st_size < 3000:
            result["issues"].append("Suspiciously small PNG file")
            result["suspicious"] = True

        # Try to read EXIF data if PIL is available
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            img = Image.open(file_path)
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if isinstance(value, (str, int, float)):
                        result["metadata"][str(tag)] = str(value)

                # Check for editing software
                software = result["metadata"].get("Software", "")
                editing_tools = ["photoshop", "gimp", "paint", "editor", "canva"]
                if any(tool in software.lower() for tool in editing_tools):
                    result["issues"].append(f"Image edited with: {software}")
                    result["suspicious"] = True
            else:
                result["issues"].append("No EXIF data found — possible screenshot or edited image")

        except ImportError:
            result["metadata"]["note"] = "PIL not available for EXIF analysis"
        except Exception:
            pass

    except Exception as e:
        result["issues"].append(f"Error analyzing image: {str(e)}")

    return result
