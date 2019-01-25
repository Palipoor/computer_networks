import time


class GraphNode:
	def __init__(self, address):
		"""

		:param address: (ip, port)
		:type address: tuple

		"""
		self.address = address
		self.parent = None
		self.left_child = None
		self.right_child = None
		self.is_on = True
		self.alive = False

	def get_children(self):
		result = []
		if self.left_child:
			result.append(self.left_child)
		if self.right_child:
			result.append(self.right_child)
		return result

	def set_parent(self, parent):
		self.parent = parent

	def set_address(self, new_address):
		self.address = new_address

	def __reset(self):
		self.address = None
		self.left_child = None
		self.right_child = None

	def can_have_child(self):
		return not (self.left_child and self.right_child)

	def add_child(self, child):
		# returns success
		if not self.left_child:
			self.left_child = child
			return True

		if not self.right_child:
			self.right_child = child
			return True

		return False


class NetworkGraph:
	def __init__(self, root):
		self.root = root
		root.alive = True
		self.nodes = {root.address: root}

	def find_live_node(self, sender):
		"""
		Here we should find a neighbour for the sender.
		Best neighbour is the node who is nearest the root and has not more than one child.

		Code design suggestion:
			1. Do a BFS algorithm to find the target.

		Warnings:
			1. Check whether there is sender node in our NetworkGraph or not; if exist do not return sender node or
			   any other nodes in it's sub-tree.

		:param sender: The node address we want to find best neighbour for it.
		:type sender: tuple

		:return: Best neighbour for sender.
		:rtype: GraphNode
		"""
		# if sender in self.nodes and self.nodes[sender].is_on:
		# 	return
		queue = [self.root]
		while True:
			print('in find alive node! ')
			print(queue)
			head = queue[0]
			print('head is' + str(head.__dict__))
			queue = queue[1:]

			# print(head.__dict__)
			# print(head.can_have_child())
			# print(head.is_on)
			# print("_____________")
			if head.can_have_child() and head.is_on:
				return head
			queue = queue + head.get_children()

	def find_node(self, ip, port):
		"""
		returns None if node is not in the graph
		:param ip:
		:param port:
		:return:
		"""
		return self.nodes.get((ip, port), None)

	def turn_on_node(self, node_address):
		the_node = self.nodes.get(node_address, None)
		if not the_node == None:
			the_node.is_on = True

	def turn_off_node(self, node_address):
		the_node = self.nodes.get(node_address, None)
		if not the_node == None:
			the_node.is_on = False

	def turn_off_subtree(self, subtree_root):
		queue = [subtree_root]
		while len(queue) > 0:
			head = queue[0]
			queue = queue[1:]
			self.turn_off_node(head)
			queue = queue + head.get_children()

	def turn_on_subtree(self, subtree_root):
		queue = [subtree_root]
		while len(queue) > 0:
			head = queue[0]
			queue = queue[1:]
			self.turn_on_node(head)
			queue = queue + head.get_children()

	def remove_node(self, node_address):
		# returns the removed node
		# returns None if hasn't find anything
		print('gonna remove ' + str(node_address))
		removed = self.nodes.pop(node_address, None)
		if not removed is None:
			if removed.parent.left_child:
				if removed.parent.left_child.address == node_address:
					removed.parent.left_child = None
			if removed.parent.right_child:
				if removed.parent.right_child.address == node_address:
					removed.parent.right_child = None

			self.turn_off_subtree(removed)

		return removed

	def add_node(self, ip, port, father_address):
		"""
		Add a new node with node_address if it does not exist in our NetworkGraph and set its father.

		Warnings:
			1. Don't forget to set the new node as one of the father_address children.
			2. Before using this function make sure that there is a node which has father_address.

		:param ip: IP address of the new node.
		:param port: Port of the new node.
		:param father_address: Father address of the new node

		:type ip: str
		:type port: int
		:type father_address: tuple


		:return:
		"""
		# return success
		new_node = self.nodes.get((ip, port), GraphNode((ip, port)))
		new_node.alive = True
		parent = self.nodes.get(father_address, None)
		if parent == None:
			return False
		new_node.set_parent(parent)
		parent.add_child(new_node)
		self.nodes.update({new_node.address: new_node})
		self.turn_on_subtree(new_node)
