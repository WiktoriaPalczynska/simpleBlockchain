## simpleBlockchain

Edukacyjny projekt lokalnego blockchaina stworzony w języku Python, wykorzystujący algorytm konsensusu Proof-of-Stake (PoS). System umożliwia tworzenie transakcji między użytkownikami, przechowywanie ich, walidację bloków oraz sprawdzenie integralności łańcucha. Prawdopodobieństwo wyboru walidatora określa dodatkowy czynnik "coin age". W celu zapewnienia autentyczności transakcji i bloków wykorzystano kryptografię asymetryczną ECDSA. System został zaprojektowany w celach edukacyjnych, aby w przystępny sposób zilustrować podstawowe koncepcje technologii blockchain.

---

## Spis treści
* [O projekcie](#simpleBlockchain)
* [Technologie](#technologie)
* [Funkcjonalności](#funkcjonalności)
* [Struktury danych](#struktury-danych)

---

## Technologie

- Python 3.12.0
- biblioteki: cryptography, hashlib, json, base64, time, random

---

## Funkcjonalności

- Dodawanie transakcji między użytkownikami
- Wybór walidatora oparty o Proof-of-Stake i coin age
- Tworzenie i podpisywanie bloków
- Weryfikacja poprawności łańcucha
- Serializacja danych do formatu JSON

---

## Struktury danych

### `transaction.py`
Definiuje klasę Transaction. Przechowuje dane o nadawcy, odbiorcy i kwocie oraz weryfikuje cyfrowe podpisy transakcji.

### `block.py`
Zawiera klasę Block. Odpowiada za strukturę bloku, przechowywanie listy transakcji, powiązanie z poprzednim blokiem (previous_hash) oraz obliczanie skrótów SHA-256.

### `validator.py`
Klasa Validator reprezentuje uczestnika sieci. Zarządza kluczami prywatnymi/publicznymi i bierze udział w procesie wyboru twórcy bloku.

### `blockchain.py`
Główny silnik systemu (PoSBlockchainCoinAge). Zarządza łańcuchem bloków, rejestrem walidatorów, saldami użytkowników oraz procesem konsensusu.

### `main.py`
Skrypt demonstracyjny uruchamiający standardowy obieg sieci (rejestracja, transakcje, kopanie bloków).

### `simulate_attack.py`
Moduł do testowania odporności sieci na próby manipulacji danymi i fałszerstwa.

---
