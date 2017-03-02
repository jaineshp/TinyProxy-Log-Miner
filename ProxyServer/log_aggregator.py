#########################################################################################
# This code reads the logs of the proxy server sends the latest data to the redis server
# Data it sends - 
#					1. Attempts to blocked Websites
#					2. Total websites accessed
#########################################################################################

from dateutil import parser
import socket, redis

NOTICE  = "NOTICE"
CONNECT = "CONNECT"

NOTICE_STATEMENT = "Proxying refused on filtered domain"

r = redis.Redis(
		host	 = "", #Redis Server
		password = "",
		port	 = 6379,
	)

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def get_last_read_line():
	ip = get_my_ip()
	ip = 'curr_line:' + ip
	res = r.get(ip)
	if res == None:
		return -1
	return res

def main():
	last_read_line = get_last_read_line()
	curr_line = last_read_line + 1
	blocked_attempts  = []
	accessed_websites = []
	ignore = {}

	with open('ignore-websites') as file:
		for line in file:
			ignore[line.strip()] = 1

	with open('log2') as file: #Replace it by /var/log/tinyproxy.log
		lines = file.read().splitlines()[curr_line:]
		for line in lines:
			data = line.split()
			if NOTICE_STATEMENT in line and data[0] == NOTICE: #Attempt to Blocked Website
				url = data[len(data) - 1]
				url = url[1:len(url) - 1]
				date_time = "{0} {1} {2}".format(data[1], data[2], data[3])
				blocked_attempts.append([date_time, url])
			elif data[0] == CONNECT and "HTTP/1.1" in line:
				url = data[len(data) - 2]
				if "www" in url:
					com_ind = url.find(":")
					url = url[url.find("www"):com_ind]
					date_time = "{0} {1} {2}".format(data[1], data[2], data[3])
#					dt = parser.parse(date_time)
					if url:
						if url not in ignore:
							accessed_websites.append([date_time, url])
			curr_line += 1

	curr_line -= 1

	#Push data to Redis Server

	#Push Last read line
	ip = get_my_ip()
	key = 'curr_line:' + ip
	r.set(key, curr_line)

	#Push blocked_attempts
	blocked_url = []
	blocked_time = []
	for attempt in blocked_attempts:
		blocked_time.append(attempt[0])
		blocked_url.append(attempt[1])

	key = 'blocked_url:' + ip
	r.rpush(key, *blocked_url)

	key = 'blocked_time:' + ip
	r.rpush(key, *blocked_time)

	#Pushing accessed attempts
	accessed_url = []
	accessed_time = []
	for attempt in accessed_websites:
		accessed_time.append(attempt[0])
		accessed_url.append(attempt[1])

	key = 'accessed_url:' + ip
	r.rpush(key, *accessed_url)

	key = 'accessed_time' + ip
	r.rpush(key, *accessed_time)

if __name__ == '__main__':
	main()