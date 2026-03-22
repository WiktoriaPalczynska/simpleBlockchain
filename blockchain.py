import time
import random
import logging
import json
import base64
from transaction import Transaction
from block import Block
from validator import Validator

class PoSBlockchainCoinAge:
    """Prosty blockchain oparty o Proof-of-Stake z wykorzystaniem mechanizmu coin age."""
    def __init__(self):
        self.chain = [] #lista bloków w blockchainie
        self.unconfirmed_transactions = [] #transakcje niezatwierdzone
        self.validators_map = {} #{validator.id:validator}
        self.balances = {} #salda uzytkownikow
        self.last_nonces = {} #ostatni numer transakcji
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), previous_hash="0", validator="genesis")
        genesis_block.signature = b"genesis_signature"
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]

    def register_validator(self, validator):
        self.validators_map[validator.id] = validator

    def is_valid_transaction(self, tx: Transaction) -> bool:
        """
        Weryfikacja poprawności transakcji:
        - kwota musi być większa od zera
        - sender musi mieć wystarczające saldo.
        """
        if not isinstance(tx.amount, (int, float)) or tx.amount <= 0:
            return False #czy poprawna kwota
        if tx.sender not in self.balances or self.balances[tx.sender] < tx.amount:
            return False #czy sender ma zarejestrowane saldo i wystarczajace srodki
        if not tx.sender or not tx.recipient:
            return False #nadawca i odbiorca są wymagani
        if not isinstance(tx.nonce, int) or tx.nonce <= 0:
            return False, f"Nieprawidłowy nonce"

        validator = self.validators_map.get(tx.sender)
        if not validator:
            return False, f"Transakcja od niezweryfikowanego nadawcy {tx.sender}"
        if not tx.verify_signature(validator.public_key):
            return False, "Błąd weryfikacji podpisu"

        return True

    def add_transaction(self, tx: Transaction):
        valid = self.is_valid_transaction(tx)
        if not valid:
            logging.warning(f"Nie udało się dodać transakcji")
            raise ValueError(f"Niepoprawna transakcja")
        self.balances[tx.sender] -= tx.amount
        self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount
        self.last_nonces[tx.sender] = tx.nonce
        self.unconfirmed_transactions.append(tx)

    def select_validator(self):
        """
        Wybór walidatora do zatwierdzenia bloku.
        Prawdopodobienstwo wyboru walidatora wazone: weights = stake * coin_age,
        gdzie stake to ilość udziałow, a coin_age to czas od ostatniego zatwierdzenia bloku.
        Po wyborze, last_validated_time wybranego walidatora jest resetowany.
        """
        current_time = time.time()
        max_coin_age = 86400  #maksymalny coin age: 1 dzień
        weights = [] #prawdopodobienstwo wyboru walidatora
        validators = list(self.validators_map.values())
        if not validators:
            raise Exception("Brak zarejestrowanych walidatorów!")
        for v in validators:
            coin_age = min(current_time - v.last_validated_time, max_coin_age)
            weights.append(v.stake * coin_age)

        total_weight = sum(weights)
        if total_weight == 0:
            raise Exception("Brak walidatorów lub coin age jest zerowy!")
        selected = random.choices(validators, weights=weights, k=1)[0]
        selected.last_validated_time = current_time
        return selected

    def create_block(self):
        """Utworzenie nowego bloku na blockchainie wykorzystując wybranego walidatora."""
        if not self.unconfirmed_transactions: #czy są transakcje do zatwierdzenia
            return None

        #weryfikacja transakcji przed dodaniem do bloku
        valid_transactions = [tx for tx in self.unconfirmed_transactions if self.is_valid_transaction(tx)]
        if not valid_transactions:
            return None

        last_block = self.get_last_block()
        new_index  = last_block.index + 1

        selected_validator = self.select_validator()

        #utworzenie nowego bloku bez podpisu
        new_block = Block(
            index = new_index,
            transactions = valid_transactions,
            timestamp = time.time(),
            previous_hash = last_block.hash,
            validator = selected_validator.id,
            signature = None
        )

        #podpisanie i wyliczenie hash
        signing_string = new_block.get_signing_data()
        new_block.signature = selected_validator.sign_data(signing_string)
        new_block.hash = new_block.compute_hash()

        self.chain.append(new_block)
        self.unconfirmed_transactions.clear() #resetujemy liste transakcji

        return new_block

    def is_chain_valid(self) -> bool:
        """
        Weryfikacja poprawnosci blokow blockchaina:
         - poprawnosc powiazania hashy blokow (czy kazdy blok poprawnie wskazuje hash poprzedniego)
         - spojnosc hasha bloku
         - poprawnosc podpisu bloku (czy hash zgodny z obliczeniami)
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            #weryfikacja powiazania hashy
            if current.previous_hash != previous.hash:
                logging.error(f"Block {current.index}: invalid previous_hash")
                return False

            #spojnosc hasha łacznie z podpisem
            recalculated_hash = current.compute_hash()
            if current.hash != recalculated_hash: #sprawdzenie hasha po walidacji poprzedniego
                logging.error(f"Block {current.index}: invalid hash (expected {recalculated_hash})")
                return False

            #weryfikacja podpisu
            validator = self.validators_map.get(current.validator)
            if not validator:
                logging.error(f"Block {current.index}: unknown validator '{current.validator}'")
                return False

            signing_data = current.get_signing_data()
            if not validator.verify_signature(signing_data, current.signature):
                logging.error(f"Block {current.index}: signature verification failed")
                return False
        return True

    def export_chain_to_file(self, filename="blockchain_export.json"):
        try:
            data = []
            for block in self.chain:
                data.append({
                    'index': block.index,
                    'transactions': [tx.to_dict() for tx in block.transactions],
                    'timestamp': block.timestamp,
                    'previous_hash': block.previous_hash,
                    'validator': block.validator,
                    'signature': base64.b64encode(block.signature).decode('utf-8') if isinstance(block.signature, bytes) else str(block.signature),
                    'hash': block.hash
                })
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            logging.error(f"Błąd podczas zapisu do pliku {filename}: {e}")
            raise