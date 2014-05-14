# -*- coding: utf-8 -*-


class Dataset:
    """
    self.words
    self.tagged_words
    self.sents
    self.tagged_sents
    """
    def __init__(self, wrd_file, pos_chk_file, srl_file):
        wrd = open(wrd_file, 'r')
        pos_chk = open(pos_chk_file, 'r')
        srl = open(srl_file, 'r')


        self.sents = []
        self.tagged_sents = []
        self.chked_sents = []
        self.words = []
        self.tagged_words = []
        self.vocabulary = []
        self.tag_set = []

        self.srl_tokens = []

        sent = []
        tagged_sent = []
        chked_sent = []

        while True:
            word = wrd.readline()
            line = pos_chk.readline()

            if word == '\n' or word == '':
                if len(sent) > 0:
                    self.sents.append(sent)
                if len(tagged_sent) > 0:
                    self.tagged_sents.append(tagged_sent)
                if (len(chked_sent) > 0):
                    self.chked_sents.append(chked_sent)
                sent = []
                tagged_sent = []
                chked_sent = []
                if word == '\n':
                    continue
                else:
                    break

            word = word.rstrip('\n')
            tag, chunk = line.rstrip('\n').split('\t')
            sent.append(word)
            tagged_sent.append((word, tag))
            chked_sent.append((word, tag, chunk))

            self.words.append(word)
            self.tagged_words.append((word, tag))

        self.vocabulary = set(self.words)
        self.tag_set = set(tag for (word, tag) in self.tagged_words)

        print len(self.sents), 'sentences,', len(self.words), 'words'


train = Dataset('../data/trn.wrd', '../data/trn.pos-chk')
develop = Dataset('../data/dev.wrd', '../data/dev.pos-chk')