from __future__ import annotations

import os
from pathlib import Path
from config import get_gemini_client, load_skill_prompt


def ask_admin_data(question: str) -> str:
    question = (question or "").strip()
    if not question:
        return "Vui lòng nhập câu hỏi tra cứu."

    try:
        client = get_gemini_client()
        system_prompt = load_skill_prompt()

        full_prompt = f"""{system_prompt}

=== DÀNH CHO QUẢN TRỊ VIÊN ===
Câu hỏi tra cứu của giáo viên: {question}
Hãy phản hồi rõ ràng, chính xác theo nhiệm vụ phân tích dữ liệu/SQL được quy định trong hướng dẫn.
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=full_prompt,
        )

        # Trích xuất văn bản an toàn
        response_text = ""
        try:
            if response.text:
                response_text = response.text
            elif response.candidates and response.candidates[0].content.parts:
                texts = [p.text for p in response.candidates[0].content.parts if getattr(p, 'text', None)]
                if texts:
                    response_text = "".join(texts)
        except Exception:
            pass

        if not response_text:
            return "📌 Kết quả: Không tìm thấy dữ liệu phù hợp trong hệ thống."

        return response_text.strip()

    except Exception as e:
        return f"Lỗi xử lý tra cứu: {e}"