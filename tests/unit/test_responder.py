import pytest
from aiohttp import ClientSession

from local_responder import BindAddressException, InvalidPathException, respond


@pytest.mark.asyncio
async def test_text_response(session: ClientSession) -> None:
    async with respond(text="Hello, world!"):
        response = await session.get("http://localhost:5000/")
        text = await response.text()

        assert text == "Hello, world!"
        assert response.status == 200


@pytest.mark.asyncio
async def test_json_response(session: ClientSession) -> None:
    data = {"status": "OK", "values": [1, 2, 3]}
    async with respond(json=data):
        response = await session.get("http://localhost:5000/")
        response_json = await response.json()

        assert response_json == data
        assert response.status == 200


@pytest.mark.asyncio
async def test_body_response(session: ClientSession) -> None:
    body = b"body contents"
    async with respond(body=body):
        response = await session.get("http://localhost:5000/")
        data = await response.read()

        assert data == body
        assert response.status == 200


@pytest.mark.asyncio
async def test_post_view(session: ClientSession) -> None:
    async with respond(text="Success", status_code=201, path="/create", method="post"):
        response = await session.post("http://localhost:5000/create")
        text = await response.text()

        assert text == "Success"
        assert response.status == 201


@pytest.mark.asyncio
async def test_delete_view(session: ClientSession) -> None:
    async with respond(
        text="Success", status_code=202, path="/delete", method="delete"
    ):
        response = await session.delete("http://localhost:5000/delete")
        text = await response.text()

        assert text == "Success"
        assert response.status == 202


@pytest.mark.asyncio
async def test_custom_status_code(session: ClientSession) -> None:
    async with respond(text="Uh oh, this isn't good", status_code=400):
        response = await session.get("http://localhost:5000/")

        text = await response.text()

        assert text == "Uh oh, this isn't good"
        assert response.status == 400


@pytest.mark.asyncio
async def test_custom_path(session: ClientSession) -> None:
    async with respond(text="Where am I?", path="/secret/path"):
        response = await session.get("http://localhost:5000/secret/path")

        text = await response.text()

        assert text == "Where am I?"
        assert response.status == 200


@pytest.mark.asyncio
async def test_invalid_path(session: ClientSession) -> None:
    with pytest.raises(
        InvalidPathException, match='Invalid GET request made to "/doesnt/exist"'
    ):
        async with respond(text="Hmm.."):
            response = await session.get("http://localhost:5000/doesnt/exist")

            # Still responds normally with 404: Not Found
            assert response.status == 404


@pytest.mark.asyncio
async def test_invalid_method(session: ClientSession) -> None:
    with pytest.raises(
        InvalidPathException, match='Invalid POST request made to "/does/exist"'
    ):
        async with respond(text="Hmm..", path="/does/exist"):
            response = await session.post("http://localhost:5000/does/exist")

            # Still responds normally with 405: Method Not Allowed
            assert response.status == 405


@pytest.mark.asyncio
async def test_custom_port(session: ClientSession) -> None:
    async with respond(text="What port is this?", port=9999):
        response = await session.get("http://localhost:9999")

        text = await response.text()
        assert text == "What port is this?"
        assert response.status == 200


@pytest.mark.asyncio
async def test_respond_raises_if_unable_to_bind_port() -> None:
    with pytest.raises(
        BindAddressException, match="Unable to bind address:.*address already in use"
    ):
        async with respond(text="First"), respond(text="Second"):
            pass


@pytest.mark.asyncio
async def test_multiple_concurrent_responses(session: ClientSession) -> None:
    async with respond(text="Hi, I'm Bob!", path="/bob", port=5001), respond(
        text="Hi, I'm Alice!",
        path="/alice",
        port=5002,
    ):
        bob_response = await session.get("http://localhost:5001/bob")
        bob_text = await bob_response.text()
        assert bob_text == "Hi, I'm Bob!"

        alice_response = await session.get("http://localhost:5002/alice")
        alice_text = await alice_response.text()
        assert alice_text == "Hi, I'm Alice!"


@pytest.mark.asyncio
async def test_tracked_get_requests(session: ClientSession) -> None:
    async with respond(text="Hello, there!") as api:
        await session.get("http://localhost:5000/", params={"foo": "bar"})
        assert len(api.calls) == 1
        assert api.calls[0].query == {"foo": "bar"}

        await session.get("http://localhost:5000/", params={"baz": "qux"})
        assert len(api.calls) == 2
        assert api.calls[1].query == {"baz": "qux"}


@pytest.mark.asyncio
async def test_tracked_requests_reset(session: ClientSession) -> None:
    async with respond(text="Hello, there!") as api:
        await session.get("http://localhost:5000/", params={"foo": "bar"})
        assert len(api.calls) == 1
        assert api.calls[0].query == {"foo": "bar"}

    async with respond(text="Hello, there!") as api:
        await session.get("http://localhost:5000/", params={"baz": "qux"})
        assert len(api.calls) == 1
        assert api.calls[0].query == {"baz": "qux"}


@pytest.mark.asyncio
async def test_tracked_post_requests_with_json(session: ClientSession) -> None:
    async with respond(text="Hello, there!", method="post") as api:
        await session.post("http://localhost:5000/", json={"foo": "bar"})
        assert len(api.calls) == 1
        assert api.calls[0].json == {"foo": "bar"}

        await session.post("http://localhost:5000/", json={"baz": "qux"})
        assert len(api.calls) == 2
        assert api.calls[1].json == {"baz": "qux"}
