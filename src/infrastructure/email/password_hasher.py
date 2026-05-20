from passlib.context import CryptContext

from ...domain.services import PasswordHashService

password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class PasswordHasher(PasswordHashService):
    @staticmethod
    def hash_password(password: str) -> str:
        return password_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return password_context.verify(plain_password, hashed_password)
