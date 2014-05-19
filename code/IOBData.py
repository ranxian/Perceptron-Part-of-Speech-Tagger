class IOBData:
    def __init__(self, token_file_path):
        self.sents = []
        token_file = open(token_file_path, 'r')

        tokens = []
        while True:
            line = token_file.readline()
            if line == '':
                break
            line = line.rstrip('\n')
            if line == '':
                self.sents.append(tokens)
                tokens = []
            else:
                word, pos, chunk, role = line.split('\t')
                tokens.append((word, pos, chunk, role))

        print '%d sents loaded' % len(self.sents)
        token_file.close()

trn_iob = IOBData('../data/trn2.tokens')
dev_iob = IOBData('../data/dev.tokens')
tst_iob = IOBData('test.tokens')
