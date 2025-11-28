"""Centralized error types and JSON handlers for users-service."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from flask import Flask, jsonify


@dataclass
class ApiError(Exception):
    message: str
    status_code: int = 400
    code: str = "bad_request"
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {"message": self.message, "code": self.code}
        if self.details:
            payload["details"] = self.details
        return payload


class UnauthorizedError(ApiError):
    def __init__(self, message: str = "Não autorizado", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=401, code="unauthorized", details=details)


class ForbiddenError(ApiError):
    def __init__(self, message: str = "Acesso negado", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=403, code="forbidden", details=details)


class NotFoundError(ApiError):
    def __init__(self, message: str = "Recurso não encontrado", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=404, code="not_found", details=details)


class ValidationError(ApiError):
    def __init__(self, message: str = "Payload inválido", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=422, code="validation_error", details=details)


class ConflictError(ApiError):
    def __init__(self, message: str = "Conflito de dados", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=409, code="conflict", details=details)


class ServiceUnavailableError(ApiError):
    def __init__(self, message: str = "Serviço indisponível", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=503, code="service_unavailable", details=details)



def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):  # type: ignore[override]
        response = {"error": exc.to_dict()}
        return jsonify(response), exc.status_code

    @app.errorhandler(422)
    @app.errorhandler(400)
    def handle_bad_request(err):  # pragma: no cover - Flask generated errors
        return jsonify({"error": {"code": "bad_request", "message": "Requisição inválida"}}), getattr(err, "code", 400)

    @app.errorhandler(Exception)
    def handle_exception(err: Exception):  # pragma: no cover - safety net
        app.logger.exception("Unhandled exception", exc_info=err)
        return jsonify({"error": {"code": "internal_error", "message": "Erro interno inesperado"}}), 500
