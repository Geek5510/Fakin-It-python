import select
import socket
import threading
from Player import Player
from KeyComm import RSA_encrypt, gen_AES_key, AESCipher


class ServerComm:
    """
    class to represent server communication
    """
    def __init__(self, server_port, msg_q):
        """
        Initializes the client communication object
        :param server_port: port that server will run on
        :param msg_q: Queue that server will put all received messages into
        """
        self.socket = None              # Server socket
        self.port = server_port         # Server port
        self.msg_q = msg_q              # Received messages queue
        self.is_in_progress = False     # Is the game in progress
        self.has_disconnect = False     # Updates when approved client disconnects
        self.open_clients = {}          # Open client sockets --> player object relating to them
        self.waiting_for_key = {}       # Sockets waiting for key trading --> ip
        self.waiting_for_name = {}      # sockets waiting for name verification --> ip and AES key
        self.AES_cipher = AESCipher(0)  # AES Cipher object
        threading.Thread(target=self._main_loop).start()  # Starting the main receiving thread

    def _main_loop(self):
        """
        Initializes the server and runs a receiving loop also responsible for key trading and username approval
        """

        self.socket = socket.socket()  # Creating server socket
        self.socket.bind(("0.0.0.0", self.port))  # Binding to port
        self.socket.listen(3)

        # === Main loop ===
        while True:
            # Using select to know when clients send a message
            rlist, wlist, xlist = select.select([self.socket] + list(self.open_clients.keys()) +
                                                list(self.waiting_for_name.keys()) + list(self.waiting_for_key.keys()),
                                                list(self.open_clients.keys()) + list(self.waiting_for_name.keys()) +
                                                list(self.waiting_for_key.keys()), [])

            # Iterating though the rlist - list of sockets that have sent the server a message
            for current_socket in rlist:
                # If it's the server socket then a new client is trying to connect
                if current_socket is self.socket:
                    # Accepting new client
                    (new_client, addr) = self.socket.accept()
                    print(f"{addr[0]} - connected")
                    # Adding the new client into the waiting for key dictionary
                    self.waiting_for_key[new_client] = addr[0]

                # If the socket that sent a message is in the key trading process
                elif current_socket in self.waiting_for_key.keys():
                    # == Trading keys with client ==
                    # Getting RSA public key from client (length is always 271 bytes)
                    try:
                        client_public_key = current_socket.recv(271)
                    except Exception as e:
                        self._handle_disconnect_client(current_socket)
                    else:
                        AES_key = gen_AES_key()
                        # Encrypting the key using the client's public key
                        enc_key = RSA_encrypt(AES_key, client_public_key)
                        # Sending encrypted key to client (length is always 172 bytes)
                        try:
                            current_socket.send(enc_key)
                        except Exception as e:
                            self._handle_disconnect_client(current_socket)
                        else:
                            # Moving client to next dictionary - waiting for username approval
                            self.waiting_for_name[current_socket] = (self.waiting_for_key[current_socket], AES_key)
                            del self.waiting_for_key[current_socket]

                # If the socket is waiting for username approval
                elif current_socket in self.waiting_for_name.keys():
                    # === Username approval process ===
                    msg = self._receive_msg(current_socket)
                    if msg is not None and msg[0] == 'U':  # If msg is not None (meaning client has disconnected)
                        msg = msg[1:]
                        if not self.is_in_progress:
                            # Checking if username is taken
                            taken = False
                            for player in list(self.open_clients.values()):
                                if player.username == msg:
                                    taken = True
                                    break
                            if taken:
                                self.send_one("NUsername is already taken, please choose another", current_socket)
                            else:
                                # Username is valid
                                self.send_one("Y", current_socket)  # Approving username
                                # Moving client to open clients dictionary and creating player object for them
                                self.open_clients[current_socket] = Player(self.waiting_for_name[current_socket][0],
                                                                           self.waiting_for_name[current_socket][1], msg)
                                # Erasing from waiting for name dictionary
                                del self.waiting_for_name[current_socket]

                                # Updating everyone on the new player
                                player_list = self._format_player_list()
                                self.send_all(player_list)
                        else:
                            # Game is already in progress
                            self.send_one("NGame is already in progress", current_socket)

                    else:
                        self._handle_disconnect_client(current_socket)

                # Client is in open clients
                else:
                    try:
                        data_len = int(current_socket.recv(2).decode())  # Receiving two bytes of length
                        data = current_socket.recv(data_len).decode()    # Receiving data
                    except Exception as e:
                        print("ServerComm - main_loop", str(e))
                        self._handle_disconnect_client(current_socket)
                    else:
                        # If the client has disconnected
                        if data == "":
                            self._handle_disconnect_client(current_socket)
                        else:
                            # Putting the message into the message queue
                            self.msg_q.put((current_socket, data))

    def _handle_disconnect_client(self, socket_to_disconnect: socket.socket):
        """
        Handles disconnection of client
        """
        if socket_to_disconnect in self.open_clients.keys():
            ip = self.open_clients[socket_to_disconnect].ip
            print(f"{ip} - disconnected")
            del self.open_clients[socket_to_disconnect]

            # Updating all clients on updated player list
            player_list = self._format_player_list()
            self.send_all_exl(player_list, socket_to_disconnect)

            self.has_disconnect = True

        elif socket_to_disconnect in self.waiting_for_name.keys():
            ip = self.waiting_for_name[socket_to_disconnect][0]
            print(f"{ip} - disconnected")
            del self.waiting_for_name[socket_to_disconnect]

        elif socket_to_disconnect in self.waiting_for_key.keys():
            ip = self.waiting_for_key[socket_to_disconnect]
            print(f"{ip} - disconnected")
            del self.waiting_for_key[socket_to_disconnect]

        socket_to_disconnect.close()

    def send_all_exl(self, data, exclude):
        """
        sends message to all approved sockets but one
        :param data: message to send
        :param exclude: Socket to not send to
        """
        if type(data) == str:
            data = data.encode()
        len_msg = str(len(data)).zfill(2).encode()

        # Iterating over all approved sockets
        for sock in self.open_clients.keys():
            if sock is not exclude:  # If the socket is not the excluded one
                try:
                    # Sending the message length and the message itself
                    sock.send(len_msg)
                    sock.send(data)
                except socket.error:
                    self._handle_disconnect_client(sock)

    def send_all(self, data):
        """
        Sends message to all
        :param data:  message to send
        """
        if type(data) == str:
            data = data.encode()
        len_msg = str(len(data)).zfill(2).encode()
        # Iterating though all open sockets
        for sock in self.open_clients.keys():
            try:
                # Sending the message length and the message itself
                sock.send(len_msg)
                sock.send(data)
            except socket.error:
                self._handle_disconnect_client(sock)

    def send_one(self, data, target):
        """
        sends message to one client
        :param data:  message to send
        :param target: Socket to send to
        """
        if type(data) == str:
            data = data.encode()
        len_msg = str(len(data)).zfill(2).encode()
        # Making sure target is connected to server
        if target in self.open_clients.keys() or target in self.waiting_for_name.keys():
            try:
                # Sending the message length and the message itself
                target.send(len_msg)
                target.send(data)
            except socket.error:
                self._handle_disconnect_client(target)

    def send_one_encrypted(self, data, target):
        """
        sends encrypted message to one client, can only send to sockets in open_clients
        :param data: message to send, must be a string
        :param target:
        :return:
        """
        if target in self.open_clients.keys():
            self.AES_cipher.key = self.open_clients[target].key  # Setting the encryption to be the client's key
            enc_data = self.AES_cipher.encrypt(data)
            len_msg = str(len(enc_data)).zfill(3).encode()
            try:
                target.send("04!ENC".encode())  # Sending encryption heads up
                # Sending the message length and the encrypted message itself
                target.send(len_msg)
                target.send(enc_data)
            except socket.error:
                self._handle_disconnect_client(target)

    def send_all_exl_encrypted(self, data, exclude):
        """
        sends encrypted message to all but one, can only send to sockets in open_clients
        :param data: message to send, must be a string
        :param exclude: Ip to not send to
        """

        for sock in self.open_clients.keys():
            if sock is not exclude:
                self.AES_cipher.key = self.open_clients[sock].key  # Setting the encryption to be the client's key
                enc_data = self.AES_cipher.encrypt(data)  # Encrypting the data
                len_msg = str(len(enc_data)).zfill(3).encode()  # Calculating the encrypted message's length
                try:
                    sock.send("04!ENC".encode())  # Sending encryption heads up
                    # Sending the message length and the encrypted message itself
                    sock.send(len_msg)
                    sock.send(enc_data)
                except socket.error:
                    self._handle_disconnect_client(sock)

    def username_to_socket(self, username):
        """
        Gets username and returns matching socket, returns None if there isn't such a socket
        :param username: Username to search for
        :return: Socket with according username
        """
        rtr = None
        for sock in self.open_clients.keys():
            if self.open_clients[sock].username == username:
                rtr = sock
                break
        return rtr

    def _format_player_list(self):
        """
        Returns formatted player list to send to all clients
        """
        # Making player list
        player_list = "L"
        for connected_player in list(self.open_clients.values()):
            player_list += connected_player.username + "&"
        player_list = player_list[:-1]  # Removing last &
        return player_list

    def _receive_msg(self, client_sock):
        """
        Receives message with 2 digits of length, Returns None if receiving failed
        :param client_sock: socket to receive from
        :return: Message from given socket or None if receiving failed
        """
        try:
            # Receiving length then message by length
            msg_len = client_sock.recv(2).decode()
            msg = client_sock.recv(int(msg_len)).decode()
        except socket.error or ValueError:
            self._handle_disconnect_client(client_sock)
            msg = None
        return msg
