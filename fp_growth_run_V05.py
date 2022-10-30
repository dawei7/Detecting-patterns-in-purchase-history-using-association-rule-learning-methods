from collections import defaultdict, OrderedDict
from csv import reader
from itertools import chain, combinations
from optparse import OptionParser
from queue import Empty
from unicodedata import numeric
# from fpgrowth_py.utils import *
import pandas as pd
import math
import datetime
import copy

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

    def display(self, ind=1): # Recursive function
        print('  ' * ind, self.itemName, ' ', self.count)
        for child in list(self.children.values()):
            child.display(ind+1) 
    
    """
    def create_association_rules(self,association_rules,counter,lvl=1):
        assoc_rules.append((self.itemName,self.count))
        for child in list(self.children.values()): # Recursive function
            counter +=1
            child.create_association_rules(association_rules,counter,lvl+1)
    """
    
    def create_association_rules(self,assoc_rules,path=""):
        assoc_rules.append((self.itemName,self.count,path))
        for child in list(self.children.values()):
            child.create_association_rules(assoc_rules,path+","+str(self.itemName))
        else: # After Recursion, clean up list
            return assoc_rules




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
        # updateHeaderTable(item, newItemNode, headerTable)

    return treeNode.children[item]


def associationRule(assoc_rules, headerTable, minConf, maxConf, numTransaction):

    dict_assoc_rules = dict()
    for elements in assoc_rules:
        consequent,support_antecedent_consequent,antecedent = elements
        if consequent != "Null":
            antecedent = antecedent[1:].split(",") #Split by comma, delete first ","
            antecedent.pop(0) #Pop Root Null Element
            antecedent_consequent = copy.deepcopy(antecedent)
            antecedent_consequent.append(str(consequent))
            dict_assoc_rules[frozenset(antecedent_consequent)]=[antecedent,consequent,headerTable[consequent][0],support_antecedent_consequent]


    rules = []
    for key, value in dict_assoc_rules.items():
        
        # Support
        antecedentConsequent = list(key)
        antecedent = value[0]
        consequent = [str(value[1])]
        supAntecedentConsequent = value[3]
        supConsequent = value[2]

        if antecedent != []:
            supAntecedent = dict_assoc_rules[frozenset(value[0])][3]

            # Percentage measures
            percItemSetSup = supAntecedentConsequent / numTransaction #in %
            percSupAntecedent = supAntecedent / numTransaction #in %
            percSupConsequent = supConsequent / numTransaction #in %

            # Success metrics
            confidence = supAntecedentConsequent / supAntecedent
            lift = percItemSetSup/(percSupAntecedent * percSupConsequent)
            improvement = confidence - percSupConsequent
            bi_improvement = percItemSetSup-(percSupAntecedent * percSupConsequent/(1-percItemSetSup))
            csa = (confidence-percSupConsequent)/math.sqrt((percSupConsequent*(1-percSupConsequent))/numTransaction) #set chi-square-analysis
        else:
            supAntecedent = "NA"
            confidence = "NA"
            lift = "NA"
            improvement = "NA"
            bi_improvement = "NA"
            csa = "NA"

        if(confidence == "NA" or confidence >= minConf):
            rules.append(
                    [antecedent,
                    supAntecedent,
                    consequent,
                    supConsequent,
                    antecedentConsequent,
                    supAntecedentConsequent,
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
        assoc_rules = fpTree.create_association_rules(list())
        rules = associationRule(assoc_rules, headerTable, minConf, maxConf, numTransaction)
        rules_pd = pd.DataFrame(rules,columns=["antecedent","sup_antecedent","consequent","sup_consequent","antecedent&consequent","sup_antecedent&consequent","confidence","lift","improvement","bi-improvement","csa"])
        return rules_pd

########################EXECUTION######################################################

data = pd.read_csv("kz_part_1 copy 2.csv")
data["date"] = pd.to_datetime(data['event_time']).dt.date
max_date = data["date"].max()
data["margin"] = 0.1
data["profit"] = data["price"] * data["margin"]
max_profit = data["profit"].max()

data = data.groupby("order_id",dropna=True)["product_id","date","price","margin"].agg(lambda x: list(x))

rules = fpgrowthFromDataFrame(data,minSupRatio=0.001,maxSupRatio=1,minConf=0,maxConf=1,item_col=1,date_col=2,max_date=max_date,date_range=90,profit_col=3, max_profit=max_profit, profit_sensitivity=1) #Success
#freqItemSet, rules = fpgrowthFromFile("data7.csv", minSupRatio=0.1, minConf=0.5)
print(rules) 
rules.to_excel("fp_groth_out.xlsx")
# [[{'beer'}, {'rice'}, 0.6666666666666666], [{'rice'}, {'beer'}, 1.0]]
# rules[0] --> rules[1], confidence = rules[2]
