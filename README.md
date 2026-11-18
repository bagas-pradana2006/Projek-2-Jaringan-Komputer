# Echo Server TCP vs UDP

Aplikasi Echo Server sederhana dalam dua versi socket, dipakai untuk membandingkan karakteristik TCP (`SOCK_STREAM`) dan UDP (`SOCK_DGRAM`) dengan workload yang identik. Client mengirim pesan, server mengembalikan isi yang sama persis, lalu client mengukur RTT, throughput, dan integritas data.

## Isi folder

| File | Peran | Port |
|---|---|---|
| `tcp_server.py` | Server echo TCP | 5000 |
| `tcp_client.py` | Client TCP: kirim workload, ukur RTT dan throughput | 5000 |
| `udp_server.py` | Server echo UDP | 5001 |
| `udp_client.py` | Client UDP: kirim workload, ukur RTT, throughput, dan paket hilang | 5001 |

## Kebutuhan

- Python 3.8 atau lebih baru
- Tidak ada library tambahan (hanya modul bawaan Python)

## Workload pengujian

Kedua client mengirim workload yang sama:

- Ukuran pesan: 64, 512, 1024, dan 1400 byte (panjang total pesan aplikasi)
- Jumlah pesan: 100 per ukuran, total 400 pesan
- Pola kirim: stop-and-wait (kirim satu pesan, tunggu echo, baru kirim berikutnya)
- Format pesan: header 12 byte (`seq` 4 byte + `timestamp` 8 byte, big-endian) diikuti isian
- Timeout UDP: 1 detik per pesan (melewati batas ini dicatat sebagai `lost`)

## Cara menjalankan

Semua perintah dijalankan dari **folder utama repo** (bukan dari dalam `src`), supaya hasil tersimpan di folder `data/`.

### Pengujian di dua laptop (LAN / hotspot)

1. Sambungkan kedua laptop ke hotspot yang sama.
2. Di laptop server, cek IP dengan `ipconfig` (Windows) atau `ip a` (Linux).
3. Saat Windows meminta izin firewall untuk Python, izinkan untuk **Private networks**. Pastikan profil jaringan hotspot diatur sebagai Private.

**TCP**

```
# Laptop server
python src/tcp_server.py

# Laptop client (ganti dengan IP laptop server)
python src/tcp_client.py 192.168.x.x
```

**UDP**

```
# Laptop server
python src/udp_server.py

# Laptop client (ganti dengan IP laptop server)
python src/udp_client.py 192.168.x.x
```

Server harus sudah berjalan sebelum client dijalankan. Server tetap hidup setelah client selesai, jadi bisa dipakai untuk beberapa kali pengujian. Hentikan server dengan Ctrl+C (atau tutup jendela terminal).

### Pengujian di satu laptop (localhost)

Jalankan server dan client di dua terminal berbeda, tanpa argumen IP (default `127.0.0.1`):

```
python src/tcp_server.py
python src/tcp_client.py
```

## Hasil

Client menyimpan hasil ke folder `data/`:

| File | Isi |
|---|---|
| `tcp_results.csv`, `udp_results.csv` | Satu baris per pesan: `protokol, ukuran, seq, rtt_ms, status` |
| `tcp_summary.csv`, `udp_summary.csv` | Satu baris per ukuran: jumlah ok, RTT rata-rata, durasi, throughput (kbps). Versi UDP juga mencatat `lost`, `corrupt`, dan `terlambat` |

Arti kolom `status`:

- `ok`: echo kembali dan isinya sama persis dengan pesan yang dikirim
- `corrupt`: echo kembali tetapi isinya berbeda
- `lost`: echo tidak datang dalam batas timeout (khusus UDP)

Setiap kali client dijalankan, file CSV lama akan ditimpa. Ganti nama atau pindahkan file hasil sebelum menjalankan pengujian berikutnya jika ingin menyimpannya.

## Capture Wireshark

Capture dilakukan di **laptop client** pada interface Wi-Fi. Filter yang dipakai:

| Tujuan | Filter |
|---|---|
| Semua trafik TCP aplikasi | `tcp.port == 5000` |
| Semua trafik UDP aplikasi | `udp.port == 5001` |
| 3-way handshake | `tcp.port == 5000 && tcp.flags.syn == 1` |
| Penutupan koneksi | `tcp.port == 5000 && tcp.flags.fin == 1` |
| Retransmission TCP | `tcp.analysis.retransmission` |

## Catatan khusus Windows

- Jika client UDP mencatat semua pesan sebagai `lost` dan selesai dalam sekejap, server UDP kemungkinan belum berjalan. Windows melaporkan port tujuan yang tertutup sebagai `ConnectionResetError` (WinError 10054).
- `TCP_NODELAY` diaktifkan di server dan client TCP untuk mematikan algoritma Nagle, sehingga RTT tidak tertunda oleh penahanan segmen kecil dan perbandingan dengan UDP tetap adil.
