import sqlite3
import os
from sqlite3.dbapi2 import Timestamp

def initialize_db():
    # Creates 'message_app.db' database
    conn = sqlite3.connect('DB/message_app.db')
    # Creates a cursor
    curs = conn.cursor()

    curs.execute("""CREATE TABLE IF NOT EXISTS users (
        user_name text PRIMARY KEY,
        password text,
        key text,
        is_deleted int DEFAULT 0
    )""")

    curs.execute("""CREATE TABLE IF NOT EXISTS messages (
        user_name text REFERENCES users(user_name) ,
        message text,
        timestamp text,
        sender text REFERENCES users(user_name),
        is_image int DEFAULT 0
    )""")


    # Commit and close connection
    conn.commit()
    conn.close()
    print("created db")


def teardown_db():
    os.remove('DB/message_app.db')


def add_user(user_name, password, key):
    # Connect to the database
    conn = sqlite3.connect('DB/message_app.db')
    curs = conn.cursor()

    try:
        curs.execute("INSERT INTO users (user_name, password, key) VALUES (?,?,?)", (user_name, password, key))

    except sqlite3.Error as e:
        # TODO custom message if user exists
        print(e)

    # Commit and close connection
    conn.commit()
    conn.close()


def remove_user(username):
    # Connect to the database
    conn = sqlite3.connect('DB/message_app.db')
    curs = conn.cursor()

    try:
        curs.execute("""
        UPDATE users
        SET is_deleted = 1
        WHERE user_name = (?) """, (username,))

    except sqlite3.Error as e:
        print("error\n")
        print(e)

    # Commit and close connection
    conn.commit()
    conn.close()


# checks if user_name exists in users and returns count
# 0 - username not in db
# 1 - username in db
def check_username(input):
    # Connect to the database
    conn = sqlite3.connect('DB/message_app.db')
    curs = conn.cursor()

    curs.execute("""
    SELECT count(*) FROM users 
    WHERE user_name = (?) 
    """, (input,))

    result = curs.fetchone()
    if result:
        username_count = result[0]
        
    else: username_count = 0

    # Commit and close connection
    conn.commit()
    conn.close()
    return (username_count)


def check_password(user_name, password):
    # Connect to the database
    conn = sqlite3.connect('DB/message_app.db')
    curs = conn.cursor()

    curs.execute("""
    SELECT count(*) FROM users 
    WHERE user_name = (?)
    AND password = (?) 
    """, (user_name, password))

    result = curs.fetchone()
    if result:
        password_verified = result[0]
    else: password_verified = 0

    # Commit and close connection
    conn.commit()
    conn.close()
    return (password_verified)


def check_deleted(user_name):
    # Connect to the database
    conn = sqlite3.connect('DB/message_app.db')
    curs = conn.cursor()
    is_deleted = False

    curs.execute("""
    SELECT is_deleted FROM users 
    WHERE user_name = (?)
    """, (user_name,))

    result = curs.fetchone()
    if result:
        is_deleted = result[0]

    # Commit and close connection
    conn.commit()
    conn.close()
    return (is_deleted)


# returns a list of message objects [{user_name, message, timestamp, sender, is_image}, ...] for chat history
def get_messages(user_name):
    message_list = []
    conn = sqlite3.connect('DB/message_app.db')
    curs = conn.cursor()
    curs.execute("""
    SELECT * FROM messages 
    WHERE user_name = (?)
    OR sender = (?)
    """, (user_name, user_name,))

    results = curs.fetchall()
    for result in results:
        user_name = result[0]
        message = result[1]
        timestamp = result[2]
        sender = result[3]
        is_image = result[4]
        message = {'user_name': user_name, 'message': message, 'timestamp': timestamp, 'sender': sender, 'is_image': is_image}
        message_list.append(message)
        
    conn.commit()
    conn.close()
    return(message_list)

# returns a list of message objects [{user_name, message, timestamp, sender, is_image}, ...] for chat history
def get_message_update(user_name, timestamp, sender):
    message_list = []
    conn = sqlite3.connect('DB/message_app.db')
    curs = conn.cursor()
    curs.execute("""
    SELECT * FROM messages 
    WHERE user_name = (?)
    AND sender = (?)
    AND timestamp >= (?)
    """, (user_name, sender, timestamp,))

    results = curs.fetchall()
    for result in results:
        user_name = result[0]
        message = result[1]
        timestamp = result[2]
        sender = result[3]
        is_image = result[4]
        message = {'user_name': user_name, 'message': message, 'timestamp': timestamp, 'sender': sender, 'is_image': is_image}
        message_list.append(message)
        
    conn.commit()
    conn.close()
    return(message_list)

# add a single message to the db. Call this function when sending a message
def add_message(message):
    conn = sqlite3.connect('DB/message_app.db')
    curs = conn.cursor()
    curs.execute("""
    INSERT INTO messages (user_name, message, timestamp, sender, is_image)
    VALUES (?,?,?,?,?)
    """, ( message.get('user_name'), message.get('message'), message.get('timestamp'), message.get('sender'), message.get('is_image')))

    conn.commit()
    conn.close()  

def delete_message(sender, message, user_name):
    conn = sqlite3.connect('DB/message_app.db')
    curs = conn.cursor()
    curs.execute("""
    DELETE FROM messages
    WHERE user_name = (?)
    AND message = (?)
    AND sender = (?)
    """, (user_name, message, sender,))

    conn.commit()
    conn.close()

# Calls initialize funtion if db does not exist
if not os.path.isfile('DB/message_app.db'):
    initialize_db()


