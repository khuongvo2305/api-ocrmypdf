import os
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    basedir: Path = Path(os.path.dirname(os.path.abspath(__file__))).resolve()
    workdir: Path = "workdir"
    base_command_ocr: str = "/usr/local/bin/ocrmypdf"
    api_key_secret: str = "triviet2022"
    base_command_option: str = "--output-type pdf --fast-web-view 0 --optimize 0 --force-ocr"
    max_ocr_process: int = 1
    document_expire_hour: int = 1
    enable_wsl_compat: bool = False
    related_document_api: str = "http://10.19.1.122:8000"

config = Settings()
