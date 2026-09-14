from typing import Protocol

from fastapi import Request


class AuthenticationService(Protocol):
    def authenticate(self, request: Request) -> str | None: ...


class DevelopmentAuthenticationService:
    def authenticate(self, request: Request) -> str | None:
        return request.headers.get("x-user-id")
