#skeleton from: https://pythonprogramming.net/sockets-tutorial-python-3/
import socket
from sqlite3.dbapi2 import Error
import sys
import threading
import time
import datetime
import DB.database as db
from operator import itemgetter
import encryption as encrypt
from cryptography.fernet import Fernet
#External lib crypto must be installed inorder for this to work.

#Encryption: Lydu
#DB Related: Joey
#Sever functionality: Aaron

username = [None] * 5
password = [None] * 5

key = Fernet.generate_key()
fernet = Fernet(key)

'''
When detecting a new connect, direct and create a new thread for them
This will allow clients to talk to server concurrently
'''
class Sever_thread(threading.Thread):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.thread_index = -1
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.address, self.port))

    def listen(self):
        self.s.listen(5)
        while True:
            client_socket, client_address = self.s.accept()
            threading.Thread(target = self.listen_client, args= (client_socket, client_address)).start()
        
    def listen_client(self, client_socket, client_address):
        self.thread_index+=1
        verified = False

        while not verified:
            verified = collect_info(client_socket, client_address, self.thread_index)
        
        if verified:
            temp_name = username[self.thread_index%5]
            client_options(client_socket, client_address, temp_name, self.thread_index)
            reset_user_pass_fields(self.thread_index%5)            
            self.s.close()

'''
This section will give clients the option to either login or signup
When a client successfully  logs in, the function will return True.
This in turn allows them to access the rest of the application
'''
def collect_info(clientsocket, address, thread_num):
    while True:
        option = ''
        clientsocket.sendall(bytes("For signup, please enter 1\nFor login, please enter 0 |END|","utf-8"))
            
        verified = False
        while not option:
            option = clientsocket.recv(5096)
            option = option.decode("utf-8")

            if option.rstrip() == '0':
                verified = login(clientsocket, address,thread_num)
            elif option.rstrip() == '1':
                signup(clientsocket, address, thread_num)
                verified = login(clientsocket, address, thread_num)
            else:
                clientsocket.sendall(bytes("Incorrect input, please try again. |END|","utf-8"))
                option = ''
                time.sleep(0.1)

        return verified     

'''
This will parse and store user input for login.
'''
def info_fetch(clientsocket, address, thread_point):
    clientsocket.send(bytes("\nPlease enter User: |END|","utf-8"))
    time.sleep(0.1)

    while not username[thread_point]:
        username[thread_point] = clientsocket.recv(5096)
        username[thread_point] = username[thread_point].decode("utf-8").rstrip()
        if verify_username_availability(username[thread_point]):
            print(f"Valid user {username[thread_point]}\n")
            break
        else:
            clientsocket.send(bytes("Username not found, try again |END|\n","utf-8"))
            username[thread_point] = ''

    print(f"Input from {address} recieved, waiting for password...")

    clientsocket.send(bytes("Please enter Password: |END|","utf-8"))
    time.sleep(0.1)

    while not password[thread_point]:
        password[thread_point] = clientsocket.recv(5096)
        password[thread_point] = password[thread_point].decode("utf-8").rstrip()
    print(f"input from {address} recieved, authenticating...")

'''
When a user successfully logs in, clear their data that was stored
to allow room for new connections
'''
def reset_user_pass_fields(thread_point):
    username[thread_point] = ''
    password[thread_point] = ''

'''
Similar to info_fetch(), this allows a user who has entered a correct username
but wrong password to try 3 times. After that, they will be redirected to main menu
'''
def password_fetch(clientsocket, thread_point, num_attempts):
    clientsocket.send(bytes(f"{3 - num_attempts} attempts left. Please enter Password: |END|", "utf-8"))
    password[thread_point] = clientsocket.recv(5096)
    password[thread_point] = password[thread_point].decode("utf-8").rstrip()

'''
This will guide the user in the signup process. If username is take, it will
send and error. If the username is not taken, ask for a password and then store
this information into the DataBase
'''
def signup(clientsocket, address, thread_num):
    thread_point = thread_num % 5
    print(f"Detected signup option from {address}...\n")

    clientsocket.send(bytes("Enter username: |END|", "utf-8"))
    time.sleep(0.1)

    while not username[thread_point]:
        username[thread_point] = clientsocket.recv(5096)
        username[thread_point] = username[thread_point].decode("utf-8").rstrip()
        print(f"Recived signup input from {address}, checking db...")

        if verify_username_availability(username[thread_point]):
            reset_user_pass_fields(thread_point)
            clientsocket.send(bytes("Username is taken... Try again |END|\n","utf-8"))
            time.sleep(0.1)

    print(f"Recived user from {address}, waiting for pw")
    clientsocket.send(bytes("Enter password: |END|", "utf-8"))
    time.sleep(0.1)

    while not password[thread_point]:
        password[thread_point] = clientsocket.recv(5096)
        password[thread_point] = password[thread_point].decode("utf-8").rstrip()
    
    clientsocket.sendall(bytes("User and password okay, generating key...\n\nRedirecting to login","utf-8"))
    print("username: {} || password: {}".format(username[thread_point].rstrip(), password[thread_point].rstrip()))
    

    print("sending user info to db...")
    db.add_user(username[thread_point], password[thread_point], key)
    reset_user_pass_fields(thread_point)


'''
This will guide users through the login process. The information entered by
the user will be checked by the DataBase. If credentials match, users are
granted access to the other functions of the application
'''
def login(clientsocket, address, thread_num):
    thread_point = thread_num % 5
    time.sleep(0.1)

    info_fetch(clientsocket, address,thread_point)

    if  not verify_account_active(username[thread_point].rstrip()):
        print(f"Authentication failed for {username}, account not active")
        clientsocket.send(bytes("\nUnable to sign in, user is no longer active\n","utf-8"))
        time.sleep(0.1)
        username[thread_point] = ''
        return False

    elif verify_password(username[thread_point].rstrip(),password[thread_point].rstrip()):
        clientsocket.send(bytes("Welcome to the server! |AUTHENTICATED|\n", "utf-8"))
        time.sleep(0.1)
        #get key from db here
        key = 1
        clientsocket.send(bytes("{} {}".format(username[thread_point], key),"utf-8"))
        return True

    else:
        print(f"Authentication failed for {address}")
        clientsocket.send(bytes("Incorrect password, type 'exit' to quit or any key to continue|END|\n","utf-8"))
        time.sleep(0.1)
        password[thread_point] = ''
        temp = clientsocket.recv(5096).decode("utf-8").rstrip()
        if temp == 'exit':
            reset_user_pass_fields(thread_point)
            return False
        

        for i in range (3):
            password_fetch(clientsocket, thread_point, i)
            if verify_password(username[thread_point].rstrip(),password[thread_point].rstrip()):
                clientsocket.send(bytes("Welcome to the server! |AUTHENTICATED|\n", "utf-8"))
                time.sleep(0.1)
                key = 1
                clientsocket.send(bytes("{} {}".format(username[thread_point], key),"utf-8"))
                ret_uid = username[thread_point]
                reset_user_pass_fields(thread_point)
                return True
            else:
                password[thread_point] = ''
            
        reset_user_pass_fields(thread_point)
        return False

    #the follow code should not execute, if it does something went wrong
    print("thread {} stoppping".format(thread_num))
    clientsocket.close()

'''
This section detects options requested by a client. It includes deleting an account,
handling messages and checking validity of input from users.
The default is handling messages, when users are sending messages to their chat partners.
'''
def client_options(clientsocket, address, uid, num):
    time.sleep(0.1)
    clientsocket.send(bytes("Entering Option Menu...\n |OPTION|", "utf-8"))
    update_loop_flag = True
    while True:
        msg = clientsocket.recv(5096)

        if '|TERMINATE|' in msg.decode("utf-8"):
            break

        if '|DELETE ACCOUNT|' in msg.decode("utf-8"):
            delete_account(uid)
            break

        if '|CONFIRM|' in msg.decode("utf-8"):
            confirm_name = clientsocket.recv(5096).decode("utf-8").rstrip()
            if verify_username_availability (confirm_name.rstrip()):
                clientsocket.send(bytes("1","utf-8"))
            else:
                clientsocket.send(bytes("0","utf-8"))
            continue

        if '|HISTORY|' in msg.decode("utf-8"):
            history_log = fetch_history(uid)
            # sorts history_log by timestamp
            history_log.sort(key=itemgetter("timestamp"))
            # save message objects as string formated Sender | message | recipient
            for log in history_log:
                image_count = 1
                sender = log.get('sender')
                message = log.get('message')
                recipient = log.get('user_name')
                is_image = log.get('is_image')
                message_string = f"{sender}|{message}|{recipient}|{is_image}"
                clientsocket.send(bytes(message_string, "utf-8"))
            
            clientsocket.send(bytes("|END|", "utf-8"))

            # ----------------->
            msg_to_delete = clientsocket.recv(5096).decode("utf-8")
            d_sender, d_msg, d_reciver = msg_to_delete.split("|")
            db.delete_message(d_sender, d_msg, d_reciver)
            # ---------------->


            clientsocket.send(bytes("|END|", "utf-8"))

        if '|UPDATE|' in msg.decode("utf-8"):
            temp_msg = clientsocket.recv(5096)
            if '|OFF|' in temp_msg.decode("utf-8"):
                update_loop_flag = False
                continue
            sender, ts, chat_partner = temp_msg.decode("utf-8").split("|")
            message_list = update_client(sender, ts, chat_partner)
            print(f"{sender} has send update request at time:{ts}.\n")

            #check here if message_list is empty or not, send client true or false
            for m in message_list:
                if m.get('is_image'):
                    encoded_img = m.get("message")
                    clientsocket.send(bytes(f"IMAGE|{encoded_img}","utf-8"))
                    time.sleep(0.05)
                else: 
                    chat_msg = m.get('message')
                    incomming_msg = f"From: {chat_partner}\n> {chat_msg}"
                    clientsocket.send(bytes(incomming_msg,"utf-8"))
                    time.sleep(0.05)

            clientsocket.send(bytes("|END|","utf-8"))
            time.sleep(0.1)
            if not update_loop_flag:
                clientsocket.send(bytes("|OFF|","utf-8"))
                update_loop_flag = True
                time.sleep(0.05)
            continue

        if '|IMAGE|' in msg.decode("utf-8"):
            img = clientsocket.recv(5096)
            time.sleep(0.1)
            msg = clientsocket.recv(5096)
            time.sleep(5)
            recipient , new_uid = msg.decode("utf-8").split("|")
            print(f"Packaging message for {uid} to send to DB")
            time_stamp = datetime.datetime.now()
            ts_string = time_stamp.strftime("%Y%m%d%H%M%S") 
            package_and_store_message(recipient.rstrip(), img, ts_string.rstrip(), new_uid.rstrip(), "1")
            continue
        else:    
            recipient , new_uid , new_msg = msg.decode("utf-8").split("|")
            print(f"Packaging message for {uid} to send to DB")
            time_stamp = datetime.datetime.now()
            ts_string = time_stamp.strftime("%Y%m%d%H%M%S") 
            package_and_store_message(recipient, new_msg, ts_string.rstrip(), new_uid, "0")

'''
The continuation of the default option from client_options. This will pack a message into
the appropriate format accepted by the DataBase.
'''
def package_and_store_message(recipient , msg, timestamp, uid, img_flag):
    print("Packaging message for {} and sending to {}".format(uid, recipient))
    package = {'user_name':recipient, 'message':msg, 'timestamp':timestamp, 'sender':uid, 'is_image': img_flag}
    send_message(recipient, package) 

'''
When two clients are connected and sending messages to eachother, this will
update the user when a message is sent from the other user
'''
def update_client(recipient, timestamp, sender):

    updated_message_list = db.get_message_update(recipient, timestamp, sender)

    return(updated_message_list)


'''
When a user wishes to view their history, the server will retrieve and send back all
messages related to the user. This is also used when a client is trying to delete their history
'''
def fetch_history(uid):
    #decrypt here as well
    messages = db.get_messages(uid)
    return (messages)

#Joey's DB section
'''
The following functions handle the interaction between server and Database
'''
def verify_password(user_name, password):
    correct_password = db.check_password(user_name, password)
    if correct_password:
        print(f"Password verified for user: {user_name}")
        return True
    else: print(f"User: {user_name} entered incorrect password")


def verify_username_availability(user_name):
    user_exists = db.check_username(user_name)
    if user_exists:
        print("Username matched")
        return True
    else: print("Username available")


def verify_account_active(user_name):
    is_deleted = db.check_deleted(user_name)
    if is_deleted:
        return False
    else: return True
    

def delete_account(user_name):
    db.remove_user(user_name)
    account_deleated = db.check_deleted(user_name)
    if account_deleated:
        print(f"User: {user_name} has been succesfully deleted")
    else: print("Error deleting user: {user_name}")


def send_message(recipient , package):
    account_deleated = db.check_deleted(recipient)
    if account_deleated:
        print(f"Failed to find {recipient} in DB to send message to")
        #maybe send message to client failed to send message
        return
    db.add_message(package)

#Server startup
print("Booting up server...\n")
Sever_thread('localhost', 1234).listen()