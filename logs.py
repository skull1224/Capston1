#
import cv2
import datetime
import random
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from flask import Flask, render_template
from threading import Thread
# from flask_paginate import Pagination

# Firebase 인증 정보
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://capston1-771fd-default-rtdb.firebaseio.com/'
})

# Firebase 참조
ref_logs = db.reference('logs')

# 얼굴 인식 모델 로드
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# 웹캠으로부터 프레임을 읽어올 객체 생성 라즈베리 파이 카메라로 수정해야함
cap = cv2.VideoCapture(0)

app = Flask(__name__)


@app.route('/')
def logs():
    # Firebase에서 출입 로그 가져오기
    logs = ref_logs.get()

    # 출입 로그 데이터 정제
    log_list = []
    if logs:
        for key, log in logs.items():
            log['key'] = key  # 로그의 키 추가
            log_list.append(log)

    # 최신 출입 로그부터 정렬
    log_list = sorted(log_list, key=lambda x: x['time'], reverse=True)

    return render_template('logs.html', logs=log_list)


def process_frame():
    while True:
        ret, frame = cap.read()

        if ret:
            # 회색조 변환
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 얼굴 인식
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

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

                # 얼굴 영역 표시
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                # 대기
                cv2.waitKey(5000)

            # 화면에 출력
            cv2.imshow('얼굴 인식', frame)

        # q 키를 누르면 종료 (라즈베리파이 실시간으로 띄우게 되면 없어도 되는코드)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 객체 해제
    cap.release()
    cv2.destroyAllWindows()


def run():
    # process_frame() 함수를 스레드로 실행
    Thread(target=process_frame).start()

    # Flask 애플리케이션 실행
    app.run(debug=True, use_reloader=False)


if __name__ == '__main__':
    run()
