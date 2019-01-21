def ip_parts_integer(ip_string):
	ip_parts = tuple([int(part) for part in ip_string.split('.')])
	return ip_parts


def ip_int_parts_to_15byte(ip_1,ip_2,ip_3,ip_4):
	ip_1 = str(ip_1).zfill(3)
	ip_2 = str(ip_2).zfill(3)
	ip_3 = str(ip_3).encode('utf-8').zfill(3)
	ip_4 = str(ip_4).encode('utf-8').zfill(3)
	list = [ip_1, ip_2, ip_3, ip_4]
	return '.'.join(list)
