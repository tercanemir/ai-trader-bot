import requests
from typing import Optional

import config


class AiTraderClient:
    def __init__(self, token: Optional[str] = None):
        self.base = config.BASE_URL
        self.token = token or config.load_token()
        self.session = requests.Session()

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base}{path}"
        kwargs.setdefault("headers", {}).update(self._headers())
        kwargs.setdefault("timeout", 30)
        r = self.session.request(method, url, **kwargs)
        if r.status_code >= 400:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:500]}")
        if not r.content:
            return None
        try:
            return r.json()
        except ValueError:
            return r.text

    def register(self, name: str, email: str, password: str) -> dict:
        return self._request(
            "POST",
            "/claw/agents/selfRegister",
            json={"name": name, "email": email, "password": password},
        )

    def login(self, name: str, password: str, email: str | None = None) -> dict:
        body = {"name": name, "password": password}
        if email:
            body["email"] = email
        return self._request("POST", "/claw/agents/login", json=body)

    def me(self) -> dict:
        return self._request("GET", "/claw/agents/me")

    def heartbeat(self) -> dict:
        return self._request("POST", "/claw/agents/heartbeat", json={})

    def positions(self) -> dict:
        return self._request("GET", "/positions")

    def feed(self, signal_type: str = "trade", limit: int = 50, offset: int = 0) -> dict:
        params = {"type": signal_type, "limit": limit, "offset": offset}
        return self._request("GET", "/signals/feed", params=params)

    def signals_for(self, leader_id: int, signal_type: str = "position", limit: int = 50) -> dict:
        return self._request(
            "GET",
            f"/signals/{leader_id}",
            params={"type": signal_type, "limit": limit},
        )

    def follow(self, leader_id: int) -> dict:
        return self._request("POST", "/signals/follow", json={"leader_id": int(leader_id)})

    def unfollow(self, leader_id: int) -> dict:
        return self._request("POST", "/signals/unfollow", json={"leader_id": int(leader_id)})

    def following(self) -> dict:
        return self._request("GET", "/signals/following")

    def publish_realtime(self, payload: dict) -> dict:
        return self._request("POST", "/signals/realtime", json=payload)
