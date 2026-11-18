import socket
import struct
import time
import csv
import os
import sys

SERVER_IP = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = 5000
SIZES = [64, 512, 1024, 1400]
COUNT = 100
HEADER = struct.Struct("!Id")  # seq (4 byte) + timestamp (8 byte) = 12 byte


def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        potongan = sock.recv(n - len(data))
        if not potongan:
            raise ConnectionError("Server menutup koneksi")
        data += potongan
    return data


def main():
    os.makedirs("data", exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((SERVER_IP, PORT))
    print(f"[TCP] Terhubung ke {SERVER_IP}:{PORT}")

    hasil = []
    ringkasan = []

    for size in SIZES:
        isian = bytes(i % 256 for i in range(size - HEADER.size))
        ok = 0
        mulai = time.perf_counter()

        for seq in range(COUNT):
            pesan = HEADER.pack(seq, time.perf_counter()) + isian
            sock.sendall(pesan)
            balasan = recv_exact(sock, size)
            selesai = time.perf_counter()

            _, ts = HEADER.unpack(balasan[:HEADER.size])
            rtt_ms = (selesai - ts) * 1000
            status = "ok" if balasan == pesan else "corrupt"
            if status == "ok":
                ok += 1
            hasil.append(["TCP", size, seq, round(rtt_ms, 3), status])

        durasi = time.perf_counter() - mulai
        throughput_kbps = (size * COUNT * 8) / durasi / 1000
        rata_rtt = sum(r[3] for r in hasil[-COUNT:]) / COUNT
        ringkasan.append(["TCP", size, COUNT, ok, round(rata_rtt, 3),
                          round(durasi, 4), round(throughput_kbps, 2)])
        print(f"[TCP] {size:>5} B | ok {ok}/{COUNT} | RTT rata-rata {rata_rtt:.3f} ms "
              f"| throughput {throughput_kbps:.2f} kbps")

    sock.close()
    print("[TCP] Koneksi ditutup")

    with open("data/tcp_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["protokol", "ukuran", "seq", "rtt_ms", "status"])
        w.writerows(hasil)

    with open("data/tcp_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["protokol", "ukuran", "dikirim", "ok", "rtt_rata_ms",
                    "durasi_s", "throughput_kbps"])
        w.writerows(ringkasan)


if __name__ == "__main__":
    main()