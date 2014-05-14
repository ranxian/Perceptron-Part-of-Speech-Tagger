def cstr(collection):
    if isinstance(collection, list):
        brackets = '[%s]'
        single_add = ''
    elif isinstance(collection, tuple):
        brackets = '(%s)'
        single_add =','
    else:
        return str(collection)
    items = ', '.join([cstr(x) for x in collection])
    if len(collection) == 1:
        items += single_add
    return brackets % items

def printc(*collections):
    for collection in collections:
        print cstr(collection)