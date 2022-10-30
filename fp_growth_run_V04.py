from collections import defaultdict, OrderedDict
from csv import reader
from itertools import chain, combinations
from optparse import OptionParser
from queue import Empty
from unicodedata import numeric
from fpgrowth_py.utils import *
import pandas as pd
import math
import datetime

#######################UTILS#######################################################

class Node:
    def __init__(self, itemName, support, parentNode):
        self.itemName = itemName
        self.count = support
        self.parent = parentNode
        self.children = {}
        self.next = None

    def increment(self, support):
        self.count += support

    def display(self, ind=1):
        print('  ' * ind, self.itemName, ' ', self.count)
        for child in list(self.children.values()):
            child.display(ind+1)

# Added by David Schmid
def getFromDataFrame(data,item_col,date_col,max_date,date_range,profit_col, max_profit, profit_sensitivity):

    # Date based mofidier Added by David Schmid
    def modified_sigmoid(x):
        return 1 / (1 + math.exp(-x+4)) # Modified sigmoid

    # Profit based modifier Added by David Schmid
    def profitSupport(profit):
        return profit / max_profit * profit_sensitivity # If profit_sensitivity = 1, then range [0,1], if profit_sensitivity = 3, then range [0,3]

    dateSupportDict = dict()

    # Date based mofidier
    if date_col != False and max_date != False:
        for i in range(date_range):
            dateSupportDict[max_date-datetime.timedelta(days = i)]=modified_sigmoid((date_range-i)/date_range*8) # Create time support dictionary for every date in range


    itemSetList = []
    support = []
    numTransaction = 0

    # Mofified and extended by David Schmid
    for row in data.values:
        tempSupport = []
        tempItemSetList = []
        for idx, item in enumerate(row[item_col-1]):
                try:
                    idx_multi = tempItemSetList.index(item) # If not double, it will fail
                    tempSupport[idx_multi] += dateSupportDict[row[date_col-1][idx_multi]]*profitSupport(row[profit_col-1][idx_multi]) # Solve problem of multiple items per transaction
                except:
                    try:
                        if math.isnan(dateSupportDict[row[date_col-1][idx]]*profitSupport(row[profit_col-1][idx])) == False:
                            tempSupport.append(dateSupportDict[row[date_col-1][idx]]*profitSupport(row[profit_col-1][idx])) # Support = Date Function * Value Function
                            tempItemSetList.append(item) # Append every new element
                    except:
                        pass # Errors like not found date in index -> intentionally has toi be skipped
        
        if tempSupport:
            itemSetList.append(tempItemSetList) #Shortened list every item only one time
            if max(tempSupport) != max(tempSupport):
                print("Hello Error")
            numTransaction+=max(tempSupport) # Support of each item is different, get max Support of highest item
            support.append(tempSupport) # Add List to List representing each item has individual support
    return itemSetList, support, numTransaction


def constructTree(itemSetList, support, minSup, maxSup):
    headerTable = defaultdict(int)
    # Counting support and create header table
    for idx, itemSet in enumerate(itemSetList):
        for idx2, item in enumerate(itemSet):
            headerTable[item] += support[idx][idx2]

    # Deleting items below minSup
    headerTable = dict((item, sup) for item, sup in headerTable.items() if sup >= minSup and sup <= maxSup) 
    if(len(headerTable) == 0):
        return None, None

    # HeaderTable column [Item: [support, headNode]]
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
        for idx2, item in enumerate(itemSet):
            currentNode = updateTree(item, currentNode, headerTable, support[idx][idx2])

    return fpTree, headerTable

def constructTreeMine(itemSetList, frequency, minSup, maxSup):
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

def updateTree(item, treeNode, headerTable, support):
    if item in treeNode.children:
        # If the item already exists, increment the count
        treeNode.children[item].increment(support)
    else:
        # Create a new branch
        newItemNode = Node(item, support, treeNode)
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
    support = []
    while treeNode != None:
        prefixPath = []
        # From leaf node all the way to root
        ascendFPtree(treeNode, prefixPath)  
        if len(prefixPath) > 1:
            # Storing the prefix path and it's corresponding count
            condPats.append(prefixPath[1:])
            support.append(treeNode.count)

        # Go to next node
        treeNode = treeNode.next  
    return condPats, support

def mineTree(headerTable, minSup, maxSup, preFix, freqItemList):
    # Sort the items with support and create a list
    sortedItemList = [item[0] for item in sorted(list(headerTable.items()), key=lambda p:p[1][0])] 
    # Start with the lowest support
    for item in sortedItemList:  
        # Pattern growth is achieved by the concatenation of suffix pattern with frequent patterns generated from conditional FP-tree
        newFreqSet = preFix.copy()
        newFreqSet.add(item)
        freqItemList.append(newFreqSet)
        # Find all prefix path, constrcut conditional pattern base
        conditionalPattBase, support = findPrefixPath(item, headerTable) 
        # Construct conditonal FP Tree with conditional pattern base
        conditionalTree, newHeaderTable = constructTreeMine(conditionalPattBase, support, minSup, maxSup) 
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

def associationRule(freqItemSet, itemSetList, support, minConf, maxConf, numTransaction):
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


##############################################################################


# Added by David Schmid
def fpgrowthFromDataFrame(data,minSupRatio=0.001,maxSupRatio=1,minConf=0.5,maxConf=1,item_col=1,date_col=False,max_date=False,date_range=90,profit_col=False, max_profit=False, profit_sensitivity=1):
    itemSetList, support, numTransaction = getFromDataFrame(data,item_col,date_col,max_date,date_range,profit_col, max_profit, profit_sensitivity)
    minSup = numTransaction * minSupRatio
    maxSup = numTransaction * maxSupRatio
    fpTree, headerTable = constructTree(itemSetList, support, minSup, maxSup)
    if(fpTree == None):
        print('No frequent item set')
    else:
        freqItems = []
        mineTree(headerTable, minSup, maxSup, set(), freqItems)
        rules = associationRule(freqItems, itemSetList, support, minConf, maxConf, numTransaction)
        rules_pd = pd.DataFrame(rules,columns=["antecedent","consequent","antecedent&consequent","confidence","lift","improvement","bi-improvement","csa"])
        return freqItems, rules_pd


########################EXECUTION######################################################

data = pd.read_csv("kz_part_1 copy.csv")
data["date"] = pd.to_datetime(data['event_time']).dt.date
max_date = data["date"].max()
data["margin"] = 0.1
data["profit"] = data["price"] * data["margin"]
max_profit = data["profit"].max()

data = data.groupby("order_id",dropna=True)["product_id","date","price","margin"].agg(lambda x: list(x))

freqItemSet, rules = fpgrowthFromDataFrame(data,minSupRatio=0.001,maxSupRatio=1,minConf=0.2,maxConf=1,item_col=1,date_col=2,max_date=max_date,date_range=90,profit_col=3, max_profit=max_profit, profit_sensitivity=1) #Success
#freqItemSet, rules = fpgrowthFromFile("data7.csv", minSupRatio=0.1, minConf=0.5)
print(rules) 
rules.to_excel("fp_groth_out.xlsx")
# [[{'beer'}, {'rice'}, 0.6666666666666666], [{'rice'}, {'beer'}, 1.0]]
# rules[0] --> rules[1], confidence = rules[2]
