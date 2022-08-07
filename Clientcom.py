import queue
import socket
import threading
from KeyComm import RSACipher, AESCipher


class ClientComm:
    """
    class to represent client communication
    """
    def __init__(self, server_ip, port, msg_q):
        """
        Initializes the client communication object
        :param server_ip: Server's ip
        :param port: Port of communication
        :param msg_q: Queue of received messages
        """
        self.socket = None  # Socket for communication
        self.server_ip = server_ip
        self.port = port
        self.msg_q = msg_q
        self.connected = False  # Changes to None when disconnected and True when connected

        # Ciphers
        self.AES_cipher = None
        self.RSA_cipher = RSACipher()

        # Starting the main loop (receiving and key trade) thread
        self.thread = threading.Thread(target=self._main_loop, daemon=True)
        self.thread.start()

    def _main_loop(self):
        """
        Connects to server, trades keys for encryption and then gets in a receiving loop
        """

        self.socket = socket.socket()  # Creating socket object

        # Attempting to connect to server
        try:
            self.socket.connect((self.server_ip, self.port))
        except Exception as e:
            print("clientComm - _main_loop", str(e))
            self.connected = None
            exit()
        else:

            # == Trading keys process before continuing ==
            public_key = self.RSA_cipher.key.publickey().exportKey()
            # Sending client public key to server (Length is always 271 bytes)
            try:
                self.socket.send(public_key)
            except Exception as e:
                self.connected = None
                print("clientComm - _main_loop, key trading", str(e))
                exit()

            # Getting back encrypted AES key (length is always 172 bytes)
            try:
                enc_key = self.socket.recv(172)
            except Exception as e:
                print("clientComm - _main_loop, key trading", str(e))
                self._disconnect()
            # Decoding AES key and creating aes object
            self.AES_cipher = AESCipher(self.RSA_cipher.decrypt(enc_key))

            # === Main receiving loop ===
            self.connected = True
            while True:
                data = ""
                try:
                    data_len = self.socket.recv(2).decode()  # Receiving 2 bits of data
                    data = self.socket.recv(int(data_len)).decode()  # Receiving actual message
                except Exception as e:  # If communication was faulty
                    print("clientComm - _main_loop", str(e))
                    self._disconnect()
                # If data is a special receive encrypted command
                if data == "!ENC":
                    # The next message is encrypted
                    try:
                        data_len = self.socket.recv(3).decode()  # Encrypted message have a lengths of 3 bits
                        data = self.socket.recv(int(data_len))   # Receiving encrypted message
                        data = self.AES_cipher.decrypt(data).decode()  # Decrypting message
                    except Exception as e:
                        print("clientComm - _main_loop, encryption recv", str(e))
                        self._disconnect()
                self.msg_q.put(data)  # Putting message into queue for processing in the main client program

    def send(self, msg: str):
        """
        sends message to server
        :param msg: Message to send (String)
        """
        msg = msg.encode()  # Encoding message into bytes
        msg_len = str(len(msg)).zfill(2).encode()  # Calculating message length
        try:
            # Trying to send message to server
            self.socket.send(msg_len)
            self.socket.send(msg)
        except Exception as e:
            print("clientComm - send", str(e))
            self._disconnect()

    def _disconnect(self):
        """
        Internal method to disconnect from server
        """
        self.connected = None
        exit()
