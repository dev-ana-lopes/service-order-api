from datetime import timedelta
from typing import Any

from jose import JWTError, jwt

from ...domain.services import AccessTokenService
from ...domain.time import utcnow
from ..config.settings import Settings


class JwtService(AccessTokenService):
    def __init__(self, settings: Settings):
        self.settings = settings

    def create_token(self, user_id: str, email: str) -> str:
        expire = utcnow() + timedelta(minutes=self.settings.JWT_EXPIRATION_MINUTES)
        payload = {
            "user_id": user_id,
            "email": email,
            "role": "admin",
            "iss": f"service-order-api/{self.settings.ENVIRONMENT}",
            "exp": expire,
        }
        token = jwt.encode(
            payload,
            self.settings.JWT_SECRET,
            algorithm=self.settings.JWT_ALGORITHM,
        )
        return token

    def verify_token(self, token: str) -> dict[str, Any] | None:
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET,
                algorithms=[self.settings.JWT_ALGORITHM],
                options={"verify_aud": False},
            )
            return payload
        except JWTError:
            return None
