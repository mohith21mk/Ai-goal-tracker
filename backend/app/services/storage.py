import os
import re
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import httpx

logger = logging.getLogger(__name__)

IMAGE_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
    (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
    (b"GIF87a", ".gif", "image/gif"),
    (b"GIF89a", ".gif", "image/gif"),
]

AUDIO_SIGNATURES = [
    (b"\x1a\x45\xdf\xa3", ".webm", "audio/webm"),
    (b"OggS", ".ogg", "audio/ogg"),
    (b"ID3", ".mp3", "audio/mpeg"),
]

ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"},
    "voice": {".webm", ".ogg", ".wav", ".mp3", ".m4a", ".aac"}
}


def validate_media_file(contents: bytes, filename: str, content_type: str) -> Tuple[str, str, str]:
    ext = Path(filename).suffix.lower()
    ct = (content_type or "").lower()
    
    is_image = ext in ALLOWED_EXTENSIONS["image"] or "image" in ct
    is_voice = ext in ALLOWED_EXTENSIONS["voice"] or "audio" in ct
    
    if not is_image and not is_voice:
        raise ValueError("Unsupported media format. Allowed: Images (JPEG, PNG, WebP, GIF, SVG) or Audio (WebM, WAV, OGG, MP3).")
    
    size = len(contents)
    if size == 0:
        raise ValueError("Cannot upload empty file.")
        
    if is_image:
        if size > 5 * 1024 * 1024:
            raise ValueError("Image file size exceeds maximum limit of 5MB.")
            
        matched_ext = None
        matched_mime = "image/png"
        for sig, s_ext, s_mime in IMAGE_SIGNATURES:
            if contents.startswith(sig):
                matched_ext = s_ext
                matched_mime = s_mime
                break
                
        if not matched_ext and len(contents) >= 12 and contents.startswith(b"RIFF") and contents[8:12] == b"WEBP":
            matched_ext = ".webp"
            matched_mime = "image/webp"
            
        if not matched_ext and ("<svg" in contents[:500].decode("utf-8", errors="ignore").lower()):
            matched_ext = ".svg"
            matched_mime = "image/svg+xml"
            
        final_ext = matched_ext if matched_ext else (ext if ext in ALLOWED_EXTENSIONS["image"] else ".png")
        final_mime = matched_mime if matched_ext else (ct if ct.startswith("image/") else "image/png")
        return "image", final_ext, final_mime
        
    else:
        if size > 10 * 1024 * 1024:
            raise ValueError("Audio voice file size exceeds maximum limit of 10MB.")
            
        matched_ext = None
        matched_mime = "audio/webm"
        for sig, s_ext, s_mime in AUDIO_SIGNATURES:
            if contents.startswith(sig):
                matched_ext = s_ext
                matched_mime = s_mime
                break
                
        if not matched_ext and len(contents) >= 12 and contents.startswith(b"RIFF") and contents[8:12] == b"WAVE":
            matched_ext = ".wav"
            matched_mime = "audio/wav"
            
        if not matched_ext and len(contents) >= 2 and contents[0] == 0xFF and (contents[1] & 0xE0) == 0xE0:
            matched_ext = ".mp3"
            matched_mime = "audio/mpeg"
            
        final_ext = matched_ext if matched_ext else (ext if ext in ALLOWED_EXTENSIONS["voice"] else ".webm")
        final_mime = matched_mime if matched_ext else (ct if ct.startswith("audio/") else "audio/webm")
        return "voice", final_ext, final_mime


async def upload_to_cloudinary(contents: bytes, filename: str, resource_type: str = "auto") -> Optional[str]:
    cloudinary_url = os.getenv("CLOUDINARY_URL", "")
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    api_key = os.getenv("CLOUDINARY_API_KEY", "")
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "")
    
    if cloudinary_url and not (cloud_name and api_key and api_secret):
        m = re.match(r"^cloudinary://([^:]+):([^@]+)@(.+)$", cloudinary_url)
        if m:
            api_key, api_secret, cloud_name = m.group(1), m.group(2), m.group(3)
            
    if not (cloud_name and api_key and api_secret):
        return None
        
    try:
        import time
        import hashlib
        
        timestamp = str(int(time.time()))
        params_to_sign = f"timestamp={timestamp}{api_secret}"
        signature = hashlib.sha1(params_to_sign.encode("utf-8")).hexdigest()
        
        url = f"https://api.cloudinary.com/v1_1/{cloud_name}/{resource_type}/upload"
        data = {
            "api_key": api_key,
            "timestamp": timestamp,
            "signature": signature,
        }
        files = {
            "file": (filename, contents)
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, data=data, files=files)
            if resp.status_code == 200:
                res_data = resp.json()
                return res_data.get("secure_url") or res_data.get("url")
            else:
                logger.warning(f"Cloudinary upload failed ({resp.status_code}): {resp.text}")
    except Exception as e:
        logger.error(f"Cloudinary upload exception: {e}")
        
    return None


async def save_media_file(contents: bytes, orig_filename: str, content_type: str) -> Dict[str, Any]:
    file_type, ext, validated_mime = validate_media_file(contents, orig_filename, content_type)
    file_size = len(contents)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    
    cloud_resource_type = "image" if file_type == "image" else "video"
    cloud_url = await upload_to_cloudinary(contents, safe_name, resource_type=cloud_resource_type)
    
    if cloud_url:
        return {
            "status": "success",
            "url": cloud_url,
            "filename": safe_name,
            "file_type": file_type,
            "size": file_size,
            "mime_type": validated_mime,
            "storage_provider": "cloudinary"
        }
        
    uploads_dir = Path(__file__).resolve().parent.parent.parent / "uploads" / "chat"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    dest_path = uploads_dir / safe_name
    
    with open(dest_path, "wb") as f:
        f.write(contents)
        
    file_url = f"/api/uploads/chat/{safe_name}"
    return {
        "status": "success",
        "url": file_url,
        "filename": safe_name,
        "file_type": file_type,
        "size": file_size,
        "mime_type": validated_mime,
        "storage_provider": "local"
    }
