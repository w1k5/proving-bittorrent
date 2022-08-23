import re
import numpy as np
from tokenize import group
import matplotlib.pyplot as plt
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.rm'] = 'Bitstream Vera Sans'
plt.rcParams['mathtext.it'] = 'Bitstream Vera Sans:italic'
plt.rcParams['mathtext.bf'] = 'Bitstream Vera Sans:bold'
# Code adapted from Sven Seuken, University of Zurichn

class Stats:
    @staticmethod
    def uploadedBlocks(peerIds, history):
        """
        peerIds: list of peerIds
        history: a History object

        Returns:
        dict: peerId -> total upload blocks used
        """
        uploaded = dict((peerId, 0) for peerId in peerIds)
        for peerId in peerIds:
            for ds in history.downloads[peerId]:
                for download in ds:
                    uploaded[download.fromId] += download.blocks
                
        return uploaded

    @staticmethod
    def communicateCount(peerIds, history):
        """
        peerIds: list of peerIds
        history: a History object

        Returns:
        frequenciesDict -> dictionary in the form {(A, B): int], logging the int number of blocks uploaded from A to B
        """
        frequenciesDict = dict()
        for peerId in peerIds:
            for ds in history.downloads[peerId]:
                for download in ds:
                    if re.match("Seed", download.fromId):
                        continue
                    if frequenciesDict.get((download.fromId, download.toId), None) == None:
                        frequenciesDict[(download.fromId, download.toId)] = download.blocks
                    else:
                        frequenciesDict[(download.fromId, download.toId)] = frequenciesDict.get((download.fromId, download.toId)) + download.blocks
                        
        return frequenciesDict

    def unchokeCount(peerIds, history):
        """
        peerIds: list of peerIds
        history: a History object

        Returns:
        frequenciesDict -> dictionary in the form {(A, B): int], logging the number of unchokes from A to B
        """
        frequenciesDict = dict()
        for peerId in peerIds:
            for ds in history.downloads[peerId]:
                for download in ds:
                    if re.match("Seed", download.fromId):
                        continue
                    if frequenciesDict.get((download.fromId, download.toId), None) == None:
                        frequenciesDict[(download.fromId, download.toId)] = 1
                    else:
                        frequenciesDict[(download.fromId, download.toId)] = frequenciesDict.get((download.fromId, download.toId)) + 1
                        
        return frequenciesDict

    @staticmethod
    def uploadedBlocksStr(peerIds, history):
        """ Return a pretty stringified version of uploaded_blocks """
        d = Stats.uploadedBlocks(peerIds, history)

        #k = lambda id: d[id]
        return "\n".join("%s: %d, bw=%d" % (id, d[id], history.uploadRates[id])
                         for id in sorted(d, key=d.get))


        
    @staticmethod
    def completionRounds(peerIds, history):
        """Returns dict: peer_id -> round when completed,
        or -1 if not completed"""
        d = dict(history.roundDone)
        for id in peerIds:
            if id not in d:
                d[id] = -1 
        return d

    @staticmethod
    def completionRoundsStr(peerIds, history):
        """ Return a pretty stringified version of completionRounds """
        d = Stats.completionRounds(peerIds, history)
        return "\n".join("%s: %s" % (id, d[id])
                         for id in sorted(d, key=d.get))
        #return "Not completed \n:" + "\n".join("%s: %s" % 
        #       id for id in d)
    

    @staticmethod
    def allDoneRound(peerIds, history):
        d = Stats.completionRounds(peerIds, history)
        dVal = d.values()
        if -1 in dVal:
            return -1
        return max(dVal)

    @staticmethod
    def frequencyMap(frequenciesList, bandwidths, sortby=None):
        """
        given the dict of bandwidths for the agents listed in the frequency lists, a tag which is used to define how a list is sorted, and a list of lists where each contains at least three items, the last of which is an int

        if sortby is set to None, the pairs will be sorted by the bandwidths of the agent, and if it is set to alpha, the peers will be sorted on the chart alphabetically, grouping them together by type

        will make a heatmap showing the frequencies of the different pairs
        """
        groupList = []
        recievers = set()
        if sortby == None:
            frequenciesList.sort(key=lambda x: x[0])
        if sortby == "alpha":
            frequenciesList.sort(key=lambda x: (bandwidths.get(x[0]), x))
        for frequency in frequenciesList:
            if frequency[0] not in groupList:
                groupList.append(frequency[0])
            recievers.add(frequency[1])
        for x in recievers:
            if x not in groupList:
                groupList.append(x)
    
        frequenciesMatrix = [[[0 for k in list(range(2))] for j in list(range(len(groupList)))] for i in list(range(len(groupList)))]
        resultMatrix = [[0 for j in list(range(len(groupList)))] for i in list(range(len(groupList)))]
        for frequency in frequenciesList:
            toIndex = groupList.index(frequency[0])
            fromIndex = groupList.index(frequency[1])
            freqVal = frequency[2]
            currAvgFreq = frequenciesMatrix[toIndex][fromIndex][0]
            currFreqOcc = frequenciesMatrix[toIndex][fromIndex][1]
            newFreq = ((currFreqOcc * currAvgFreq) + freqVal) / (currFreqOcc + 1)
            frequenciesMatrix[toIndex][fromIndex][0] = newFreq
            frequenciesMatrix[toIndex][fromIndex][1]+=1
            resultMatrix[toIndex][fromIndex] = newFreq

        fig, ax = plt.subplots()
        
        plt.imshow(resultMatrix, cmap='Greys', interpolation='nearest')
        plt.colorbar()
        ax.set_xticks(np.arange(len(groupList)), labels=groupList)
        ax.set_yticks(np.arange(len(groupList)), labels=groupList)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        plt.show()