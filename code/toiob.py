from helper import printc
import sys

def poschk2iob(pos_chk_path):
    poschk = open(pos_chk_path, 'r')
    dest = open(pos_chk_path+'.iob', 'w')
    
    in_chunk = 'O'
    while True:
        line = poschk.readline()
        if line == '':
            break
        line = line.rstrip('\n')
        if line != '':
            pos, chunk = line.split('\t')

            if chunk.startswith('(') and chunk.endswith(')'):
                head = chunk[1:-1]
                head = head[0:(len(head) / 2)]
                chunk = 'EB-' + head
                in_chunk = 'O'
            elif chunk.startswith('('):
                head = chunk[1:-1]
                chunk = 'B-' + head
                in_chunk = head
            elif chunk.endswith(')'):
                head = chunk[1:-1]
                chunk = 'E-' + head
                in_chunk = 'O'
            else:
                if in_chunk != 'O':
                    chunk = 'I-' + in_chunk
                else:
                    chunk = in_chunk

            dest.write('%s\t%s\n' % (pos, chunk))
        else:
            dest.write('\n')


    poschk.close()
    dest.close()

def srl2iob(srl_path, trn=False, test=False):
    srl = open(srl_path, 'r')
    dest = open(srl_path+'.iob', 'w')

    in_chunk = None
    preds = []
    while True:
        line = srl.readline()
        if line == '':
            break
        line = line.rstrip('\n')

        if line != '':
            if not test:
                sp = line.split('\t')
                word = sp[0]
                roles = sp[1:]

                if len(roles) == 0:
                    roles = ['O'] * 20

                for idx, role in enumerate(roles):
                    if in_chunk is None:
                        in_chunk = ['O'] * len(roles)
                    if role.startswith('(') and role.endswith(')'):
                        head = role[1:-2]
                        if trn:
                            head = head[0:(len(head) / 2)]
                        role = 'EB-' + head
                        in_chunk[idx] = 'O'
                    elif role.startswith('('):
                        head = role[1:-1]
                        role = 'B-' + head
                        in_chunk[idx] = head
                    elif role.endswith(')'):
                        role = 'E-' + in_chunk[idx]
                        in_chunk[idx] = 'O'
                    else:
                        if in_chunk[idx] != 'O':
                            role = 'I-' + in_chunk[idx]
                        else:
                            role = in_chunk[idx]
                    roles[idx] = role


                dest.write('%s\t%s\n' % (word, '\t'.join(roles)))
            else:
                word = line
                preds.append(word)
        else:
            if test:
                cnt = 0
                for p in preds:
                    if p != '-':
                        cnt += 1
                cnt = 1 if cnt == 0 else cnt
                roles = ['O'] * cnt
                for p in preds:
                    dest.write('%s\t%s\n' % (p, '\t'.join(roles)))
                preds = []
            dest.write('\n')
            in_chunk = None

    srl.close()
    dest.close()


def iob2token(wordpath, poschkpath, target, srlpath):

    def normrole(role):
        if role.startswith('EB'):
            return 'E' + role[2:]
        else:
            return role

    wordfile = open(wordpath, 'r')
    poschkfile = open(poschkpath, 'r')
    dest = open(target, 'w')
    srlfile = open(srlpath, 'r') if srlpath else None
    f = open('temp', 'w')

    words = []
    poses = []
    chunks = []
    roles = []
    predicates = []

    i = 0
    has_ebv = False
    see_in_the_begin = []
    see_in_the_begin2 = []
    while True:
        i += 1
        # if i > 10: break
        word = wordfile.readline()
        if word == '':
            break

        word = word.rstrip('\n')
        poschk = poschkfile.readline().rstrip('\n')
        srl = srlfile.readline().rstrip('\n')

        if word != '':
            pos, chunk = poschk.split('\t')
            f.write('%s\t%s\n' % (word, chunk))
            sp = srl.split('\t')
            predicate = sp[0]
            lineroles = sp[1:]
            if len(roles) == 0:
                roles = [ [] for i in range(len(lineroles)) ]

            if '-VP' in chunk:

                if chunk == 'B-VP' or chunk == 'EB-VP':
                    see_in_the_begin = lineroles;

                for idx, role in enumerate(lineroles):
                    if role == 'EB-V':
                        roles[idx].append(('*'+word, pos, role))
                        has_ebv = True
                    # elif role != 'O':
                        # if len(roles[idx][-1]) <= 1 or roles[idx][-1][0] != word:
                            # roles[idx].append((word, pos, role))

                if chunk == 'E-VP' or chunk == 'EB-VP':
                    lenth = max([len(_roles) for _roles in roles])
                    if not has_ebv:
                        for _roles in roles:
                            _roles.append((word, pos, 'O'))
                    for idx, _roles in enumerate(roles):
                        while (len(_roles)) < lenth:
                            _roles.append((word, pos, see_in_the_begin[idx]))
                    # print lenth, [len(_roles) for _roles in roles]

                    chunks.append(chunk)
                    words.append('placeholder')
                    poses.append('placeholder')
                    # for _roles in roles:
                    #     printc(_roles)
                    # printc(chunks)
                    has_ebv = False
                    see_in_the_begin = []
            else:
                if chunk[0] == 'B' or (chunk[0] == 'E' and chunk[1] == 'B'):
                    see_in_the_begin2 = lineroles
                if chunk[0] == 'E':
                    words.append(word)
                    chunks.append(chunk)

                    poses.append(pos)
                    for idx, role in enumerate(lineroles):
                        print word, lineroles, idx
                        if role[0] == 'E':
                            roles[idx].append(role)
                        else:
                            print see_in_the_begin2
                            print word
                            roles[idx].append(see_in_the_begin2[idx])
                    see_in_the_begin2 = []
                if chunk[0] == 'O':
                    words.append(word)
                    chunks.append(chunk)
                    poses.append(pos)
                    for idx, role in enumerate(lineroles):
                        roles[idx].append(role)

        else:
            for _roles in roles:
                if len(_roles) == 0:
                    continue
                for idx, role in enumerate(_roles):
                    if chunks[idx] == 'E-VP' or chunks[idx] == 'EB-VP':
                        chunk_to_write = chunks[idx]
                        if '-' in chunk_to_write:
                            chunk_to_write = chunk_to_write.split('-')[1]
                        dest.write('%s\t%s\t%s\t%s\n' % (role[0], role[1], chunk_to_write, normrole(role[2])))
                    else:
                        chunk_to_write = chunks[idx]
                        if '-' in chunk_to_write:
                            chunk_to_write = chunk_to_write.split('-')[1]
                        dest.write('%s\t%s\t%s\t%s\n' % (words[idx], poses[idx], chunk_to_write, normrole(role)))
                dest.write('\n')
            roles = []
            words = []
            poses = []
            chunks = []

    wordfile.close()
    poschkfile.close()
    srlfile.close()
    if srlfile is not None:
        srlfile.close()

def token2props(token_path, word_path, dest_path):
    wordfile = open(word_path, 'r')
    tokenfile = open(token_path, 'r')
    destfile = open(dest_path, 'w')

    sents = []
    words = []
    while True:
        line = wordfile.readline()
        if line == '':
            break

        word = line.rstrip('\n')

        if word == '':
            sents.append(words)
            words = []
        else:
            words.append(word)

    print len(sents)

    records = []
    tagged_sents = []

    nline = 0
    while True:
        line = tokenfile.readline()
        nline += 1
        if line == '':
            break

        line = line.rstrip('\n')

        if line == '':
            if len(tagged_sents) == 0:
                tagged_sents.append([records])
            else:
                last = tagged_sents[-1][-1]
                same = True

                if len(last) != len(records):
                    same = False
                else:
                    for idx,record in enumerate(last):
                        if record[2] != records[idx][2]:
                            same = False
                            break
                if same:
                    tagged_sents[-1].append(records)
                else:
                    tagged_sents.append([records])
            records = []
        else:
            word, pos, chunk, role = line.split('\t')
            records.append([word, role, chunk])


    print len(tagged_sents)

    # printc(tagged_sents[0:10])

    finals = []
    for idx, tsents in enumerate(tagged_sents):
        final = [[] for i in range(len(tsents))]
        for idx2, sent in enumerate(tsents):
            i, j = 0, 0
            while i < len(sent):
                word, role = sent[i][:2]
                if role != 'O':
                    role = role[2:]
                first = False
                while True:
                    if sents[idx][j] == word:
                        final[idx2].append(role)
                        j += 1
                        break
                    else:
                        if role == 'V':
                            final[idx2].append('O')
                        else:
                            final[idx2].append(role)
                        j += 1
                i += 1
            for k in range(j, len(sents[idx])):
                final[idx2].append('O')
            # print len(sents[idx]), len(final[idx2])
            # printc(sents[idx])
            # print final[idx2]
            assert(len(sents[idx]) == len(final[idx2]))
        finals.append(final)
        # print idx2

    # for f, v in zip(finals[:10], sents[:10]):
    #     printc(f)
    #     printc(v)

    print len(finals)

    for idx, sent in enumerate(sents):
        for idx2, word in enumerate(sent):
            lastone = []
            nextone = []
            
            thisone = [roles[idx2] for roles in finals[idx]]

            if idx2-1 < 0:
                lastone = ['START'] * len(finals[idx])
            else:
                lastone = [roles[idx2-1] for roles in finals[idx]]
            
            if idx2+1 >= len(finals[idx][0]):
                nextone = ['END'] * len(finals[idx])
            else:
                nextone = [roles[idx2+1] for roles in finals[idx]]

            for k, one in enumerate(thisone):
                if one == 'O':
                    thisone[k] = '*'
                else:
                    if lastone[k] != one:
                        thisone[k] = '(' + one + '*'
                        if nextone[k] != one:
                            thisone[k] += one + ')'
                    else:
                        if nextone[k] != one:
                            thisone[k] = '*' + ')'
                        else:
                            thisone[k] = '*'
            
            s = '\t'.join(thisone)
            word = word if '(V*V)' in s else '-'
            destfile.write('%s\t%s\n' % (word, s))
        destfile.write('\n')

    destfile.close()
    wordfile.close()
    tokenfile.close()

if len(sys.argv) > 1:
    if sys.argv[1] == 'train':
        poschk2iob('../data/trn.pos-chk')
        srl2iob('../data/trn.props', True)
        iob2token('../data/trn.wrd', '../data/trn.pos-chk.iob', '../data/trn.tokens', '../data/trn.props.iob')
    elif sys.argv[1] == 'dev':
        poschk2iob('../data/dev.pos-chk')
        srl2iob('../data/dev.props')
        iob2token('../data/dev.wrd', '../data/dev.pos-chk.iob', '../data/dev.tokens', '../data/dev.props.iob')        
    elif sys.argv[1] == 'props':
        token2props('props.txt', '../data/dev.wrd', '../result.txt')
    elif sys.argv[1] == 'test':
        poschk2iob('test.pos-chk')
        srl2iob('test.tgt', test=True)
        iob2token('test.wrd', 'test.pos-chk.iob', 'test.tokens', 'test.tgt.iob')


# poschk2iob('../data/dev.pos-chk')
# srl2iob('../data/dev.props')
# iob2token('../data/dev.wrd', '../data/dev.pos-chk.iob', '../data/dev.tokens', '../data/dev.props.iob')

# poschk2iob('../data/trn.pos-chk')
# srl2iob('../data/trn.props', True)
# iob2token('../data/trn.wrd', '../data/trn.pos-chk.iob', '../data/trn.tokens', '../data/trn.props.iob')
