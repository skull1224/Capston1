import cv2
import imagezmq
from flask import Flask, render_template, Response

app = Flask(__name__)
image_hub = imagezmq.ImageHub()
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def gen_frames():
    while True:
        rpi_name, image = image_hub.recv_image()

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(cv2.UMat(gray),
                                              scaleFactor=1.1,
                                              minNeighbors=5,
                                              minSize=(30, 30),
                                              flags=cv2.CASCADE_SCALE_IMAGE)

        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)

        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        image_hub.send_reply(b'OK')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host="192.168.0.27", port="8080")
