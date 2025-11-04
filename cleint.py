import socket
import sys
import threading
import time

peer_final_addr = None
connection_established = threading.Event()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def receive_thread(sock):
    global peer_final_addr

    sock.settimeout(0.1)
    while not connection_established.is_set():
        try:
            data, addr = sock.recvfrom(1024)
            if data:
                peer_final_addr = addr
                print(f"\nConnection established with {peer_final_addr}")
                connection_established.set()
        except socket.timeout:
            continue
        except Exception:
            return

    sock.settimeout(None) 
    while True:
        try:
            data, _ = sock.recvfrom(1024)

            if data == b'punch':
                continue

            print(f"\rPeer: {data.decode()}      ")
            print("You: ", end="", flush=True) 
        except Exception:
            return

def punch_thread(sock, peer_public, peer_local):
    print(f"Starting NAT punch to public={peer_public} and local={peer_local}")
    while not connection_established.is_set():
        sock.sendto(b'punch', peer_public)
        if peer_local and peer_public != peer_local:
             sock.sendto(b'punch', peer_local)
        time.sleep(1)
    print("Punching completed.")

if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} <rendezvous_server_ip>")
    sys.exit(1)

RENDEZVOUS_ADDR = (sys.argv[1], 9999)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 0))

local_ip = get_local_ip()
local_port = sock.getsockname()[1]
register_msg = f'REGISTER {local_ip}:{local_port}'.encode()
print(f"Registering with server {RENDEZVOUS_ADDR}...")

sock.settimeout(2.0)
peer_info_received = False
while not peer_info_received:
    sock.sendto(register_msg, RENDEZVOUS_ADDR)
    try:
        data, _ = sock.recvfrom(1024)
        parts = data.decode().split(' ')
        if parts[0] == 'PEER':
            pub_ip, pub_port = parts[1].split(':')
            loc_ip, loc_port = parts[2].split(':')
            peer_public_addr = (pub_ip, int(pub_port))
            peer_local_addr = (loc_ip, int(loc_port))
            print(f"Received peer: public={peer_public_addr}, local={peer_local_addr}")
            peer_info_received = True
    except socket.timeout:
        continue
    except Exception as e:
        print(f"Failed to get peer data: {e}")
        sock.close()
        sys.exit(1)

receiver = threading.Thread(target=receive_thread, args=(sock,), daemon=True)
puncher = threading.Thread(target=punch_thread, args=(sock, peer_public_addr, peer_local_addr), daemon=True)

receiver.start()
puncher.start()

connection_established.wait()

print("--- Chat started ---")
try:
    while True:
        msg = input("You: ")
        if peer_final_addr:
            sock.sendto(msg.encode(), peer_final_addr)
except KeyboardInterrupt:
    print("\nExiting.")
finally:
    sock.close()
    sys.exit(0)