import socket

HOST = "0.0.0.0"
PORT = 5000
BUFFER = 4096

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"[TCP] Server mendengarkan di {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        print(f"[TCP] Terhubung dengan {addr[0]}:{addr[1]}")

        total = 0
        while True:
            data = conn.recv(BUFFER)
            if not data:
                break
            conn.sendall(data)
            total += len(data)

        conn.close()
        print(f"[TCP] Koneksi ditutup, {total} byte di-echo")

if __name__ == "__main__":
    main()