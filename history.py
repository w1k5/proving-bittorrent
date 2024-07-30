# Code adapted from Sven Seuken, University of Zurich

import copy
import pprint


class AgentHistory:
    """
    History available to a single peer

    history.downloads: [[Download objects for round]]  (one sublist for each round)
         All the downloads _to_ this agent.
        
    history.uploads: [[Upload objects for round]]  (one sublist for each round)
         All the downloads _from_ this agent.

    """
    def __init__(self, peerId, downloads, uploads):
        """
        Pull out just the info for peerId.
        """
        self.uploads = uploads
        self.downloads = downloads
        self.peerId = peerId

    def lastRound(self):  # Make an @property?
        return len(self.downloads)-1

    def currentRound(self):  # Make an @property?
        """ 0 is the first """
        return len(self.downloads)

    def __repr__(self):
        return "AgentHistory(downloads=%s, uploads=%s)" % (
            pprint.pformat(self.downloads),   
            pprint.pformat(self.uploads))


class History:
    """History of the whole sim"""
    def __init__(self, peerIds, uploadRates):
        """
        uploads:
                   dict : peerId -> [[uploads] -- one list per round]
        downloads:
                   dict : peerId -> [[downloads] -- one list per round]
                   
        Keep track of the uploads _from_ and downloads _to_ the
        specified peer id.
        """
        self.uploadRates = uploadRates  # peerId -> upBw
        self.peerIds = peerIds[:]

        self.roundDone = dict()   # peerId -> round finished
        self.downloads = dict((pid, []) for pid in peerIds)
        self.uploads = dict((pid, []) for pid in peerIds)

    def update(self, dls, ups):
        """
        dls: dict : peerId -> [downloads] -- downloads for this round
        ups: dict : peerId -> [uploads] -- uploads for this round

        append these downloads to to the history
        """
        for pid in self.peerIds:
            self.downloads[pid].append(dls[pid])
            self.uploads[pid].append(ups[pid])

    def peerIsDone(self, r, peerId):
        # Only save the _first_ round where we hear this
        if peerId not in self.roundDone:
            self.roundDone[peerId] = r

    def peerHistory(self, peerId):
        return AgentHistory(peerId, self.downloads[peerId], self.uploads[peerId])

    def lastRound(self):
        """index of the last completed round"""
        p = self.peerIds[0]
        return len(self.downloads[p])-1

    def prettyForRound(self, r):
        s = "\nRound %s:\n" % r
        for peerId in self.peerIds:
            ds = self.downloads[peerId][r]
            stringify = lambda d: "%s downloaded %d blocks of piece %d from %s\n" % (
                peerId, d.blocks, d.piece, d.fromId)
            s += "".join(map(stringify, ds))
        return s

    def pretty(self):
        s = "History\n"
        for r in range(self.lastRound()+1):
            s += self.prettyForRound(r)
        return s

    def __repr__(self):
        return """History(
        uploads=%s
        downloads=%s
        )""" % (
        pprint.pformat(self.uploads),
        pprint.pformat(self.downloads))

