# 이진 분류 데이터 학습
import os
import cv2
import numpy as np
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.model_selection import train_test_split

# 이미지 크기 및 경로 설정
IMG_SIZE = 224
KNOWN_FACES_DIR = 'models/known_faces/'
UNKNOWN_FACES_DIR = 'models/unknown_faces/'

# 이미지 불러오기 및 라벨링
def load_images_and_labels(directories, label):
    data = []
    labels = []
    for directory in directories:
        for filename in os.listdir(directory):
            img = cv2.imread(os.path.join(directory, filename))
            if img is not None:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
                data.append(img)
                labels.append(label)
    return data, labels

known_faces, known_labels = load_images_and_labels([KNOWN_FACES_DIR], 1)
unknown_faces, unknown_labels = load_images_and_labels([UNKNOWN_FACES_DIR], 0)

# 데이터 합치기
data = known_faces + unknown_faces
labels = known_labels + unknown_labels

# 데이터셋 분할
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)

# 정규화
X_train = np.array(X_train) / 255.0
X_test = np.array(X_test) / 255.0
y_train = np.array(y_train)
y_test = np.array(y_test)

# 데이터 확장
datagen = ImageDataGenerator(
    rotation_range=20,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True)

datagen.fit(X_train)

# 모델 생성
model = Sequential()
model.add(Conv2D(32, (3,3), padding='same', activation='relu', input_shape=(IMG_SIZE, IMG_SIZE, 3)))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Conv2D(64, (3,3), padding='same', activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Conv2D(128, (3,3), padding='same', activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Flatten())
model.add(Dense(256, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(1, activation='sigmoid'))

# 모델 컴파일
opt = Adam(lr=0.0001)
model.compile(optimizer=opt, loss='binary_crossentropy', metrics=['accuracy'])

# 콜백 설정
checkpoint = ModelCheckpoint("face_recognition_model.h5",
                             monitor="val_loss",
                             mode="min",
                             save_best_only = True,
                             verbose=1)

earlystop = EarlyStopping(monitor = 'val_loss', 
                          min_delta = 0, 
                          patience = 5,                         
                          verbose = 1,
                          restore_best_weights = True)

callbacks = [earlystop, checkpoint]

# 모델 학습
history = model.fit(datagen.flow(X_train, y_train, batch_size=32),
                    epochs=25,
                    validation_data=(X_test, y_test),
                    callbacks=callbacks)
