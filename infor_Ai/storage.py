from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

# Đường dẫn file CSDL SQLite lưu cùng thư mục với storage.py
DB_PATH = Path(__file__).parent / "homeroom.db"


def get_connection() -> sqlite3.Connection:
    """Tạo kết nối tới CSDL SQLite và cấu hình trả về định dạng dict-like."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Tự động khởi tạo các bảng trong CSDL nếu chưa tồn tại."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Bảng lưu thông tin các ca tư vấn / ghi chú học sinh từ AI
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone_interest TEXT,
                note TEXT,
                source TEXT DEFAULT 'psychology-chatbot',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # 2. Bảng lưu thông tin tài khoản đăng nhập (Học sinh / Quản trị viên)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def _hash_password(password: str) -> str:
    """Mã hóa mật khẩu bằng thuật toán SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Các hàm quản lý danh sách học sinh / Ca tư vấn (Students / Customers)
# ---------------------------------------------------------------------------
def save_student(
    name: str,
    email: str = "",
    phone_interest: str = "",
    note: str = "",
    source: str = "psychology-chatbot",
) -> int:
    """Lưu vết ca cần tư vấn/hỗ trợ học sinh vào CSDL và trả về ID."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO students (name, email, phone_interest, note, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, phone_interest, note, source),
        )
        conn.commit()
        return cursor.lastrowid or 0


# Alias lưu tên hàm save_customer để tương thích hoàn toàn với web.py
save_customer = save_student


def list_customers() -> list[dict]:
    """Lấy toàn bộ danh sách ca tư vấn / thông tin học sinh đã ghi nhận."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_customer(customer_id: int) -> bool:
    """Xóa một bản ghi học sinh theo ID."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = ?", (customer_id,))
        conn.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Các hàm quản lý Tài khoản Người dùng (Users)
# ---------------------------------------------------------------------------
def save_user_info(
    username: str, password: str, name: str, role: str = "student"
) -> bool:
    """Đăng ký tài khoản mới vào hệ thống CSDL."""
    init_db()
    pwd_hash = _hash_password(password)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, name, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, pwd_hash, name, role),
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        # Tên đăng nhập đã tồn tại trong bảng users
        return False


def get_user_by_username(username: str, password: str | None = None) -> dict | None:
    """
    Xác thực và truy vấn tài khoản.
    Nếu truyền thêm password, hàm sẽ đối chiếu mật khẩu đã mã hóa.
    """
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        if password is not None:
            pwd_hash = _hash_password(password)
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password_hash = ?",
                (username, pwd_hash),
            )
        else:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

        row = cursor.fetchone()
        return dict(row) if row else None


# Khởi tạo bảng tự động khi mô-đun được nạp
init_db()