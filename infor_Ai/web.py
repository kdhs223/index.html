from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, redirect, request, session, jsonify

from config import get_gemini_client, load_skill_prompt
try:
    from storage import get_user_by_username, save_student, save_user_info
except ImportError:
    from storage import get_user_by_username, save_student, save_user_info

load_dotenv(Path(__file__).parent / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "homeroom-psychology-secret-key")

INDEX_HTML_PATH = Path(__file__).parent / "index.html"


@app.get("/")
def index():
    if INDEX_HTML_PATH.exists():
        return INDEX_HTML_PATH.read_text(encoding="utf-8")
    return "Không tìm thấy file index.html!"


@app.post("/api/register")
def api_register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    name = (data.get("name") or "").strip()

    if not username or not password or not name:
        return jsonify({"message": "Vui lòng nhập đầy đủ thông tin!"}), 400

    success = save_user_info(username=username, password=password, name=name, role="student")
    if success:
        return jsonify({"message": "Tạo tài khoản thành công!"})
    else:
        return jsonify({"message": "Tên đăng nhập đã tồn tại trong hệ thống!"}), 400


@app.post("/api/login")
def api_login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"message": "Vui lòng nhập tên đăng nhập và mật khẩu!"}), 400

    user = get_user_by_username(username, password)
    if user:
        return jsonify({"message": "Đăng nhập thành công!", "name": user["name"]})
    else:
        return jsonify({"message": "Tên đăng nhập hoặc mật khẩu không chính xác!"}), 401


@app.get("/api/students")
def api_students():
    try:
        from storage import list_customers
        students = list_customers()
        return jsonify({"success": True, "students": students})
    except Exception as e:
        return jsonify({"success": False, "students": [], "error": str(e)})


@app.post("/api/chat")
def api_chat():
    data = request.get_json() or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"reply": "Vui lòng nhập nội dung cần tư vấn."})

    try:
        client = get_gemini_client()
        system_prompt = load_skill_prompt()

        prompt = f"""{system_prompt}

=== DÀNH CHO HỌC SINH ===
Học sinh tâm sự: {user_message}
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )

        reply_text = ""
        try:
            if response.text:
                reply_text = response.text
            elif response.candidates and response.candidates[0].content.parts:
                texts = [p.text for p in response.candidates[0].content.parts if getattr(p, 'text', None)]
                if texts:
                    reply_text = "".join(texts)
        except Exception:
            pass

        if not reply_text:
            reply_text = "Cô đang lắng nghe em đây, em chia sẻ thêm nhé."

        if "[SAVE_STUDENT]" in reply_text or "111" in user_message:
            try:
                save_student(name="Học sinh trực tuyến", note=user_message, source="psychology-chatbot")
            except Exception:
                pass

        return jsonify({"reply": reply_text})

    except Exception as e:
        return jsonify({"reply": f"Lỗi kết nối tới hệ thống AI: {e}"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)