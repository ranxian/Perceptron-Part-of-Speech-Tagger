chk = open('../data/dev.pos-chk', 'r')
words = open('../data/dev.wrd', 'r')
srl = open('../data/dev.props', 'r')

i = 0
while True:
    i += 1
    if i > 100:
        break

    pc = chk.readline()
    word = words.readline()
    role = srl.readline()

    if pc is None:
        break

    pc = pc.rstrip('\n')
    word = word.rstrip('\n')
    role = role.rstrip('\n')

    in_bracket = False

    last_role = False

    if len(word) > 1:
        pos, chunk = pc.split('\t')
        role = role.split('\t')

        if role.startswith('('):
            last_role = role

        if chunk.endswith(')'):
            print '%20s %20s %20s' % (word, pos, chunk),
            print '\t%20s' % '\t'.join(role[1:])



chk.close()
words.close()
srl.close()
