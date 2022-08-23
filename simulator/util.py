# Code adapted from Sven Seuken, University of Zurich

# Util functions ################

# http://stackoverflow.com/questions/5098580/implementing-argmax-in-python

from itertools import count
import math


def argmax(pairs):
    """
    given an iterable of pairs return the key corresponding to the greatest value
    """
    return max(pairs, key=lambda a,b: b)[0]

 
def argmaxIndex(values):
    """
    given an iterable of values return the index of the greatest value
    """
    return argmax(zip(count(), values))

def argmaxFunc(keys, f):
    """
    given an iterable of keys and a function f, return the key with largest f(key)
    """
    return argmax((k, f(k)) for k in keys)

def argmaxFuncTuples(keys, f):
    """
    given an iterable of key tuples and a function f, return the key with largest f(*key)
    """
    return max(map(lambda key: (f(*key), key), keys))[1]

def mean(lst):
    """Throws a div by zero exception if list is empty"""
    return sum(lst) / float(len(lst))

def stddev(lst):
    if len(lst) == 0:
        return 0
    m = mean(lst)
    return math.sqrt(sum((x-m)*(x-m) for x in lst) / len(lst))


def median(numeric):
    vals = sorted(numeric)
    count = len(vals)
    if count % 2 == 1:
        return vals[(count+1)/2-1]
    else:
        lower = vals[count/2-1]
        upper = vals[count/2]
        return (float(lower + upper)) / 2

def convertDictList(frequenciesDict):
    """
    given a dictionary of frequencies, where the keys are a touple (a, b), where a is the peer uploading and b is the peer downloading in a given round, and the value of the key-value pair is the quantity of exchanges that went in that direction, return a list of lists where each of the smaller lists is made up of [a, b, frequency]
    """
    uploaded = []
    for x in frequenciesDict.items():
        uploaded.append([x[0][0], x[0][1], x[1]])
    return uploaded

def evenSplit(n, k):
    """
    n and k must be ints.
    
    returns a list of as-even-as-possible shares when n is divided into k pieces.

    Excess is left for the end.  If you want random order, shuffle the output.

    >>> evenSplit(2,1)
    [2]
    
    >>> evenSplit(2,2)
    [1, 1]

    >>> evenSplit(3,2)
    [1, 2]

    >>> evenSplit(11,3)
    [3, 4, 4]
    >>> evenSplit(3,2)
    """
    ans = []
    if type(n) is not int or type(k) is not int:
        raise TypeError("n and k must be ints")

    r = n % k
    ans = ([n//k] * (k-r))
    ans.extend([n//k + 1] * r)
    return ans


def loadModules(agentClasses):
    """Each agent class must be in module className.lower().
    Returns a dictionary className->class"""
    def load(className):
        moduleName = className.lower()  # by convention / fiat
        module = __import__(moduleName)
        agentClass = module.__dict__[className]
        return (className, agentClass)
    return dict([load(classN) for classN in agentClasses])
    


class Params:
    def __init__(self):
        self._init_keys = set(self.__dict__.keys())
    
    def add(self, k, v):
        self.__dict__[k] = v

    def __repr__(self):
        return "; ".join("%s=%s" % (k, str(self.__dict__[k])) for k in self.__dict__.keys() if k not in self._init_keys)
        


class IllegalUpload(Exception):
    pass

class IllegalRequest(Exception):
    pass

