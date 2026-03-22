import time
import logging
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from transaction import Transaction
from validator import Validator
from blockchain import PoSBlockchainCoinAge

#wyłączenie logów dla czytelniejszych wyników ataków
logging.basicConfig(level=logging.ERROR)

def setup_simulation():
    """Generowanie blockchain z kilkoma blokami do testów."""
    blockchain = PoSBlockchainCoinAge()

    #rejestracja walidatorów
    user_a = Validator("UserA", 100)
    user_b = Validator("UserB", 50)
    blockchain.register_validator(user_a)
    blockchain.register_validator(user_b)

    blockchain.balances["UserA"] = 1000
    blockchain.balances["UserB"] = 1000

    #generowanie 2 bloki z transakcjami (potrzebne do ataku na indeks 1 i 2)
    for i in range(2):
        tx = Transaction("UserA", "UserB", 10 * (i+1), i+1, user_a.sign_data(f"UserAUserB{10*(i+1)}"))
        blockchain.add_transaction(tx)
        time.sleep(0.2) #dla coin age
        blockchain.create_block()

    return blockchain, user_a, user_b

def run_attacks():
    blockchain, user_a, user_b = setup_simulation()
    print("="*60)
    print("SYMULACJA ATAKÓW NA BLOCKCHAIN")
    print("="*60)
    print(f"Początkowa liczba bloków: {len(blockchain.chain)}")
    print(f"Czy blockchain jest poprawny? {blockchain.is_chain_valid()}\n")

    print("--- SCENARIUSZ 1: Manipulacja transakcją w bloku 1 ---")
    block_to_modify = blockchain.chain[1]

    print(f"Oryginalna kwota transakcji: {block_to_modify.transactions[0].amount}")
    block_to_modify.transactions[0].amount += 50  #nielegalna zmiana
    print(f"Zmodyfikowana kwota transakcji: {block_to_modify.transactions[0].amount}")

    #uruchomienie weryfikacji łańcucha
    is_valid_1 = blockchain.is_chain_valid()
    print(f"WYNIK: Czy blockchain jest poprawny? {is_valid_1}")
    print("Status: " + ("WYKRYTO MANIPULACJĘ" if not is_valid_1 else "ATAK UDANY! (Błąd bezpieczeństwa)"))

    #cofnięcie zmiany, aby przetestować drugi atak na "czystym" łańcuchu
    block_to_modify.transactions[0].amount -= 50
    print("-" * 60)

    # =====================================================================================================

    print("\n--- SCENARIUSZ 2: Sfałszowanie podpisu walidatora ---")

    #wygenerowanie kluczy napastnika (nieautoryzowanych)
    hacker_private_key = ec.generate_private_key(ec.SECP256R1())

    #wybór bloku docelowego (indeks 2)
    block_to_spoof = blockchain.chain[2]
    print(f"Oryginalny walidator bloku: {block_to_spoof.validator}")

    #wygenerowanie fałszywego podpisu dla danych bloku
    signing_data = block_to_spoof.get_signing_data()
    fake_signature = hacker_private_key.sign(
        signing_data.encode('utf-8'),
        ec.ECDSA(hashes.SHA256())
    )

    #podstawienie sfałszowanego podpisu i zmiana ID walidatora
    block_to_spoof.signature = fake_signature #zmiana podpisu
    block_to_spoof.validator = "UserA" #próba podszycia się pod UserA
    print(f"Atakujący podmienił podpis i ustawił walidatora na: {block_to_spoof.validator}")

    #weryfikacja łańcucha
    print("\nUruchamianie weryfikacji podpisów...")
    is_valid_2 = blockchain.is_chain_valid()
    print(f"Czy blockchain zaakceptował fałszywy podpis? {is_valid_2}")
    print("Status: " + ("ODRZUCONO SFAŁSZOWANY PODPIS" if not is_valid_2 else "ATAK UDANY! (Błąd bezpieczeństwa)"))

if __name__ == "__main__":
    run_attacks()