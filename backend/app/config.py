import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "NOVA Protocol — 失落基地 API"
    VERSION: str = "1.0.0"

    # Database configuration: supports Render PostgreSQL URL, custom PostgreSQL URL,
    # or embedded local PostgreSQL / SQLite fallback for local testing
    RAW_DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    PG_DATA_DIR: str = os.getenv("PG_DATA_DIR", "/tmp/nova_protocol_pgdata")
    USE_EMBEDDED_PG: bool = os.getenv("USE_EMBEDDED_PG", "true").lower() in ("true", "1", "yes")

    # CORS origins (comma-separated in env, e.g. "https://nova-protocol.onrender.com,http://localhost:5173")
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
        ).split(",")
        if origin.strip()
    ]

    # Teacher passkey / auth secret (configured via env on Render)
    TEACHER_DEMO_PASSKEY: str = os.getenv("TEACHER_PASSKEY", "NOVA-TEACHER-2026")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nova-protocol-dev-secret-change-in-prod")

    # Execution Engine Safety Limits (Section 6.4 & 6.5)
    MAX_INSTRUCTIONS: int = int(os.getenv("MAX_INSTRUCTIONS", "200"))
    MAX_LOOP_ITERATIONS: int = int(os.getenv("MAX_LOOP_ITERATIONS", "100"))
    MAX_EXECUTION_STEPS: int = int(os.getenv("MAX_EXECUTION_STEPS", "500"))
    MAX_NESTING_DEPTH: int = int(os.getenv("MAX_NESTING_DEPTH", "6"))

settings = Settings()

