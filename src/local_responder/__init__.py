import dataclasses as dc
from contextlib import asynccontextmanager
from json.decoder import JSONDecodeError
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional, Union
from typing_extensions import Literal

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


@dc.dataclass
class TrackedRequest:
    method: str
    path: str
    valid: bool
    headers: Dict
    query: Dict
    json: Optional[Dict]


class RequestTracker:
    calls: List[TrackedRequest]
    expected_method: str
    expected_path: str

    def __init__(
        self: "RequestTracker", expected_path: str, expected_method: str
    ) -> None:
        self.calls = []
        self.expected_method = expected_method.lower()
        self.expected_path = expected_path

    @property
    def invalid_calls(self: "RequestTracker") -> List[TrackedRequest]:
        return [tr for tr in self.calls if not tr.valid]

    async def add(self: "RequestTracker", request: web.Request) -> None:
        valid = (
            request.method.lower() == self.expected_method
            and request.path == self.expected_path
        )
        try:
            json = await request.json()
        except JSONDecodeError:
            json = None

        self.calls.append(
            TrackedRequest(
                method=request.method.lower(),
                path=request.path,
                valid=valid,
                headers=dict(request.headers),
                query=dict(request.query),
                json=json,
            )
        )


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
) -> AsyncIterator[RequestTracker]:
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
    request_tracker = RequestTracker(expected_method=method, expected_path=path)

    @web.middleware
    async def track_requests(
        request: web.Request, handler: Handler
    ) -> web.StreamResponse:
        # request_tracker.add.append((request.method.lower(), request.path))
        await request_tracker.add(request)
        return await handler(request)

    app = web.Application(middlewares=[track_requests])
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
        yield request_tracker
    finally:
        await runner.cleanup()

    # Make sure no requests were made to invalid paths
    if request_tracker.invalid_calls:
        invalid_call = request_tracker.invalid_calls[0]
        raise InvalidPathException(
            f'Invalid {invalid_call.method.upper()} request made to "{invalid_call.path}"'
        )
