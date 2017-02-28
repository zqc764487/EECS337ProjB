
def loadCategorization(fname):
    localDict = {}
    with open(fname) as f:
        lines = f.read().splitlines()
        for line in lines:
            buff = line.split(',')
            category = buff[0]

            if category not in localDict.keys():
                localDict[category] = [x for x in buff[1:] if x]
    return localDict

