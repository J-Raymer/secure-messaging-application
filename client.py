#from: https://pythonprogramming.net/sockets-tutorial-python-3/
import socket
import select
import sys
import threading
import time
import datetime
import io
from PIL import Image
import encryption as encrypt
from cryptography.fernet import Fernet
#External lib crypto  and Pillow must be installed inorder for this to work.

#Encryption: Lydu
#DB related: Joey
#Client functionality: Aaron

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 1234))
full_msg = ''
uid = ''
private_key = ''

encryption_key = ''

mac_key = ''
public_key = ''
#need to store key with message?

print("Waiting for server...\n")

'''
This is where clients can send messages to another user. Users are expected
to know their chatting partner's name, like knowing a friend's phone number
The server will check if the name is valid and continue if it is. Options 
are given to the user to send pictures or return to main menu
All messages are encrypter before sending.
'''
def chat_mode():
	print("\n> Welcome to chat mode.")
	confirm_name = ''
	recipient = ''
	msg = ''

	while True:
		recipient = input("\n> Please enter who you wish to send message to.\n> ").rstrip()
		confirm_name = input("\n> Is {} correct? y/n\n> ".format(recipient)).rstrip()
		if confirm_name != 'n' and confirm_name != 'y':
			print("> Incorrect input.\n")
		if confirm_name == 'y':
			s.send(bytes("|CONFIRM|","utf-8"))
			time.sleep(0.1)
			s.send(bytes(recipient,"utf-8"))
			valid_name_check = s.recv(5096).decode("utf-8")
			if valid_name_check.rstrip() == '0':
				print(f"\n> Could not Find User of name: {recipient}")
				recipient = ''
				confirm_name = 'n'
				continue
			break

	message_To_From = "{}|{}|".format(recipient, uid)

	print("\n> Please type /sendpic when you wish to send picutres or /return to return to main menu.")
	print("> ====		Chat Box		====\n")
	
	update_thread = threading.Thread(target=update_mode, args=(recipient, uid,))
	update_thread.start()

	send_to_server = ''
	while msg != '/return':
		msg = input("> ")
		if msg == '/sendpic':
			send_pic(recipient, uid)
			continue
		if msg == '/return':
			break
		else:
			send_to_server = message_To_From + msg
			s.send(bytes(send_to_server, "utf-8"))
			time.sleep(0.1)
			send_to_server = ''
		send_to_server = ''
	
	s.send(bytes("|UPDATE|","utf-8"))
	time.sleep(0.1)
	s.send(bytes("|OFF|","utf-8"))
	time.sleep(0.1)
	update_thread.join()

'''
Every couple seconds, the client will send a request to the server to update themselves 
for any new messages coming from their chatting partner, if they are also logged in.
This is also the place where users can send images. Images must be in the same file.
When recieving an image from chatting partner, it will open up after a short delay
'''
def update_mode(recipient, uid):
	#implement forward secrecy here, need to know recipient and user

	time_stamp = datetime.datetime.now()
	ts_string = time_stamp.strftime("%Y%m%d%H%M%S")
	update_loop = True
	while True:
		s.send(bytes("|UPDATE|","utf-8"))
		time.sleep(0.1)
		s.send(bytes(f"{uid}|{ts_string.rstrip()}|{recipient}","utf-8"))
		while True:
			msg = s.recv(5096).decode("utf-8").rstrip()
			#if msg: DB should send a flag if messages were sent since last update
			#only update timestamp when messages are printed
			if '|END|' in msg:
				break
			if '|OFF|' in msg:
				update_loop = False
				break
			if 'IMAGE|' in msg:
				print(f"{recipient} has sent you an image... Opening\n")
				encoded_image = msg.split("|")[1]
				continue
			else:
				print(msg)
				time_stamp = datetime.datetime.now()
				ts_string = time_stamp.strftime("%Y%m%d%H%M%S")

		if not update_loop:
			break
		time.sleep(5)

		#don't print past histories'

'''
When called, this will display all the messages the user has. It also allows
a user to delete a message the user has previously sent. User must select correct
message ID and relay that to the server. All messages are decrypted after being
recieved
'''
def history_and_delete_mode():
	print("\n> Fetching history...")
	msg_arr = []
	s.send(bytes("|HISTORY|", "utf-8"))

	print("ID | Sender | message | recipient")
	id = 1
	img_count = 1
	while True:
		msg = s.recv(2048).decode("utf-8")
		# print(f"msg here ---> {msg}")
		if "|END|" in msg:
			#go into del.
			break
		else:
			#remember to unencrpyt message
			sender, message, receiver, is_image = msg.split("|")
			log = {'sender': sender, 'message': message, 'receiver': receiver, 'msg_id': id, 'is_image': is_image}
			msg_arr.append(log)
			# if is_image:
			# 	print(f"{id} | {sender} | IMAGE{img_count} | {receiver}")
			# 	img_count += 1
			# else:
			print(f"{id} | {sender} | {message} |{receiver}")
			id += 1
	while True:
		#starting here
		msg = input("\n> Would you like to delete a sent message? y/n\n> ")
		# print(f"msg: {msg}")
		time.sleep(0.025)
		msg_id = -1
		
		if msg == 'y':
			msg_id = input("\n> To delete a message, please enter message ID\n> ")
			msg_id = int(msg_id)
		if msg == 'n':
			break
		# else:
		# 	print("\n> Invalid Input")
		
		if msg_id > 0 and msg_id <= id:
			for l in msg_arr:
				# print(l)
				if l.get('msg_id') == msg_id:
				
					d_sender = l.get('sender')
					d_msg = l.get('message')
					d_receiver = l.get('receiver')

					# print(d_sender, d_msg, d_receiver)
					message_to_delete = f"{d_sender}|{d_msg}|{d_receiver}"
					s.send(bytes(message_to_delete,"utf-8"))
					time.sleep(0.025)
					continue
			# display history

'''
Delete a user account
'''
def delete_account():
	while True:
		msg = input("\n> Are you sure you wish to delete your account? y/n\n> ")
		if msg == 'y':
			is_deleted = ''
			print("\n> Deleting Account...")
			s.send(bytes("|DELETE ACCOUNT|", "utf-8"))
			time.sleep(3)
			print("\n> Account deleted... Closing application\n")
			time.sleep(3)
			break
		elif msg == 'n':
			break
		else:
			print("\n> Incorrect input...")

'''
This encodes a picture to be sent to chatting partner
'''
def send_pic(recipient, uid):
	img_name = input("\n> Please enter image name including .jpg or .png...\n> ")
	try:
		raw_img = Image.open(img_name)
		raw_img.resized = raw_img.resize((500,500))
		imgbuffer = io.BytesIO()
		if '.png' in img_name:
			raw_img.save(imgbuffer, format='png')
		else:
			raw_img.save(imgbuffer, format='jpg')
		byte_img = imgbuffer.getvalue()
	except OSError:
		print("Could not find file, returning to Chat Box\n> ")
		return
	time.sleep(0.1)
	print("> ==== Sending Image ====\n> ")
	s.send(bytes("|IMAGE|","utf-8"))
	time.sleep(0.05)
	s.send(byte_img)
	time.sleep(0.05)
	s.send(bytes(f"{recipient}|{uid}", "utf-8"))
	time.sleep(0.05)

'''
This section is to detect user options and direct them to the right place
as well as set variables to the client whilst they're logged in
'''
def read_mode(message):
	if '|END|' in message:
		return message.replace('|END|', ''), False
	if '|OPTION|' in message:
		print(message.replace('|OPTION|', ''))
		option_mode()
		exit(0)
	if '|AUTHENTICATED|' in message:
		global uid
		global key
		print(message.replace('|AUTHENTICATED|', ''))
		get_uid_key = s.recv(5096).decode("utf-8")
		uid, key = get_uid_key.split(" ", 1)
		return "", True
	else:
		return message, True

'''
This gives options in which the user can select from.
'''
def option_mode():
	print("Welcome to the option menu. Please select the number assosiated with the options provided.")
	while True:
		detect_option = input(">Chatmode: 1; History or Remove Message 2; Delete Account 3; Exit 4\n>")
		if detect_option.rstrip() == '1':
			chat_mode()
		if detect_option.rstrip() == '2':
			history_and_delete_mode()
		if detect_option.rstrip() == '3':
			delete_account()
			break
		if detect_option.rstrip() == '4':
			s.send(bytes("|TERMINATE|", "utf-8"))
			print("Shutting down client...")
			time.sleep(2)
			s.close
			break
		else:
			pass

'''
On startup, this will guide the user through either login or signup as well as
handle all general input from user
'''
message = ''
while message != 'exit()':
	read_in = True
	while read_in:
		message, read_in = read_mode(s.recv(5096).decode("utf-8"))
		print(message)
	message = input("> ")
	while not message:
		message = input("> ")
	s.send(bytes(message, "utf-8"))


s.close()
exit(0)