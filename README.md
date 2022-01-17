# SENG360 A3

## Security Specification and Implementation (SDI)
### *Authors: Joey Raymer, Aaron Mok, Lydia Mekonnen Lulie, Taimur Niazi*

## Project Overview
We are creating a secure messaging application (SM) in python with the following requirements (and their descriptions beneath them):
> Taken from the assignment description

- SM must support 1:1 messaging and may support group chats (that’s optional)

- Text messages as well as pictures should be supported

- Message history is kept in encrypted form (at-rest encryption)

- Message history (for a particular conversation) can be deleted by a user

- Message transport uses end-to-end encryption with perfect forward secrecy (https://en.wikipedia.org/wiki/Forward_secrecy)

- Users are authenticated (i.e.,they should be guaranteed to talk to the right person)

- Message integrity must be assured

- Users can plausibly deny having sent a message (see https://signal.org/blog/simplifying-otr-deniability/)

- Users can sign up for an account and also delete their account

- SM must be implemented in Python :snake:

## Diagrams

### Signup
![Client signs up with Server]()

### Login
![Client logs in with Server]()

### Client's messages being stored in server DB
![Storing Client msg in DB Diagram]()

### Client's messages being accessed from server DB
![Accessing Client msg from DB Diagram]()

### Deleting message
![Client deletes their messages from server]()

## Database
The database for this prototype is implemented using SQLite3. SQLite3 is a lightweight database that also supports the use of SQL. The database including all data is saved locally as DB/message_app.db. Removing all data for a fresh start can easily be done by deleting message_app.db manually or automating a script to call teardown_db() from DB/database.py. The database file is generated the first time server.py and client.py are run. All functions that work directly with the database are located in DB/database.py. 

## Sever/client sign
Detailed explanation of each functions are within the code.
Server: Server does most of the work here as it handles all the requests from the client. When the sever starts, it will create a database locally in which everything is kept. While the server runs, it will listen to any incomming connections. When a connection is found, it will create a thread dedicated to that client. This will allow clients to send messages concurrently to the server. These messages include 'flags' which acts as directions so the server will know what to do, or just regular messages that need to be stored into the Database. The server is also connected to the Database for queries.
Client: The main function of client is to send messages. On the client side, users will be prompted extra options to improve functionality. Otherwise, everything is mostly handled by the server. 

## Extra Comments
U can also link certain sections within markdown like "We implemented encrypted form as shown in [diagram](#Client's messages being accessed from server DB)"

### SM must support 1:1 messaging and may support group chats (that’s optional)
Currently, we're only supporting 1:1 messaging using client -> server -> client.

### Message history (for a particular conversation) can be deleted by a user
Users can selectively delete messages.

### Encryption/Users can plausibly deny having sent a message 
(https://en.wikipedia.org/wiki/Forward_secrecy) | (see https://signal.org/blog/simplifying-otr-deniability/)  

Elliptic-Curve Diffie Hellman key exchange allows the clients to simultaneously compute the same key. The clients have a private key for every session which is never shared and an authentication key that is used to establish identity by signing the data. They clients generate a public key that is signed by the authentication key and exchange the signed public keys through the server in order to generate the final session key that will encrypt the data. The encryption system changes keys it uses to encrypt and decrypt information in every message sent making the keys ephemeral achieving perfect forward secrecy. The messages are plausibly deniable because the encryption key is generated from a shared secret. 

## Run Instructions
Run server before running client(s)
