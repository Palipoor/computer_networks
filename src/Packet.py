"""

    This is the format of packets in our network:
    


                                                **  NEW Packet Format  **
     __________________________________________________________________________________________________________________
    |           Version(2 Bytes)         |         Type(2 Bytes)         |           Length(Long int/4 Bytes)          |
    |------------------------------------------------------------------------------------------------------------------|
    |                                            Source Server IP(8 Bytes)                                             |
    |------------------------------------------------------------------------------------------------------------------|
    |                                           Source Server Port(4 Bytes)                                            |
    |------------------------------------------------------------------------------------------------------------------|
    |                                                    ..........                                                    |
    |                                                       BODY                                                       |
    |                                                    ..........                                                    |
    |__________________________________________________________________________________________________________________|

    Version:
        For now version is 1
    
    Type:
        1: Register
        2: Advertise
        3: Join
        4: Message
        5: Reunion
                e.g: type = '2' => Advertise packet.
    Length:
        This field shows the character numbers for Body of the packet.

    Server IP/Port:
        We need this field for response packet in non-blocking mode.



    ***** For example: ******

    version = 1                 b'\x00\x01'
    type = 4                    b'\x00\x04'
    length = 12                 b'\x00\x00\x00\x0c'
    ip = '192.168.001.001'      b'\x00\xc0\x00\xa8\x00\x01\x00\x01'
    port = '65000'              b'\x00\x00\\xfd\xe8'
    Body = 'Hello World!'       b'Hello World!'

    Bytes = b'\x00\x01\x00\x04\x00\x00\x00\x0c\x00\xc0\x00\xa8\x00\x01\x00\x01\x00\x00\xfd\xe8Hello World!'




    Packet descriptions:
    
        Register:
            Request:
        
                                 ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |                  IP (15 Chars)                 |
                |------------------------------------------------|
                |                 Port (5 Chars)                 |
                |________________________________________________|
                
                For sending IP/Port of the current node to the root to ask if it can register to network or not.

            Response:
        
                                 ** Body Format **
                 _________________________________________________
                |                  RES (3 Chars)                  |
                |-------------------------------------------------|
                |                  ACK (3 Chars)                  |
                |_________________________________________________|
                
                For now only should just send an 'ACK' from the root to inform a node that it
                has been registered in the root if the 'Register Request' was successful.
                
        Advertise:
            Request:
            
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |________________________________________________|
                
                Nodes for finding the IP/Port of their neighbour peer must send this packet to the root.

            Response:

                                ** Packet Format **
                 ________________________________________________
                |                RES(3 Chars)                    |
                |------------------------------------------------|
                |              Server IP (15 Chars)              |
                |------------------------------------------------|
                |             Server Port (5 Chars)              |
                |________________________________________________|
                
                Root will response Advertise Request packet with sending IP/Port of the requester peer in this packet.
                
        Join:

                                ** Body Format **
                 ________________________________________________
                |                 JOIN (4 Chars)                 |
                |________________________________________________|
            
            New node after getting Advertise Response from root must send this packet to the specified peer
            to tell him that they should connect together; When receiving this packet we should update our
            Client Dictionary in the Stream object.


            
        Message:
                                ** Body Format **
                 ________________________________________________
                |             Message (#Length Chars)            |
                |________________________________________________|

            The message that want to broadcast to hole network. Right now this type only includes a plain text.
        
        Reunion:
            Hello:
        
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |________________________________________________|
                
                In every interval (for now 20 seconds) peers must send this message to the root.
                Every other peer that received this packet should append their (IP, port) to
                the packet and update Length.

            Hello Back:
        
                                    ** Body Format **
                 ________________________________________________
                |                  RES (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |________________________________________________|

                Root in an answer to the Reunion Hello message will send this packet to the target node.
                In this packet, all the nodes (IP, port) exist in order by path traversal to target.
            
    
"""
from struct import *

from src.tools.helpers import ip_parts_integer, ip_int_parts_to_15byte


class PacketType:
	REGISTER = 1
	ADVERTISE = 2
	JOIN = 3
	MESSAGE = 4
	REUNION = 5


VERSION = 1
pack_header_format = 'h h i h h h h i '


class Packet:
	def __init__(self, buf):
		"""
		The decoded buffer should convert to a new packet.

		:param buf: Input buffer was just decoded.
		:type buf: bytes
		"""
		self.length = self.__get_body_length(buf)
		pack_format = pack_header_format + f'{self.length}s'
		self.version, self.type, _, ip_1, ip_2, ip_3, ip_4, port, self.body = unpack(pack_format, buf)

		self.body = self.body.decode('utf-8')
		self.source_ip = ip_int_parts_to_15byte(ip_1, ip_2, ip_3, ip_4)
		self.source_port = str(port).zfill(5)

	def __get_body_length(self, buf):
		"""
		:param buf: the input buffer for initiating packet
		:return: length of packet's body
		:rtype: int
		"""
		return unpack('i', buf[4:8])[0]


	def get_version(self):
		"""

		:return: Packet Version
		:rtype: int
		"""
		return self.version

	def get_type(self):
		"""

		:return: Packet type
		:rtype: int
		"""
		return self.type

	def get_length(self):
		"""

		:return: Packet length
		:rtype: int
		"""
		return self.length

	def get_body(self):
		"""

		:return: Packet body
		:rtype: str
		"""
		return self.body

	def get_buf(self):
		"""
		In this function, we will make our final buffer that represents the Packet with the Struct class methods.

		:return The parsed packet to the network format.
		:rtype: bytes
		"""
		self.length = len(self.body)
		pack_format = pack_header_format + f'{self.length}s'
		ip_1, ip_2, ip_3, ip_4 = ip_parts_integer(self.source_ip)
		return pack(pack_format, self.version, self.type, self.length, ip_1, ip_2, ip_3, ip_4, int(self.source_port),
					self.body.encode())

	def get_source_server_ip(self):
		"""

		:return: Server IP address for the sender of the packet.
		:rtype: str
		"""
		return self.source_ip

	def get_source_server_port(self):
		"""

		:return: Server Port address for the sender of the packet.
		:rtype: str
		"""
		return self.source_port

	def get_source_server_address(self):
		"""

		:return: Server address; The format is like ('192.168.001.001', '05335').
		:rtype: tuple
		"""
		return self.source_ip, self.source_port

	def is_reunion_hello(self):
		return self.type == PacketType.REUNION and self.body.startswith('REQ')

	def is_reunion_hello_back(self):
		return self.type == PacketType.REUNION and self.body.startswith('RES')

	def get_first_address_hello_packet(self):
		return (self.body[5:20], self.body[20:25])


class PacketFactory:
	"""
	This class is only for making Packet objects.
	"""

	@staticmethod
	def __new_packet(version, type, length, source_ip, source_port, body):
		ip_1, ip_2, ip_3, ip_4 = ip_parts_integer(source_ip)
		port = int(source_port)
		packet_format = pack_header_format + f'{length}s'
		body = bytes(body, encoding='utf-8')
		buf = pack(packet_format, version, type, length, ip_1, ip_2, ip_3, ip_4, port, body)
		packet = Packet(buf)
		return packet

	@staticmethod
	def parse_buffer(buffer):
		"""
		In this function we will make a new Packet from input buffer with struct class methods.

		:param buffer: The buffer that should be parse to a validate packet format
		:return new packet
		:rtype: Packet

		"""
		packet = Packet(buffer)
		return packet

	@staticmethod
	def new_reunion_packet(type, source_address, nodes_array):
		"""
		:param type: Reunion Hello (REQ) or Reunion Hello Back (RES)
		:param source_address: IP/Port address of the packet sender.
		:param nodes_array: [(ip0, port0), (ip1, port1), ...] It is the path to the 'destination'.

		:type type: str
		:type source_address: tuple
		:type nodes_array: list

		:return New reunion packet.
		:rtype Packet
		"""
		source_ip, source_port = source_address
		number_of_entries = str(len(nodes_array))
		addresses = [ip + port for ip, port in nodes_array]

		if type == 'REQ':
			full_body_string = 'REQ' + number_of_entries + ''.join(addresses)
		elif type == 'RES':
			addresses.reverse()
			full_body_string = 'RES' + number_of_entries + ''.join(addresses)
		else:
			full_body_string = ''

		return PacketFactory.__new_packet(VERSION, PacketType.REUNION, len(full_body_string), source_ip, source_port,
										  body=full_body_string)

	@staticmethod
	def new_advertise_packet(type, source_server_address, neighbour=None):
		"""
		:param type: Type of Advertise packet
		:param source_server_address Server address of the packet sender.
		:param neighbour: The neighbour for advertise response packet; The format is like ('192.168.001.001', '05335').

		:type type: str
		:type source_server_address: tuple
		:type neighbour: tuple

		:return New advertise packet.
		:rtype Packet

		"""

		server_ip, server_port = source_server_address
		if type == 'REQ':
			body = 'REQ'
		elif type == 'RES':
			if neighbour is None:
				return None
			neighbour_ip, neighbour_port = neighbour
			body = 'RES' + neighbour_ip + neighbour_port
		else:
			body = ''

		return PacketFactory.__new_packet(VERSION, PacketType.ADVERTISE, len(body), server_ip, server_port, body)

	@staticmethod
	def new_join_packet(source_server_address):
		"""
		:param source_server_address: Server address of the packet sender.

		:type source_server_address: tuple

		:return New join packet.
		:rtype Packet

		"""
		body = 'JOIN'
		return PacketFactory.__new_packet(VERSION, PacketType.JOIN, len(body), source_server_address[0],
										  source_server_address[1], body)

	@staticmethod
	def new_register_packet(type, source_server_address, address=(None, None)):
		"""
		:param type: Type of Register packet
		:param source_server_address: Server address of the packet sender.
		:param address: If 'type' is 'request' we need an address; The format is like ('192.168.001.001', '05335').

		:type type: str
		:type source_server_address: tuple
		:type address: tuple

		:return New Register packet.
		:rtype Packet

		"""
		source_ip, source_port = source_server_address
		if type == 'REQ':
			body ='REQ' + address[0] + address[1]
		elif type == 'RES':
			body = 'RESACK'
		else:
			body = ''

		return PacketFactory.__new_packet(VERSION, PacketType.REGISTER, len(body), source_ip, source_port, body)

	@staticmethod
	def new_message_packet(message, source_server_address):
		"""
		Packet for sending a broadcast message to the whole network.

		:param message: Our message
		:param source_server_address: Server address of the packet sender.

		:type message: str
		:type source_server_address: tuple

		:return: New Message packet.
		:rtype: Packet
		"""
		body = message
		return PacketFactory.__new_packet(VERSION, PacketType.MESSAGE, len(body), source_server_address[0],
										  source_server_address[1], body)


