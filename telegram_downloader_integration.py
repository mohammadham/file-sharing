"""
TelegramDownloader (Modified for File Sharing Bot)
Stand-alone downloader wrapper over telegram-uploader with streaming support
Author: Modified for UxB-File-Sharing Bot
"""

import json
import os
import time
import tempfile
import datetime as dt
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# ---------- config ----------
TEMP_DIR = Path(os.getenv("TEMP_PATH", Path(tempfile.gettempdir()) / "tg_gdrive_cache"))
TEMP_DIR.mkdir(exist_ok=True)

# ---------- JSON response ----------
@dataclass
class DownloadResp:
    success: bool
    local_path: Optional[str] = None
    size_bytes: int = 0
    download_time_sec: float = 0.0
    error: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

# ---------- main class ----------
class TelegramDownloader:
    """
    High-level downloader for UxB-File-Sharing Bot:
        - JSON in / JSON out
        - parallel & split-file support
        - delete-after-download
        - streaming support
        - zero DB touch
    """

    def __init__(self, config_file: Optional[str] = None):
        try:
            from telegram_uploader import create_client
            from telegram_uploader.download_files import KeepDownloadSplitFiles, JoinDownloadSplitFiles
            from telegram_uploader.client.telegram_manager_client import TelegramManagerClient
            
            self.KeepDownloadSplitFiles = KeepDownloadSplitFiles
            self.JoinDownloadSplitFiles = JoinDownloadSplitFiles
            
            self.client = create_client(config_file=config_file)
            self.client.start()
        except ImportError:
            raise ImportError("telegram-uploader package not found. Please install it.")

    # -------------------------------------------------
    # 1. download by entity (chat) → ALL latest files
    # -------------------------------------------------
    def download_from_entity(
        self,
        entity: Union[str, int],
        output_dir: str = ".",
        split_mode: str = "keep",          # keep | join
        delete_after: bool = False,
        max_parallel: int = 1,
        overwrite: bool = False,
        limit_files: int = 1,             # Download only N latest files (1=latest file only)
    ) -> List[str]:
        """
        Download latest files from a chat/channel with parallel support.
        """
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        # choose split strategy
        strategy_cls = {"keep": self.KeepDownloadSplitFiles, "join": self.JoinDownloadSplitFiles}[split_mode]
        
        # Get latest N files
        messages = list(self.client.find_files(entity))[:limit_files]  # Limit to N latest
        download_iter = strategy_cls(messages)
        download_files = list(download_iter)  # Convert iterator to list for parallel processing
        
        return self._sequential_download(
            entity=entity,
            download_files=download_files,
            output_path=output_path,
            delete_after=delete_after,
            overwrite=overwrite
        )
            
    def _sequential_download(
        self,
        entity: Union[str, int],
        download_files: List[Any],
        output_path: Path,
        delete_after: bool,
        overwrite: bool
    ) -> List[str]:
        """Helper for sequential downloads"""
        results: List[str] = []
        for download_file in download_files:
            start = time.perf_counter()
            try:
                final_name = download_file.file_name
                final_path = output_path / final_name
                if final_path.exists() and not overwrite:
                    results.append(
                        DownloadResp(
                            success=False,
                            error=f"File exists & overwrite=False: {final_name}",
                        ).to_json()
                    )
                    continue

                self.client.download_files(
                    entity=entity,
                    download_files=[download_file],
                    delete_on_success=delete_after,
                    save_dir=output_path,
                    overwrite=overwrite,
                )
                elapsed = time.perf_counter() - start
                size = download_file.size

                results.append(
                    DownloadResp(
                        success=True,
                        local_path=str(final_path),
                        size_bytes=size,
                        download_time_sec=elapsed,
                    ).to_json()
                )

            except Exception as e:
                elapsed = time.perf_counter() - start
                results.append(
                    DownloadResp(
                        success=False,
                        error=str(e),
                        download_time_sec=elapsed,
                    ).to_json()
                )
        return results

    # -------------------------------------------------
    # 2. download by message_id(s)
    # -------------------------------------------------
    def download_by_message_ids(
        self,
        entity: Union[str, int],
        message_ids: List[int],
        output_dir: str = ".",
        split_mode: str = "keep",
        delete_after: bool = False,
        max_parallel: int = 3,
        overwrite: bool = False,
    ) -> List[str]:
        """
        Download **specific** message(s) by ID.
        Returns list of JSON strings (DownloadResp).
        """
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        strategy_cls = {"keep": self.KeepDownloadSplitFiles, "join": self.JoinDownloadSplitFiles}[split_mode]

        # fetch only requested messages
        messages = []
        for mid in message_ids:
            msg = self.client.get_messages(entity, ids=mid)
            if msg and msg.document:
                messages.append(msg)

        download_iter = strategy_cls(messages)

        # same loop as above
        results: List[str] = []
        for download_file in download_iter:
            start = time.perf_counter()
            try:
                final_name = download_file.file_name
                final_path = output_path / final_name
                if final_path.exists() and not overwrite:
                    results.append(
                        DownloadResp(
                            success=False,
                            error=f"File exists & overwrite=False: {final_name}",
                        ).to_json()
                    )
                    continue

                self.client.download_files(
                    entity=entity,
                    download_files=[download_file],
                    delete_on_success=delete_after,
                    save_dir=output_path,
                    overwrite=overwrite,
                )
                elapsed = time.perf_counter() - start
                size = download_file.size

                results.append(
                    DownloadResp(
                        success=True,
                        local_path=str(final_path),
                        size_bytes=size,
                        download_time_sec=elapsed,
                    ).to_json()
                )

            except Exception as e:
                elapsed = time.perf_counter() - start
                results.append(
                    DownloadResp(
                        success=False,
                        error=str(e),
                        download_time_sec=elapsed,
                    ).to_json()
                )

        return results

    # -------------------------------------------------
    # 3. generate **direct** download link (Telegram URL)
    # -------------------------------------------------
    def generate_telegram_link(
        self,
        entity: Union[str, int],
        message_id: int,
    ) -> str:
        """
        Build a **public** Telegram download URL (t.me/c/chat_id/message_id).
        Works for public channels/groups only.
        """
        try:
            msg = self.client.get_messages(entity, ids=message_id)
            if not msg or not msg.document:
                return DownloadResp(
                    success=False,
                    error="Message not found or does not contain a file",
                ).to_json()

            # public link pattern
            chat = self.client.get_entity(entity)
            if chat.username:                       # public channel
                link = f"https://t.me/{chat.username}/{message_id}"
            else:                                   # private → numeric link
                link = f"https://t.me/c/{chat.id}/{message_id}"

            return DownloadResp(
                success=True,
                local_path=link,          # we reuse field for URL
                size_bytes=msg.document.size,
            ).to_json()

        except Exception as e:
            return DownloadResp(success=False, error=str(e)).to_json()

    # -------------------------------------------------
    # 4. stream telegram file function
    # -------------------------------------------------
    async def stream_telegram_file(self, chat: str, message_id: int, chunk_size: int = 1024*64):
        """
        استریم فایل تلگرام به صورت async generator (بدون ذخیره روی دیسک)
        قابل استفاده برای StreamingResponse در FastAPI
        
        Example:
            @app.get("/download/{chat}/{message_id}")
            async def download(chat: str, message_id: int):
                generator = downloader.stream_telegram_file(chat, message_id)
                return StreamingResponse(generator, media_type="application/octet-stream")
        """
        if not hasattr(self.client, 'stream_file'):
            raise NotImplementedError("client must support streaming")
        
        async for chunk in self.client.stream_file(chat, message_id, chunk_size=chunk_size):
            yield chunk

    # -------------------------------------------------
    # 5. get file info
    # -------------------------------------------------
    def get_file_info(self, entity: Union[str, int], message_id: int) -> Dict[str, Any]:
        """
        Get file information without downloading
        """
        try:
            msg = self.client.get_messages(entity, ids=message_id)
            if not msg or not msg.document:
                return {"error": "Message not found or does not contain a file"}
            
            return {
                "success": True,
                "file_name": msg.document.attributes[0].file_name if msg.document.attributes else "unknown",
                "file_size": msg.document.size,
                "mime_type": msg.document.mime_type,
                "message_id": message_id,
                "chat_id": str(entity)
            }
        except Exception as e:
            return {"error": str(e)}

    # -------------------------------------------------
    # 6. statistics
    # -------------------------------------------------
    def stats(self, entity: Union[str, int]) -> str:
        """
        Return JSON: total files + total size in the latest N messages.
        """
        try:
            messages = list(self.client.find_files(entity))
            total_files = len(messages)
            total_size = sum(msg.document.size for msg in messages if msg.document)
            return json.dumps(
                {
                    "total_files": total_files,
                    "total_size_bytes": total_size,
                    "total_size_human": self._human_bytes(total_size),
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    # -------------------------------------------------
    # 7. helper – human readable size
    # -------------------------------------------------
    @staticmethod
    def _human_bytes(b: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if b < 1024.0:
                return f"{b:.2f} {unit}"
            b /= 1024.0
        return f"{b:.2f} PB"