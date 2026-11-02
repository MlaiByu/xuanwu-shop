"""文件上传（需求 FR-A-04）。

安全：同时校验 Content-Type 与文件头魔数，重命名存储，禁止保留原始文件名。
"""
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_admin
from app.config import BASE_DIR
from app.core.errors import BizException, ErrorCode
from app.core.responses import success

router = APIRouter(prefix="/upload", tags=["管理端-上传"], dependencies=[Depends(get_current_admin)])

MAX_SIZE = 5 * 1024 * 1024
CHUNK_SIZE = 64 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _sniff_extension(content: bytes) -> str | None:
    if content[:3] == b"\xff\xd8\xff":
        return "jpg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


@router.post("", summary="上传图片")
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise BizException(ErrorCode.PARAM_INVALID, "仅支持 jpg/png/webp 图片")

    # 分块累加、边读边判上限：不能先 read() 全量再校验，
    # 否则超大文件会先在内存里摊开再被拒绝，构成内存耗尽攻击面（审查报告 M3）。
    buffer = bytearray()
    while chunk := await file.read(CHUNK_SIZE):
        buffer.extend(chunk)
        if len(buffer) > MAX_SIZE:
            raise BizException(ErrorCode.PARAM_INVALID, "图片大小不能超过 5MB")

    content = bytes(buffer)
    if not content:
        raise BizException(ErrorCode.PARAM_INVALID, "文件内容为空")

    ext = _sniff_extension(content)
    if ext is None:
        raise BizException(ErrorCode.PARAM_INVALID, "文件内容与图片格式不符")

    now = datetime.now(UTC)
    rel_dir = Path("static") / "uploads" / f"{now:%Y}" / f"{now:%m}"
    abs_dir = BASE_DIR / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    (abs_dir / filename).write_bytes(content)

    url = f"/{(rel_dir / filename).as_posix()}"
    return success({"url": url})
