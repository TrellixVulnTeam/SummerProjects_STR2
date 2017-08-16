import numpy as np

# keras model architectures for model design
from keras.models import Sequential
from keras.layers import Dense,Dropout,Activation,Flatten
from keras.layers import Convolution2D, MaxPooling2D
from keras.utils import np_utils

from keras.datasets import mnist

#training and test data, passed as tuples (input data, actual value)
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# reshape training and test data to one dimensional, 28x28 image inputs
x_train = x_train.reshape(x_train.shape[0], 1, 28, 28)
x_test = x_test.reshape(x_test.shape[0], 1, 28, 28)

# convert training and test data to float types
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

y_train = np_utils.to_categorical(y_train, 10)
y_test = np_utils.to_categorical(y_test, 10)


model = Sequential()
#model.add input parameters: number of conv. filters used, rows in each kernel, columns in each kernel
model.add(Convolution2D(32,3,3, activation='relu',
                        input_shape=(1,28,28), dim_ordering = 'th'))
model.add(Convolution2D(32, 3, 3, activation = 'relu'))
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(Dropout(0.25))

#final layers are flattened into a 1-dimensional array before passed to Dense layer
model.add(Flatten())

# dense layer output first parameter
model.add(Dense(128, activation = 'relu'))
model.add(Dropout(0.5))
model.add(Dense(10, activation = 'softmax'))

model.compile( loss = 'categorical_crossentropy',
               optimizer = 'adam',
               metrics = ['accuracy'])

model.fit(x_train, y_train,
          batch_size = 32, nb_epoch = 10, verbose = 1)

score = model.evaluate(x_test, y_test, verbose=0)








