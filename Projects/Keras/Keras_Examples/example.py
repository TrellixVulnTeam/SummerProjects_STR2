import numpy as np
import keras

# keras has Sequential and Functional models.
from keras.models import Sequential

# import the type of layers used for a particular problem
from keras.layers import Dense, Dropout
from keras.datasets import mnist
from keras.optimizers import SGD


# Keras requires the modeling of data into tuples
print ('Loading data...')
(x_train, y_train), (x_test, y_test) = mnist.load_data()


x_train = x_train.reshape(x_train.shape[0], 784)
x_test = x_test.reshape(x_test.shape[0],784)


print x_train.shape

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

y_train = keras.utils.to_categorical(y_train, 10)
y_test = keras.utils.to_categorical(y_test, 10)


print x_train.shape

model = Sequential()
model.add(Dense(30, activation='sigmoid', input_dim= (784)))
model.add(Dropout(0.25))
model.add(Dense(512, activation='relu'))
model.add(Dropout(0.25))
model.add(Dense(10, activation='softmax'))



model.compile(loss= 'mse',
              optimizer ='SGD',
              metrics = ['accuracy'])

model.fit(x_train,y_train, batch_size=10,epochs=30, )
model.evaluate(x_test, y_test)