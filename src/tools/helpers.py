def parse_ip(ip_string):
	ip_parts = tuple([int(part) for part in ip_string.split('.')])
	return ip_parts