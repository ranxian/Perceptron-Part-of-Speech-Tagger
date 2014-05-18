# coding: utf-8
from __future__ import division
from collections import defaultdict
import random
import dataset
from perceptron import Perceptron
from helper import printc
from helper import cstr
import copy


class Chunker:
    def __init__(self):
        '''map of single tag words'''
        self.single_tag_words = {}
        self.chk_set = set()
        self.perceptron = Perceptron()

    def train(self, sents, niter):
        # make single_tag_words
        self.perceptron.reset()
        chked_sents = sents
        self._make_stw(chked_sents)
        self.chk_set = set(chunk for sent in chked_sents for (word, tag, chunk) in sent)
        self.perceptron.tag_set = self.chk_set
        length = int(len(chked_sents))

        for iteration in range(niter):
            ncorrect = 0
            ntotal = 0
            for sent in chked_sents[:length]:
                sent = [(self._normalize(word), tag, chk) for (word, tag, chk) in sent]
                for idx, (word, tag, chk) in enumerate(sent):
                    pred = self.single_tag_words.get(word)
                    if not pred:
                        features = self._get_features(idx, sent)
                        pred = self.perceptron.predict(features)
                        self.perceptron.update(chk, pred, features)
                    # successful prediction
                    ncorrect += pred == chk
                    ntotal += 1
            random.shuffle(chked_sents)
            print "iteration #{0}, {1}/{2}=precision: {3}".format(iteration,
                                                          ncorrect, ntotal, ncorrect / ntotal)

        self.perceptron.average_weights()

    def _make_stw(self, chked_sents):
        counts = defaultdict(lambda: defaultdict(int))
        for sent in chked_sents:
            sent = [(self._normalize(word), tag, chunk) for (word, tag, chunk) in sent]
            for word, tag, chunk in sent:
                counts[word][chunk] += 1

        threshold = 0.98
        freqthres = 15

        for word, tag_freqs in counts.items():
            chunk, freq = max(tag_freqs.items(), key=lambda item: item[1])
            total = sum(tag_freqs.values())
            if freq >= freqthres and freq / total >= threshold:   # unambiguity
                self.single_tag_words[word] = chunk
            elif freq == total and total >= 3:
                self.single_tag_words[word] = chunk


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
    def _get_features(self, i, sent):
        def add(name, *args):
            features['_'.join((name, ) + tuple(args))] = 1

        pword1, ptag1, pchk1 = ('START1_WORD', 'START1_TAG', 'START1_CHK') if i <= 0 else sent[i-1]
        pword2, ptag2, pchk2 = ('START2_WORD', 'START2_TAG', 'START2_CHK') if i <= 1 else sent[i-2]
        word, tag, chk = sent[i]
        fword1, ftag1, fchk1 = ('END1_WORD', 'END1_TAG', 'END1_CHK') if i >= len(sent)-1 else sent[i+1]
        fword2, ftag2, fchk2 = ('END2_WORD', 'END2_TAG', 'END2_CHK') if i >= len(sent)-2 else sent[i+2]

        # def deletes(word):
        #     return word[1:] if word[0] == '*' else word

        # deletes(word)
        # deletes(fword1)
        # deletes(fword2)
        # deletes(pword1)
        # deletes(pword2)

        features = defaultdict(int)
        add('bias')
        add('i word', word)
        add('i tag', tag)
        add('i tag prefix', tag[0])
        add('i suffix1', word[-3:])
        add('i-1 suffix1', word[-3:])

        add('i-1 word', pword1)
        add('i-1 tag', ptag1)
        add('i-1 tag prefix', ptag1[0])
        add('i i-1 word', word, pword1)
        add('i-2 i-1 i pos', ptag2, ptag1, tag)
        add('i-2 i-1 chunk', pchk2, pchk1)

        add('i-i i pos', ptag1, tag)
        add('i i+1 pos', tag, ftag1)
        add('i+1 word i pos', fword1, tag)
        add('i-1 word i pos', pword1, tag)
        add('i-1 pos i+1 pos', ptag1, ftag1)
        add('i pos i+2 pos', tag, ftag2)

        # add('i-1 tag i word', ptag1, word)
        # add('i-1 i-2 tag', ptag1, ptag2)
        add('i-2 word', ptag2)
        add('i-2 tag', ptag2)
        add('i-2 tag prefix', ptag2[0])
        # add('i-2 tag i-1 word', ptag2, pword1)

        add('i+1 word', fword1)
        add('i+1 tag', ftag1)
        add('i+1 tag prefix', ftag1[0])

        add('i+1 word', fword2)
        add('i+2 tag', ftag2)
        add('i+2 tag prefix', ftag2[0])

        for j in xrange(i-1, -1, -1):
            if sent[j][2].endswith(")"):
                add('out chunk', sent[j][2])
                break
            elif sent[j][2].startswith("("):
                add('in chunk', sent[j][2].split('*')[0][1:])

        for j in xrange(i-1, -1, -1):
            if sent[j][2].endswith(")"):
                for k in xrange(j, -1, -1):
                    if sent[k][2].startswith('('):
                        add('before chunk', sent[k][2].split('*')[0][1:])
                        break
            break

        if i == 0:
            add('i begin')
        elif i == len(sent)-1:
            add('i end')
        return features

    def tag(self, tagged_sent):
        chked = [[self._normalize(word), tag, None] for word, tag in tagged_sent]

        for idx, (word, tag, chunk) in enumerate(chked):
            pred = self.single_tag_words.get(word)
            if not pred:
                features = self._get_features(idx, chked)
                pred = self.perceptron.predict(features)
            chked[idx][2] = pred

        in_bracket = False
        for idx, (word, tag, chunk) in enumerate(chked):
            if chunk.startswith('('):
                if in_bracket:
                    if chunk.endswith(')'):  # in brack
                        j = idx-1
                        while j > 0:
                            if chked[j][2].startswith('('):
                                break
                            j -= 1
                        chked[idx][2] = '*' + chked[j][2][1:-1] + ')'
                        in_bracket = False
                    else:
                        chked[idx][2] = '*'
                else:
                    if not chunk.endswith(')'):
                        in_bracket = True
            elif chunk.endswith(')'):
                if in_bracket:
                    j = idx-1
                    while j > 0:
                        if chked[j][2].startswith('('):
                            break
                        j -= 1
                    chked[idx][2] = '*' + chked[j][2][1:-1] + ')'
                    in_bracket = False
                else:
                    chunk = chunk[1:-2]
                    chked[idx][2] = '(' + chunk + '*' + chunk + ')'
            else:
                if in_bracket:
                    if idx == len(chked)-1:
                        j = idx-1
                        while j > 0:
                            if chked[j][2].startswith('('):
                                break
                            j -= 1
                        chked[idx][2] = '*' + chked[j][2][1:-1] + ')'
                    else:
                        chked[idx][2] = '*'
            if in_bracket and idx == len(chked)-1:
                j = idx-1
                while j > 0:
                    if chked[j][2].startswith('('):
                        break
                    j -= 1
                chked[idx][2] = '*' + chked[j][2][1:-1] + ')'
        return chked

    def tag2(self, sent):
        tagged = [[self._normalize(word), None] for word in sent]

        nword = len(sent)
        ntag = len(self.chk_set)
        pi = [[[[0, None, None] for k in range(ntag)] for j in range(ntag)] for i in range(nword)]

        for i, (word, tag) in enumerate(tagged):
            pword1 = 'START1_WORD' if i <= 0 else tagged[i-1][0]
            pword2 = 'START2_WORD' if i <= 1 else tagged[i-2][0]
            fword1 = 'END1_WORD' if i >= len(sent)-1 else tagged[i+1][0]
            fword2 = 'END2_WORD' if i >= len(sent)-2 else tagged[i+2][0]
            for j, u in enumerate(self.chk_set):
                ptag2 = 'START1_TAG' if i <= 0 else u
                for k, v in enumerate(self.chk_set):
                    ptag1 = 'START2_TAG' if i <= 1 else v
                    for t, tag in enumerate(self.chk_set):
                        score = 0 if i <= 0 else pi[i-1][t][j][0]
                        score += self.perceptron.get_score(self._make_features((word, tag), (pword1, ptag1), (pword2, ptag2), fword1, fword2), tag)
                        if score > pi[i][j][k][0]:
                            pi[i][j][k][0] = score
                            pi[i][j][k][1] = tag
                            pi[i][j][k][2] = t
        i = len(tagged)-1
        t, j = None, None
        for j, u in enumerate(self.chk_set):
            for k, v in enumerate(self.chk_set):
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

    def evaluate(self, chked_sents, log=False):
        ntotal = 0
        ncorrect = 0
        faults = []
        likely = {}
        faults_count = defaultdict(int)

        # for chked_sent in chked_sents:
        #     tagged_sent = [(word, tag) for (word, tag, chunk) in chked_sents]
        #     chked = self.tag(tagged_sent)
        #     for word, tag in tagged:
        #         # print word, tag,
        #         if tag == 'NR' and not word in likely:
        #             likely[word] = 'NR'

        f = open('test.pos-chk', 'w')
        for chked_sent in chked_sents:
            tagged_sent = [(word, tag) for (word, tag, chunk) in chked_sent]
            chked = self.tag(tagged_sent)

            for word, tag, chunk in chked:
                f.write('%s\t%s\n' % (tag, chunk))
            f.write('\n')
            has_false = False
            for idx, (word, tag, chunk) in enumerate(chked_sent):
                ntotal += 1
                if chunk == chked[idx][2]:
                    ncorrect += 1
                else:
                    has_false = True
            if has_false and log:
                record = []
                for idx, (word, tag, chunk) in enumerate(chked_sent):
                    if chunk == chked[idx][2]:
                        record.append((word, tag, chunk))
                    else:
                        record.append((word, tag, chunk, '【' + chked[idx][2] + '】'))
                        faults_count[chunk + ' is chked as ' + chked[idx][2]] += 1
                faults.append(record)
        f.close()

        print 'precision:', ncorrect / ntotal * 100, '%'
        sorted_fault_count = sorted(faults_count.items(), key=lambda item: item[1], reverse=True)
        for key, value in sorted_fault_count:
            print key, value
        return faults

chunker = Chunker()
chunker.train(dataset.train.chked_sents, 5)
faults = chunker.evaluate(dataset.read_word_pos('test.pos'), log=False)

f = open('log2.txt', 'w')
for fault in faults:
    f.write(cstr(fault))
    f.write('\n\n')