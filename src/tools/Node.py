from src.tools.simpletcp.clientsocket import ClientSocket


class Node:
	def __init__(self, server_address, set_register=False):
		"""
		The Node object constructor.

		This object is our low-level abstraction for other peers in the network.
		Every node has a ClientSocket that should bind to the Node TCPServer address.

		Warnings:
			1. Insert an exception handler when initializing the ClientSocket;
			when a socket is closed here we will face
			   an exception and we should detach this Node and clear its output buffer.

		:param server_address:
		:param set_root:
		:param set_register:
		"""
		self.server_ip = Node.parse_ip(server_address[0])
		self.server_port = Node.parse_port(server_address[1])
		self.register = set_register
		self.client_socket = ClientSocket(self.server_ip, int(self.server_port), single_use=False)

		self.out_buff = []

	def send_message(self):
		"""
		Final function to send buffer to the client's socket.

		:return:
		"""
		for message in self.out_buff:
			try:
				self.client_socket.send(message)
			except Exception as e:
				print("Seems like the socket is closed for " + str(self.get_server_address()))
				self.out_buff.clear()
				raise e
		self.out_buff.clear()

	def add_message_to_out_buff(self, message):
		"""
		Here we will add a new message to the server out_buff, then in 'send_message' will send them.

		:param message: The message we want to add to out_buff
		:return:
		"""
		self.out_buff.append(message.get_buf())

	def close(self):
		"""
		Closing client's object.
		:return:
		"""
		self.client_socket.close()

	def get_server_address(self):
		"""

		:return: Server address in a pretty format.
		:rtype: tuple
		"""
		return self.server_ip, self.server_port

	@staticmethod
	def parse_ip(ip):
		"""
		Automatically change the input IP format like '192.168.001.001'.
		:param ip: Input IP
		:type ip: str

		:return: Formatted IP
		:rtype: str
		"""
		return '.'.join(str(int(part)).zfill(3) for part in ip.split('.'))

	@staticmethod
	def parse_port(port):
		"""
		Automatically change the input IP format like '05335'.
		:param port: Input IP
		:type port: str

		:return: Formatted IP
		:rtype: str
		"""
		return str(int(port)).zfill(5)
