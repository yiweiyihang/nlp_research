#-*- coding:utf-8 -*-
import tensorflow as tf
from common.layers import get_initializer
from common.activations import get_activation
from encoder import EncoderBase
#from kim cnn 2014:https://arxiv.org/abs/1408.5882


class TextCNN(EncoderBase):
    def __init__(self, **kwargs):
        super(TextCNN, self).__init__(**kwargs)
        self.embedding_size = kwargs['embedding_size']
        self.filter_sizes = [3, 4, 5]
        self.num_filters = 100

    def __call__(self, embed, name = 'encoder', reuse = tf.AUTO_REUSE, **kwargs):
        #input: [batch_size, sentence_len, embedding_size,1]
        #output:[batch_size, num_output]
        with tf.variable_scope("text_cnn", reuse = reuse):
            embed = tf.expand_dims(embed, -1)
            conv_outputs = []
            for i, size in enumerate(self.filter_sizes):
                with tf.variable_scope("conv%d" % i, reuse = reuse):
                    # Convolution Layer begins
                    conv_filter = tf.get_variable(
                        "conv_filter%d" % i, [size, self.embedding_size, 1, self.num_filters],
                        initializer=get_initializer(type = 'random_uniform',
                                                    minval = -0.01, 
                                                    maxval = 0.01)
                    )
                    bias = tf.get_variable(
                        "conv_bias%d" % i, [self.num_filters],
                        initializer=get_initializer(type = 'zeros')
                    )
                    output = tf.nn.conv2d(embed, conv_filter, [1, 1, 1, 1], "VALID") + bias
                    # Applying non-linearity
                    output = get_activation('swish')(output)
                    # Pooling layer, max over time for each channel
                    output = tf.reduce_max(output, axis=[1, 2])
                    conv_outputs.append(output)

            # Concatenate all different filter outputs before fully connected layers
            conv_outputs = tf.concat(conv_outputs, axis=1)
            h_pool_flat = tf.reshape(conv_outputs, [-1, self.num_filters * len(self.filter_sizes)])
            h_drop = tf.nn.dropout(h_pool_flat, self.keep_prob)
            dense = tf.layers.dense(h_pool_flat, 
                                    self.num_output, 
                                    kernel_regularizer=tf.contrib.layers.l2_regularizer(0.001),
                                    activation=None,
                                    reuse = reuse)
        return dense
