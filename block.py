import hashlib
import json
import base64
from transaction import Transaction

class Block:
    """Klasa reprezentująca blok w blockchainie."""
    def __init__(self, index: int, transactions: list, timestamp: float, previous_hash: str, validator: str, signature: bytes = None):
        if not isinstance(index, int) or index < 0:
            raise ValueError("Indeks musi być nieujemną liczbą całkowitą.")
        if not isinstance(transactions, list) or not all(isinstance(tx, Transaction) for tx in transactions):
            raise ValueError("Transakcje muszą być listą obiektów Transaction.")
        if not isinstance(timestamp, (int, float)) or timestamp <= 0:
            raise ValueError("Znacznik czasu musi być dodatnią liczbą.")
        if not isinstance(previous_hash, str) or not previous_hash:
            raise ValueError("Hash poprzedniego bloku musi być niepustym ciągiem znaków.")
        if not isinstance(validator, str) or not validator:
            raise ValueError("Walidator musi być niepustym ciągiem znaków.")
        if signature is not None and not isinstance(signature, bytes):
            raise TypeError("Podpis musi być typu bytes lub None.")

        self.index = index #numer bloku w łańcuchu
        self.transactions = transactions #lista obiektów Transaction
        self.timestamp = timestamp #czas utworzenia bloku
        self.previous_hash = previous_hash #hash poprzedniego bloku
        self.validator = validator #user zatwierdzający blok
        self.signature = signature #uproszczony podpis bloku
        self.hash = None #ostateczny hash całego bloku (wraz z podpisem)

    def to_canonical_dict(self, include_signature=False):
        data = {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'validator': self.validator
        }
        if include_signature:
            sig = base64.b64encode(self.signature).decode('utf-8') if self.signature else None
            data['signature'] = sig
        return data

    def to_canonical_json(self, include_signature=False):
        try:
            return json.dumps(
                self.to_canonical_dict(include_signature),
                sort_keys=True,
                separators=(',', ':')
            )
        except TypeError as e:
            raise ValueError(f"Błąd serializacji JSON: {e}")

    def compute_hash(self):
        """Tworzenie wartosci hasha (SHA-256) po serializacji całego bloku."""
        canonical = self.to_canonical_json(include_signature=True)
        self.hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        return self.hash

    def get_signing_data(self):
        try:
            return self.to_canonical_json(include_signature=False)
        except TypeError as e:
            raise ValueError(f"Błąd generowania danych do podpisu: {e}")