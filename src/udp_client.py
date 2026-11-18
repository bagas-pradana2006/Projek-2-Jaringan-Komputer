import socket
import struct
import time
import csv
import os
import sys

SERVER_IP = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = 5001
SIZES = [64, 512, 1024, 1400]
COUNT = 100
TIMEOUT = 1.0
BUFFER = 65535
HEADER = struct.Struct("!Id")  # seq (4 byte) + timestamp (8 byte) = 12 byte


def tunggu_echo(sock, seq, deadline):
    """Menunggu echo dengan seq yang cocok sampai deadline.
    Mengembalikan (data, waktu_terima, jumlah_echo_terlambat)."""
    terlambat = 0
    while True:
        sisa = deadline - time.perf_counter()
        if sisa <= 0:
            return None, None, terlambat
        sock.settimeout(sisa)
        try:
            data, _ = sock.recvfrom(BUFFER)
        except (socket.timeout, ConnectionResetError):
            return None, None, terlambat
        waktu_terima = time.perf_counter()

        if len(data) >= HEADER.size and HEADER.unpack(data[:HEADER.size])[0] == seq:
            return data, waktu_terima, terlambat
        terlambat += 1  # echo milik pesan lama, dibuang


def main():
    os.makedirs("data", exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tujuan = (SERVER_IP, PORT)
    print(f"[UDP] Mengirim ke {SERVER_IP}:{PORT} (tanpa handshake)")

    hasil = []
    ringkasan = []
    seq = 0

    for size in SIZES:
        isian = bytes(i % 256 for i in range(size - HEADER.size))
        ok = lost = corrupt = terlambat_total = 0
        rtt_ok = []
        mulai = time.perf_counter()

        for _ in range(COUNT):
            pesan = HEADER.pack(seq, time.perf_counter()) + isian
            sock.sendto(pesan, tujuan)
            balasan, waktu_terima, terlambat = tunggu_echo(
                sock, seq, time.perf_counter() + TIMEOUT)
            terlambat_total += terlambat

            if balasan is None:
                status, rtt_ms = "lost", ""
                lost += 1
            else:
                _, ts = HEADER.unpack(balasan[:HEADER.size])
                rtt_ms = round((waktu_terima - ts) * 1000, 3)
                if balasan == pesan:
                    status = "ok"
                    ok += 1
                    rtt_ok.append(rtt_ms)
                else:
                    status = "corrupt"
                    corrupt += 1

            hasil.append(["UDP", size, seq, rtt_ms, status])
            seq += 1

        durasi = time.perf_counter() - mulai
        throughput_kbps = (size * ok * 8) / durasi / 1000
        rata_rtt = sum(rtt_ok) / len(rtt_ok) if rtt_ok else 0
        ringkasan.append(["UDP", size, COUNT, ok, lost, corrupt, terlambat_total,
                          round(rata_rtt, 3), round(durasi, 4), round(throughput_kbps, 2)])
        print(f"[UDP] {size:>5} B | ok {ok}/{COUNT} | lost {lost} | corrupt {corrupt} "
              f"| RTT rata-rata {rata_rtt:.3f} ms | throughput {throughput_kbps:.2f} kbps")

    sock.close()
    print("[UDP] Selesai (tidak ada proses penutupan koneksi)")

    with open("data/udp_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["protokol", "ukuran", "seq", "rtt_ms", "status"])
        w.writerows(hasil)

    with open("data/udp_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["protokol", "ukuran", "dikirim", "ok", "lost", "corrupt", "terlambat",
                    "rtt_rata_ms", "durasi_s", "throughput_kbps"])
        w.writerows(ringkasan)


if __name__ == "__main__":
    main()