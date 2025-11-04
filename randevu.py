import socket

print("Rendezvous Server - Starting")

clients = {} # { public_addr: local_addr_str }
waiting_clients = []

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 9999))

print("Listening on 0.0.0.0:9999")

while True:
    data, public_addr = sock.recvfrom(1024)
    
    message = data.decode()
    if message.startswith('REGISTER'):
        local_addr_str = message.split(' ')[1]
        clients[public_addr] = local_addr_str
        
        if public_addr not in waiting_clients:
            waiting_clients.append(public_addr)
        
        print(f"Registered client: public {public_addr}, local {local_addr_str}")

    if len(waiting_clients) == 2:
        pub_addr1, pub_addr2 = waiting_clients
        loc_addr1 = clients.get(pub_addr1)
        loc_addr2 = clients.get(pub_addr2)

        print(f"Exchanging addresses between {pub_addr1} and {pub_addr2}")

        msg_for_1 = f"PEER {pub_addr2[0]}:{pub_addr2[1]} {loc_addr2}".encode()
        sock.sendto(msg_for_1, pub_addr1)

        msg_for_2 = f"PEER {pub_addr1[0]}:{pub_addr1[1]} {loc_addr1}".encode()
        sock.sendto(msg_for_2, pub_addr2)
        
        waiting_clients.clear()
        clients.pop(pub_addr1, None)
        clients.pop(pub_addr2, None)