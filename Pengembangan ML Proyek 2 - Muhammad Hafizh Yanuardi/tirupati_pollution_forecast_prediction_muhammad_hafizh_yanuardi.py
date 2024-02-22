# -*- coding: utf-8 -*-
"""Tirupati Pollution Forecast Prediction_Muhammad Hafizh Yanuardi.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13JpY7iWvXBX5dZR_284eromnmV678Dml

# Proyek ini akan membuat model dari dataset Time Series untuk memprediksi tingkat polusi PM2.5 untuk periode kedepan

Mengimport Library yang akan digunakan
"""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import Callback

"""Membaca Dataset CSV Ke dalam DataFrame"""

df = pd.read_csv('./tirupati_air_quality.csv')

"""Melihat detail dari Dataset"""

df.info()

"""Melihat Grafik Plot dari PM2.5"""

date = df['From Date'].values
PM = df['PM2.5 (ug/m3)'].values

plt.figure(figsize=(15,5))
plt.plot(date, PM)
plt.title('PM2.5',
          fontsize=20);

"""Menyalin Dataset untuk Preprocessing"""

X = df.copy(deep=True)

"""Menghapus setiap attribut Dataset kecuali Date dan PM2.5"""

column_name = X.columns.values

delcol = column_name[3:23]

delcol

delete = []
for col in delcol:
  delete.append(col)

delete

X.drop(['To Date'], axis=1, inplace=True)
X.drop(delete, axis=1, inplace=True)

"""Mengecek Dataset yang sudah dilakukan *drop*"""

X.head()

"""Menghilangkan sampel yang bernilai NaN"""

X = X.dropna(axis=0)

"""Melihat dataset dengan sampel tanpa NaN"""

X.head()

"""Membuat fungsi windowed_dataset"""

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    # series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

"""Melakukan normalisasi menggunakan MinMaxScaler"""

mms = MinMaxScaler()
val = X['PM2.5 (ug/m3)'].values
val = val.reshape(-1, 1)
X_scaled = mms.fit_transform(val)

X_scaled

"""Memasukkan kedua kolom dalam variabel X dan y untuk training"""

X_date = X['From Date'].values
y_quality = X_scaled

y_quality

"""Membagi dataset menjadi 80% training set dan 20% validation set"""

X_train, X_test, y_train, y_test = train_test_split(X_date, y_quality, test_size=0.2, shuffle=False)

"""Menentukan Threshold Mean Absolute Error (MAE) dan membuat fungsi Callback"""

threshold_mae = ((y_quality.max() - y_quality.min()) * 10/100)
print("Threshold MAE dari data adalah: " + str(threshold_mae))

# Commented out IPython magic to ensure Python compatibility.
# Callback untuk menghentikan training ketika MAE dari model <10% skala data.
class MAE_Callback(Callback):
    def on_epoch_end(self, epoch, logs={}):
        if logs.get('mae') < threshold_mae and logs.get('val_mae') < threshold_mae:
          self.model.stop_training = True
          print("\n[MAE & MAE Validasi yang didapatkan senilai %2.2f%% & %2.2f%% dari skala data, training dihentikan.]\n"
#                 % ((logs.get('mae')*10/threshold_mae), (logs.get('val_mae')*10/threshold_mae)))

        else:
          print("\n[MAE & MAE Validasi yang didapatkan senilai %2.2f%% & %2.2f%% dari skala data, lanjut ke epoch berikutnya]\n"
#                 % ((logs.get('mae')*10/threshold_mae), (logs.get('val_mae')*10/threshold_mae)))

mae_callback = MAE_Callback()

"""Membuat Model

"""

train_set = windowed_dataset(y_train, window_size=30, batch_size=100, shuffle_buffer=1000)
val_set = windowed_dataset(y_test, window_size=30, batch_size=100, shuffle_buffer=1000)

model = tf.keras.models.Sequential([
  tf.keras.layers.LSTM(60, return_sequences=True),
  tf.keras.layers.LSTM(60),
  tf.keras.layers.Dense(30, activation="relu"),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(10, activation="relu"),
  tf.keras.layers.Dense(1),
])

"""Melakukan Training"""

optimizer = tf.keras.optimizers.SGD(learning_rate=1.0000e-04, momentum=0.9)
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])
history = model.fit(
    train_set,
    validation_data=val_set,
    callbacks=[mae_callback],
    epochs=10)

# Menampilkan output dari training

message = '--- Menampilkan output dari training ---'
print(message)

mae = history.history['mae']
val_mae = history.history['val_mae']

loss = history.history['loss']
val_loss = history.history['val_loss']

plt.figure(figsize=(8, 8))
plt.subplot(2, 1, 1)
plt.plot(mae, label='MAE Training')
plt.plot(val_mae, label='MAE Validation')
plt.legend(loc='lower right')
plt.ylabel('MAE')
plt.ylim([min(plt.ylim()),1])
plt.title('Mean Absolute Error Training dan Validation')

plt.subplot(2, 1, 2)
plt.plot(loss, label='Training Loss')
plt.plot(val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.ylabel('Cross Entropy')
plt.ylim([0,1.5])
plt.title('Training dan Validation Loss')
plt.xlabel('epoch')
plt.show()