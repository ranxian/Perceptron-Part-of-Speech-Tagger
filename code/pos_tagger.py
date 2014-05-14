# -*- coding: utf-8 -*-
from __future__ import division
import nltk
from helper import printc


class PerceptronTagger:
    def __init__(self, dataset):
        self.dataset = dataset
        self.thetas = []
        self.vocabulary = self.high_freq_vocabulary()
        self.tag_set = dataset.tag_set
        self.train(dataset.tagged_sents)

    def train(self, tagged_sents):
        # get features
        features = self.extract_features(tagged_sents)
        # initial theta
        self.thetas = [0] * len(features[0])
        print len(self.thetas)

    def tag(self, sent):
        pass

    def extract_features(self, tagged_sents):
        features = []
        self.vdict = {}
        self.tdict = {}
        for i in range(len(self.vocabulary)):
            word = self.vocabulary[i]
            self.vdict[word] = i
        for idx, val in enumerate(self.tag_set):
            self.tdict[val] = idx

        i = 0
        for tagged_sent in tagged_sents:
            for history in nltk.bigrams(tagged_sent):
                features.append(self.extract_feature_from_history(history))
            i += 1
            print i, 'processed'

        return features

    def high_freq_vocabulary(self):
        freq = nltk.FreqDist(self.dataset.words)
        vocabulary = []

        cover = 0
        total = len(self.dataset.words)
        for (word, count) in freq.items():
            vocabulary.append(word)
            cover += count
            if cover / total >= 0.7:
                break
        return vocabulary

    def extract_feature_from_history(self, history):
        nfeature1 = len(self.vocabulary) * len(self.tag_set)
        nfeature2 = len(self.vocabulary)
        nfeature3 = len(self.tag_set)
        nfeature = nfeature1 + nfeature2 + nfeature3
        feature = [0] * nfeature

        word = history[0][0]
        tag = history[1][1]
        if word in self.vdict:
            index = self.vdict[word] * len(self.tag_set) + self.tdict[tag]
            feature[index] = 1
            index = nfeature1 + self.vdict[word]
            feature[index] = 1
            index = nfeature2 + self.tdict[tag]
            feature[index] = 1

        return feature

import dataset
tagger = PerceptronTagger(dataset.test)
