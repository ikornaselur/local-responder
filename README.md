# Local Responder

Local Responder is a helper function that creates a simple web server with just
one view that has only one purpose, to return simple data.

This is created just for the purpose of using in tests, to mock out an API in a
very simple manner.

## Usage

You can import the `respond` function and use it as an asynchronous context manager

```python
import aiohttp
from local_responder import respond

async def func() -> None:
    async with aiohttp.ClientSession() as session:
        async with respond(
            json={"status": "OK"},
            path="/health",
            method="get",
            status_code=200,
        ):
            response = session.get('http://localhost:5000/health')

            data = await response.json()

            assert data == {"status": "OK"}
            assert response.status_code == 200

        async with respond(
            json={"status": "Error"},
            path="/health",
            method="get",
            status_code=500,
        ):
            response = session.get('http://localhost:5000/health')

            data = await response.json()

            assert data == {"status": "Error"}
            assert response.status_code == 500
```

The context manager will raise an error if a request is made to an undefined
path or using an unsupported method.

You need to provide one of `json`, `text` or `body` for the view to return, the
other arguments are all optional, defaulting to creating a `GET` view with a
status code 200 and listen on port 5000.
