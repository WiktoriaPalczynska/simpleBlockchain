import json
import logging
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature

class Transaction:
    """Klasa reprezentująca transakcję użytkowników."""
    def __init__(self, sender, recipient, amount, nonce, signature=None):
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Kwota musi być dodatnią liczbą.")
        if not isinstance(sender, (str, bytes)) or not isinstance(recipient, (str, bytes)):
            raise ValueError("Nadawca i odbiorca muszą być typu str lub bytes.")
        if not sender or not recipient:
            raise ValueError("Nadawca i odbiorca nie mogą być puste.")
        if not isinstance(nonce, int) or nonce <= 0:
            raise ValueError("Nonce musi być dodatnią liczbą całkowitą.")

        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.nonce = nonce # unikalny dla nadawcy, inkrementowany numer transakcji w bloku
        self.signature = signature # podpis ECDSA

    def to_dict(self):
        return {
            'sender': self.sender.decode('utf-8') if isinstance(self.sender, bytes) else self.sender,
            'recipient': self.recipient.decode('utf-8') if isinstance(self.recipient, bytes) else self.recipient,
            'amount': self.amount,
            'nonce': self.nonce,
        }

    def verify_signature(self, public_key: ec.EllipticCurvePrivateKey) -> bool:
        """Weryfikacja podpisu transakcji za pomocą klucza publicznego nadawcy."""
        if not self.signature:
            return False
        try:
            data = json.dumps(self.to_dict(), sort_keys=True).encode('utf-8')
            public_key.verify(self.signature, data, ec.ECDSA(hashes.SHA256()))
            return True

        except InvalidSignature:
            return False
        except Exception as e:
            logging.error(f"Błąd weryfikacji transakcji: {e}")
            return False