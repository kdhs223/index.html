"""Cấu hình dùng chung: nạp .env và khởi tạo client Gemini chuẩn."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).parent
SKILL_PATH = BASE_DIR / "skill.md"


def load_env() -> None:
    for name in (".env", "_env"):
        path = BASE_DIR / name
        if path.exists():
            load_dotenv(path, override=True, encoding="utf-8-sig")
            return


load_env()


def get_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not key:
        raise ValueError("Chưa cấu hình GOOGLE_API_KEY trong file .env.")
    return key


def get_gemini_client() -> genai.Client:
    return genai.Client(api_key=get_api_key())


def load_skill_prompt() -> str:
    """Đọc prompt dùng chung từ file skill.md"""
    if SKILL_PATH.exists():
        return SKILL_PATH.read_text(encoding="utf-8").strip()
    return "Bạn là trợ lý AI hỗ trợ tư vấn tâm lý và phân tích dữ liệu học đường."