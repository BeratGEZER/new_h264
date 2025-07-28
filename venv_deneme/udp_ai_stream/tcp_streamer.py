import cv2
import socket
import threading
import time
import os

class StreamManager:
    def __init__(self):
        self.active_streams = {}
        self.base_port = 4000  # TCP portlar 4000'den başlar

    def get_tcp_port(self, video_id):
        return self.base_port + int(video_id)

    def start_stream(self, video_id):
        if video_id in self.active_streams:
            return f"🎥 Video {video_id} zaten yayında."

        stop_flag = threading.Event()
        t = threading.Thread(target=self.stream_video, args=(video_id, stop_flag))
        t.start()
        self.active_streams[video_id] = {"thread": t, "stop_flag": stop_flag}
        return f"✅ Video {video_id} yayına başladı."

    def stop_stream(self, video_id):
        if video_id not in self.active_streams:
            return f"⚠️ Video {video_id} yayında değil."

        self.active_streams[video_id]["stop_flag"].set()
        self.active_streams[video_id]["thread"].join()
        del self.active_streams[video_id]
        return f"⛔ Video {video_id} yayını durduruldu."

    def get_status(self):
        return {"active_streams": list(self.active_streams.keys())}

    def stream_video(self, video_id, stop_flag):
        # Video dosyasının tam yolu
        path = os.path.join(os.path.dirname(__file__), "videos", f"{video_id}.mp4")
        if not os.path.exists(path):
            print(f"❌ Dosya bulunamadı: {path}")
            return

        cap = cv2.VideoCapture(path)
        tcp_ip = "127.0.0.1"
        tcp_port = self.get_tcp_port(video_id)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((tcp_ip, tcp_port))
            print(f"🚀 TCP bağlantı kuruldu: {tcp_ip}:{tcp_port}")
        except Exception as e:
            print(f"❌ TCP bağlantı hatası: {e}")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or fps is None:
            fps = 25
        frame_interval = 1 / fps

        gönderilen_paket_sayısı = 0
        gönderilen_toplam_byte = 0

        while cap.isOpened() and not stop_flag.is_set():
            start = time.time()

            ret, frame = cap.read()
            if not ret:
                break

            suc, buffer = cv2.imencode('.jpg', frame)
            if not suc:
                continue

            data = buffer.tobytes()
            length = len(data).to_bytes(4, byteorder='big')  # 4 byte'lık uzunluk bilgisi

            try:
                sock.sendall(length + data)
                gönderilen_paket_sayısı += 1
                gönderilen_toplam_byte += len(data)
            except Exception as e:
                print(f"⚡ Veri gönderim hatası: {e}")
                break

            elapsed = time.time() - start
            remaining = frame_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)

            print(f"📤 Gönderilen Paket: {gönderilen_paket_sayısı}, Toplam: {gönderilen_toplam_byte / 1024:.2f} KB")

        cap.release()
        sock.close()
        print(f"🔌 TCP bağlantı kapatıldı: {tcp_ip}:{tcp_port}")
