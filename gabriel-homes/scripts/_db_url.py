"""Print shell assignments for a mysql:// DATABASE_URL (used by the scripts)."""
import shlex
import sys
from urllib.parse import unquote, urlparse

u = urlparse(sys.argv[1])
if u.scheme not in ("mysql",):
    sys.exit("DATABASE_URL must start with mysql:// (MariaDB)")
parts = {
    "DB_USER": unquote(u.username or ""),
    "DB_PASS": unquote(u.password or ""),
    "DB_HOST": u.hostname or "localhost",
    "DB_PORT": str(u.port or 3306),
    "DB_NAME": (u.path or "/").lstrip("/"),
}
if not parts["DB_NAME"]:
    sys.exit("DATABASE_URL has no database name")
for k, v in parts.items():
    print(f"{k}={shlex.quote(v)}")
