# -*- coding: utf-8 -*-
"""cook_smart_training.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rArdtIx3gdXMwq3_kOxMbSsK-Z7udnny

# Recognize ingredients using Transfer Learning
"""

# Commented out IPython magic to ensure Python compatibility.
from __future__ import absolute_import, division, print_function, unicode_literals
# from google_images_download import google_images_download

try:
  # The %tensorflow_version magic only works in colab.
#   %tensorflow_version 2.x
except Exception:
  pass
import tensorflow as tf

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

tf.__version__

import os
from tqdm import tqdm
from tensorflow.keras import models, layers
from tensorflow.keras.models import Model
from tensorflow.keras.layers import BatchNormalization, Activation, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.regularizers import l2
from tensorflow.keras.layers import Dense,AveragePooling2D,BatchNormalization,Conv2D,Input,Flatten,Activation,concatenate,Dropout,GlobalAveragePooling2D, GlobalMaxPooling2D
from keras.preprocessing.image import ImageDataGenerator
from time import time
from datetime import datetime
from tensorflow.python.keras.callbacks import TensorBoard

"""## Setup Input Pipeline"""

from google.colab import drive
drive.mount('/content/drive')

!pwd

path = 'drive/My Drive/Project ideas/Recipe_Finder/'

os.chdir(path)

base_dir = os.path.join('/content/drive/My Drive/Project ideas/Recipe_Finder/', 'downloads') #'drive/My Drive/Project ideas/Recipe_Finder/downloads/'

base_dir

os.chdir(base_dir)
!ls







"""# Method-1

## Train and test Image set preparation

Use `ImageDataGenerator` to rescale the images.

Create the train generator and specify where the train dataset directory, image size, batch size.

Create the validation generator with similar approach as the train generator with the flow_from_directory() method.
"""

IMAGE_SIZE = 224
BATCH_SIZE = 64

datagen = tf.keras.preprocessing.image.ImageDataGenerator(
    rescale=1./255, 
    validation_split=0.2)

# rotation_range=40,
#     width_shift_range=0.2,
#     height_shift_range=0.2,
#     shear_range=0.2,
#     zoom_range=0.2,
#     horizontal_flip=True,
#     fill_mode='nearest',


train_generator = datagen.flow_from_directory(
    base_dir,
    target_size=(IMAGE_SIZE, IMAGE_SIZE),
    batch_size=BATCH_SIZE, 
    subset='training')

val_generator = datagen.flow_from_directory(
    base_dir,
    target_size=(IMAGE_SIZE, IMAGE_SIZE),
    batch_size=BATCH_SIZE, 
    subset='validation')

datagen

# len_len()

x,y = train_generator.next()
for i in range(0,3):
    image = x[i]
    label = y[i]
    print (label)
    plt.imshow(image)
    plt.show()

base_dir

for image_batch, label_batch in train_generator:
  break
image_batch.shape, label_batch.shape

"""Save the labels in a file which will be downloaded later."""

print (train_generator.class_indices)

labels = '\n'.join(sorted(train_generator.class_indices.keys()))

with open('labels.txt', 'w') as f:
  f.write(labels)

print(len(train_generator.class_indices))

!cat labels.txt

input_shape_img = (image_batch.shape[1],image_batch.shape[2],image_batch.shape[3])
print(input_shape_img)

"""## Create the base model from the pre-trained convnets

Create the base model from the **MobileNet V2** model developed at Google, and pre-trained on the ImageNet dataset, a large dataset of 1.4M images and 1000 classes of web images.

First, pick which intermediate layer of MobileNet V2 will be used for feature extraction. A common practice is to use the output of the very last layer before the flatten operation, the so-called "bottleneck layer". The reasoning here is that the following fully-connected layers will be too specialized to the task the network was trained on, and thus the features learned by these layers won't be very useful for a new task. The bottleneck features, however, retain much generality.

Let's instantiate an MobileNet V2 model pre-loaded with weights trained on ImageNet. By specifying the `include_top=False` argument, we load a network that doesn't include the classification layers at the top, which is ideal for feature extraction.
"""

IMG_SHAPE = (IMAGE_SIZE, IMAGE_SIZE, 3)


# Create the base model from the pre-trained model MobileNet V2
base_model = tf.keras.applications.MobileNetV2(input_shape=IMG_SHAPE,
                                              include_top=False, 
                                              weights='imagenet')

base_model.trainable = True

# Let's take a look to see how many layers are in the base model
print("Number of layers in the base model: ", len(base_model.layers))

# Fine tune from this layer onwards
fine_tune_at = 100 #20 # 100 thila

# Freeze all the layers before the `fine_tune_at` layer
for layer in base_model.layers[:fine_tune_at]:
  layer.trainable =  False

from keras.models import Sequential
from keras.layers import Conv2D,MaxPooling2D
from keras.layers import Activation, Dense, Flatten, Dropout
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ModelCheckpoint
from keras import backend as K



from keras.regularizers import l2,l1

base_model.trainable = False


model = tf.keras.Sequential([
  base_model,
  tf.keras.layers.Conv2D(filters = 128, kernel_size = (3,3), activation= 'relu'),
  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.Conv2D(filters = 256, kernel_size = (3,3), activation= 'relu'),
#   tf.keras.layers.Dropout(0.5),
#   tf.keras.layers.Conv2D(filters = 512, kernel_size = (3,3), activation= 'relu'),
  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.Dense(150, activation= 'relu'),
  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.GlobalAveragePooling2D(),
  tf.keras.layers.Dense(len(train_generator.class_indices), activation='softmax')
])

model.summary()

# sgd = tf.keras.optimizers.SGD(lr = 0.1,momentum = 0.7, nesterov = True)
rmsprop = tf.keras.optimizers.RMSprop(learning_rate=0.001, rho=0.9)
adam = tf.keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, amsgrad=True)
adam_0 = tf.keras.optimizers.Adam(1e-5)

model.compile(loss='categorical_crossentropy',
              optimizer=rmsprop, #adam_0,#adam #rmsprop  
              metrics=['accuracy'])
# print('Compiled!')

# model.summary()

# Call Backs
filepath = "weights.{epoch:02d}-{val_loss:.2f}.hdf5"
history = tf.keras.callbacks.History()
tensorboard = TensorBoard(log_dir="logs/{}".format(time()))
filepath = "weights.{epoch:02d}-{val_accuracy:.2f}.hdf5"
path = os.path.abspath('__model_save/')

filepath = os.path.join(path, filepath)
learning_rate_reduction = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_accuracy', patience=10, verbose=1, factor=0.5, min_lr=0.00001)
checkpoint_save = tf.keras.callbacks.ModelCheckpoint(filepath, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
early_stoping = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=25)
callbacks_list = [checkpoint_save,history,tensorboard,learning_rate_reduction,early_stoping]#learning_rate_reduction,early_stoping]

filepath

os.getcwd()

epochs = 300

model.load_weights(os.path.join(path, 'weights.28-0.65.hdf5')) # weights.52-1.54  # 40-1.67.hdf5 # weights.01-1.53

history = model.fit_generator(train_generator, epochs=epochs, callbacks = callbacks_list, validation_data=val_generator)

#Loss plot
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

loss = history.history['loss']
val_loss = history.history['val_loss']

plt.figure(figsize=(8, 8))
plt.subplot(2, 1, 1)
plt.plot(acc, label='Training Accuracy')
plt.plot(val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.ylabel('Accuracy')
plt.ylim([min(plt.ylim()),1.2])
plt.title('Training and Validation Accuracy')

plt.subplot(2, 1, 2)
plt.plot(loss, label='Training Loss')
plt.plot(val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.ylabel('Cross Entropy')
plt.ylim([0,3.0])
plt.title('Training and Validation Loss')
plt.xlabel('epoch')
plt.show()



"""## Convert to TFLite

Saved the model using `tf.saved_model.save` and then convert the saved model to a tf lite compatible format.
"""

saved_model_dir = 'save/fine_tuning'
tf.saved_model.save(model, saved_model_dir)

converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
tflite_model = converter.convert()

with open('model.tflite', 'wb') as f:
  f.write(tflite_model)

"""Download the converted model and labels"""

from google.colab import files

files.download('model.tflite')
files.download('labels.txt')

"""Let's take a look at the learning curves of the training and validation accuracy/loss, when fine tuning the last few layers of the MobileNet V2 base model and training the classifier on top of it. The validation loss is much higher than the training loss, so you may get some overfitting.

You may also get some overfitting as the new training set is relatively small and similar to the original MobileNet V2 datasets.
"""

acc = history_fine.history['accuracy']
val_acc = history_fine.history['val_accuracy']

loss = history_fine.history['loss']
val_loss = history_fine.history['val_loss']

plt.figure(figsize=(8, 8))
plt.subplot(2, 1, 1)
plt.plot(acc, label='Training Accuracy')
plt.plot(val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.ylabel('Accuracy')
plt.ylim([min(plt.ylim()),1])
plt.title('Training and Validation Accuracy')

plt.subplot(2, 1, 2)
plt.plot(loss, label='Training Loss')
plt.plot(val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.ylabel('Cross Entropy')
plt.ylim([0,1.0])
plt.title('Training and Validation Loss')
plt.xlabel('epoch')
plt.show()









"""## CNN 4 layer Own Model"""

model = tf.keras.Sequential([
  tf.keras.layers.Conv2D(filters = 32, kernel_size = 3, input_shape=input_shape_img, activation='relu', padding='same', ),
  tf.keras.layers.MaxPooling2D(2),
  tf.keras.layers.BatchNormalization(),
  tf.keras.layers.Dropout(0.5),

  tf.keras.layers.Conv2D(filters = 32, kernel_size = 3, activation= 'relu', padding='same', kernel_initializer = 'he_uniform'),
  tf.keras.layers.MaxPooling2D(2),
  tf.keras.layers.BatchNormalization(),
  tf.keras.layers.Dropout(0.5),

  tf.keras.layers.Conv2D(filters = 64, kernel_size = 3, activation= 'relu', padding='same', kernel_initializer = 'he_uniform'),
  tf.keras.layers.MaxPooling2D(2),
  tf.keras.layers.BatchNormalization(),
  tf.keras.layers.Dropout(0.5),

  tf.keras.layers.Conv2D(filters = 64, kernel_size = 3, activation= 'relu', padding='same', kernel_initializer = 'he_uniform'),
  tf.keras.layers.MaxPooling2D(2),
  tf.keras.layers.BatchNormalization(),
  tf.keras.layers.Dropout(0.5),

  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.Flatten(),
  tf.keras.layers.Dense(128, activation= 'relu'),
  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.Dense(len(train_generator.class_indices), activation='softmax')
])

model.summary()

# filepath = "weights.{epoch:02d}-{val_loss:.2f}.hdf5"
history = tf.keras.callbacks.History()
tensorboard = TensorBoard(log_dir="logs/{}".format(time()))
filepath = "own_weights-epoch:{epoch:02d}-train_acc{accuracy:.2f}-test_acc{val_accuracy:.2f}.hdf5"
path = os.path.abspath('__model_save/')
filepath = os.path.join(path, filepath)
learning_rate_reduction = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_accuracy', patience=5, verbose=1, factor=0.5, min_lr=0.00001)
checkpoint_save = tf.keras.callbacks.ModelCheckpoint(filepath, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
early_stoping = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=25)
callbacks_list = [checkpoint_save,history,tensorboard,learning_rate_reduction,early_stoping]#learning_rate_reduction,early_stoping]

rmsprop = tf.keras.optimizers.RMSprop(learning_rate=0.001, rho=0.9)
adam = tf.keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, amsgrad=True)
adam_0 = tf.keras.optimizers.Adam(1e-5)

model.compile(loss='categorical_crossentropy',
              optimizer=adam,
              metrics=['accuracy'])
print('Compiled!')

# own_weights.23-2.37.hdf5
# model.load_weights(os.path.join(path, 'own_weights.27-2.29.hdf5'))

history = model.fit_generator(train_generator, epochs=100, callbacks = callbacks_list, validation_data=val_generator)

rmsprop = tf.keras.optimizers.RMSprop(learning_rate=0.001, rho=0.9)
adam = tf.keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, amsgrad=True)
adam_0 = tf.keras.optimizers.Adam(1e-5)

model.compile(loss='categorical_crossentropy',
              optimizer=adam,
              metrics=['accuracy'])
print('Compiled!')



"""## Inception Model"""

IMG_SHAPE = (IMAGE_SIZE, IMAGE_SIZE, 3)

insp_base_model = tf.keras.applications.InceptionV3(input_shape=IMG_SHAPE,
                                              include_top=False, 
                                              weights='imagenet')

for layer in insp_base_model.layers[:20]: # add [:50] for next time
    layer.trainable = False

insp_model = tf.keras.Sequential([
  insp_base_model,
  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.GlobalAveragePooling2D(name='avg_pool'),
  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.Dense(len(train_generator.class_indices), activation='softmax')
])        

insp_model.summary()

history = tf.keras.callbacks.History()
tensorboard = TensorBoard(log_dir="logs/{}".format(time()))
filepath = "insp_weights-epoch:{epoch:02d}-train_acc:_{accuracy:.2f}-test_acc:_{val_accuracy:.2f}.hdf5"
path = os.path.abspath('__model_save/')
filepath = os.path.join(path, filepath)
learning_rate_reduction = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_accuracy', patience=5, verbose=1, factor=0.5, min_lr=0.00001)
checkpoint_save = tf.keras.callbacks.ModelCheckpoint(filepath, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
early_stoping = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=25)
callbacks_list = [checkpoint_save,history,tensorboard,learning_rate_reduction,early_stoping]

rmsprop = tf.keras.optimizers.RMSprop(learning_rate=0.001, rho=0.9)
adam = tf.keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, amsgrad=True)
adam_0 = tf.keras.optimizers.Adam(1e-5)

insp_model.compile(loss='categorical_crossentropy',
              optimizer=adam,
              metrics=['accuracy'])
print('Compiled!')

# own_weights.23-2.37.hdf5
# model.load_weights(os.path.join(path, 'own_weights.27-2.29.hdf5'))

history = insp_model.fit_generator(train_generator, epochs=100, callbacks = callbacks_list, validation_data=val_generator)

"""## VGG16 Model"""

IMG_SHAPE = (IMAGE_SIZE, IMAGE_SIZE, 3)

vgg16_base_model = tf.keras.applications.VGG16(input_shape=IMG_SHAPE,
                                              include_top=False, 
                                              weights='imagenet')

for layer in vgg16_base_model.layers[:]: # add [:50] for next time
    layer.trainable = False

vgg16_model = tf.keras.Sequential([
  vgg16_base_model,
  tf.keras.layers.Conv2D(filters = 128, kernel_size = 2, activation= 'relu'),
  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.Conv2D(filters = 256, kernel_size = 2, activation= 'relu'),
#   tf.keras.layers.Dropout(0.5),
#   tf.keras.layers.Conv2D(filters = 512, kernel_size = (3,3), activation= 'relu'),
  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.Dense(150, activation= 'relu'),
  tf.keras.layers.Dropout(0.5),
  tf.keras.layers.GlobalAveragePooling2D(),
  tf.keras.layers.Dense(len(train_generator.class_indices), activation='softmax')
])


vgg16_model.summary()

# filepath = "weights.{epoch:02d}-{val_loss:.2f}.hdf5"
history = tf.keras.callbacks.History()
tensorboard = TensorBoard(log_dir="logs/{}".format(time()))
filepath = "vgg_weights-epoch:{epoch:02d}-train_acc:_{accuracy:.2f}-test_acc:_{val_accuracy:.2f}.hdf5"
path = os.path.abspath('__model_save/')
filepath = os.path.join(path, filepath)
learning_rate_reduction = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_accuracy', patience=5, verbose=1, factor=0.5, min_lr=0.00001)
checkpoint_save = tf.keras.callbacks.ModelCheckpoint(filepath, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
early_stoping = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=25)
callbacks_list = [checkpoint_save,history,tensorboard,learning_rate_reduction,early_stoping]#learning_rate_reduction,early_stoping]

rmsprop = tf.keras.optimizers.RMSprop(learning_rate=0.001, rho=0.9)
adam = tf.keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, amsgrad=True)
adam_0 = tf.keras.optimizers.Adam(1e-5)

vgg16_model.compile(loss='categorical_crossentropy',
              optimizer=adam,
              metrics=['accuracy'])
print('Compiled!')

#vgg_weights-epoch_31-train_acc__0.99-test_acc__0.75
vgg16_model.load_weights(os.path.join(path, 'vgg_weights-epoch_31-train_acc__0.99-test_acc__0.75.hdf5'))#'vgg_weights-epoch:31-train_acc:_0.99-test_acc:_0.75.hdf5'))

history = vgg16_model.fit_generator(train_generator, epochs=100, callbacks = callbacks_list, validation_data=val_generator)

#Loss plot
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

loss = history.history['loss']
val_loss = history.history['val_loss']

plt.figure(figsize=(8, 8))
plt.subplot(2, 1, 1)
plt.plot(acc, label='Training Accuracy')
plt.plot(val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.ylabel('Accuracy')
plt.ylim([min(plt.ylim()),1.2])
plt.title('Training and Validation Accuracy')

plt.subplot(2, 1, 2)
plt.plot(loss, label='Training Loss')
plt.plot(val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.ylabel('Cross Entropy')
plt.ylim([0,3.0])
plt.title('Training and Validation Loss')
plt.xlabel('epoch')
plt.show()

"""### Saving to tflite"""



saved_model_dir = 'save/fine_tuning'
tf.saved_model.save(vgg16_model, saved_model_dir)

converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
tflite_model = converter.convert()

with open('model_75.tflite', 'wb') as f:
  f.write(tflite_model)

from google.colab import files

files.download('model_75.tflite')
files.download('labels.txt')

