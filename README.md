# cs357-s22-BitTorrent-M
This is the shared repository for CS357 Final Project (Spring 22).

For the purposes of this project, three different agents were created: FairTorrent (``fairtorrent.py``), BitTorrent(``bittorrent.py``), and AngwyTorrent (``angwytorrent.py``).

Having entered the simulator directory, the following lines were used to run the program as seen in the experimental report:

``python3 sim.py --numPieces=128 --blocksPerPiece=16 --minBw=16 --maxBw=32 --maxRound=1000 --iters=32 Seed,2 BitTorrent,9 Freerider,1``

``python3 sim.py --numPieces=128 --blocksPerPiece=16 --minBw=16 --maxBw=32 --maxRound=1000 --iters=32 Seed,2 FairTorrent,9 Freerider,1``

``python3 sim.py --numPieces=128 --blocksPerPiece=16 --minBw=16 --maxBw=32 --maxRound=1000 --iters=32 Seed,2 FairTorrent,5 AngwyTorrent,5``

``python3 sim.py --numPieces=128 --blocksPerPiece=16 --minBw=16 --maxBw=32 --maxRound=1000 --iters=32 Seed,2 BitTorrent,5 AngwyTorrent,5``

The new functions created in the project are the following:

For sim.py, ``upBwEven(self, peerIds)``: Sets the upload bandwidth of seeds to max, and the bandwidth of other agents to the middle point between the minimum bandwidth and maximum bandwidth

For stats.py,
``unchokeCount(peerIds, history)``: takes in a list of peerIds and a History object and returns a dictionary in the form {(A, B): int], logging the number of unchokes from A to B.

``frequencyMap(frequenciesList, bandwidths, sortby=None)``: given the dict of bandwidths for the agents listed in the frequency lists, a tag which is used to define how a list is sorted, and a list of lists where each contains at least three items, the last of which is an int. if sortby is set to None, the pairs will be sorted by the bandwidths of the agent, and if it is set to alpha, the peers will be sorted on the chart alphabetically, grouping them together by type. this will generate a heatmap showing the frequencies of the different pairs.

For util.py,
``convertDictList(frequenciesDict)``: convert a dictionary where the keys are touples into a list of lists. given a dictionary of frequencies, where the keys are a touple (a, b), where a is the peer uploading and b is the peer downloading in a given round, and the value of the key-value pair is the quantity of exchanges that went in that direction, return a list of lists where each of the smaller lists is made up of [a, b, frequency].
