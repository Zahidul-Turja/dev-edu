import json
import logging
import subprocess
from celery import shared_task
from media_processing.models import VideoAsset

logger = logging.getLogger(__name__)


def extract_video_metadata(file_path: str):
    """
    Uses ffprobe to extract duration in seconds and resolution height.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "format=duration:stream=height,duration",
        "-of",
        "json",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")

    data = json.loads(result.stdout)
    duration = None
    height = None

    if "format" in data and "duration" in data["format"]:
        try:
            duration = int(round(float(data["format"]["duration"])))
        except (ValueError, TypeError):
            pass

    streams = data.get("streams", [])
    if streams and "height" in streams[0]:
        try:
            height = int(streams[0]["height"])
        except (ValueError, TypeError):
            pass

    return duration, height


@shared_task
def process_video_asset(asset_id: int):
    """
    Asynchronous task to inspect uploaded video asset and extract metadata.
    """
    try:
        asset = VideoAsset.objects.get(id=asset_id)
    except VideoAsset.DoesNotExist:
        logger.error("VideoAsset with id %s does not exist", asset_id)
        return

    asset.status = VideoAsset.Status.PROCESSING
    asset.error_message = ""
    asset.save(update_fields=["status", "error_message"])

    try:
        file_path = asset.original_file.path
        duration, height = extract_video_metadata(file_path)
        asset.duration_seconds = duration
        asset.source_height = height
        asset.status = VideoAsset.Status.READY
        asset.save(update_fields=["duration_seconds", "source_height", "status"])
        logger.info(
            "VideoAsset %s processed successfully. Duration: %ss, Height: %sp",
            asset_id,
            duration,
            height,
        )
    except Exception as exc:
        logger.exception("Failed to process VideoAsset %s", asset_id)
        asset.status = VideoAsset.Status.FAILED
        asset.error_message = str(exc)
        asset.save(update_fields=["status", "error_message"])
