from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Awaitable, Callable, Literal, Optional, Union

from aiohttp import web

Method = Union[Literal["get"], Literal["post"], Literal["delete"]]
METHODS = ("get", "post", "delete")


class ResponderException(Exception):
    pass


class InvalidPathException(ResponderException):
    pass


class BindAddressException(ResponderException):
    pass


Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


@asynccontextmanager
async def respond(
    *,
    json: Optional[Any] = None,
    body: Optional[Any] = None,
    text: Optional[str] = None,
    method: Method = "get",
    path: str = "/",
    status_code: int = 200,
    port: int = 5000,
) -> AsyncIterator[None]:
    if method.lower() not in METHODS:
        raise ValueError(f'"{method}" method isn\'t supported')
    arg_count = sum(param is not None for param in (json, body, text))
    if arg_count != 1:
        raise ValueError("You need to provide only one of `json`, `body` or `text`")

    # Set up temporary view
    async def view(request: web.Request) -> web.Response:
        if json is not None:
            return web.json_response(json, status=status_code)
        return web.Response(body=body, text=text, status=status_code)

    # Handle invalid paths
    requests = []

    @web.middleware
    async def handle_invalid_path(
        request: web.Request, handler: Handler
    ) -> web.StreamResponse:
        requests.append((request.method.lower(), request.path))
        return await handler(request)

    app = web.Application(middlewares=[handle_invalid_path])
    app.add_routes([getattr(web, method.lower())(path, view)])

    # Set up async runner
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", port)
    try:
        await site.start()
    except OSError as e:
        raise BindAddressException(f"Unable to bind address: {e.strerror}") from e

    # Yield and then cleanup
    try:
        yield
    finally:
        await runner.cleanup()

    # Make sure no requests were made to invalid paths
    invalid_requests = list(
        (m, p) for m, p in requests if m.lower() != method.lower() or p != path
    )
    if invalid_requests:
        inv_method, inv_path = invalid_requests[0]
        raise InvalidPathException(
            f'Invalid {inv_method.upper()} request made to "{inv_path}"'
        )
