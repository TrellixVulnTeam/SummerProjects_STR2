from __future__ import print_function
from keras.models import Sequential
from keras import layers
import numpy as np
from six.moves import range


class CharacterTable(object):


    def __init__(self,chars):
        self.chars = sorted(set(chars))
        self.char_indices = dict((c,i) for i, c in enumerate(self.chars))
        self.indices_char = dict((i,c) for i, c in enumerate(self.chars))


    ''' One hot encoding based on string C '''
    def encode(self, C, num_rows):
        #create array with rows= num_rows and len= chars
        x = np.zeros((num_rows, len(self.chars)))
        #for each character, translate to one-hot representation
        for i, c in enumerate(C):
            x[i, self.char_indices[c]] = 1
        return x

    def decode(self, x, calc_argmax = True):
        if calc_argmax:
            x = x.argmax(axis = -1)
        return ''.join(self.indices_char[x] for x in x)


class colors:
    ok = '\033[92m'
    fail = '\033[91m'
    close = '\033[0m'


TRAINING_SIZE = 50000
DIGITS = 3
INVERT =True

MAXLEN = DIGITS + 1 + DIGITS

chars = '0123456789+ '
ctable = CharacterTable(chars)

questions = []
expected = []
seen = set()

while len(questions) < TRAINING_SIZE:

    # Generate a random int from 1 to DIGITS + 1. Then for each element
    # in that range, join them with a random integer 0-9
    f = lambda: int(''.join(np.random.choice(list('0123456789'))
                    for i in range(np.random.randint(1, DIGITS + 1))))

    #create a tuple by calling the f function twice
    a, b = f(), f()

    # set the variable key to the sorted tuple a,b
    key = tuple(sorted((a, b)))

    #if key is already seen, continue. Otherwise add key to seen

    if key in seen:
        continue
    seen.add(key)

    # concatenate a,b as numbers, creating a four digit representation
    q = '{}+{}'.format(a,b)
    # pad q with spaces so that it is equal to MAXLEN
    query = q + '' *(MAXLEN - len(q))
    ans = str(a+b)

    #answers can be max size of DIGITS + 1
    ans += '' *(DIGITS + 1 -len(ans))
    if INVERT:

    # sets query to the reverse of query by taking query and slicing it backward
    #with stride = -1
        query = query[::-1]
    questions.append(query)
    expected.append(ans)
print('Total addition questions:', len(questions))


print('Vectorization...')
# creates two 3D arrays (an array of arrays of arrays) Yikes!

x = np.zeros((len(questions), MAXLEN, len(chars)),dtype=np.bool)
y = np.zeros((len(questions), DIGITS + 1, len(chars)), dtype=np.bool)



# for each entry in array x, create an index list of questions.
# Encode each instance of sentence with its one-hot representation
for i, sentence in enumerate(questions):
    x[i] = ctable.encode(sentence,MAXLEN)
for i, sentence in enumerate(expected):
    y[i] = ctable.encode(sentence, DIGITS + 1)

#create an array with all numbers up to len(y)
indices = np.arange(len(y))
#shuffle the indices
np.random.shuffle(indices)
x = x[indices]
y= y[indices]


#set aside 10% for validation data
split_at = len(x) - len(x)//10

(x_train, x_val) = x[:split_at], x[split_at:]
(y_train, y_val) = y[:split_at], y[split_at:]


print('Training Data:')
print(x_train.shape)
print(y_train.shape)

print('Validation Data:')
print(x_val.shape)
print(y_val.shape)

RNN = layers.LSTM
HIDDEN_SIZE = 128
BATCH_SIZE = 128
LAYERS = 1


model = Sequential()

model.add(RNN(HIDDEN_SIZE, input_shape=(MAXLEN, len(chars))))
model.add(layers.RepeatVector(DIGITS+1))

for _ in range(LAYERS):
    model.add(RNN(HIDDEN_SIZE, return_sequences=True))

model.add(layers.TimeDistributed(layers.Dense(len(chars))))
model.add(layers.Activation('softmax'))
model.compile(loss = 'categorical_crossentropy',
              optimizer= 'adam',
              metrics = ['accuracy'])
model.summary


for iteration in range(1, 200):
    print()
    print('-' * 50)
    print('Iteration', iteration)
    model.fit(x_train, y_train,
              batch_size=BATCH_SIZE,
              epochs=1,
              validation_data=(x_val, y_val))


