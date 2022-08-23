# Code adapted from Sven Seuken, University of Zurich

import random
from messages import Upload, Request
from util import evenSplit
from peer import Peer

class Seed(Peer):
    def requests(self, peers, history):
        # Seeds don't need anything.
        return []

    def uploads(self, requests, peers, history):
        maxUpload = 4  # max num of peers to upload to at a time
        requesterIds = list(set(map(lambda r: r.requesterId, requests)))
        n = min(maxUpload, len(requesterIds))
        if n == 0:
            return []
        bws = evenSplit(self.upBw, n)
        uploads = [Upload(self.id, pId, bw)
                   for (pId, bw) in zip(random.sample(requesterIds, n), bws)]
        return uploads
