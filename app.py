import cv2
import random
import datetime
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, render_template, Response, request, session, redirect
from functools import wraps
import re
import hashlib

app = Flask(__name__)
app.secret_key = 'capston1_4'

# Firebase Admin SDK 초기화
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://capston1-771fd-default-rtdb.firebaseio.com/'
})

ref_logs = db.reference('logs')

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def gen_frames():
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        success, frame = capture.read()
        if not success:
            break
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray,
                                                  scaleFactor=1.1,
                                                  minNeighbors=5,
                                                  minSize=(30, 30),
                                                  flags=cv2.CASCADE_SCALE_IMAGE)
            # 얼굴이 인식되면
            if len(faces) > 0:
                now = datetime.datetime.now()
                date = now.strftime('%Y-%m-%d')
                time = now.strftime('%H:%M:%S')

                # 랜덤으로 얼굴이 등록되었는지 여부 기록
                is_registered = random.choice([True, False])

                # 출입로그 데이터 작성
                log = {
                    'date': date,
                    'time': time,
                    'is_registered': is_registered
                }

                # Firebase에 출입로그 데이터 추가
                ref_logs.push(log)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    capture.release()


@app.route('/')
def index():
    if 'user' in session:
        logs = ref_logs.get()

        log_list = []
        if logs:
            for key, log in logs.items():
                log['key'] = key
                log_list.append(log)

        log_list = sorted(log_list, key=lambda x: x['time'], reverse=True)
        return render_template('streaming.html', logs=log_list[:10])
    else:
        return redirect('/login')


@app.route('/live_streaming')
@login_required
def live_streaming():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/logs')
@login_required
def logs():
    logs = ref_logs.get()

    log_list = []
    if logs:
        for key, log in logs.items():
            log['key'] = key
            log_list.append(log)

    log_list = sorted(log_list, key=lambda x: x['time'], reverse=True)

    return render_template('logs.html', logs=log_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        password = hashlib.sha256(password.encode()).hexdigest()
        try:
            # Realtime Database에서 유저 정보 가져오기
            users_ref = db.reference('users')
            query = users_ref.order_by_child('email').equal_to(email)
            results = query.get()
            user_id = list(results.keys())[0]
            user = results[user_id]
            if user['password'] == password:

                # 세션에 유저 정보 저장하기
                session['user'] = {'uid': user_id, 'email': email}
                # 로그인 성공시 / 주소로 redirect
                return redirect('/')

            else:
                return render_template('login.html', message='이메일이나 비밀번호가 일치하지 않습니다.')
        except Exception as e:
            return render_template('login.html', message='이메일이나 비밀번호가 일치하지 않습니다.')
    else:
        return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        # 이메일 유효성 검사
        if not re.match(r'^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            return render_template('signup.html', message='이메일 형식이 올바르지 않습니다.')

        # 비밀번호 유효성 검사
        if not re.match(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*()\-_=+\\\|\[\]{};\':"\\,.<>\/?])([A-Za-z\d!@#$%^&*()\-_=+\\\|\[\]{};\':"\\,.<>\/?]{8,})$', password):
            return render_template('signup.html', message='비밀번호는 영문, 숫자, 특수문자를 조합한 8자리 이상이어야 합니다.')

        # 비밀번호를 해시로 변환
        password = hashlib.sha256(password.encode()).hexdigest()

        try:
            # Realtime Database에서 이미 등록된 이메일인지 확인하기
            ref = db.reference('users')
            snapshot = ref.order_by_child('email').equal_to(email).get()
            if snapshot:
                return render_template('signup.html', message='이미 등록된 이메일입니다.')

            # Realtime Database에 유저 정보 저장하기
            ref.push({
                'email': email,
                'phone': phone,
                'password': password
            })

            return "<script>alert('회원가입이 완료되었습니다.');location.href='/login';</script>"
        except Exception as e:
            return render_template('signup.html', message=f'회원가입 중 오류가 발생했습니다.{(e)}')
    else:
        return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
