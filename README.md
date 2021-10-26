# Local Responder

Local Responder is a helper context manager that creates a web server with just
one view that has only one purpose, to return simple predefined data.

This is created just for the purpose of using in tests, to mock out an API in a
very simple manner. It's mostly useful for a blackbox like test where you are
mocking out an external API while making requests to the "blackbox" api.

## Usage

You can import the `respond` function and use it as an asynchronous context manager

```python
import asyncio
import aiohttp
from local_responder import respond


async def func() -> None:
    async with aiohttp.ClientSession() as session:
        async with respond(
            json={"status": "OK"},
            path="/health",
            method="get",
            status_code=200,
        ) as api:
            response = await session.get("http://localhost:5000/health", params={"foo": "bar"})

            data = await response.json()

            assert data == {"status": "OK"}
            assert response.status == 200
            assert len(api.calls) == 1
            assert api.calls[0].query == {"foo": "bar"}

        async with respond(
            json={"status": "Error"},
            path="/health",
            method="get",
            status_code=500,
        ):
            response = await session.get("http://localhost:5000/health")

            data = await response.json()

            assert data == {"status": "Error"}
            assert response.status == 500


if __name__ == "__main__":
    asyncio.run(func())
```

The context manager will raise an error if a request is made to an undefined
path or using an unsupported method.

You need to provide one of `json`, `text` or `body` for the view to return, the
other arguments are all optional, defaulting to creating a `GET` view with a
status code 200 and listen on port 5000.

## Request tracking

Each request made to the view while it is alive is tracked. The tracker simply
tracks the request method, path, headers, query and json payload if there is
one. Each tracked request is stored in a `RequestTracker` instance that is
yielded from the context manager. Example of call verification is in the
example above.
