# api-gateway/app/proxy.py
from typing import Dict

import requests
from flask import Response, request

# Cabeçalhos que NÃO devem ser repassados
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "host",
}


def _filter_request_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for k, v in request.headers.items():
        if k.lower() in HOP_BY_HOP_HEADERS:
            continue
        headers[k] = v
    return headers


def forward_request(base_url: str, subpath: str = "") -> Response:
    """
    Encaminha a requisição atual para o serviço de destino.

    base_url: ex: http://management-service:5002
    subpath:  ex: "customers/1"  -> vira http://management-service:5002/customers/1
    """
    method = request.method

    if subpath:
        url = base_url.rstrip("/") + "/" + subpath.lstrip("/")
    else:
        url = base_url.rstrip("/")

    headers = _filter_request_headers()

    resp = requests.request(
        method=method,
        url=url,
        headers=headers,
        params=request.args,
        data=request.get_data(),
        cookies=request.cookies,
        timeout=30,
    )

    excluded = {"content-encoding", "transfer-encoding", "connection"}
    response_headers = [
        (name, value)
        for name, value in resp.headers.items()
        if name.lower() not in excluded
    ]

    return Response(resp.content, status=resp.status_code, headers=response_headers)
