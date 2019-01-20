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

    def get_children(self):
        result = []
        if not self.left_child:
            result.append(self.left_child)
        if not self.right_child:
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
        #returns success
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
        self.nodes = [root]

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
        queue = [self.root]
        while True:
            head = queue[0]
            queue = queue[1:]
            if head.can_have_child():
                return head
            queue = queue + head.get_children()



    def find_node(self, ip, port):
        """
		returns None if node is not in the graph
        :param ip:
        :param port:
        :return:
        """
        address = (ip,port)
        queue = [self.root]
        #FIXME off nodes
        while queue:
            head = queue[0]
            queue = queue[1:]
            if head.address == address:
                return head
            queue = queue + head.get_children()
        return None

    def turn_on_node(self, node_address):
        pass

    def turn_off_node(self, node_address):
        pass

    def remove_node(self, node_address):
        #returns None if hasn't find anything
        if self.root.address == node_address:
            temp = self.root
            self.root = None
            return temp
        queue = [self.root]
        while queue:
            head = queue[0]
            queue = queue[1:]
            if head.right_child.address == node_address:
                temp = head.right_child
                head.right_child = None
                return temp
            if head.left_child.address == node_address:
                temp = head.left_child
                head.left_child = None
                return temp
            queue = queue + head.get_children()
        return None

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
        new_node = GraphNode((ip,port))
        parent = self.find_node(ip, port)
        new_node.set_parent(new_node)
        parent.add_child(new_node)
        
