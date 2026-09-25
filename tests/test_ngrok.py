import requests

import core.ngrok as ngrok


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


TUNNELS = {
    "tunnels": [
        {"public_url": "http://abc.ngrok-free.app", "config": {"addr": "http://localhost:8080"}},
        {"public_url": "https://outra.ngrok-free.app", "config": {"addr": "http://localhost:3000"}},
        {"public_url": "https://abc.ngrok-free.app", "config": {"addr": "http://localhost:8080"}},
    ]
}


def test_picks_https_tunnel_for_the_api_port(monkeypatch):
    monkeypatch.setattr(ngrok.requests, "get", lambda url, timeout: FakeResponse(TUNNELS))

    assert ngrok.discover_public_url("http://localhost:4040", 8080) == "https://abc.ngrok-free.app"


def test_returns_none_when_ngrok_is_not_running(monkeypatch):
    def refuse(url, timeout):
        raise requests.ConnectionError("recusado")

    monkeypatch.setattr(ngrok.requests, "get", refuse)

    assert ngrok.discover_public_url("http://localhost:4040", 8080, attempts=2, delay_seconds=0) is None


def test_waits_for_the_tunnel_to_come_up(monkeypatch):
    responses = iter([FakeResponse({"tunnels": []}), FakeResponse(TUNNELS)])
    monkeypatch.setattr(ngrok.requests, "get", lambda url, timeout: next(responses))

    assert ngrok.discover_public_url("http://localhost:4040", 8080, delay_seconds=0) == "https://abc.ngrok-free.app"
