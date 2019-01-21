from src.Stream import Stream
from src.Packet import Packet, PacketFactory, PacketType
from src.UserInterface import UserInterface
from src.tools.NetworkGraph import NetworkGraph, GraphNode
import time
import threading

"""
	Peer is our main object in this project.
	In this network Peers will connect together to make a tree graph.
	This network is not completely decentralised but will show you some real-world challenges in Peer to Peer networks.
	
"""


class Peer:
	def __init__(self, server_ip, server_port, is_root=False, root_address=None):
		"""
		The Peer object constructor.

		Code design suggestions:
			1. Initialise a Stream object for our Peer. --- done
			2. Initialise a PacketFactory object. ----- done
			3. Initialise our UserInterface for interaction with user commandline. ----- done
			4. Initialise a Thread for handling reunion daemon. ------- done

		Warnings:
			1. For root Peer, we need a NetworkGraph object. ----- done
			2. In root Peer, start reunion daemon as soon as possible. ------ done
			3. In client Peer, we need to connect to the root of the network, Don't forget to set this connection
			   as a register_connection. ------ done


		:param server_ip: Server IP address for this Peer that should be pass to Stream.
		:param server_port: Server Port address for this Peer that should be pass to Stream.
		:param is_root: Specify that is this Peer root or not.
		:param root_address: Root IP/Port address if we are a client.

		:type server_ip: str
		:type server_port: int
		:type is_root: bool
		:type root_address: tuple
		"""
		if root_address:
			root_address = (root_address[0], str(root_address[1]))
		server_port = str(server_port)
		self.is_root = is_root
		self.is_client_connected = False
		self.client_predecessor_address = tuple()
		self.successors_address = []
		self.client_is_waiting_for_helloback = False
		self.register_node = None
		self.client_reunion_timeout = False
		self.client_timeout_threshold = 20
		self.root_timeout_threshold = 20
		self.client_last_hello_time = 0
		self.nodes_for_root = {}  # {(address) : last_time_hello_came}
		self.address = (server_ip, server_port)
		self.stream = Stream(server_ip, server_port)
		self.user_interface = UserInterface()

		if self.is_root:
			graph_node_root = GraphNode(self.address)
			self.network_graph = NetworkGraph(graph_node_root)
			reunion_thread = threading.Thread(target=self.run_reunion_daemon)
			reunion_thread.start()
		else:
			self.root_address = root_address
			print("Set root address! " + str(self.root_address))
			self.stream.add_node(self.root_address, True)

	def start_user_interface(self):
		"""
		For starting UserInterface thread.

		:return:
		"""
		print('Starting User Interface')
		self.user_interface.run()

	def handle_user_interface_buffer(self):
		"""
		In every interval, we should parse user command that buffered from our UserInterface.
		All of the valid commands are listed below:
			1. Register:  With this command, the client send a Register Request packet to the root of the network.
			2. Advertise: Send an Advertise Request to the root of the network for finding first hope.
			3. SendMessage: The following string will be added to a new Message packet and broadcast through the network.

		Warnings:
			1. Ignore irregular commands from the user.
			2. Don't forget to clear our UserInterface buffer.
		:return:
		"""
		for message in self.user_interface.buffer:
			print('handling : ' + message)
			if message == 'Register':
				reg_packet = PacketFactory.new_register_packet("REQ", self.address, self.address)
				self.send_packet(reg_packet, self.root_address)
				self.stream.send_out_buf_messages(only_register=True)
			elif message == 'Advertise':
				advertise_packet = PacketFactory.new_advertise_packet(type="REQ", source_server_address=self.address)
				self.send_advertise_packet(advertise_packet)
				self.stream.send_out_buf_messages(only_register=True)
			elif message.startswith('SendMessage'):
				to_be_sent = message.split()[1]
				message_packet = PacketFactory.new_message_packet(message=to_be_sent,
																  source_server_address=self.address)
				self.send_broadcast_packet(message_packet)
			else:
				continue

		self.user_interface.buffer.clear()

	def run(self):
		"""
		The main loop of the program.

		Code design suggestions:
			1. Parse server in_buf of the stream. ---- done
			2. Handle all packets were received from our Stream server. ---- done
			3. Parse user_interface_buffer to make message packets.  ---- done
			4. Send packets stored in nodes buffer of our Stream object. ---- done
			5. ** sleep the current thread for 2 seconds ** -------- done

		Warnings:
			1. At first check reunion daemon condition; Maybe we have a problem in this time
			   and so we should hold any actions until Reunion acceptance. ------- done
			2. In every situation checkout Advertise Response packets; even if Reunion in failure mode or not ------- done

		:return:
		"""

		while True:
			if not self.is_root:
				if self.is_client_connected:
					input_buffer = self.stream.read_in_buf()
					for buf in input_buffer:
						packet = Packet(buf)
						self.handle_packet(packet)
					self.stream.clear_in_buff()
					self.stream.send_out_buf_messages()
				else:
					input_buffer = self.stream.read_in_buf()
					for buf in input_buffer:
						packet = Packet(buf)
						if packet.type == PacketType.ADVERTISE:
							self.__handle_advertise_packet(packet)
					self.stream.clear_in_buff()
				self.handle_user_interface_buffer()
			else:
				input_buffer = self.stream.read_in_buf()
				for buf in input_buffer:
					packet = Packet(buf)
					self.handle_packet(packet)

				self.stream.clear_in_buff()
				self.handle_user_interface_buffer()
				self.stream.send_out_buf_messages()
			time.sleep(2)

	def run_reunion_daemon(self):
		"""

		In this function, we will handle all Reunion actions.

		Code design suggestions:
			1. Check if we are the network root or not; The actions are not identical.
			2. If it's the root Peer, in every interval check the latest Reunion packet arrival time from every node;
			   If time is over for the node turn it off (Maybe you need to remove it from our NetworkGraph).
			3. If it's a non-root peer split the actions by considering whether we are waiting for Reunion Hello Back
			   Packet or it's the time to send new Reunion Hello packet.

		Warnings:
			1. If we are the root of the network in the situation that we want to turn a node off, make sure that you will not
			   advertise the nodes sub-tree in our GraphNode.
			2. If we are a non-root Peer, save the time when you have sent your last Reunion Hello packet; You need this
			   time for checking whether the Reunion was failed or not.
			3. For choosing time intervals you should wait until Reunion Hello or Reunion Hello Back arrival,
			   pay attention that our NetworkGraph depth will not be bigger than 8. (Do not forget main loop sleep time)
			4. Suppose that you are a non-root Peer and Reunion was failed, In this time you should make a new Advertise
			   Request packet and send it through your register_connection to the root; Don't forget to send this packet
			   here, because in the Reunion Failure mode our main loop will not work properly and everything will be got stock!
			   --- done

		:return:
		"""
		while True:

			if self.is_root:
				now = time.time()
				to_be_deleted = []
				for peer, latest_reunion_msg in self.nodes_for_root.items():
					passed_time = now - latest_reunion_msg
					if passed_time > self.root_timeout_threshold:
						to_be_deleted.append(peer)
						self.network_graph.turn_off_node(peer)

				for peer in to_be_deleted:
					self.nodes_for_root.pop(
						peer)
					self.network_graph.remove_node(peer)
			else:
				if not self.client_is_waiting_for_helloback:
					reunion_packet = PacketFactory.new_reunion_packet("REQ", self.address, [self.address])
					self.send_broadcast_packet(broadcast_packet=reunion_packet)
					self.client_last_hello_time = time.time()
					self.client_is_waiting_for_helloback = True
				elif time.time() - self.client_last_hello_time >= self.client_timeout_threshold:
					self.client_is_waiting_for_helloback = False
					self.is_client_connected = False
					self.client_predecessor_address = None
					adv_pckt = PacketFactory.new_advertise_packet("REQ", self.address)
					self.send_advertise_packet(adv_pckt)

			time.sleep(4)

	def send_packet(self, packet, address):
		packet = self.change_header(packet)
		self.stream.add_message_to_out_buff(address, packet)

	def send_broadcast_packet(self, broadcast_packet):
		"""

		For setting broadcast packets buffer into Nodes out_buff.

		Warnings:
			1. Don't send Message packets through register_connections.

		:param broadcast_packet: The packet that should be broadcast through the network.
		:type broadcast_packet: Packet

		:return:
		"""
		broadcast_packet = self.change_header(broadcast_packet)
		print('Going to broadcast a Packet! type: ' + str(broadcast_packet.type))
		if self.is_root:
			for address in self.successors_address:
				self.stream.add_message_to_out_buff(address, broadcast_packet)
		else:
			if broadcast_packet.is_reunion_hello() and self.successors_address:
				self.stream.add_message_to_out_buff(self.successors_address, message=broadcast_packet)
			elif broadcast_packet.is_reunion_hello_back():
				for address in self.successors_address:
					self.stream.add_message_to_out_buff(address,
														broadcast_packet)
			elif broadcast_packet.type == PacketType.MESSAGE:
				all_addreses = [self.client_predecessor_address] + self.successors_address
				for address in all_addreses:
					self.stream.add_message_to_out_buff(address,
														broadcast_packet)
			else:
				return

	def handle_packet(self, packet):
		"""

		This function act as a wrapper for other handle_###_packet methods to handle the packet.

		Code design suggestion:
			1. It's better to check packet validation right now; For example Validation of the packet length.

		:param packet: The arrived packet that should be handled.

		:type packet Packet

		"""

		print('Received a packet with type : ' + str(packet.type))
		if packet.type == PacketType.REGISTER:
			self.__handle_register_packet(packet)
		elif packet.type == PacketType.MESSAGE:
			self.__handle_message_packet(packet)
		elif packet.type == PacketType.ADVERTISE:
			self.__handle_advertise_packet(packet)
		elif packet.type == PacketType.JOIN:
			self.__handle_join_packet(packet)
		elif packet.type == PacketType.REUNION:
			self.__handle_reunion_packet(packet)
		else:
			return

	def __check_registered(self, source_address):
		"""
		If the Peer is the root of the network, we need to find that is a node registered or not.

		:param source_address: Unknown IP/Port address.
		:type source_address: tuple

		:return:
		"""
		if not self.is_root:
			return False
		node = self.network_graph.find_node(source_address[0], source_address[1])
		return not node is None

	def __handle_advertise_packet(self, packet):
		"""
		For advertising peers in the network, It is peer discovery message.

		Request:
			We should act as the root of the network and reply with a neighbour address in a new Advertise Response packet.

		Response:
			When an Advertise Response packet type arrived we should update our parent peer and send a Join packet to the
			new parent.

		Code design suggestion:
			1. Start the Reunion daemon thread when the first Advertise Response packet received.
			2. When an Advertise Response message arrived, make a new Join packet immediately for the advertised address.

		Warnings:
			1. Don't forget to ignore Advertise Request packets when you are a non-root peer.
			2. The addresses which still haven't registered to the network can not request any peer discovery message.
			3. Maybe it's not the first time that the source of the packet sends Advertise Request message. This will happen
			   in rare situations like Reunion Failure. Pay attention, don't advertise the address to the packet sender
			   sub-tree.
			4. When an Advertise Response packet arrived update our Peer parent for sending Reunion Packets.

		:param packet: Arrived register packet

		:type packet Packet

		:return:
		"""
		if self.is_root:
			sender_address = packet.get_source_server_address()
			neighbour = self.__get_neighbour(sender_address)
			self.network_graph.add_node(sender_address[0], sender_address[1], neighbour.address)
			print("Someone has requested a neighbour")
			print(str(neighbour.address))
			if self.__check_registered(sender_address) and neighbour is not None:
				adv_packet = PacketFactory.new_advertise_packet("RES", self.address, neighbour=neighbour.address)
				self.send_packet(adv_packet, sender_address)
		elif packet.body.startswith('RES'):
			reunion_thread = threading.Thread(target=self.run_reunion_daemon)
			reunion_thread.start()
			join_pckt = PacketFactory.new_join_packet(self.address)
			self.client_predecessor_address = (packet.body[-20:-5], packet.body[-5:])
			print("I've found a father! " + str(self.client_predecessor_address))
			self.send_packet(join_pckt, self.client_predecessor_address)
			self.is_client_connected = True
		else:
			return

	def __handle_register_packet(self, packet):
		"""
		For registration a new node to the network at first we should make a Node with stream.add_node for'sender' and
		save it.

		Code design suggestion:
			1.For checking whether an address is registered since now or not you can use SemiNode object except Node.

		Warnings:
			1. Don't forget to ignore Register Request packets when you are a non-root peer.

		:param packet: Arrived register packet
		:type packet Packet
		:return:
		"""
		if not self.is_root:
			return
		else:
			sender = packet.get_source_server_address()
			if sender not in self.nodes_for_root:
				self.stream.add_node(sender)
				self.nodes_for_root.update({sender: time.time()})
			else:
				return

	def __handle_message_packet(self, packet):
		"""
		Only broadcast message to the other nodes.

		Warnings:
			1. Do not forget to ignore messages from unknown sources.
			2. Make sure that you are not sending a message to a register_connection.

		:param packet: Arrived message packet

		:type packet Packet

		:return:
		"""
		self.send_broadcast_packet(packet)

	def __handle_reunion_packet(self, packet):
		"""
		In this function we should handle Reunion packet was just arrived.

		Reunion Hello:
			If you are root Peer you should answer with a new Reunion Hello Back packet.
			At first extract all addresses in the packet body and append them in descending order to the new packet.
			You should send the new packet to the first address in the arrived packet.
			If you are a non-root Peer append your IP/Port address to the end of the packet and send it to your parent.

		Reunion Hello Back:
			Check that you are the end node or not; If not only remove your IP/Port address and send the packet to the next
			address, otherwise you received your response from the root and everything is fine.

		Warnings:
			1. Every time adding or removing an address from packet don't forget to update Entity Number field.
			2. If you are the root, update last Reunion Hello arrival packet from the sender node and turn it on.
			3. If you are the end node, update your Reunion mode from pending to acceptance.


		:param packet: Arrived reunion packet
		:return:
		"""
		if self.is_root:
			sender_address = packet.get_first_address_hello_packet()
			self.nodes_for_root[sender_address] = time.time()
			self.network_graph.turn_on_node(sender_address)
			self.send_helloback(packet)
		else:
			if packet.is_reunion_hello():
				packet.body += str(self.address[0]) + str(self.address[1])
				new_number_of_elements = int(packet.body[3:5]) + 1
				packet.body = 'REQ' + str(new_number_of_elements) + packet.body[5:]
				self.send_broadcast_packet(packet)
			else:
				if not self.helloback_is_mine(packet):
					packet.body = packet.body[:-20]
					new_number_of_elements = int(packet.body[3:5]) - 1
					packet.body = 'REQ' + str(new_number_of_elements) + packet.body[5:]
					self.send_broadcast_packet(packet)
				else:
					self.client_is_waiting_for_helloback = False

	def __handle_join_packet(self, packet):
		"""
		When a Join packet received we should add a new node to our nodes array.
		In reality, there is a security level that forbids joining every node to our network.

		:param packet: Arrived register packet.
		:type packet Packet

		:return:
		"""
		address = packet.get_source_server_address()
		self.successors_address.append(address)

	def __get_neighbour(self, sender):
		"""
		Finds the best neighbour for the 'sender' from the network_nodes array.
		This function only will call when you are a root peer.

		Code design suggestion:
			1. Use your NetworkGraph find_live_node to find the best neighbour.

		:param sender: Sender of the packet
		:return: The specified neighbour for the sender; The format is like ('192.168.001.001', '05335').
		"""
		return self.network_graph.find_live_node(sender)

	def send_helloback(self, packet):
		if not self.is_root:
			return
		print('Sending Hello back')
		list_of_addreses = packet.body[5:]
		new_list = []
		for substring in divide_string(list_of_addreses, int(packet.body[3:5])):
			new_list.append(substring)

		new_list_of_addreses = ''.join(new_list)

		packet.body = packet.body[:5] + new_list_of_addreses
		packet.body = 'RES' + packet.body[3:]

		self.send_broadcast_packet(packet)

	def send_advertise_packet(self, advertise_packet):
		print('Sending advertise packet!')
		advertise_packet = self.change_header(advertise_packet)
		self.send_packet(advertise_packet, self.root_address)

	def __check_neighbour(self, address):
		"""
		It checks if the address is in our neighbours array or not.

		:param address: Unknown address

		:type address: tuple

		:return: Whether is address in our neighbours or not.
		:rtype: bool
		"""
		return address == self.client_predecessor_address or address in self.successors_address

	def helloback_is_mine(self, packet):
		latest_address = (packet.body[-20:-15], packet.body[-15:])
		return latest_address == self.address

	def change_header(self, packet):
		packet.source_ip, new_source_port = self.address[0], self.address[1]
		packet = Packet(packet.get_buf())
		return packet


def divide_string(string, n):
	str_size = len(string)

	# Calculate the size of parts to find the division points
	part_size = str_size // n
	k = 0
	for i in range(n):
		yield string[k:(k + part_size)]
		k += part_size
