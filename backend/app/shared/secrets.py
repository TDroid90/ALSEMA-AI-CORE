import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import Settings, get_settings


class SecretDecryptionError(ValueError):
    pass


class SecretCipher:
    def __init__(self, settings: Settings | None = None) -> None:
        current = settings or get_settings()
        master = current.secret_encryption_key.get_secret_value()
        if not master:
            master = current.app_secret_key.get_secret_value()
        derived = hashlib.sha256(f"alsema-plugin-secrets-v1:{master}".encode()).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(derived))

    def encrypt(self, value: str) -> str:
        if not value:
            raise ValueError("El secreto no puede estar vacío.")
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, encrypted_value: str) -> str:
        try:
            return self._fernet.decrypt(encrypted_value.encode()).decode()
        except InvalidToken as exc:
            raise SecretDecryptionError("No se pudo descifrar el secreto configurado.") from exc
