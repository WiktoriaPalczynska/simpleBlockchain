import time
import logging
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
from transaction import Transaction

class Validator:
    """Klasa reprezentująca walidatora (użytkownik akceptujący blok) w systemie PoS."""
    def __init__(self, id, stake):
        if not isinstance(id, str) or not id:
            raise ValueError("Identyfikator walidatora musi być niepustym ciągiem znaków.")
        if not isinstance(stake, (int, float)) or stake <= 0:
            raise ValueError("Stake musi być dodatnią liczbą.")

        self.id = id
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        self.stake = stake
        self.last_validated_time = time.time()

    def sign_data(self, data: str) -> bytes:
        """Podpis danych transakcji za pomocą klucza prywatnego ECDSA."""
        if not data:
            raise ValueError("Dane do podpisania nie mogą być puste.")
        if not isinstance(data, str):
            raise TypeError("Dane muszą być typu string.")
        try:
            return self.private_key.sign(
                data.encode('utf-8'),
                ec.ECDSA(hashes.SHA256())
            )
        except Exception as e:
            raise ValueError(f"Błąd podczas podpisywania danych: {e}")

    def sign_transaction(self, transaction: Transaction):
        data = transaction.get_signing_data()
        return self.sign_data(data)

    def verify_signature(self, data: str, signature: bytes) -> bool:
        if not isinstance(data, str):
            raise TypeError("Dane muszą być typu str.")
        if not isinstance(signature, bytes):
            raise TypeError("Podpis musi być typu bytes.")
        try:
            self.public_key.verify(
                signature,
                data.encode('utf-8'),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            logging.error(f"Błąd weryfikacji podpisu: {e}")
            return False

    def update_validation_time(self):
        self.last_validated_time = time.time()

    def __repr__(self):
        return f"Validator(id={self.id}, stake={self.stake})"