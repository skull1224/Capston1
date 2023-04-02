from flask import Flask, render_template, request, redirect, session
import firebase_admin
from firebase_admin import credentials, db
import re

app = Flask(__name__)
app.secret_key = 'capston1_4'

# Firebase Admin SDK 초기화
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://capston1-771fd-default-rtdb.firebaseio.com/'
})

# 로그인


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
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
                return redirect('/')
            else:
                return render_template('login.html', message='이메일이나 비밀번호가 일치하지 않습니다.')
        except Exception as e:
            return render_template('login.html', message='이메일이나 비밀번호가 일치하지 않습니다.')
    else:
        return render_template('login.html')


# 회원가입
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # 이메일 유효성 검사
        if not re.match(r'^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            return render_template('signup.html', message='이메일 형식이 올바르지 않습니다.')

        # 비밀번호 유효성 검사
        if not re.match(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*()\-_=+\\\|\[\]{};\':"\\,.<>\/?])([A-Za-z\d!@#$%^&*()\-_=+\\\|\[\]{};\':"\\,.<>\/?]{8,})$', password):
            return render_template('signup.html', message='비밀번호는 영문, 숫자, 특수문자를 조합한 8자리 이상이어야 합니다.')

        try:
            # Realtime Database에서 이미 등록된 이메일인지 확인하기
            ref = db.reference('users')
            snapshot = ref.order_by_child('email').equal_to(email).get()
            if snapshot:
                return render_template('signup.html', message='이미 등록된 이메일입니다.')

            # Realtime Database에 유저 정보 저장하기
            ref.push({
                'email': email,
                'password': password
            })

            return render_template('signup.html', message='회원가입이 완료되었습니다.')
        except Exception as e:
            return render_template('signup.html', message=f'회원가입 중 오류가 발생했습니다.{(e)}')
    else:
        return render_template('signup.html')

# 로그아웃


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


# 인증된 사용자만 접근 가능한 페이지
@app.route('/')
def index():
    if 'user' in session:
        # Realtime Database에서 출입 기록 가져오기
        access_ref = db.reference('access')
        access = access_ref.get()
        return render_template('index.html', access=access)
    else:
        return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
