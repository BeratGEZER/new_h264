from flask import Flask, request, jsonify
from udp_streamer import StreamManager


app = Flask(__name__)
stream_manager = StreamManager()


@app.route('/start', methods=['POST'])
def start_stream():
    data = request.get_json()  ## Get JSON data from the request
    video_id = data.get("video_id")     # Extract video_id from the JSON data


    camera=[]
    for i in range(1, 5): # Assuming video_id can be 1, 2, or 3
        camera.append(i)
    if video_id not in camera: # Check if video_id is valid
        return jsonify({"error": "Invalid video_id"}), 400


    result = stream_manager.start_stream(video_id)  # Start the stream
    return jsonify({"message": result})




@app.route('/stop', methods=['POST'])
def stop_stream():
    data = request.get_json()
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "video_id is required"}), 400


    result = stream_manager.stop_stream(video_id)
    return jsonify({"message": result})




@app.route('/status', methods=['GET'])
def status():
    return jsonify(stream_manager.get_status())




if __name__ == '__main__':
    app.run(debug=True)