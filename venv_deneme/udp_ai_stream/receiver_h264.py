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
            print(f"⚠️ UDP {udp_port} already running.")
            return

        t = threading.Thread(target=self.receive_stream, args=(udp_port,))
        t.start()
        self.receivers[udp_port] = t
        print(f"✅ Receiver started on UDP {udp_port}")

    def receive_stream(self, udp_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)  # 4 MB buffer

        sock.bind(("127.0.0.1", udp_port))

        # ✅ OS-level UDP buffer temizliği (önceki yayından kalanları sil)
        sock.setblocking(False)
        try:
            while True:
                sock.recvfrom(65536)
        except BlockingIOError:
            pass
        sock.setblocking(True)

        buffer = b""
        codec = av.codec.CodecContext.create('h264', 'r')

        frame_paket = 0
        frame_byte = 0
        total_paket = 0
        total_byte = 0
        first_frame = True

        print(f"🎥 Listening on UDP {udp_port}")
        while True:
            try:
                data, _ = sock.recvfrom(65536)
                if not data:
                    continue

                buffer += data
                frame_paket += 1
                frame_byte += len(data)

                if b'__FRAME_END__' in buffer:
                    if first_frame:
                        total_paket = 0
                        total_byte = 0
                        first_frame = False

                    total_paket += frame_paket
                    total_byte += frame_byte

                    raw_frame = buffer.replace(b'__FRAME_END__', b'')
                    try:
                        packet = av.packet.Packet(raw_frame)
                        frames = codec.decode(packet)
                        buffer = b""

                        print("[*************************-------------------------------------****************************")
                        print(f"[Receiver {udp_port}] ✅ Frame alındı → Paket: {frame_paket}, Veri: {frame_byte / 1024:.2f} KB")
                        print(f"🔹 Toplam Alınan Paket: {total_paket}")
                        print(f"🔹 Toplam Alınan Veri: {total_byte / 1024:.2f} KB ≈ {total_byte / (1024 * 1024):.2f} MB")

                        frame_paket = 0
                        frame_byte = 0

                        for frame in frames:
                            img = frame.to_ndarray(format='bgr24')
                            resized = cv2.resize(img, (800, 600))
                            cv2.imshow(f"UDP Stream {udp_port}", resized)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                raise KeyboardInterrupt

                    except Exception as decode_err:
                        print(f"[Receiver {udp_port}] ⚠️ Decode hatası: {decode_err}")
                        buffer = b""
                        continue

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⛔ UDP {udp_port} alım hatası: {e}")
                break

        print(f"\n📊 [UDP {udp_port}] Yayın Özeti:")
        print(f"🔹 Toplam Alınan Paket: {total_paket}")
        print(f"🔹 Toplam Alınan Veri: {total_byte / 1024:.2f} KB ≈ {total_byte / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    manager = ReceiverManager()
    for port in [4001, 4002, 4003, 4004]:
        manager.start_receiver(port)
