#!/usr/bin/env python
# coding: utf-8

# In[1]:


#NumPy Imports
# used to create arrays of zeros and ones
#used to expand the dimensions of a NumPy array
#used to convert a Python list to a NumPy array.
from numpy import zeros, ones, expand_dims, asarray
from numpy.random import randn, randint
#Keras Imports
from keras.datasets import fashion_mnist
from keras.optimizers import Adam
from keras.models import Model, load_model
#layers for training the model
from keras.layers import Input, Dense, Reshape, Flatten
from keras.layers import Conv2D, Conv2DTranspose, Concatenate
# used to introduce non-linearity ,regularization,vector representations.
from keras.layers import LeakyReLU, Dropout, Embedding
from keras.layers import BatchNormalization, Activation
#RandomNormal Import
#RandomNormal is an initializer used for weight initialization in certain layers
from keras import initializers
from keras.initializers import RandomNormal
#optimizers
from keras.optimizers import Adam, RMSprop, SGD
from matplotlib import pyplot
import numpy as np
from math import sqrt


# In[2]:


#Loading Datasets
(X_train, _), (_, _) = fashion_mnist.load_data()
#suitable format,range[-1,1]
X_train = X_train.astype(np.float32) / 127.5 - 1
#expanding dim(cnn),(h,w,channel)2Dto3D
X_train = np.expand_dims(X_train, axis=3)
print(X_train.shape)
len(X_train)


# In[3]:


#latent_dim=size,n_sam=samp to gen
def generate_latent_points(latent_dim, n_samples):
    #gen array of rand no.,randn=gen values(nrmldistbtn=mean0,std dvtn1)
    x_input = randn(latent_dim * n_samples)#1D
    z_input = x_input.reshape(n_samples, latent_dim)#2D
    return z_input#row=latent vector,col=feature,input for gan


# In[4]:


#used to create real data for training a gan 
def generate_real_samples(X_train, n_samples):
    ix = randint(0, X_train.shape[0], n_samples) #nsam from x_train
    X = X_train[ix]#subset of real data
    y = ones((n_samples, 1))#labeled as 1
    return X, y#tuple,helping discriminator


# In[5]:


def generate_fake_samples(generator, latent_dim, n_samples):#nsam=gen fake data
    z_input = generate_latent_points(latent_dim, n_samples)#input(latentvect)
    images = generator.predict(z_input)#produce fake data  
    y = zeros((n_samples, 1))#labeled as 0
    return images, y#generated fake images,labels


# In[6]:


#evaluate and visualize
def summarize_performance(step, g_model, latent_dim, n_samples=100):
    X, _ = generate_fake_samples(g_model, latent_dim, n_samples)
    X = (X + 1) / 2.0#range [0, 1]
    for i in range(100):
        pyplot.subplot(10, 10, 1 + i)
        pyplot.axis('off')#removing axis label
        pyplot.imshow(X[i, :, :, 0], cmap='gray_r')#X=fakeimg(n,h,w,channel)(i-index(0-99img))
    filename2 = 'model_%04d.h5' % (step+1)
    g_model.save(filename2)
    print('>Saved: %s' % (filename2))


# In[7]:


def save_plot(examples, n_examples):#(ex=total no.img,n_ex=to display in grid)
    for i in range(n_examples):
        pyplot.subplot(sqrt(n_examples), sqrt(n_examples), 1 + i)#(9=3*3,current)
        pyplot.axis('off')
        pyplot.imshow(examples[i, :, :, 0], cmap='gray_r')
    pyplot.show()


# In[8]:


#Model Building
def define_discriminator(in_shape=(28, 28, 1)):
    init = RandomNormal(stddev=0.02)#Weight initialization
    in_image = Input(shape=in_shape)#28*28
    fe = Flatten()(in_image)
    fe = Dense(1024)(fe)
    fe = LeakyReLU(alpha=0.2)(fe)
    fe = Dropout(0.3)(fe)
    fe = Dense(512)(fe)
    fe = LeakyReLU(alpha=0.2)(fe)
    fe = Dropout(0.3)(fe)
    fe = Dense(256)(fe)
    fe = LeakyReLU(alpha=0.2)(fe)
    fe = Dropout(0.3)(fe)
    out = Dense(1, activation='sigmoid')(fe)#real (close to 1) or fake (close to 0)
    model = Model(in_image, out)
    opt = Adam(lr=0.0002, beta_1=0.5) 
    model.compile(loss='binary_crossentropy', optimizer=opt, metrics=['accuracy'])
    return model


discriminator = define_discriminator()


# In[9]:


def define_generator(latent_dim): 
    init = RandomNormal(stddev=0.02)
    in_lat = Input(shape=(latent_dim,)) 
    gen = Dense(256, kernel_initializer=init)(in_lat)
    gen = LeakyReLU(alpha=0.2)(gen)
    gen = Dense(512, kernel_initializer=init)(gen)
    gen = LeakyReLU(alpha=0.2)(gen)
    gen = Dense(1024, kernel_initializer=init)(gen)
    gen = LeakyReLU(alpha=0.2)(gen)
    gen = Dense(28 * 28 * 1, kernel_initializer=init)(gen)
    out_layer = Activation('tanh')(gen)#range of [-1, 1]
    out_layer = Reshape((28, 28, 1))(gen)
    model = Model(in_lat, out_layer)
    return model
generator = define_generator(100)


# In[10]:


#combining both
def define_gan(g_model, d_model):#g-generating,d=discriminating
    d_model.trainable = False#non-trainable
    gan_output = d_model(g_model.output)
    model = Model(g_model.input, gan_output)
    opt = Adam(lr=0.0002, beta_1=0.5)
    model.compile(loss='binary_crossentropy', optimizer=opt, metrics=['accuracy'])
    return model
gan_model = define_gan(generator, discriminator)


# In[11]:


#to monitor 
def train(g_model, d_model, gan_model, X_train, latent_dim, n_epochs=100, n_batch=64):
    bat_per_epo = int(X_train.shape[0] / n_batch)#how many batch_size
    n_steps = bat_per_epo * n_epochs#training steps
    for i in range(n_steps):
        X_real, y_real = generate_real_samples(X_train, n_batch)#real data,generate_real_samples
        d_loss_r, d_acc_r = d_model.train_on_batch(X_real, y_real)#from rel data loss,acc
        X_fake, y_fake = generate_fake_samples(g_model, latent_dim, n_batch)#fake data,generate_fake_samples
        d_loss_f, d_acc_f = d_model.train_on_batch(X_fake, y_fake)#from fake data loss,acc
        z_input = generate_latent_points(latent_dim, n_batch)
        y_gan = ones((n_batch, 1)) 
        g_loss, g_acc = gan_model.train_on_batch(z_input, y_gan)#from latent vectors
        print('>%d, dr[%.3f,%.3f], df[%.3f,%.3f], g[%.3f,%.3f]' % (i+1, d_loss_r,d_acc_r, d_loss_f,d_acc_f, g_loss,g_acc))
        if (i+1) % (bat_per_epo * 1) == 0:
            summarize_performance(i, g_model, latent_dim)
latent_dim = 100
train(generator, discriminator, gan_model, X_train, latent_dim, n_epochs=2, n_batch=64)


# In[21]:


#Generating Samples Using GAN to montior model performance
model = load_model('model_2811.h5')
latent_dim = 100
n_examples = 100
latent_points = generate_latent_points(latent_dim, n_examples)
X  = model.predict(latent_points)
X = (X + 1) / 2.0
def save_plot(examples, n_examples):
    # Calculate the number of rows and columns as integers
    n_rows = int(sqrt(n_examples))
    n_cols = int(sqrt(n_examples))

    for i in range(n_examples):
        pyplot.subplot(n_rows, n_cols, 1 + i)  # Use n_rows and n_cols
        pyplot.axis('off')
        pyplot.imshow(examples[i, :, :, 0], cmap='gray_r')

pyplot.show()


# In[ ]:




