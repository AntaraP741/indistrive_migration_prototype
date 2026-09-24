import os


def _require_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_pg_config():
    return {
        "host": os.getenv("PG_HOST", "localhost").strip(),
        "port": int(os.getenv("PG_PORT", "5432")),
        "database": _require_env("PG_DATABASE"),
        "user": _require_env("PG_USER"),
        "password": _require_env("PG_PASSWORD"),
    }


def load_pg_schema():
    return os.getenv("PG_SCHEMA", "public").strip() or "public"


def load_mongo_config():
    return {
        "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017/").strip(),
        "database": _require_env("MONGO_DATABASE"),
    }
