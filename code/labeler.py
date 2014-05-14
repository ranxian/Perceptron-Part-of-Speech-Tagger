# coding: utf-8
from __future__ import division
from collections import defaultdict
import random
from perceptron import Perceptron
from helper import printc
from helper import cstr
import copy
import IOBData
import sys


class Labeler:
    def __init__(self):
        '''map of single tag words'''
        self.single_tag_words = {}
        self.chk_set = set()
        self.perceptron = Perceptron()

    def train(self, sents, niter):
        # make single_tag_words
        self.perceptron.reset()
        roled_sents = sents
        # self._make_stw(roled_sents)
        self.role_set = set(role for sent in roled_sents for (word, tag, chunk, role) in sent)
        self.perceptron.tag_set = self.role_set
        length = int(len(roled_sents))

        for iteration in range(niter):
            ncorrect = 0
            ntotal = 0
            for sent in roled_sents[:length]:
                sent  = [(self._normalize(word), tag, chk, role) for (word, tag, chk, role) in sent]
                for idx, (word, tag, chk, role) in enumerate(sent):
                    # pred = self.single_tag_words.get(word)
                    pred = None
                    if not pred:
                        features = self._get_features(idx, sent)
                        pred = self.perceptron.predict(features)
                        self.perceptron.update(role, pred, features)
                    # successful prediction
                    ncorrect += pred == role
                    ntotal += 1
            random.shuffle(roled_sents)
            print "iteration #{0}, {1}/{2}=precision: {3}".format(iteration,
                                                          ncorrect, ntotal, ncorrect / ntotal)

        self.perceptron.average_weights()

    def _make_stw(self, chked_sents):
        counts = defaultdict(lambda: defaultdict(int))
        for sent in chked_sents:
            sent = [(self._normalize(word), tag, chunk, role) for (word, tag, chunk, role) in sent]
            for word, tag, chunk, role in sent:
                counts[word][role] += 1

        threshold = 0.95
        freqthres = 15

        for word, tag_freqs in counts.items():
            role, freq = max(tag_freqs.items(), key=lambda item: item[1])
            total = sum(tag_freqs.values())
            if freq >= freqthres and freq / total >= threshold:   # unambiguity
                self.single_tag_words[word] = role
            elif freq == total and total >= 3:
                self.single_tag_words[word] = role


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

    def _make_features(self, current, prev1, prev2, fword1, fword2):
        def add(name, *args):
            features['_'.join((name, ) + tuple(args))] = 1

        word, tag, chk, role = current
        pword1, ptag1, pchk1, prole1 = prev1
        pword2, ptag2, pchk2, prole2 = prev2
        fword1, ftag1, fchk1 = fword1
        fword2, ftag2, fchk2 = fword2

        features = defaultdict(int)

        if chk != 'VP':
            add('i chunk', chk)
        add('bias')
        add('i word', word)
        add('i tag', tag)
        
        add('i-1 word', pword1)
        add('i-1 tag', ptag1)
        add('i-1 role', prole1)
        add('i-1 chunk', pchk1)

        add('i-2 tag', ptag2)
        add('i-2 word', pword2)
        add('i-2 role', prole2)
        add('i-2 chunk', pchk2)

        add('i+1 word', fword1)
        add('i+1 tag', ftag1)
        add('i+1 chunk', pchk1)

        add('i+2 word', fword2)
        add('i+2 tag', ftag2)
        add('i+2 chunk', pchk2)

        if prole1[0] == 'E' or prole1[0] == 'O':
            add('out role')
        elif prole1[0] == 'I' or prole1[0] == 'B':
            add('in role', prole1.split('-')[1])

        return features
        

    # current, prev1, prev2, after1, after2
    def _get_features(self, i, sent):
        def add(name, *args):
            features['_'.join((name, ) + tuple(args))] = 1

        def deletes(word):
            return word[1:] if word[0] == '*' else word

        def pretag(j):
            if j < 0:
                return 'START1_TAG'
            elif j >= len(sent):
                return 'END1_TAG'
            else:
                word, pos, chk, role = sent[j]
                if pos == 'PP':
                    return word
                else:
                    return pos

        def prechk(j):
            if j == -2:
                return 'START2_CHK'
            elif j == -1:
                return 'START1_CHK'
            elif j == len(sent):
                return 'END1_CHK'
            elif j == len(sent)+1:
                return 'END2_CHK'
            else:
                return sent[j][2]

        pword1, ptag1, pchk1, prole1 = ('START1_WORD', 'START1_TAG', 'START1_CHK', 'START1_ROLE') if i <= 0 else sent[i-1]
        pword2, ptag2, pchk2, prole2 = ('START2_WORD', 'START2_TAG', 'START2_CHK', 'START2_ROLE') if i <= 1 else sent[i-2]
        word, tag, chk, role = sent[i]
        fword1, ftag1, fchk1, frole1 = ('END1_WORD', 'END1_TAG', 'END1_CHK', 'END1_ROLE') if i >= len(sent)-1 else sent[i+1]
        fword2, ftag2, fchk2, frole2 = ('END2_WORD', 'END2_TAG', 'END2_CHK', 'END2_ROLE') if i >= len(sent)-2 else sent[i+2]

        pword1 = deletes(pword1)
        pword2 = deletes(pword2)
        word = deletes(word)
        fword1 = deletes(fword1)
        fword2 = deletes(fword2)

        sent_len = len(sent)

        features = defaultdict(int)

        hasa0 = False
        for j in range(0, i):
            if 'A0' in sent[j][3]:
                hasa0 = True
                break
        add('i has-A0') if hasa0 else add('i No-A0')

        pred_pos = 0
        predicate = None

        if word[0] == '*':
            add('i is-predicate')
            word = word[:1]
            pred_pos = i
        else:
            for j in range(len(sent)):
                if sent[j][0][0] == '*':
                    pred_pos = j
                    predicate = sent[j]

            if pred_pos < i:
                add('i before')
            else:
                add('i after')

            r = range(i, pred_pos+1) if i < pred_pos else range(pred_pos, i+1)
            r2 = range(i+1, pred_pos) if i < pred_pos else range(pred_pos+1, i)

            path = []
            nbp, nvp, nnp = 0, 0, 0
            for j in r:
                if j == i:
                    path.append(word)
                elif j == pred_pos:
                    path.append(sent[j][1])
                else:
                    path.append(sent[j][2])

            for j in r2:
                if sent[j][2] != 'O':
                    nbp += 1
                if sent[j][2] == 'VP':
                    nvp += 1
                if sent[j][2] == 'NP':
                    nnp += 1
            path = '-'.join(path)
            add('i path', path)
            add('i D-BP', str(nbp))
            add('i D-VP', str(nvp))
            add('i D-NP', str(nnp))

        predicate = sent[pred_pos]
        pre_word, pre_pos, pre_chk, pre_role = predicate
        pre_word = pre_word[1:]
        pre_role = 'E-V'

        add('pred', pre_word)
        add('pred-tag', pre_pos)
        add('pred-before-tag', pretag(pred_pos-1))
        add('pred-after-tag', pretag(pred_pos+1))

        add('pred-1 bp', prechk(pred_pos-1))
        add('pred-2 bp', prechk(pred_pos-2))
        add('pred+1 bp', prechk(pred_pos+1))
        add('pred+2 bp', prechk(pred_pos+2))
          
        if i == 0:
            add('i begin')

        if i == len(sent)-1:
            add('i end')

        add('i chunk', chk)
        add('bias')
        add('i word', word)
        add('i tag', tag)
        add('i suffix2', word[-6:])
        add('i suffix1', word[-3:])
        
        add('i-1 word', pword1)
        add('i-1 tag', ptag1)
        add('i-1 role', prole1)
        add('i-1 chunk', pchk1)

        add('i-2 tag', ptag2)
        add('i-2 word', pword2)
        add('i-2 role', prole2)
        add('i-2 chunk', pchk2)

        add('i+1 word', fword1)
        add('i+1 tag', ftag1)
        add('i+1 chunk', pchk1)

        add('i+2 word', fword2)
        add('i+2 tag', ftag2)
        add('i+2 chunk', pchk2)

        if prole1[0] == 'E' or prole1[0] == 'O':
            add('out role')
        elif prole1[0] == 'I' or prole1[0] == 'B':
            add('in role', prole1[2:])

        return features

    def tag(self, tagged_sent):
        roled = [[self._normalize(word), tag, chk, None] for word, tag, chk in tagged_sent]

        for it in range(3):
            for idx, (word, tag, chunk, role) in enumerate(roled):
                # pred = self.single_tag_words.get(word)
                pred = None
                if not pred:
                    features = self._get_features(idx, roled)
                    if features['i is-predicate'] == 1:
                        pred = 'E-V'
                    else:
                        pred = self.perceptron.predict(features)
                roled[idx][3] = pred

        # in_role = 'O'
        # for idx, (word, tag, chunk, role) in enumerate(roled):
        #     if role[0] == 'E':
        #         in_role = 'O'
        #     elif role[0] == 'B':
        #         in_role = role[2:]
        #     else:
        #         if in_role == 'O':
        #             roled[idx][3] = 'O'
        #         else:
        #             roled[idx][3] = 'I-' + in_role

        return roled

    def tag2(self, sent):
        tagged = [[self._normalize(word), pos, chk, None] for word, pos, chk in sent]

        nword = len(sent)
        ntag = len(self.role_set)
        pi = [[[[0, None, None] for k in range(ntag)] for j in range(ntag)] for i in range(nword)]

        for i, (word, tag, chk, role) in enumerate(tagged):
            pword1, ptag1, pchk1 = ('START1_WORD', 'START1_TAG', 'START1_CHK') if i <= 0 else tagged[i-1][:3]
            pword2, ptag2, pchk2 = ('START2_WORD', 'START2_TAG', 'START2_CHK') if i <= 1 else tagged[i-2][:3]
            word, tag, chk = tagged[i][:3]
            fword1, ftag1, fchk1 = ('END1_WORD', 'END1_TAG', 'END1_CHK') if i >= len(tagged)-1 else tagged[i+1][:3]
            fword2, ftag2, fchk2 = ('END2_WORD', 'END2_TAG', 'END2_CHK') if i >= len(tagged)-2 else tagged[i+2][:3]
            for j, u in enumerate(self.role_set):
                prole2 = 'START2_ROLE' if i <= 0 else u
                for k, v in enumerate(self.role_set):
                    prole1 = 'START1_ROLE' if i <= 1 else v
                    for t, role in enumerate(self.role_set):
                        score = 0 if i <= 0 else pi[i-1][t][j][0]
                        score += self.perceptron.get_score(self._make_features(
                            (word, tag, chk, role), (pword1, ptag1, pchk1, prole1), (pword2, ptag2, pchk2, prole2), (fword1, ftag1, fchk1), 
                            (fword2, ftag2, fchk2)), role)
                        if score > pi[i][j][k][0]:
                            pi[i][j][k][0] = score
                            pi[i][j][k][1] = role
                            pi[i][j][k][2] = t
        i = len(tagged)-1
        t, j = None, None
        for j, u in enumerate(self.role_set):
            for k, v in enumerate(self.role_set):
                tag, t = pi[i][j][k][1:3]
                tagged[i][3] = tag
        i -= 1
        while i >= 0:
            tagged[i][3] = pi[i][t][j][1]
            j = t
            t = pi[i][t][j][2]
            i -= 1
        printc(tagged)

        return tagged

    def evaluate(self, roled_sents):
        ntotal = 0
        ncorrect = 0
        faults = []
        likely = {}
        faults_count = defaultdict(int)

        f = open('props.txt', 'w')
        for roled_sent in roled_sents:
            tagged_sent = [(word, tag, chunk) for (word, tag, chunk, role) in roled_sent]
            roled = self.tag(tagged_sent)

            for idx, (word, tag, chunk, role) in enumerate(roled):
                thword = tagged_sent[idx][0]
                if thword[0] == '*':
                    thword = thword[1:]
                f.write('%s\t%s\t%s\t%s\n' % (thword, tag, chunk, role))
            f.write('\n')
            has_false = False
            for idx, (word, tag, chunk, role) in enumerate(roled_sent):
                ntotal += 1
                if role == roled[idx][3]:
                    ncorrect += 1
                else:
                    has_false = True
            if has_false:
                record = []
                for idx, (word, tag, chunk, role) in enumerate(roled_sent):
                    if role == roled[idx][3]:
                        record.append((word, tag, chunk, role))
                    else:
                        record.append((word, tag, chunk, role, '【' + roled[idx][3] + '】'))
                        faults_count[role + ' is roled as ' + roled[idx][3]] += 1
                faults.append(record)

        print 'precision:', ncorrect / ntotal * 100, '%'
        sorted_fault_count = sorted(faults_count.items(), key=lambda item: item[1], reverse=True)
        f.close()
        # for key, value in sorted_fault_count:
            # print key, value
        return faults


train_rate = 0.93
test_rate = 1 - train_rate

ntrain = int(len(IOBData.dev_iob.sents) * train_rate)
ntest = int(len(IOBData.dev_iob.sents) * test_rate)
labeler = Labeler()

faults = []
if len(sys.argv) > 1:
    niter = int(sys.argv[2])
    if sys.argv[1] == 'real':
        labeler.train(IOBData.trn_iob.sents, niter)
        faults = labeler.evaluate(IOBData.dev_iob.sents)
    else:
        labeler.train(IOBData.dev_iob.sents[:ntrain], niter)
        faults = labeler.evaluate(IOBData.dev_iob.sents[ntrain:ntrain+ntest])


f = open('log.txt', 'w')
for fault in faults:
    f.write(cstr(fault))
    f.write('\n\n')
