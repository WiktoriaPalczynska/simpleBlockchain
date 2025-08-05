## simpleBlockchain

Prosty blockchain stworzony w języku Python oparty na mechanizmie konsensusu Proof-of-Stake (PoS). Blockchain umożliwia tworzenie transakcji między użytkownikami, przechowywanie ich, walidację bloków oraz sprawdzenie integralności łańcucha. Prawdopodobieństwo wyboru walidatora określa dodatkowy czynnik "coin age". W celu zapewnienia autentyczności transakcji i bloków wykorzystano algorytm RSA z dopełnieniem PSS (Probabilistic Signature Scheme) i haszowaniem SHA-256. System został zaprojektowany w celach edukacyjnych, aby w przystępny sposób zilustrować podstawowe koncepcje technologii blockchain.

---

## Spis treści
* [O projekcie](#simpleClockchain)
* [Technologie](#technologie)
* [Funkcjonalności](#funkcjonalnosci)
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

### `Transaction`
Klasa reprezentująca transakcję między użytkownikami:
- `sender`: nadawca
- `recipient`: odbiorca
- `amount`: kwota
- `nonce`: unikalny, inkrementowany numer transakcji w bloku
- `signature`: cyfrowy podpis

### `Block`
Klasa reprezentująca blok w blockchainie:
- `index`: numer bloku w łańcuchu
- `transactions`: lista obiektów Transaction
- `timestamp`: czas utworzenia bloku
- `previous_hash`: hash poprzedniego bloku
- `validator`: użytkownik zatwierdzający blok
- `signature`: uproszczony podpis bloku
- `hash`: ostateczny hash całego bloku (wraz z podpisem)

### `Validator`
Klasa reprezentująca walidatora (użytkownik akceptujący blok) w systemie Proof-of-Stake:
- `id`: identyfikator walidatora
- `stake`: posiadany przez użytkownika stake
- `last_validated_time`: czas przez jaki walidator trzyma swoje środki
- `public_key`: klucz publiczny RSA
- `private_key`: klucz prywatny RSA

### `PoSBlockchainCoinAge`
Prosty blockchain oparty o Proof-of-Stake z wykorzystaniem mechanizmu coin age:
- `chain`: lista wszystkich bloków (pierwszy to blok genesis)
- `unconfirmed_transactions`: pamięć podręczna (mempool) przychodzących, ale jeszcze niezatwierdzonych transakcji
- `validators_map`:  słownik rejestrujący walidatorów (validator.id→Validator), potrzebny do weryfikacji podpisów.
- `balances`: bieżące salda każdego uczestnika, wykorzystywane przy walidacji transakcji
- `last_nonces`: ostatnie wartości nonce dla każdego nadawcy
- `create_genesis_block()`: dodaje blok startowy z ustalonym hashem i sygnaturą

---