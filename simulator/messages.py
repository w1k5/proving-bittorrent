# Code adapted from Sven Seuken, University of Zurich

class Upload:
    def __init__(self, fromId, toId, upBw, actual=0):
        self.fromId = fromId
        self.toId = toId
        self.bw = upBw
        self.actual = actual

    def __repr__(self):
        return "Upload(fromId = %s, toId=%s, bw=%d)" % (
            self.fromId, self.toId, self.bw)

class Request:
    def __init__(self, requesterId, peerId, pieceId, start):
        self.requesterId = requesterId
        self.peerId = peerId   # peer data is requested from
        self.pieceId = pieceId
        self.start = start  # the block index

    def __repr__(self):
        return "Request(requesterId=%s, peerId=%s, pieceId=%d, start=%d)" % (
            self.requesterId, self.peerId, self.pieceId, self.start)

class Download:
    """ Not actually a message--just used for accounting and history tracking of
     what is actually downloaded.
    """
    def __init__(self, fromId, toId, piece, blocks):
        self.fromId = fromId  # who did the agent download from?
        self.toId = toId      # Who downloaded?
        self.piece = piece      # Which piece?
        self.blocks = blocks    # How much did the agent download?

    def __repr__(self):
        return "Download(fromId=%s, toId=%s, piece=%d, blocks=%d)" % (
            self.fromId, self.toId, self.piece, self.blocks)



            
class PeerInfo:
    """
    Only passing peer ids and the pieces they have available to each agent.
    This prevents them from accidentally messing up the state of other agents.
    """
    def __init__(self, id, available):
        self.id = id
        self.availablePieces = available

    def __repr__(self):
        return "PeerInfo(id=%s)" % self.id

