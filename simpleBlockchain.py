import hashlib
import json
import time
import random
import logging
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

"""
Prosty blockchain do przechowywania i weryfikacji transakcji między użytkownikami.
W celu walidacji poprawności utworzonych bloków zastosowano uproszczony mechanizm konsensusu Proof-of-Stake
z dodatkowym czynnikiem „coin age”, co wpływa na wybór walidatora.
"""

logging.basicConfig(level=logging.INFO)

class Transaction:
    'Klasa reprezentująca transakcję użytkowników.'
    def __init__(self, sender, recipient, amount, nonce, signature=None):
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Kwota musi być dodatnią liczbą.")
        if not sender or not recipient:
            raise ValueError("Nadawca i odbiorca nie mogą być puste.")
        if not isinstance(nonce, int) or nonce <= 0:
            raise ValueError("Nonce musi być dodatnią liczbą całkowitą.")

        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.nonce = nonce #unikalny, inkrementowany numer transakcji w bloku
        self.signature = signature

    def to_dict(self):
        return {
            'sender': self.sender.decode() if isinstance(self.sender, bytes) else self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'nonce': self.nonce,
            'signature': (
                base64.b64encode(self.signature).decode('utf-8')
                if self.signature and isinstance(self.signature, bytes) else self.signature
            )
        }

    def verify_signature(self, public_key, data: str) -> bool:
        'weryfikacja podpisu transakcji za pomocą klucza publicznego nadawcy.'
        if not self.signature:
            return False
        try:
            public_key.verify(
                self.signature,
                f"{self.sender}{self.recipient}{self.amount}".encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

class Block:
    'Klasa reprezentująca blok w blockchainie.'
    def __init__(self, index: int, transactions: list, timestamp: float, previous_hash: str, validator: str, signature: bytes = None):
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
            sig = base64.b64encode(self.signature).decode() if self.signature else None
            data['signature'] = sig
        return data

    def to_canonical_json(self, include_signature=False):
        return json.dumps(
            self.to_canonical_dict(include_signature),
            sort_keys=True,
            separators=(',', ':')
        )

    def compute_hash(self):
        'tworzenie wartosci hasha (SHA-256) po serializacji całego bloku.'
        canonical = self.to_canonical_json(include_signature=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def get_signing_data(self):
        return self.to_canonical_json(include_signature=False) #podpis bez signature


class Validator:
    'Klasa reprezentująca walidatora (użytkownik akceptujący blok) w systemie PoS.'
    def __init__(self, id, stake):
        if not isinstance(stake, (int, float)) or stake <= 0:
            raise ValueError("Stake musi być dodatnią liczbą.")
        self.id = id
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
        self.stake = stake
        self.last_validated_time = time.time()

    def sign_data(self, data):
        'Podpis danych za pomocą klucza prywatnego.'
        return self.private_key.sign(
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    def verify_signature(self, data: str, signature: bytes) -> bool:
        try:
            self.public_key.verify(
                signature,
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def __repr__(self):
        return f"Validator(id={self.id}, stake={self.stake})"

class PoSBlockchainCoinAge:
    'Prosty blockchain oparty o Proof-of-Stake z wykorzystaniem mechanizmu coin age.'
    def __init__(self):
        self.chain = [] #lista bloków w blockchainie
        self.unconfirmed_transactions = [] #transakcje niezatwierdzone
        self.validators_map = {} #{validator.id:validator}
        self.balances = {} #salda uzytkownikow
        self.last_nonces = {} #ostatni numer transakcji
        self.create_genesis_block()


    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), previous_hash="0", validator="genesis")
        #genesis hash
        genesis_block.signature = b"genesis_signature"
        genesis_block.hash = genesis_block.compute_hash()

        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]

    def register_validator(self, validator):
        self.validators_map[validator.id] = validator

    def is_valid_transaction(self, tx: Transaction) -> (bool, str):
        """
        Weryfikacja poprawności transakcji:
        - kwota musi być większa od zera
        - sender musi mieć wystarczające saldo.
        """
        if not isinstance(tx.amount, (int, float)) or tx.amount <= 0:
            return False #czy poprawna kwota
        if tx.sender not in self.balances and self.balances[tx.sender] < tx.amount:
            return False #czy sender ma zarejestrowane saldo i wystarczajace srodki
        if not tx.sender or not tx.recipient:
            return False #nadawca i odbiorca są wymagani
        if not isinstance(tx.nonce, int) or tx.nonce <= 0:
            return False, f"Nieprawidłowy nonce"

        validator = self.validators_map.get(tx.sender)
        if not validator:
            return False, f"Transakcja od niezweryfikowanego nadawcy {tx.sender}"

        data = f"{tx.sender}|{tx.recipient}|{tx.amount}|{tx.nonce}"

        if not tx.verify_signature(validator.public_key, data):
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
        Wybor walidatora do zatwierdzenia bloku.
        Prawdopodobienstwo wyboru walidatora wazone: stake * coin_age,
        gdzie stake to ilość udziałow, a coin_age to czas od ostatniego zatwierdzenia bloku.
        Po wyborze, last_validated_time wybranego walidatora jest resetowany.
        """
        current_time = time.time()
        max_coin_age = 86400  # Maksymalny coin age: 1 dzień
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
        'Utworzenie nowego bloku na blockchainie wykorzystując wybranego walidatora.'
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

    def export_chain_to_file(self, filename="blockchain_export.json"): #plik do eksportu
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

#Przykładowe użycie
if __name__ == "__main__":
    blockchain = PoSBlockchainCoinAge()

    #Konfiguracja
    MIN_STAKE = 10
    MAX_STAKE = 30
    COIN_AGE_DELAY = 1

    #Rejestracja walidatorów z określonymi udziałami (stake)
    validator_names = ["UserA", "UserB", "UserC"] #nazwa walidatora
    validators = {}
    for name in validator_names:
        try:
            stake = random.randint(MIN_STAKE, MAX_STAKE) #losowo przydzielony stake
            val = Validator(name, stake)
            blockchain.register_validator(val)
            validators[name] = val
            blockchain.balances[name] = random.randint(120, 180) #saldo początkowe
            logging.info(f"Zarejestrowano walidatora {name} z saldem {blockchain.balances[name]} i stake {stake}")
        except ValueError as e:
            logging.error(f"Błąd podczas rejestracji walidatora {name}: {e}")

    time.sleep(COIN_AGE_DELAY) #opóźnienie dla coin age

    for _ in range(5): #5 transakcji
        sender, recipient = random.sample(validator_names, 2)
        if blockchain.balances.get(sender, 0) >= 5:
            amount = random.randint(5, min(20, blockchain.balances[sender]))
            sender_validator = validators[sender]
            tx_data = f"{sender}{recipient}{amount}"
            nonce = blockchain.last_nonces.get(sender, 0) + 1
            signature = sender_validator.sign_data(tx_data)
            tx = Transaction(sender, recipient, amount, nonce, signature)
            try:
                blockchain.add_transaction(tx)
                logging.info(f"Dodano transakcję: {sender} -> {recipient}, kwota: {amount}")
            except ValueError as e:
                logging.warning(f"Nie udało się dodać transakcji: {e}")
        else:
            logging.warning(f"Pomijanie transakcji: niewystarczające saldo nadawcy {sender}")

        try:
            block = blockchain.create_block()
            if block:
                logging.info(f"Nowy blok utworzony przez walidatora: {block.validator}")
                logging.info(f"Hash bloku: {block.hash}")
            else:
                logging.info("Brak transakcji do dodania w bloku.")
        except Exception as e:
            logging.error(f"Błąd podczas tworzenia bloku: {e}")

    #Weryfikacja poprawności łańcucha
    try:
        OK = blockchain.is_chain_valid()
        logging.info(f"Czy blockchain jest poprawny? {OK}")
    except Exception as e:
        logging.error(f"Błąd podczas weryfikacji łańcucha: {e}")

    #Eksport łańcucha do pliku
    try:
        blockchain.export_chain_to_file()
        logging.info("Łańcuch został wyeksportowany do pliku blockchain_export.json")
    except IOError as e:
        logging.error(f"Błąd podczas eksportu łańcucha: {e}")


