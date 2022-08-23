# Code adapted from Sven Seuken, University of Zurich

# This is a simple peer that just illustrates how the code works 


import random
import logging

from messages import Upload, Request
from util import evenSplit
from peer import Peer

class Rand(Peer):
    def postInit(self):  
        print("postInit(): %s here!" % self.id)
    
    def requests(self, peers, history):
        """
        peers: available info about the peers (who has what pieces) 
        history: what's happened so far as far as this peer can see

        returns: a list of Request() objects

        This will be called after updatePieces() with the most recent state.
        """
        needed = lambda i: self.pieces[i] < self.conf.blocksPerPiece
        neededPieces = filter(needed, range(len(self.pieces)))
        npSet = set(neededPieces)  # sets support fast intersection ops


        logging.debug("%s here: still need pieces %s" % (
            self.id, list(neededPieces)))

        logging.debug("%s still here. Here are some peers:" % self.id)
        for p in peers:
            logging.debug("id: %s, available pieces: %s" % (p.id, p.availablePieces))

        #logging.debug("And look, I have my entire history available too:")
        #logging.debug(str(history))

        requests = []   # We'll put all the pieces we want here 
        # Symmetry breaking 
        random.shuffle(list(neededPieces))
        
        # Sort peers by id.  This is probably not a useful sort, but other 
        # sorts might be useful
        peers.sort(key=lambda p: p.id)
        # request all available pieces from all peers
        # can request up to self.maxRequests from each
        for peer in peers:
            avSet = set(peer.availablePieces)
            isect = avSet.intersection(npSet)
            n = min(self.maxRequests, len(isect))
            # More symmetry breaking -- ask for random pieces.
            # This would be the place to try fancier piece-requesting strategies
            # to avoid getting the same thing from multiple peers at a time.
            for pieceId in random.sample(isect, n):
                # aha! The peer has this piece! Request it.
                # which part of the piece do we need next?
                # (must get the next-needed blocks in order)
                startBlock = self.pieces[pieceId]
                r = Request(self.id, peer.id, pieceId, startBlock)
                requests.append(r)

        return requests

    def uploads(self, requests, peers, history):
        """
        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """

        round = history.currentRound()
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        # One could look at other stuff in the history too here.
        # For example, history.downloads[round-1] (if round != 0, of course)
        # has a list of Download objects for each Download to this peer in
        # the previous round.

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            chosen = []
            bws = []
        else:
            logging.debug("Still here: uploading to a random peer")

            request = random.choice(requests)
            chosen = [request.requesterId]
            # Evenly "split" my upload bandwidth among the one chosen requester
            bws = evenSplit(self.upBw, len(chosen))
            

        # create actual uploads out of the list of peer ids and bandwidths
        uploads = [Upload(self.id, peerId, bw)
                   for (peerId, bw) in zip(chosen, bws)]
            
        return uploads
