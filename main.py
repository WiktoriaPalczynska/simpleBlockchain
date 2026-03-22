import time
import random
import logging
from transaction import Transaction
from validator import Validator
from blockchain import PoSBlockchainCoinAge

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    blockchain = PoSBlockchainCoinAge()

    #Konfiguracja
    MIN_STAKE = 10
    MAX_STAKE = 30
    COIN_AGE_DELAY = 1

    #Rejestracja walidatorów z określonymi udziałami (stake)
    validator_names = ["UserA", "UserB", "UserC"]
    validators = {}

    for name in validator_names:
        try:
            stake = random.randint(MIN_STAKE, MAX_STAKE)
            val = Validator(name, stake)
            blockchain.register_validator(val)
            validators[name] = val
            blockchain.balances[name] = random.randint(120, 180)
            logging.info(f"Zarejestrowano walidatora {name} z saldem {blockchain.balances[name]} i stake {stake}")
        except ValueError as e:
            logging.error(f"Błąd podczas rejestracji walidatora {name}: {e}")

    time.sleep(COIN_AGE_DELAY) #opóźnienie dla coin age

    #Generowanie transakcji
    for _ in range(10):
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

        #Próba zatwierdzenia bloku
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