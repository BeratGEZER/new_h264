import socket
import cv2
import numpy as np
import threading

class ReceiverManager:
    def __init__(self):
        self.servers = {}

    def start_receiver(self, tcp_port):
        if tcp_port in self.servers:
            print(f"⚠️ TCP {tcp_port} zaten dinleniyor.")
            return

        t = threading.Thread(target=self.receive_stream, args=(tcp_port,))
        t.start()
        self.servers[tcp_port] = t
        print(f"✅ TCP {tcp_port} alıcı başlatıldı.")

    def receive_stream(self, tcp_port):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(("0.0.0.0", tcp_port))
        server_sock.listen(1)
        print(f"🎥 Dinleniyor: TCP {tcp_port}")

        conn, addr = server_sock.accept()
        print(f"🔗 Bağlandı: {addr}")

        paket_sayisi = 0
        alinan_toplam_byte = 0
        data_buffer = b""

        try:
            while True:
                # 4 byte uzunluk bilgisini al
                while len(data_buffer) < 4:
                    data_buffer += conn.recv(4096)

                length = int.from_bytes(data_buffer[:4], byteorder='big')
                data_buffer = data_buffer[4:]

                # Belirtilen uzunlukta veri alınana kadar devam et
                while len(data_buffer) < length:
                    data_buffer += conn.recv(4096)

                frame_data = data_buffer[:length]
                data_buffer = data_buffer[length:]

                frame_array = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

                if frame is not None:
                    frame = cv2.resize(frame, (200, 100))
                    cv2.imshow(f"TCP Stream {tcp_port}", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                paket_sayisi += 1
                alinan_toplam_byte += length
                print(f"📥 Paket {paket_sayisi} | Boyut: {length} B | Toplam: {alinan_toplam_byte / 1024:.2f} KB")

        except Exception as e:
            print(f"⛔ Hata (TCP {tcp_port}): {e}")
        finally:
            conn.close()
            server_sock.close()
            print(f"🔌 Bağlantı kapatıldı: TCP {tcp_port}")

if __name__ == "__main__":
    manager = ReceiverManager()
    ports_to_listen = [4001, 4002, 4003]  # TCP Portları
    for port in ports_to_listen:
        manager.start_receiver(port)
