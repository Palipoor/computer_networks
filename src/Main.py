from src.Peer import Peer


def is_ip_correct(ip):
	pass


def is_port_ok(port):
	pass


if __name__ == "__main__":
	print('Type   add client/root IP-address port <Root-Ip-address> <Root-port>')
	command = str(input())

	parts_of_command = command.split()
	if parts_of_command[0] != 'add':
		print('WRONG COMMAND')
	elif len(parts_of_command) != 4 and len(parts_of_command) != 6:
		print('WRONG COMMAND')
	else:
		ip = parts_of_command[2]
		port = parts_of_command[3]

		if not is_ip_correct(ip) or not is_port_ok(port):
			print('WRONG_COMMAND')
		else:
			if command[1] == 'client':
				if len(parts_of_command) != 6:
					print('WRONG COMMAND')
				else:
					root_ip = parts_of_command[4]
					root_port = parts_of_command[5]
					if not is_ip_correct(root_ip) or not is_port_ok(root_port):
						print('WRONG_COMMAND')
					else:
						client = Peer(ip, int(port), is_root=False,
									  root_address=(root_ip, int(root_port)))
						client.run()
			elif command[1] == 'root':
				if len(parts_of_command) != 4:
					print('WRONG COMMAND')
				else:
					root = Peer(ip, int(port), is_root=True)
					root.run()
			else:
				print('WRONG COMMAND')
