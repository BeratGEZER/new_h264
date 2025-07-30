import cv2
import socket
import threading
import time
import struct
import math

class StreamManager:
    def __init__(self):
        self.active_streams = {}  # video_id: {"thread": t, "stop_flag": flag}
        self.base_port = 4000

    def get_udp_port(self, video_id):
        return self.base_port + int(video_id)

    def start_stream(self, video_id):
        if video_id in self.active_streams:
            return f"Video {video_id} zaten yayında."

        stop_flag = threading.Event()
        t = threading.Thread(target=self.stream_video, args=(video_id, stop_flag))
        t.start()
        self.active_streams[video_id] = {"thread": t, "stop_flag": stop_flag}
        return f"Video {video_id} yayına başladı."

    def stop_stream(self, video_id):
        if video_id not in self.active_streams:
            return f"Video {video_id} yayında değil."

        self.active_streams[video_id]["stop_flag"].set()
        self.active_streams[video_id]["thread"].join()
        del self.active_streams[video_id]
        return f"Video {video_id} yayını durduruldu."

    def get_status(self):
        return {
            "active_streams": list(self.active_streams.keys())
        }

    def stream_video(self, video_id, stop_flag):
        path = f"videos/{video_id}.mp4"
        cap = cv2.VideoCapture(path)
        udp_ip = "127.0.0.1"
        udp_port = self.get_udp_port(video_id)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        frame_id = 0
        CHUNK_SIZE = 60000

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
                print("🎞️ Video sona erdi.")
                break

            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                continue

            data = buffer.tobytes()
            total_chunks = math.ceil(len(data) / CHUNK_SIZE)

            for i in range(total_chunks):
                chunk_data = data[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
                header = struct.pack("!QBB", frame_id, i, total_chunks)
                packet = header + chunk_data
                sock.sendto(packet, (udp_ip, udp_port))

                gönderilen_paket_sayısı += 1
                gönderilen_toplam_byte += len(packet)

            frame_id += 1

            elapsed = time.time() - start
            remaining = frame_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)

            print(f"📦 Gönderilen Paket: {gönderilen_paket_sayısı}")
            print(f"📤 Gönderilen Veri: {gönderilen_toplam_byte} B ≈ {gönderilen_toplam_byte/1024:.2f} KB")

        cap.release()
        sock.close()
        print(f"🔚 Video {video_id} yayını sonlandırıldı.")
