import bcrypt


MAX_BCRYPT_PASSWORD_BYTES = 72


def _password_bytes(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError("Password must be 72 bytes or fewer")
    return encoded


class PasswordService:
    @staticmethod
    def hash_password(password: str) -> str:
        hashed = bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt())
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                _password_bytes(plain_password),
                hashed_password.encode("utf-8"),
            )
        except ValueError:
            return False
