from collections import defaultdict, OrderedDict
from csv import reader
from itertools import chain, combinations
from optparse import OptionParser
from fpgrowth_py.utils import *
import pandas as pd
import math
import datetime

#######################UTILS#######################################################

class Node:
    def __init__(self, itemName, frequency, parentNode):
        self.itemName = itemName
        self.count = frequency
        self.parent = parentNode
        self.children = {}
        self.next = None

    def increment(self, frequency):
        self.count += frequency

    def display(self, ind=1):
        print('  ' * ind, self.itemName, ' ', self.count)
        for child in list(self.children.values()):
            child.display(ind+1)

# Added by David Schmid
def modified_sigmoid(x):
    return 1 / (1 + math.exp(-x+4))

# Added by David Schmid
def getFromDataFrame(df):

    my_dict = dict()
    date_diff = (data["date"].max()-data["date"].min()).days

    for i in range(date_diff+1):
        my_dict[data["date"].min()+datetime.timedelta(days = i)]=modified_sigmoid(i/date_diff*8)

    itemSetList = []
    frequency = []
    numTransaction = 0
    for line in df.values:
        itemSetList.append(line[0])
        frequency.append(my_dict[line[1]])
        numTransaction+=my_dict[line[1]]
    return itemSetList, frequency, numTransaction


def constructTree(itemSetList, frequency, minSup, maxSup):
    headerTable = defaultdict(int)
    # Counting frequency and create header table
    for idx, itemSet in enumerate(itemSetList):
        for item in itemSet:
            headerTable[item] += frequency[idx]

    # Deleting items below minSup
    headerTable = dict((item, sup) for item, sup in headerTable.items() if sup >= minSup and sup <= maxSup) 
    if(len(headerTable) == 0):
        return None, None

    # HeaderTable column [Item: [frequency, headNode]]
    for item in headerTable:
        headerTable[item] = [headerTable[item], None]

    # Init Null head node
    fpTree = Node('Null', 1, None)
    # Update FP tree for each cleaned and sorted itemSet
    for idx, itemSet in enumerate(itemSetList):
        itemSet = [item for item in itemSet if item in headerTable]
        itemSet.sort(key=lambda item: headerTable[item][0], reverse=True)
        # Traverse from root to leaf, update tree with given item
        currentNode = fpTree
        for item in itemSet:
            currentNode = updateTree(item, currentNode, headerTable, frequency[idx])

    return fpTree, headerTable

def updateHeaderTable(item, targetNode, headerTable):
    if(headerTable[item][1] == None):
        headerTable[item][1] = targetNode
    else:
        currentNode = headerTable[item][1]
        # Traverse to the last node then link it to the target
        while currentNode.next != None:
            currentNode = currentNode.next
        currentNode.next = targetNode

def updateTree(item, treeNode, headerTable, frequency):
    if item in treeNode.children:
        # If the item already exists, increment the count
        treeNode.children[item].increment(frequency)
    else:
        # Create a new branch
        newItemNode = Node(item, frequency, treeNode)
        treeNode.children[item] = newItemNode
        # Link the new branch to header table
        updateHeaderTable(item, newItemNode, headerTable)

    return treeNode.children[item]

def ascendFPtree(node, prefixPath):
    if node.parent != None:
        prefixPath.append(node.itemName)
        ascendFPtree(node.parent, prefixPath)

def findPrefixPath(basePat, headerTable):
    # First node in linked list
    treeNode = headerTable[basePat][1] 
    condPats = []
    frequency = []
    while treeNode != None:
        prefixPath = []
        # From leaf node all the way to root
        ascendFPtree(treeNode, prefixPath)  
        if len(prefixPath) > 1:
            # Storing the prefix path and it's corresponding count
            condPats.append(prefixPath[1:])
            frequency.append(treeNode.count)

        # Go to next node
        treeNode = treeNode.next  
    return condPats, frequency

def mineTree(headerTable, minSup, maxSup, preFix, freqItemList):
    # Sort the items with frequency and create a list
    sortedItemList = [item[0] for item in sorted(list(headerTable.items()), key=lambda p:p[1][0])] 
    # Start with the lowest frequency
    for item in sortedItemList:  
        # Pattern growth is achieved by the concatenation of suffix pattern with frequent patterns generated from conditional FP-tree
        newFreqSet = preFix.copy()
        newFreqSet.add(item)
        freqItemList.append(newFreqSet)
        # Find all prefix path, constrcut conditional pattern base
        conditionalPattBase, frequency = findPrefixPath(item, headerTable) 
        # Construct conditonal FP Tree with conditional pattern base
        conditionalTree, newHeaderTable = constructTree(conditionalPattBase, frequency, minSup, maxSup) 
        if newHeaderTable != None:
            # Mining recursively on the tree
            mineTree(newHeaderTable, minSup, maxSup, newFreqSet, freqItemList)

def powerset(s):
    return chain.from_iterable(combinations(s, r) for r in range(1, len(s)))

def getSupport(testSet, itemSetList):
    count = 0
    for itemSet in itemSetList:
        if(set(testSet).issubset(itemSet)):
            count += 1
    return count

def associationRule(freqItemSet, itemSetList, minConf, maxConf, numTransaction):
    rules = []
    for itemSet in freqItemSet:
        subsets = powerset(itemSet)
        supItemSet = getSupport(itemSet, itemSetList) #Antecedent & Consequent
        for s in subsets:
            # Major parts in metrics added by David Schmid

            # Support
            supAntecedent = getSupport(s, itemSetList)
            supConsequent = getSupport(set(itemSet.difference(s)),itemSetList)

            # Percentage measures
            percItemSetSup = supItemSet / numTransaction #in %
            percSupAntecedent = supAntecedent / numTransaction #in %
            percSupConsequent = supConsequent / numTransaction #in %

            # Success metrics
            confidence = supItemSet / supAntecedent
            lift = percItemSetSup/(percSupAntecedent * percSupConsequent)
            improvement = confidence - percSupConsequent
            bi_improvement = percItemSetSup-(percSupAntecedent * percSupConsequent/(1-percItemSetSup))
            csa = (confidence-percSupConsequent)/math.sqrt((percSupConsequent*(1-percSupConsequent))/numTransaction) #set chi-square-analysis
            if(confidence >= minConf and confidence <= maxConf):
                rules.append(
                    [set(s),
                    set(itemSet.difference(s)),
                    itemSet,
                    confidence,
                    lift,
                    improvement,
                    bi_improvement,
                    csa
                    ])
    return rules

"""
def getFrequencyFromList(itemSetList):
    frequency = [1 for i in range(len(itemSetList))]
    return frequency
"""

##############################################################################


# Added by David Schmid
def fpgrowthFromDataFrame(df, minSupRatio = 0.01, maxSupRatio=1, minConf=0.5, maxConf=0.6): 
    itemSetList, frequency, numTransaction = getFromDataFrame(df)
    minSup = numTransaction * minSupRatio
    maxSup = numTransaction * maxSupRatio
    fpTree, headerTable = constructTree(itemSetList, frequency, minSup, maxSup)
    if(fpTree == None):
        print('No frequent item set')
    else:
        freqItems = []
        mineTree(headerTable, minSup, maxSup, set(), freqItems)
        rules = associationRule(freqItems, itemSetList, minConf, maxConf, numTransaction)
        rules_pd = pd.DataFrame(rules,columns=["antecedent","consequent","antecedent&consequent","confidence","lift","improvement","bi-improvement","csa"])
        return freqItems, rules_pd


########################EXECUTION######################################################

data = pd.read_csv("kz_part_1 copy.csv")
data = data.groupby('order_id',dropna=True).agg({'product_id':lambda x: list(x),'event_time':'first'})
data["date"] = pd.to_datetime(data['event_time']).dt.date
data.drop("event_time",axis=1, inplace=True)
data = data[(data["date"]>=datetime.date(year=2020,month=1,day=1))]



freqItemSet, rules = fpgrowthFromDataFrame(data, minSupRatio=0.001,maxSupRatio=1, minConf=0.5, maxConf=1) #Success
#freqItemSet, rules = fpgrowthFromFile("data7.csv", minSupRatio=0.1, minConf=0.5)
print(rules) 
rules.to_excel("fp_groth_out.xlsx")
# [[{'beer'}, {'rice'}, 0.6666666666666666], [{'rice'}, {'beer'}, 1.0]]
# rules[0] --> rules[1], confidence = rules[2]