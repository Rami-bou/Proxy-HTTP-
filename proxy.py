import socket, os, re

def load_config():
    config = {
        "filter": False,
        "block_sites": [],
        "block_words": [],
        "title": None
    }

    with open("config.txt") as f:
        for line in f:
            line = line.strip()

            if line == "Filtrage:ON":
                config["filter"] = True

            elif line.startswith("BLOCK_SITE:"):
                config["block_sites"].append(line.split(":",1)[1])

            elif line.startswith("BLOCK_WORD:"):
                config["block_words"].append(line.split(":",1)[1])

            elif line.startswith("TITLE:"):
                config["title"] = line.split(":",1)[1]

    return config

# socket setup
HOST = 'localhost'
PORT = 8080
proxy_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
proxy_client.bind((HOST, PORT))
proxy_client.listen(5)
print(f'Proxy server running on {HOST}:{PORT}...')

socket_client, addr_client = proxy_client.accept()
conf = load_config()
while 1:
    request = socket_client.recv(1024)
    request = request.decode('utf-8', errors='ignore')
    if not request:
        break
    print("Request 1\n\n", request)        
    lines = request.splitlines()
    if not lines:
        continue
    # Devision de la requete pour extraire method, url, host, port
    method = lines[0].split(' ')[0]
    url = lines[0].split(' ')[1]
    url = url.replace('http://', '')
    path = url.split('/', 1)
    host_port = path[0]
    
    host = host_port.split(':')[0]
    port = host_port.split(':')[1] if ':' in host_port else 80
    
    # filtring Request par site
    if conf['filter']:
        if host in conf['block_sites']:
            socket_client.sendall(b'Website Blocked By Proxy')
            print('Filtering Request')
            break
        
    
    req_server = ''
    # reconstruction de la requete
    if method == 'GET' or method == 'POST':
        req_server+= lines[0].split(" ")[0]+" "+lines[0].split(" ")[1]+" HTTP/1.0\r\n"
    if method == 'CONNECT':
        print('HTTPS ignored')

    for i in range(1,len(lines)):
        if not ((lines[i].startswith('Connection: keep-alive'))or(lines[i].startswith('Proxy-Connection: keep-alive'))
                or(lines[i].startswith('Accept-Encoding: gzip'))):
            req_server+=(lines[i]+ "\n")    

    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # proxy_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_server.connect((host, int(port)))
    print("Request 2 (after modification)\n\n", req_server)
    # envoi de la requete modifiee au serveur par la socket proxy_server
    proxy_server.sendall(req_server.encode())

    pid = os.fork()
    if not pid:
        response = b''
        data = proxy_server.recv(4096)
        if not data:
            break
        response += data
        
        if conf['filter']:
            # filtring Response par mots
            print('Filtering Response')
            text = response.decode('utf-8', errors='ignore')
            word_filtered = []
            for word in conf["block_words"]:
                if word in text:
                    word_filtered.append(word)
            for word in conf["block_words"]:
                text = text.replace(word, "*****")
            print(word_filtered)
            
        if conf['title']:
                # changement du titre pour montre que le proxy a fonctionnes
                text = re.sub(
                r"<title>.*?</title>",
                f"<title>{conf['title']}</title>",
                text,
                flags=re.IGNORECASE | re.DOTALL
            )
                # suppression des videos(mp4)
                text = re.sub(
                r"<video>.*?</video>",
                f"",
                text,
                flags=re.IGNORECASE | re.DOTALL
            )
        socket_client.sendall(text.encode())