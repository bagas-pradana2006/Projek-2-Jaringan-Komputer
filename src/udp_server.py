import socket

HOST = "0.0.0.0"
PORT = 5001
BUFFER = 65535


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    print(f"[UDP] Server mendengarkan di {HOST}:{PORT}")

    total_paket = 0
    total_byte = 0
    while True:
        try:
            data, addr = server.recvfrom(BUFFER)
        except ConnectionResetError:
            continue

        server.sendto(data, addr)
        total_paket += 1
        total_byte += len(data)
        if total_paket % 100 == 0:
            print(f"[UDP] {total_paket} datagram di-echo ({total_byte} byte), "
                  f"terakhir dari {addr[0]}:{addr[1]}")


if __name__ == "__main__":
    main()