import numpy as np
import tensorflow as tf
import pickle
import itertools

from data_generator import WordVector


class WordXCategory(object):

    def __init__(self, word_vector, som_size, n_categories, alpha=1.0, n_episodes=100):
        self.word_vector = word_vector
        self.som_size = som_size
        self.n_categories = n_categories
        self.alpha = alpha
        self.n_episodes = n_episodes

        self._sess = None

        self.words_x_categories = tf.Variable(tf.zeros([n_categories, word_vector.dim]), dtype=tf.float32)

        self._hebbian_weights = tf.placeholder("float", [word_vector.dim, som_size])
        hebb_weights_log_n = tf.div(tf.log(tf.clip_by_value(self._hebbian_weights, 1e-10, 1)), tf.log(tf.cast(som_size, dtype=tf.float32)))
        self.entropy_op = tf.negative(tf.reduce_sum(tf.multiply(self._hebbian_weights, hebb_weights_log_n), axis=1))

        self.input_iter = tf.placeholder("float")
        self.index = tf.placeholder(tf.int32)
        self.new_inverse_entropies = tf.placeholder("float", word_vector.dim)

        learning_rate = tf.subtract(1.0, tf.div(self.input_iter, self.n_episodes))
        _alpha = tf.multiply(self.alpha, learning_rate)

        new_inverse_entropies = tf.multiply(self.new_inverse_entropies, [_alpha])
        new_inverse_entropies = tf.pad(tf.reshape(new_inverse_entropies, [1, -1]), [[self.index, n_categories-1-self.index], [0, 0]])
        new_inverse_entropies = tf.add(self.words_x_categories, new_inverse_entropies)
        self.update_op = tf.assign(self.words_x_categories, new_inverse_entropies)

        entropy_sums = tf.reduce_sum(self.words_x_categories, axis=1)
        self.normalize_op = tf.assign(self.words_x_categories, tf.div(self.words_x_categories, tf.transpose(tf.stack([entropy_sums for i in range(word_vector.dim)]))))

    def entropy(self, hebb_weights):
        return self._sess.run(self.entropy_op, feed_dict={self._hebbian_weights: hebb_weights})

    def inverse_entropy(self, entropy_weights):
        return 1.0 - entropy_weights

    def update_words_x_categories(self, new_inverse_entropies, index, curr_iteration):
        return self._sess.run(self.update_op, feed_dict={self.new_inverse_entropies: new_inverse_entropies, self.index: index, self.input_iter: float(curr_iteration)})

    def normalize_all(self):
        return self._sess.run(self.normalize_op)


if __name__ == "__main__":
    word_vector = WordVector()
    som_size = 16*16
    word_to_meaning = WordXCategory(word_vector, som_size, 4)
    word_to_meaning._sess = tf.Session()
    word_to_meaning._sess.run(tf.global_variables_initializer())

    h = pickle.load(open("hebb_weights_1542724910.pickle", "rb"))
    hebb_weights = []
    for _h in h:
        hebb_weights.append(_h[0])
    hebb_weights = np.array(hebb_weights)

    entropy_weights = np.zeros([4, 16])
    for i, h in enumerate(hebb_weights):
        inv_entropy = word_to_meaning.inverse_entropy(word_to_meaning.entropy(h))
        entropy_weights = word_to_meaning.update_words_x_categories(inv_entropy, i)
        print(entropy_weights)
    entropy_weights = word_to_meaning.normalize_all()
    print(entropy_weights)
    # pickle.dump(entropy_weights, open("entropy_weights.pickle", "wb"))
    exit()
