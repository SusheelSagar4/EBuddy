"""
Request-size limit (pure ASGI middleware).

Without it every endpoint buffered a request body of any size in memory, and essay / story / chat text then went
through regex rubrics, so one large upload could stall or crash the single app process. Requests over the limit
get 413. The limit applies to the declared Content-Length and, for chunked uploads without one, to the bytes
actually received.
"""
import json
import os

DEFAULT_MAX_BYTES = 1024 * 1024  # 1 MiB: far above any legitimate JSON body this app accepts


def max_request_bytes() -> int:
    try:
        return max(1024, int(os.getenv("MAX_REQUEST_BYTES", DEFAULT_MAX_BYTES)))
    except ValueError:
        return DEFAULT_MAX_BYTES


class RequestSizeLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        limit = max_request_bytes()
        too_large = f"Request body too large (limit {limit} bytes)."

        declared = None
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    return await self._reject(send, 400, "Invalid Content-Length header.")
        if declared is not None:
            if declared > limit:
                return await self._reject(send, 413, too_large)
            return await self.app(scope, receive, send)

        if scope.get("method", "GET").upper() in ("GET", "HEAD", "OPTIONS", "DELETE"):
            return await self.app(scope, receive, send)

        # No Content-Length (chunked upload): read it here, up to the limit, then replay it to the app. Raising from
        # inside the app's receive() does not work: FastAPI turns any body-reading error into a generic 400.
        chunks, received = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            received += len(body)
            if received > limit:
                return await self._reject(send, 413, too_large)
            chunks.append(body)
            if not message.get("more_body", False):
                break
        buffered = b"".join(chunks)
        replayed = False

        async def replay():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": buffered, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

    @staticmethod
    async def _reject(send, status: int, detail: str):
        body = json.dumps({"detail": detail}).encode("utf-8")
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})
