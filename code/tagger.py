# coding: utf-8
from __future__ import division
from collections import defaultdict
import random
import dataset
from perceptron import Perceptron
from helper import printc
from helper import cstr
import copy
import time


class Tagger:
    def __init__(self):
        '''map of single tag words'''
        self.single_tag_words = {}
        self.tag_set = set()
        self.perceptron = Perceptron()

    def train(self, sents, niter):
        # make single_tag_words
        self.perceptron.reset()
        tagged_sents = sents
        self._make_stw(tagged_sents)
        self.tag_set = set(tag for sent in tagged_sents for (word, tag) in sent)
        self.perceptron.tag_set = self.tag_set
        length = int(len(tagged_sents))

        for iteration in range(niter):
            ncorrect = 0
            ntotal = 0
            for sent in tagged_sents[:length]:
                sent = [(self._normalize(word), tag) for (word, tag) in sent]
                for idx, (word, tag) in enumerate(sent):
                    pred = self.single_tag_words.get(word)
                    if not pred:
                        features = self._get_features(idx, sent)
                        pred = self.perceptron.predict(features)
                        self.perceptron.update(tag, pred, features)
                    # successful prediction
                    ncorrect += pred == tag
                    ntotal += 1
            random.shuffle(tagged_sents)
            print "iteration #{0}, {1}/{2}=precision: {3}".format(iteration,
                                                          ncorrect, ntotal, ncorrect / ntotal)

        self.perceptron.average_weights()

    def _make_stw(self, tagged_sents):
        counts = defaultdict(lambda: defaultdict(int))
        for sent in tagged_sents:
            sent = [(self._normalize(word), tag) for (word, tag) in sent]
            for word, tag in sent:
                counts[word][tag] += 1

        threshold = 0.95
        freqthres = 15

        for word, tag_freqs in counts.items():
            tag, freq = max(tag_freqs.items(), key=lambda item: item[1])
            total = sum(tag_freqs.values())
            if freq >= freqthres and freq / total >= threshold:   # unambiguity
                self.single_tag_words[word] = tag
            elif tag == 'NR':
                self.single_tag_words[word] = tag
            elif freq == total and total >= 3:
                self.single_tag_words[word] = tag


        # self.single_tag_words['的'] = 'DEG'
        self.single_tag_words['－'] = 'PU'
        self.single_tag_words['－－'] = 'PU'

    def _normalize(self, word):
        def isnum(word):
            return word.endswith(tuple('一 二 三 四 五 六 七 八 九 十 百 千 万 亿 两'.split(' ')))

        def iscal(word):
            return word.endswith(('年', '月', '日', '年代'))

        if (isnum(word)):
            return 'NUM'

        if (iscal(word)):
            return 'CAL'

        if (word.endswith(('省', '市', '区', '州', '县', '镇', '乡', '街'))):
            return 'LOCATION'

        return word

    # current, prev1, prev2, after1, after2
    def _make_features(self, current, prev1, prev2, fword1, fword2):
        def add(name, *args):
            features['_'.join((name, ) + tuple(args))] = 1

        word, tag = current
        pword1, ptag1 = prev1
        pword2, ptag2 = prev2

        features = defaultdict(int)
        add('bias')
        if word[0] == '*':
            add('i is v')
        else:
            add('i not v')
        add('i suffix', word[-3:])
        add('i-1 suffix', pword1[-3:])
        add('i+1 suffix', fword1[-3:])
        add('i suffix2', word[-6:])
        add('i-1 suffix', pword1[-6:])
        add('i+1 suffix', fword2[-6:])
        # add('i prefix', word[:3])
        # add('i-1 prefix', pword1[:3])
        # add('i-2 prefix', pword2[:3])
        add('i-1 tag', ptag1)
        add('i-2 tag', ptag2)
        add('i-1 i-2 tag', ptag1, ptag2)
        add('i-2 word', pword2)
        add('i-1 word', pword1)
        add('i word', word)
        add('i-2 i-1 word', fword2, fword1)
        add('i+1 word', fword1)
        add('i+2 word', fword2)
        add('i+1 i+2 word', fword1, fword2)
        add('i-1 tag i word', ptag1, word)
        add('i-2 tag i-1 word', ptag2, pword1)
        add('i word-len', str(len(word)))
        # if word != 'NUM' and word != 'CAL' and len(word) >= 6:
        #     for i in range(int(len(word) / 3)):
        #         add(str(i), ' charactor', word[i*3:(i+1)*3])

        return features

    def _get_features(self, i, sent):
        pword1, ptag1 = ('START1_WORD', 'START1_TAG') if i <= 0 else sent[i-1]
        pword2, ptag2 = ('START2_WORD', 'START2_TAG') if i <= 1 else sent[i-2]
        word, tag = sent[i]
        fword1, ftag1 = ('END1_WORD', 'END1_TAG') if i >= len(sent)-1 else sent[i+1]
        fword2, ftag2 = ('END2_WORD', 'END2_TAG') if i >= len(sent)-2 else sent[i+2]
        return self._make_features((word, tag), (pword1, ptag1), (pword2, ptag2), fword1, fword2)

    def tag(self, sent):
        tagged = [[self._normalize(word), None] for word in sent]

        for idx, (word, tag) in enumerate(tagged):
            pred = self.single_tag_words.get(word)
            if not pred:
                features = self._get_features(idx, tagged)
                pred = self.perceptron.predict(features)
            tagged[idx][1] = pred

        return tagged

    def tag2(self, sent):
        tagged = [[self._normalize(word), None] for word in sent]

        nword = len(sent)
        ntag = len(self.tag_set)
        pi = [[[[0, None, None] for k in range(ntag)] for j in range(ntag)] for i in range(nword)]

        for i, (word, tag) in enumerate(tagged):
            pword1 = 'START1_WORD' if i <= 0 else tagged[i-1][0]
            pword2 = 'START2_WORD' if i <= 1 else tagged[i-2][0]
            fword1 = 'END1_WORD' if i >= len(sent)-1 else tagged[i+1][0]
            fword2 = 'END2_WORD' if i >= len(sent)-2 else tagged[i+2][0]
            for j, u in enumerate(self.tag_set):
                ptag2 = 'START1_TAG' if i <= 0 else u
                for k, v in enumerate(self.tag_set):
                    ptag1 = 'START2_TAG' if i <= 1 else v
                    for t, tag in enumerate(self.tag_set):
                        score = 0 if i <= 0 else pi[i-1][t][j][0]
                        score += self.perceptron.get_score(self._make_features((word, tag), (pword1, ptag1), (pword2, ptag2), fword1, fword2), tag)
                        if score > pi[i][j][k][0]:
                            pi[i][j][k][0] = score
                            pi[i][j][k][1] = tag
                            pi[i][j][k][2] = t
        i = len(tagged)-1
        t, j = None, None
        for j, u in enumerate(self.tag_set):
            for k, v in enumerate(self.tag_set):
                tag, t = pi[i][j][k][1:3]
                tagged[i][1] = tag
        i -= 1
        while i >= 0:
            tagged[i][1] = pi[i][t][j][1]
            j = t
            t = pi[i][t][j][2]
            i -= 1
        printc(tagged)

        return tagged

    def evaluate(self, tagged_sents, log=False):
        ntotal = 0
        ncorrect = 0
        faults = []
        likely = {}
        faults_count = defaultdict(int)
        file = open('test.pos', 'w')

        for tagged_sent in tagged_sents:
            sent = [word for (word, tag) in tagged_sent]
            tagged = self.tag(sent)
            for word, tag in tagged:
                # print word, tag,
                if tag == 'NR' and not word in likely:
                    likely[word] = 'NR'

        for tagged_sent in tagged_sents:
            sent = [word for (word, tag) in tagged_sent]
            tagged = self.tag(sent)
            # for idx, (word, tag) in enumerate(tagged):
            #     if word in likely:
            #         tagged[idx][1] = 'NR'
            has_false = False

            for (word, tag) in tagged:
                word = word[1:] if word[0] == '*' else word
                file.write('%s\t%s\n' % (word, tag))
                
            file.write('\n')

            if log:
                for idx, (word, tag) in enumerate(tagged_sent):
                    ntotal += 1
                    if tag == tagged[idx][1] or (tag[0] == 'N' and tagged[idx][1][0] == 'N') or (tag == 'DEC' and tagged[idx][1] == 'DEG') or \
                        (tag == 'DEG' and tagged[idx][1] == 'DEC') or ((tag[0] == 'V' and tagged[idx][1][0] == 'V')):
                        ncorrect += 1
                    else:
                        has_false = True
            if log:
                if has_false:
                    record = []
                    for idx, (word, tag) in enumerate(tagged_sent):
                        if tag == tagged[idx][1] or (tag[0] == 'N' and tagged[idx][1][0] == 'N') or (tag == 'DEC' and tagged[idx][1] == 'DEG') or \
                        (tag == 'DEG' and tagged[idx][1] == 'DEC') or (tag[0] == 'V' and tagged[idx][1][0] == 'V'):
                            record.append((word, tag, tagged[idx][1]))
                        else:
                            record.append((word, tag, '【' + tagged[idx][1] + '】'))
                            faults_count[tag + ' is tagged as ' + tagged[idx][1]] += 1
                    faults.append(record)

        if log:
            print 'precision:', ncorrect / ntotal * 100, '%'
        file.close()
        if log:
            sorted_fault_count = sorted(faults_count.items(), key=lambda item: item[1], reverse=True)
            for key, value in sorted_fault_count:
                print key, value
        return faults


tagger = Tagger()
start = time.clock()
tagger.train(dataset.train.tagged_sents, 7)
faults = tagger.evaluate(dataset.read_words('test.wrd', 'test.tgt'))
elapsed = time.clock() - start
print elapsed, 'secs'