# Code adapted from Sven Seuken, University of Zurich

"""
Simulates one file being shared among a set of peers.  
The file is divided into a set of pieces, each comprised 
of some number of blocks.  There are two types of peers:
  - seeds, which start with all the pieces.  
  - regular peers, which start with no pieces.

The simulation proceeds in rounds.  In each round, 
peers can request pieces from other peers, and then decide 
how much to upload to others.  
Once every peer has every piece, the simulation ends.
"""

import re
import random
import sys
import logging
import copy
import itertools
import pprint
import argparse 
import math
from messages import Upload, Request, Download, PeerInfo
from util import *
from stats import Stats
from history import History



class Sim:

    def __init__(self, config):
        self.config = config
        self.upBwState = dict()


    def upBwUniform(self, peerIds):
        """Sets the upload bandwidth of seeds to max, 
        other agents uniformly at random from the range minUpBW and maxUpBw""" 
        c = self.config
        s = self.upBwState

        for peerId in peerIds:
            if re.match("Seed", peerId): 
                theUpBw = int(c.maxUpBw)
            else:
                theUpBw = random.randint(c.minUpBw, c.maxUpBw)
            s[peerId] = theUpBw
        return s

    def upBwEven(self, peerIds):
        """Sets the upload bandwidth of seeds to max, and the bandwidth of other agents to the middle point between the minimum bandwidth and maximum bandwidth""" 
        c = self.config
        s = self.upBwState

        for peerId in peerIds:
            if re.match("Seed", peerId): 
                theUpBw = int(c.maxUpBw)
            else:
                theUpBw = c.minUpBw + round((c.maxUpBw - c.minUpBw)/2)
            s[peerId] = theUpBw
        return s

    def runSimOnce(self):
        """Return a history"""
        conf = self.config
        # Keep track of the current round.  
        # Needs to be in scope for helpers.
        round = 0  

        def checkPred(pred, msg, Exc, lst):
            """Check if any element of lst matches the predicate.  
            If it does, raise an exception of type Exc, including 
            the msg and the offending element."""
            m = list(map(pred, lst))
            if True in m:
                i = m.index(True)
                raise Exc(msg + " Bad element: %s" % lst[i])

        def checkUploads(peer, uploads):
            """Raise an IllegalUpload exception if there is a problem."""
            def check(pred, msg):
                checkPred(pred, msg, IllegalUpload, uploads)

            notUpload = lambda o: not isinstance(o, Upload)
            check(notUpload, "List of Uploads contains non-Upload object.")

            selfUpload = lambda upload: upload.toId == peer.id
            check(selfUpload, "Can't upload to yourself.")
            
            notFromSelf = lambda upload: upload.fromId != peer.id
            check(notFromSelf, "Upload.from != peer id.")

            check(lambda u: u.bw < 0, "Upload bandwidth must be non-negative!")

            limit = self.upBwState[peer.id]
            # print("limit debug: peerId {}, bw {}".format(peer.id, limit)) 
            if  sum([u.bw for u in uploads]) > limit:
                raise IllegalUpload("Can't upload more than limit of %d. %s" % (
                    limit, uploads))

            # If we got here, looks ok.

        def checkRequests(peer, requests, peerPieces, available):
            """Raise an IllegalRequest exception if there is a problem."""

            def check(pred, msg):
                checkPred(pred, msg, IllegalRequest, requests)

            check(lambda o: not isinstance(o, Request),
                  "List of Requests contains non-Request object.")

            badPieceId = lambda r: (r.pieceId < 0 or
                                      r.pieceId >= self.config.numPieces)
            check(badPieceId, "Request asks for non-existent piece!")
            
            badPeerId = lambda r: r.peerId not in self.peerIds
            check(badPeerId, "Request mentions non-existent peer!")

            badRequesterId = lambda r: r.requesterId != peer.id
            check(badRequesterId, "Request has wrong peer id!")

            badStartBlock = lambda r: (
                r.start < 0 or
                r.start >= self.config.blocksPerPiece or
                r.start > peerPieces[peer.id][r.pieceId])
            # Must request the _next_ necessary block
            check(badStartBlock, "Request has bad start block!")

            def piecePeerDoesNotHave(r):
                otherPeer = self.peersById[r.peerId]
                return r.pieceId not in available[otherPeer.id]
            check(piecePeerDoesNotHave, "Asking for piece peer does not have!")
            
            # If we got here, looks ok

        def availablePieces(peerId, peerPieces):
            """
            Return a list of piece ids that this peer has available.
            """
            return list(filter(lambda i: peerPieces[peerId][i] == conf.blocksPerPiece,
                          range(conf.numPieces)))

        def peerDone(peerPieces, peerId):
            for blocksSoFar in peerPieces[peerId]:
                if blocksSoFar < conf.blocksPerPiece:
                    return False
            return True
            
        def allDone(peerPieces):
            result = True
            # Check all peers to update done status
            for peerId in peerPieces:
                if peerDone(peerPieces, peerId):
                    history.peerIsDone(round, peerId)
                else:
                    result = False
            return result

        def createPeers():
            """Each agent class must be already loaded, and have a
            constructor that takes the config, id,  pieces, and
            up and down bandwidth, in that order."""

            def load(className, params):
                agentClass = conf.agentClasses[className]
                return agentClass(*params)

            counts = dict()
            def index(name):
                if name in counts:
                    a = counts[name]
                    counts[name] += 1
                else:
                    a = 0
                    counts[name] = 1
                return a

            n = len(conf.agentClassNames)
            ids = list(map(lambda n: "%s%d" % (n, index(n)), conf.agentClassNames))

            def getPieces(id):
                if id.startswith("Seed"):
                    return [conf.blocksPerPiece]*conf.numPieces
                else:
                    return [0]*conf.numPieces
                
            peerPieces = dict()  # id -> list (blocks / piece)
            peerPieces = dict((id, getPieces(id)) for id in ids)
            pieces = [getPieces(id) for id in ids]
            r = itertools.repeat
            upBwDict = self.upBwEven(ids)
            #upBwDict = self.upBwUniform(ids)
            upBws = [upBwDict[id] for id in ids] #self.scaledUpBws(ids) #[sel for i in ids]
            params = zip(r(conf), ids, pieces, upBws)

            peers = [load(acName, p) for (acName, p) in zip(conf.agentClassNames, params)]
            # logging.debug("Peers: \n" + "\n".join(str(p) for p in peers))
            return peers, peerPieces

        def getPeerRequests(p, peerInfo, peerHistory, peerPieces, available):
            def removeMe(peerInfo):
                return [peer for peer in peerInfo if p.id != peer.id]

            pieces = copy.copy(peerPieces[p.id])
            # Made copy of pieces and the peer info this peer needs to make it's
            # decision, so that it can't change the simulation's copies.
            p.updatePieces(pieces)
            rs = p.requests(removeMe(peerInfo), peerHistory)
            checkRequests(p, rs, peerPieces, available)
            return rs

        def getPeerUploads(allRequests, p, peerInfo, peerHistory):
            def removeMe(peerInfo):
                return [peer for peer in peerInfo if p.id != peer.id]

            def requestsTo(id):
                # f = lambda r: r.peerId == id
                ans = []
                for rs in allRequests.values():
                    newR = [r for r in rs if r.peerId == id]
                    ans.extend(newR)
                return ans

            requests = requestsTo(p.id)
            us = p.uploads(requests, removeMe(peerInfo), peerHistory)
            checkUploads(p, us)
            return us

        def uploadRate(uploads, uploaderId, requesterId):
            """
            return the uploading rate from uploader to requester
            in blocks per time period, or 0 if not uploading.
            """
            for u in uploads[uploaderId]:
                if u.toId == requesterId:
                    return (u.bw, u)
            return (0, None)

        def updatePeerPieces(peerPieces, requests, uploads, available):
            """
            Process the uploads: figure out how many blocks of all the requested
            pieces the requesters ended up with.
            Make sure requesting the same thing from lots of peers doesn't
            stack.
            update the sets of available pieces as needed.
            """
            downloads = dict()  # peer_id -> [downloads]
            newPp = copy.deepcopy(peerPieces)
            shuff = list(requests.keys())
            random.shuffle(shuff)
            for requesterId in shuff:
                downloads[requesterId] = list()

            for requesterId in shuff:
                # Keep track of how many blocks of each piece this
                # requester got.  piece -> (blocks, from_who)
                newBlocksPerPiece = dict()
                def updateCount(pieceId, blocks, peerId):
                    if pieceId in newBlocksPerPiece:
                        old = newBlocksPerPiece[pieceId][0]
                        if blocks > old:
                            newBlocksPerPiece[pieceId] = (blocks, peerId)
                    else:
                        newBlocksPerPiece[pieceId] = (blocks, peerId)

                uploadsUpdated = []
                # Group the requests by peer that is being asked
                getPeerId = lambda r: r.peerId

                random.shuffle(requests[requesterId])
                rs = requests[requesterId]
                for peerId, rsForPeer in itertools.groupby(rs, getPeerId):
                    # for r in rsForPeer:
                    rate = uploadRate(uploads, peerId, requesterId)
                    bw = rate[0]
                    if bw != 0:
                        uploadsUpdated.append(rate[1])
                    if bw == 0:
                        continue
                    # This bandwidth gets applied in order to each piece requested
                    for r in rsForPeer:
                        neededBlocks = conf.blocksPerPiece - r.start
                        allocedBw = min(bw, neededBlocks)
                        updateCount(r.pieceId, allocedBw, peerId)
                        bw -= allocedBw
                        if bw == 0:
                            break

                for pieceId in newBlocksPerPiece:
                    (blocks, peerId) = newBlocksPerPiece[pieceId]
                    #update the number of blocks being uploaded
                    for x in uploadsUpdated:
                        if x.fromId == peerId:
                            x.actual = blocks
                    newPp[requesterId][pieceId] += blocks
                    if newPp[requesterId][pieceId] == conf.blocksPerPiece:
                        available[requesterId].add(pieceId)
                    d = Download(peerId, requesterId, pieceId, blocks)
                    downloads[requesterId].append(d)
            return (newPp, downloads)

        def completedPieces(peerId, available):
            return len(available[peerId])
        
        def logPeerInfo(peerPieces, available):
            for pId in self.peerIds:
                pieces = peerPieces[pId]
                # logging.debug("pieces for %s: %s" % (str(pId), str(pieces)))
            log = ", ".join("%s:%s" % (pId, completedPieces(pId, available))
                            for pId in self.peerIds)
            # logging.info("Pieces completed: " + log)
      

        logging.debug("Starting simulation with config: %s" % str(conf))

        peers, peerPieces = createPeers()
        # print("DEBUG", peers)
        self.peerIds = [p.id for p in peers]
        self.peersById = dict((p.id, p) for p in peers)
        
        uploadRates = self.upBwState
        history = History(self.peerIds, uploadRates)

        # dict : pid -> set(finished / available pieces)
        available = dict((pid, set(availablePieces(pid, peerPieces)))
                         for pid in self.peerIds)

        # logging.debug('upBwDict: {}'.format(self.upBwState))
        # Begin the event loop
        while True:
            logging.info("======= Round %d ========" % round)
            peerInfo = [PeerInfo(p.id, available[p.id])
                         for p in peers]
            requests = dict()  # peer_id -> list of Requests
            uploads = dict()   # peer_id -> list of Uploads
            h = dict()
            for p in peers:
                h[p.id] = history.peerHistory(p.id)
                requests[p.id] = getPeerRequests(p, peerInfo, h[p.id], peerPieces,
                                                   available)
                

            for p in peers:
                uploads[p.id] = getPeerUploads(requests, p, peerInfo, h[p.id])
               

            (peerPieces, downloads) = updatePeerPieces(
                peerPieces, requests, uploads, available)
            history.update(downloads, uploads)

            logging.debug(history.prettyForRound(round))

            logPeerInfo(peerPieces, available)
           
            if allDone(peerPieces):
                logging.info("All done!")                    
                break
            round += 1
            if round > conf.maxRound:
                logging.info("Out of time.  Stopping.")
                break
        # logging.info("Game history:\n%s" % history.pretty())

        logging.info("======== STATS ========")
        logging.info("Uploaded blocks:\n%s" %
                    Stats.uploadedBlocksStr(self.peerIds, history))
        logging.info("Completion rounds:\n%s" %
                    Stats.completionRoundsStr(self.peerIds, history))
        logging.info("All done round: %s" %
                    Stats.allDoneRound(self.peerIds, history))

        return history

    def runSim(self):
        histories = [self.runSimOnce() for i in  
                        range(self.config.iters)]
        logging.warning("======== SUMMARY STATS ========")
         
        uploadedBlocks = [Stats.uploadedBlocks(self.peerIds, h) for h in histories]

        completionRounds = [Stats.completionRounds(self.peerIds, h) for h in histories]

        #create structure containing number of exchanges
        communications = dict()
        for h in histories:
            current = Stats.communicateCount(self.peerIds, h)
            sharedKeys = set(communications.keys()).intersection(current.keys())
            for key in sharedKeys:
                communications[key] = communications.get(key) + current.get(key)
            seperateKeys = set(current.keys()).difference(communications.keys())
            for key in seperateKeys:
                communications[key] = current.get(key)

        unchokes = dict()
        for h in histories:
            current = Stats.unchokeCount(self.peerIds, h)
            sharedKeys = set(unchokes.keys()).intersection(current.keys())
            for key in sharedKeys:
                unchokes[key] = unchokes.get(key) + current.get(key)
            seperateKeys = set(current.keys()).difference(unchokes.keys())
            for key in seperateKeys:
                unchokes[key] = current.get(key)

        print(self.upBwState)
        Stats.frequencyMap(convertDictList(unchokes), self.upBwState, sortby="alpha")
        Stats.frequencyMap(convertDictList(unchokes), self.upBwState, sortby=None)
        Stats.frequencyMap(convertDictList(communications), self.upBwState, sortby="alpha")
        Stats.frequencyMap(convertDictList(communications), self.upBwState, sortby=None)


        def extractByPeerId(lst, peerId):
            """Given a list of dicts, pull out the entry
            for peerId from each dict.  Return a list"""
            return [d[peerId] for d in lst]

        uploadedById = dict(
            (pId, extractByPeerId(uploadedBlocks, pId))
            for pId in self.peerIds)


        completionById = dict(
            (pId, extractByPeerId(completionRounds, pId))
            for pId in self.peerIds)

        logging.warning("Upload bandwidth: avg (stddev)")
        for pId in sorted(self.peerIds,
                           key=lambda id: mean(uploadedById[id])):
            us = uploadedById[pId]
            logging.warning("%s: %.1f  (%.1f)" % (pId, mean(us), stddev(us)))

        logging.warning("Completion rounds: avg (stddev)")

        def optionize(f):
            def g(lst):
                if None in lst:
                    return None
                else:
                    return f(lst)
            return g

        optMean = optionize(mean)
        optStddev = optionize(stddev)
       
        # logging.warning("Upload Bandwidth: avg (stddev)")
 
        for pId in sorted(self.peerIds,
                           key=lambda id: optMean(completionById[id])):
            cs = completionById[pId]
            logging.warning("%s: %.1f  (%.1f)" % (pId, optMean(cs), optStddev(cs)))

        # for pId in sorted(self.peerIds,
        #                    key = lambda id: optMean(uploadBwById[id])):
        #    upBw = uploadBwById[id]
        #    logging.warning("%s: %.1f (%.1f)" % (pId, optMean(upBw), optStddev(upBw)))
        # logging.warning("Completion time per unit of upload bandwidth")
        # ratio = dict()
        # for pId in self.peerIds:
        #    if len(completionById[pId]):
        #        ratio[pId] = [c/u for (c,u) in zip(completionById[pId], uploadedById[pId]) if c!=0]
        #        
        #for pId in sorted(ratio, key=ratio.get, reverse=True):
        #    if len(ratio[pId]):
        #        logging.warning("%s: %.1f" % (pId, mean(ratio[pId])))



def configureLogging(loglevel):
    numericLevel = getattr(logging, loglevel.upper(), None)
    if not isinstance(numericLevel, int):
        raise ValueError('Invalid log level: %s' % loglevel)

    rootLogger = logging.getLogger('')
    strmOut = logging.StreamHandler(sys.__stdout__)
#    strm_out.setFormatter(logging.Formatter('%(levelno)s: %(message)s'))
    strmOut.setFormatter(logging.Formatter('%(message)s'))
    rootLogger.setLevel(numericLevel)
    rootLogger.addHandler(strmOut)
    

def parseAgents(args):
    """
    Each element is a class name like "Peer", with an optional
    count appended after a comma.  So either "Peer", or "Peer,3".
    Returns an array with a list of class names, each repeated the
    specified number of times.
    """
    ans = []
    for c in args:
        s = c.split(',')
        if len(s) == 1:
            ans.extend(s)
        elif len(s) == 2:
            name, count = s
            ans.extend([name]*int(count))
        else:
            raise ValueError("Bad argument: %s\n" % c)
    return ans
            
        

def main(args):
    usageMsg = "Usage:  %prog [args] PeerClass1[,count] PeerClass2[,count] ..."
    parser = argparse.ArgumentParser(description=usageMsg)

    def usage(msg):
        print("Error: %s\n" % msg)
        parser.printHelp()
        sys.exit()
    
    parser.add_argument("--loglevel",
                      dest="loglevel", default="info",
                      help="Set the logging level: 'debug' or 'info'")

    parser.add_argument("--numPieces",
                      dest="numPieces", default=3, type=int,
                      help="Set number of pieces in the file")

    parser.add_argument("--blocksPerPiece",
                      dest="blocksPerPiece", default=4, type=int,
                      help="Set number of blocks per piece")

    parser.add_argument("--maxRound",
                      dest="maxRound", default=5, type=int,
                      help="Limit on number of rounds")

    parser.add_argument("--minBw",
                      dest="minUpBw", default=4, type=int,
                      help="Min upload bandwidth")

    parser.add_argument("--maxBw",
                      dest="maxUpBw", default=10, type=int,
                      help="Max upload bandwidth")

    parser.add_argument("--iters",
                      dest="iters", default=1, type=int,
                      help="Number of times to run simulation to get stats")

    #parser.add_argument("--bwDis",
    #                  dest="bwDis", default="uniform",
    #                  help="set to uniform or hardcoded")
    

    args, extra = parser.parse_known_args()
    # leftover args are class names, with optional counts:
    # "Peer Seed[,4]"

    if not len(sys.argv) > 1:
        # default
        agentsToRun = ['Dummy', 'Dummy', 'Seed']
    else:
        try:
            agentsToRun = parseAgents(extra)
        except ValueError as e:
            usage(e)
    
    configureLogging(args.loglevel)
    config = Params()

    config.add("agentClassNames", agentsToRun)
    config.add("agentClasses", loadModules(config.agentClassNames))

    
    config.add("numPieces", args.numPieces)
    config.add("blocksPerPiece", args.blocksPerPiece)
    config.add("maxRound", args.maxRound)
    config.add("minUpBw", args.minUpBw)
    config.add("maxUpBw", args.maxUpBw)
    config.add("iters", args.iters)
    
    sim = Sim(config)
    sim.runSim()

if __name__ == "__main__":

    # The next two lines are for profiling...
    import cProfile
    cProfile.run('main(sys.argv)', 'out.prof')
    # main(sys.argv)
