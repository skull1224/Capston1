#다중 분류 데이터 학습
import os
import cv2
import numpy as np
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# 이미지 크기 및 경로 설정
IMG_SIZE = 220
KNOWN_FACES_DIR = 'models/known_faces/'

# 이미지 불러오기 및 라벨링
def load_images_and_labels(known_directories):
    data = []
    labels = []
    class_names = os.listdir(known_directories)  # 각 얼굴을 클래스로 간주하고 클래스 이름을 가져옵니다.

    for class_name in class_names:
        class_dir = os.path.join(known_directories, class_name)
        for filename in os.listdir(class_dir):
            img = cv2.imread(os.path.join(class_dir, filename))
            if img is not None:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
                data.append(img)
                labels.append(class_names.index(class_name))  # 클래스의 인덱스를 라벨로 설정합니다.

    return data, labels

known_faces, known_labels = load_images_and_labels(KNOWN_FACES_DIR)

# 데이터셋 분할
X_train, X_test, y_train, y_test = train_test_split(known_faces, known_labels, test_size=0.2, random_state=42)

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
model.add(Dense(len(set(known_labels)), activation='softmax'))  # 다중 분류를 위해 출력 레이어를 변경합니다.

# 모델 컴파일
opt = Adam(lr=0.0001)
model.compile(optimizer=opt, loss='sparse_categorical_crossentropy', metrics=['accuracy'])  # 다중 분류를 위한 손실 함수 설정

# 콜백 설정
checkpoint = ModelCheckpoint("face_recognition_model.h5",
                             monitor="val_loss",
                             mode="min",
                             save_best_only=True,
                             verbose=1)

earlystop = EarlyStopping(monitor='val_loss',
                          min_delta=0,
                          patience=5,
                          verbose=1,
                          restore_best_weights=True)

callbacks = [earlystop, checkpoint]

# 모델 학습
history = model.fit(datagen.flow(X_train, y_train, batch_size=16),
                    epochs=30,
                    validation_data=(X_test, y_test),
                    callbacks=callbacks)

import matplotlib.pyplot as plt

# 훈련 손실(loss)과 검증 손실(val_loss) 추출
train_loss = history.history['loss']
val_loss = history.history['val_loss']

# 훈련 정확도(accuracy)와 검증 정확도(val_accuracy) 추출
train_acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

# 에포크 수 추출
epochs = range(1, len(train_loss) + 1)

# 손실 그래프
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(epochs, train_loss, 'bo', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()

# 정확도 그래프
plt.subplot(1, 2, 2)
plt.plot(epochs, train_acc, 'bo', label='Training accuracy')
plt.plot(epochs, val_acc, 'b', label='Validation accuracy')
plt.title('Training and Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()

# 가중치 그래프
plt.figure(figsize=(12, 6))
for i, layer in enumerate(model.layers):
    if isinstance(layer, Conv2D):
        filters, biases = layer.get_weights()
        plt.subplot(2, len(model.layers)//2, i+1)
        plt.hist(filters.flatten(), bins=30)
        plt.title(f'Layer {i+1}: Conv2D')
        plt.xlabel('Weight Value')
        plt.ylabel('Count')

plt.tight_layout()
plt.show()
