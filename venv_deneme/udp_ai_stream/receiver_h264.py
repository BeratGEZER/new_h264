
import socket
import av
import cv2
import threading
import time

class ReceiverManager:
    def __init__(self):
        self.receivers = {}

    def start_receiver(self, udp_port):
        if udp_port in self.receivers:
            print(f"⚠️ UDP {udp_port} zaten dinleniyor.")
            return

        t = threading.Thread(target=self.receive_stream, args=(udp_port,))
        t.start()
        self.receivers[udp_port] = t
        print(f"✅ UDP {udp_port} alıcı başlatıldı.")

    def receive_stream(self, udp_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        sock.bind(("0.0.0.0", udp_port))
        print(f"🎥 Dinleniyor: UDP {udp_port}")

        buffer = b""
        paket_sayisi = 0
        alinan_toplam_byte = 0
        son_veri_zamani = time.time()
        CHUNK_SIZE = 60000

        codec = av.codec.CodecContext.create("h264", "r")

        while True:
            try:
                data, _ = sock.recvfrom(65536)
                buffer += data
                paket_sayisi += 1
                alinan_toplam_byte += len(data)

                now = time.time()
                if now - son_veri_zamani > 1:
                    print(f"⚠️ [UDP {udp_port}] 1 saniyedir veri alınmıyor!")
                son_veri_zamani = now

                if len(data) < CHUNK_SIZE:
                    try:
                        packets = codec.parse(buffer)
                        for packet in packets:
                            frames = codec.decode(packet)
                            for frame in frames:
                                img = frame.to_ndarray(format="bgr24")
                                img = cv2.resize(img, (600, 300))
                                cv2.imshow(f"UDP Stream {udp_port}", img)
                                if cv2.waitKey(1) & 0xFF == ord('q'):
                                    sock.close()
                                    return
                        buffer = b""
                    except Exception as decode_error:
                        print(f"⛔ Decode hatası: {decode_error}")
                        buffer = b""

                print(f"📥 Alınan Paket Sayısı: {paket_sayisi}")
                print(f"📥 Alınan Toplam Veri: {alinan_toplam_byte} B ≈ {alinan_toplam_byte / 1024:.2f} KB")

            except Exception as e:
                print(f"⛔ Hata (UDP {udp_port}): {e}")
                break

if __name__ == "__main__":
    manager = ReceiverManager()
    ports_to_listen = [4001, 4002, 4003, 4004]
    for port in ports_to_listen:
        manager.start_receiver(port)

