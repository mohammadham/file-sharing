"""
Telegram + Google Drive Uploader (Modified for File Sharing Bot)
Stand-alone, JSON-returning, no DB touch
Author: Modified for File-Sharing Bot
"""
import os
import json
import pathlib
import tempfile
import requests
import datetime as dt
from typing import Union, List, Dict, Any, Optional, Iterable
from pathlib import Path
from dataclasses import dataclass, asdict

PathLike = Union[str, pathlib.Path]

# ---------- config ----------
TEMP_DIR = Path(os.getenv("TEMP_PATH", Path(tempfile.gettempdir()) / "tg_gdrive_cache"))
TEMP_DIR.mkdir(exist_ok=True)

# ---------- dataclasses ----------
@dataclass
class UploadResp:
    success: bool
    service: str          # telegram | gdrive
    file_name: str
    size_bytes: int
    upload_time_sec: float
    download_time_sec: float = 0.0
    telegram_chat: Optional[str] = None
    telegram_message_id: Optional[int] = None
    gdrive_file_id: Optional[str] = None
    gdrive_web_view_link: Optional[str] = None
    error: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

# ---------- helpers ----------
def _now() -> str:
    return dt.datetime.utcnow().isoformat()

def _download_url(url: str, dest: pathlib.Path, chunk_size=1024 * 1024) -> float:
    """Stream download -> dest path"""
    start = dt.datetime.utcnow()
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
    elapsed = (dt.datetime.utcnow() - start).total_seconds()
    return elapsed

def _size(path: pathlib.Path) -> int:
    return path.stat().st_size

# ---------- Telegram ----------
class _Telegram:
    def __init__(self, config_file: Optional[str] = None):
        try:
            from telegram_uploader import create_client, upload_files
            self.upload_files = upload_files
            self.client = create_client(config_file=config_file)
            self.client.connect()
        except ImportError:
            raise ImportError("telegram-uploader package not found. Please install it.")

    def upload(
        self,
        paths: Union[PathLike, Iterable[PathLike]],
        to: str = "me",
        caption: str = "",
        thumbnail: Optional[PathLike] = None,
        delete_on_success: bool = False,
        force_file: bool = False,
        as_album: bool = False,
        sort: bool = False,
        *,
        directories: str = "ignore",        # ignore | recursive | fail
        large_files: str = "fail",          # fail | split
        no_thumbnail: bool = False,
        warn: Optional[callable] = None,
        **_
    ) -> List[Any]:
        """
        Upload **یک یا چند** فایل/پوشه به تلگرام – **رفتار ۱۰۰٪ مطابق CLI**
        """
        # --- 1. نرمال‌سازی مسیرها ---
        if isinstance(paths, (str, pathlib.Path)):
            paths = [paths]
        files = [str(p) for p in paths]

        # --- 2. thumbnail دقیقاً منطق CLI ---
        if no_thumbnail:
            thumbnail = False
        elif thumbnail and pathlib.Path(thumbnail).is_file():
            thumbnail = str(thumbnail)
        else:
            thumbnail = None

        # --- 3. ساخت kwargs کامل ---
        kwargs = dict(
            client=self.client,
            files=files,
            to=to or "me",
            caption=caption or None,
            thumbnail=thumbnail,
            force_file=force_file,
            delete_on_success=delete_on_success,
            as_album=as_album,
            sort=sort,
            directories=directories,
            large_files=large_files,
            no_thumbnail=no_thumbnail,
            warn=warn,
        )
        r_data = self.upload_files(**kwargs) 
        
        # --- 4. اگر بروزرسانی‌های فایل‌ها باید انجام شود ---
        if isinstance(files, list) and len(files) > 1:
            return r_data if r_data else []
        else:
            return r_data[0] if r_data and r_data[0] else []

# ---------- MAIN CLASS ----------
class TelegramUploader:
    """
    Telegram uploader for File-Sharing Bot.
    No database touch, returns JSON-serialisable objects.
    """

    def __init__(self, telegram_config_file: Optional[str] = None):
        self.tg: Optional[_Telegram] = None
        if telegram_config_file:
            self.tg = _Telegram(telegram_config_file)

    def upload_to_telegram(self, file_path: str, to: str = "me", caption: str = "",
                           thumbnail: Optional[str] = None, delete_original: bool = False, as_album: bool = False) -> str:
        """
        Upload a **local** file to Telegram.
        Returns JSON string of UploadResp.
        """
        if not self.tg:
            return TelegramUploader._err_json("Telegram client not configured")
        path = pathlib.Path(file_path)
        if not path.exists():
            return TelegramUploader._err_json("Local file not found")
        start = dt.datetime.utcnow()
        try:
            tg_msg = None
            # Retry logic for DisconnectError
            for attempt in range(2):
                try:
                    tg_msg = self.tg.upload(path,
                          to=to,
                          caption=caption,
                          thumbnail=thumbnail,
                          delete_on_success=delete_original,
                          as_album=as_album)
                    break  # Exit loop if successful
                except Exception as e:
                    if attempt < 1:
                        self.tg.client.connect()
                    else:
                        raise e  # Raise exception after 2 attempts

            elapsed = (dt.datetime.utcnow() - start).total_seconds()
            resp = UploadResp(
                success=True,
                service="telegram",
                file_name=path.name,
                size_bytes=_size(path),
                upload_time_sec=elapsed,
                telegram_chat=to,
                telegram_message_id=tg_msg.id if tg_msg else None
            )
            return resp.to_json()

        except Exception as e:
            return TelegramUploader._err_json(str(e))

    def upload_url_to_telegram(self, url: str, to: str = "me", caption: str = "",
                               thumbnail: Optional[str] = None, delete_tmp: bool = True) -> str:
        """
        Download URL → temp → upload to Telegram → optional delete temp.
        Returns JSON string of UploadResp.
        """
        if not self.tg:
            return TelegramUploader._err_json("Telegram client not configured")
        
        # Extract filename from URL
        filename = pathlib.Path(url).name or f"file_{int(dt.datetime.now().timestamp())}"
        tmp = TEMP_DIR / filename
        
        try:
            dl_sec = _download_url(url, tmp)
            json_resp = self.upload_to_telegram(str(tmp), to=to, caption=caption,
                                              thumbnail=thumbnail, delete_original=delete_tmp)
            resp_dict = json.loads(json_resp)
            resp_dict["download_time_sec"] = dl_sec
            return json.dumps(resp_dict, ensure_ascii=False, indent=2)
        except Exception as e:
            return TelegramUploader._err_json(str(e))

    def upload_batch_urls_to_telegram(self, urls: List[str], to: str = "me", caption: str = "",
                                      thumbnail: Optional[str] = None, delete_tmp: bool = True) -> List[str]:
        """
        Upload multiple URLs to Telegram.
        Returns list of JSON strings (UploadResp).
        """
        return [self.upload_url_to_telegram(u, to, caption, thumbnail, delete_tmp) for u in urls]

    @staticmethod
    def _err_json(msg: str) -> str:
        return UploadResp(success=False, service="none", file_name="", size_bytes=0,
                          upload_time_sec=0.0, error=msg).to_json()