# Code adapted from Sven Seuken, University of Zurich

import random
from messages import Upload, Request
from util import evenSplit
import logging

class Peer:
    def __init__(self, config, id, initPieces, upBandwidth):
        self.conf = config
        self.id = id
        self.pieces = initPieces[:]
        # bandwidth measured in blocks-per-time-period
        self.upBw = upBandwidth
        logging.debug('Setting bw of {} to {}.'.format(id, upBandwidth))

        # This is an upper bound on the number of requests to send to
        # each peer -- they can't possibly handle more than this in one round
        self.maxRequests = self.conf.maxUpBw // self.conf.blocksPerPiece + 1
        self.maxRequests = min(self.maxRequests, self.conf.numPieces)

        # bittorrent purposes
        self.additional = None

        # fairtorrent purposes
        self.downloaded = []

        self.postInit()

    def __repr__(self):
        return "%s(id=%s pieces=%s upBw=%d)" % (
            self.__class__.__name__,
            self.id, self.pieces, self.upBw)

    def updatePieces(self, newPieces):
        """
        Called by the sim when this peer gets new pieces.  
        Defined as a function so that adding extra processing 
        is easy.
        """
        self.pieces = newPieces

    def requests(self, peers, history):
        return []

    def uploads(self, requests, peers, history):
        return []

    def postInit(self):
        # Here to be overridden by child classes
        pass
