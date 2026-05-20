import socket

hostname = "vannmiljoapi.miljodirektoratet.no"
try:
    ip = socket.gethostbyname(hostname)
    print(f"DNS Resolved {hostname} to {ip}")
except Exception as e:
    print(f"DNS Failed for {hostname}: {e}")
