import os
import re
import mimetypes
from django.http import StreamingHttpResponse, HttpResponse, Http404


def get_ranged_file_response(
    file_path: str, range_header: str | None = None, chunk_size: int = 1024 * 1024
):
    """
    Returns a StreamingHttpResponse supporting HTTP 206 Partial Content (Range requests)
    for video streaming chunk by chunk.
    """
    if not os.path.exists(file_path):
        raise Http404("Video file not found")

    file_size = os.path.getsize(file_path)
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "video/mp4"

    if not range_header:

        def file_iterator(path, chunk_sz):
            with open(path, "rb") as f:
                while chunk := f.read(chunk_sz):
                    yield chunk

        response = StreamingHttpResponse(
            file_iterator(file_path, chunk_size),
            content_type=content_type,
            status=200,
        )
        response["Content-Length"] = str(file_size)
        response["Accept-Ranges"] = "bytes"
        return response

    range_match = re.match(r"bytes=(\d+)-(\d*)", range_header.strip())
    if not range_match:
        return HttpResponse("Invalid Range header", status=416)

    start = int(range_match.group(1))
    end_str = range_match.group(2)

    if start >= file_size:
        resp = HttpResponse("Requested range not satisfiable", status=416)
        resp["Content-Range"] = f"bytes */{file_size}"
        return resp

    if end_str:
        end = min(int(end_str), file_size - 1)
    else:
        end = min(start + chunk_size - 1, file_size - 1)

    content_length = (end - start) + 1

    def ranged_iterator(path, start_pos, length, read_chunk_sz=64 * 1024):
        with open(path, "rb") as f:
            f.seek(start_pos)
            bytes_left = length
            while bytes_left > 0:
                read_amount = min(bytes_left, read_chunk_sz)
                chunk = f.read(read_amount)
                if not chunk:
                    break
                bytes_left -= len(chunk)
                yield chunk

    response = StreamingHttpResponse(
        ranged_iterator(file_path, start, content_length),
        content_type=content_type,
        status=206,
    )
    response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(content_length)
    return response
