import logging
import os
import time
from typing import Any

from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("demoapp")

app = Flask(__name__)

# Nginx передаёт реальные IP и схему через X-Forwarded-*.
# ProxyFix доверяет одному уровню reverse proxy.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

STARTED_AT = time.time()


@app.get("/")
def index() -> tuple[dict[str, Any], int]:
    logger.info(
        "Index page requested",
        extra={
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
        },
    )

    return (
        jsonify(
            {
                "service": "demoapp",
                "version": "1.0.0",
                "message": "Hello from Flask behind Nginx",
                "uptime_seconds": round(time.time() - STARTED_AT, 2),
            }
        ),
        200,
    )


@app.get("/health")
def health() -> tuple[dict[str, str], int]:
    """
    Liveness check.

    Проверяет только то, что процесс жив и Flask может обработать запрос.
    Не проверяет внешние зависимости.
    """
    return jsonify({"status": "ok"}), 200


@app.get("/ready")
def readiness() -> tuple[dict[str, Any], int]:
    """
    Readiness check.

    Здесь можно проверять зависимости: БД, cache, внешний API.
    В demo внешних зависимостей нет, поэтому проверяем только приложение.
    """
    return (
        jsonify(
            {
                "status": "ready",
                "checks": {
                    "application": "ok",
                },
            }
        ),
        200,
    )


@app.get("/api/info")
def api_info() -> tuple[dict[str, Any], int]:
    return (
        jsonify(
            {
                "service": "demoapp",
                "python_version": os.sys.version.split()[0],
                "pid": os.getpid(),
                "uptime_seconds": round(time.time() - STARTED_AT, 2),
                "headers": {
                    "x-real-ip": request.headers.get("X-Real-IP"),
                    "x-forwarded-for": request.headers.get("X-Forwarded-For"),
                    "x-forwarded-proto": request.headers.get("X-Forwarded-Proto"),
                },
            }
        ),
        200,
    )


@app.get("/api/error")
def api_error() -> tuple[dict[str, str], int]:
    """
    Специальный endpoint для демонстрации обработки ошибок и логов.
    """
    logger.error("Intentional error endpoint was called")

    raise RuntimeError("Intentional demo error")


@app.errorhandler(404)
def not_found(_error) -> tuple[dict[str, str], int]:
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error) -> tuple[dict[str, str], int]:
    logger.exception("Unhandled application error: %s", error)
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Только для локальной разработки.
    # В demo-роли приложение запускается через Gunicorn.
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("APP_PORT", "8080")),
        debug=False,
    )
