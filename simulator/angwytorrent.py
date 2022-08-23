# Code adapted from Sven Seuken, University of Zurich

# This is a simple peer that just illustrates how the code works 
# starter code is the same as rand.py

from distutils.command.upload import upload
import random
import logging
import collections

from messages import Upload, Request
from util import evenSplit
from peer import Peer

class AngwyTorrent(Peer):
    def postInit(self):  
        print("postInit(): %s here!" % self.id)
    
    def sortPeerList(self, peers, history):
        """
        Create a list of lists that contain a peerID and a DF value for each peer for the given FairTorrent object
        """
        sortedPeerList = []
        for peer in peers:
            counter = 0
            #collect blocks downloaded from given peer
            for aRound in history.downloads:
                for event in aRound:
                    if event.fromId == peer.id:
                        counter += event.blocks
            #subtract blocks uploaded to given peer
            for aRound in history.uploads:
                for event in aRound:
                    if event.toId == peer.id:
                        counter = counter - event.actual
            sortedPeerList.append([peer.id, counter])

        random.shuffle(sortedPeerList)
        for x in range(0, len(sortedPeerList)):
                sortedPeerList[x].append(x)
        return sortedPeerList

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
        
        pieces = []
        #collect data on all avaliable pieces
        for p in peers:
            if len(p.availablePieces) != 0:
                pieces = pieces + list(p.availablePieces)
        frequencyDict = collections.Counter(pieces) #create dictionary of frequencies
        frequency = list(frequencyDict.items())
        random.shuffle(frequency) #shuffle frequencies in list form

        #add additional random int to each list of the id and frequency as a tie breaker
        frequencyLists = []
        for x in range(0, len(frequency)):
            frequencyLists.append(list(frequency[x]) + [x])

        #sort the list of ids by the frequency and then randomly via the x[2]
        frequencyLists.sort(key=lambda x: (x[1], x[2]), reverse=False)
        desireList = []
        for x in range(0, len(frequencyLists)):
            desireList.append(frequencyLists[x][0])

        # can request up to self.maxRequests from each
        for peer in peers:
            avSet = set(peer.availablePieces)
            isect = avSet.intersection(npSet)
            # More symmetry breaking -- ask for random pieces.
            # This would be the place to try fancier piece-requesting strategies
            # to avoid getting the same thing from multiple peers at a time.
            onePeer = []
            n = min(self.maxRequests, len(isect))  
            # start from the most desired piece and go down the list till you fill the max number of requests
            for pieceId in desireList:
                if pieceId in isect:
                # aha! The peer has this piece! Request it.
                # which part of the piece do we need next?
                # (must get the next-needed blocks in order)
                    if len(onePeer) < n:
                        startBlock = self.pieces[pieceId]
                        r = Request(self.id, peer.id, pieceId, startBlock)
                        onePeer.append(r)
            requests = requests + onePeer
        return requests

    def uploads(self, requests, peers, history):
        """
        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """
        #print(self.id)
        round = history.currentRound()
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        # One could look at other stuff in the history too here.
        # For example, history.downloads[round-1] (if round != 0, of course)
        # has a list of Download objects for each Download to this peer in
        # the previous round.

        # in the case that there are no requests, do not upload anything
        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            uploadList = []
            bws = []

        else:

            requestIDs = set()
            for x in requests:
                requestIDs.add(x.requesterId)

            # collect data regarding past moves of peers
            frequencyLists = self.sortPeerList(peers, history)
            #sort the list of ids by the frequency of upload and then randomly via the x[2]
            frequencyLists.sort(key=lambda x: (x[1], x[2]), reverse=False)

            limit = self.upBw
            bws = []
            uploadList = []
            while limit > 0:
                for x in frequencyLists:
                    if x[0] in requestIDs:
                        for request in requests:
                            if request.requesterId == x[0]:
                                    current = request
                        bitsToUse = self.conf.blocksPerPiece - current.start
                        b = min(bitsToUse, limit)
                        limit -= b
                        if b != 0:
                            uploadList.append(x[0])
                            bws.append(b)

            logging.debug("Still here: uploading %s", uploadList)

        # create actual uploads out of the list of peer ids and bandwidths
        uploads = [Upload(self.id, peerId, bw)
                   for (peerId, bw) in zip(uploadList, bws)]
        return uploads
