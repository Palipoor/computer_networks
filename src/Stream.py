from src.tools.simpletcp.tcpserver import TCPServer
from src.tools.Node import Node
import threading


class Stream:

	def __init__(self, ip, port):
		"""
		The Stream object constructor.

		Code design suggestion:
			1. Make a separate Thread for your TCPServer and start immediately.


		:param ip: 15 characters
		:param port: 5 characters
		"""

		ip = Node.parse_ip(ip)
		port = Node.parse_port(port)
		self.nodes = {}

		self._server_in_buf = []

		def callback(address, queue, data):
			"""
			The callback function will run when a new data received from server_buffer.

			:param address: Source address.
			:param queue: Response queue.
			:param data: The data received from the socket.
			:return:
			"""
			queue.put(bytes('ACK', 'utf8'))
			self._server_in_buf.append(data)

		self.tcp_server = TCPServer(ip, int(port), read_callback=callback)
		t = threading.Thread(target=self.tcp_server.run)
		t.start()

	def get_server_address(self):
		"""

		:return: Our TCPServer address
		:rtype: tuple
		"""
		return self.tcp_server.ip, self.tcp_server.port

	def clear_in_buff(self):
		"""
		Discard any data in TCPServer input buffer.

		:return:
		"""
		self._server_in_buf.clear()

	def add_node(self, server_address, set_register_connection=False):
		"""
		Will add new a node to our Stream.

		:param server_address: New node TCPServer address.
		:param set_register_connection: Shows that is this connection a register_connection or not.

		:type server_address: tuple
		:type set_register_connection: bool

		:return:
		"""
		try:
			self.nodes[server_address] = Node(server_address, set_register=set_register_connection)
			return self.nodes[server_address]
		except:
			return None

	def remove_node(self, node):
		"""
		Remove the node from our Stream.

		Warnings:
			1. Close the node after deletion.

		:param node: The node we want to remove.
		:type node: Node

		:return:
		"""
		node.close()
		address = (node.server_ip, node.server_port)
		self.nodes.pop(address)

	def add_message_to_out_buff(self, address, message):
		"""
		In this function, we will add the message to the output buffer of the node that has the input address.
		Later we should use send_out_buf_messages to send these buffers into their sockets.

		:param address: Node address that we want to send the message
		:param message: Message we want to send

		Warnings:
			1. Check whether the node address is in our nodes or not.

		:return:
		"""
		try:
			self.nodes[address].add_message_to_out_buff(message)
			print(
				f'Add message with type = {message.type} from  {message.get_source_server_address()}  to  {address} out buffer.')
		except Exception as e:
			# desired_trace = traceback.format_exc(sys.exc_info())
			print('Problem with sending message!' + message.body)


	def read_in_buf(self):
		"""
		Only returns the input buffer of our TCPServer.

		:return: TCPServer input buffer.
		:rtype: list
		"""
		return self._server_in_buf

	def send_messages_to_node(self, node):
		"""
		Send buffered messages to the 'node'

		Warnings:
			1. Insert an exception handler here; Maybe the node socket you want to send the message has turned off and
			you need to remove this node from stream nodes.

		:param node:
		:type node Node

		:return:
		"""

		try:
			node.send_message()
		except Exception as e:
			raise e

	def send_out_buf_messages(self, only_register=False):
		"""
		In this function, we will send hole out buffers to their own clients.

		:return:
		"""
		nodes_to_be_removed = []
		for node in self.nodes.values():

			if only_register:
				if node.register:
					try:
						self.send_messages_to_node(node)
					except:
						print('could not send to ' + str(node.get_server_address()))
						nodes_to_be_removed.append(node)

			else:
				try:
					self.send_messages_to_node(node)
				except:
					print('could not send to ' + str(node.get_server_address()))
					nodes_to_be_removed.append(node)

		for node in nodes_to_be_removed:
			self.nodes.pop(node.get_server_address())

		return [n.get_server_address() for n in nodes_to_be_removed]
