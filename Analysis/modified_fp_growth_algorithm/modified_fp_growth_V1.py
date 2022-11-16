from collections import defaultdict
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
    
    def create_association_rules(self,assoc_rules,path=""):
        assoc_rules.append((self.itemName,self.count,path))
        for child in list(self.children.values()):
            child.create_association_rules(assoc_rules,path+","+str(self.itemName))
        else: # After Recursion, clean up list
            return assoc_rules


# Added by David Schmid
def getFromDataFrame(data, item_col, date_col, profit_col, max_date, date_range, date_sensitivity, max_profit, profit_sensitivity):

    """
    # Date based mofidier Added by David Schmid
    def modified_sigmoid(x):
        return 1 / (1 + math.exp(-x+4)) # Modified sigmoid

    # Profit based modifier Added by David Schmid
    def profitSupport(profit):
        return (profit/max_profit) * profit_sensitivity # If profit_sensitivity = 1, then range [0,1], if profit_sensitivity = 3, then range [0,3]
    """

    dateSupportDict = dict()

    itemSetList = []
    support = []
    numTransaction = 0

    dateInDataframe = date_col and max_date and date_range and date_sensitivity
    profitInDataframe = profit_col and max_profit and profit_sensitivity

    # Date based mofidier
    if dateInDataframe:
        for i in range(date_range):
            dateSupportDict[max_date-datetime.timedelta(days = i)]=date_sensitivity((date_range-i)/date_range) # Create time support dictionary for every date in range

    # Mofified and extended by David Schmid
    
    for row in data.values:
        tempSupport = []
        tempItemSetList = []

        for idx, item in enumerate(row[item_col-1]):
                try: # Solve problem of multiple items per transaction
                    idx_multi = tempItemSetList.index(item) # If not double, it will fail
                    if(dateInDataframe and profitInDataframe): #Date & Profit available in Dataframe
                        tempSupport[idx_multi] += dateSupportDict[row[date_col-1][idx]]*profit_sensitivity(row[profit_col-1][idx]/max_profit) # Support of Date Function * Profit Function
                    elif(dateInDataframe): #Date available in Dataframe
                        tempSupport[idx_multi] += dateSupportDict[row[date_col-1][idx]] # Support of Date Function
                    elif(profitInDataframe): #Profit available in Dataframe
                        tempSupport[idx_multi] += profit_sensitivity(row[profit_col-1][idx]/max_profit) # Support of Profit Function
                    else: # Simple Count but without consideration of multiple items per Transactions as in the Association Rules Algorithms, therefore pass
                        pass # Therefore in this case pass
                        
                except:
                    try:
                        if(dateInDataframe and profitInDataframe): #Date & Profit available in Dataframe
                            if math.isnan(dateSupportDict[row[date_col-1][idx]]*profit_sensitivity(row[profit_col-1][idx])) == False:
                                tempSupport.append(dateSupportDict[row[date_col-1][idx]]*profit_sensitivity(row[profit_col-1][idx]/max_profit)) # Support of Date Function * Profit Function
                                tempItemSetList.append(item) # Append every new element
                        elif(dateInDataframe): #Date available in Dataframe
                            if math.isnan(dateSupportDict[row[date_col-1][idx]]) == False:
                                tempSupport.append(dateSupportDict[row[date_col-1][idx]]) # Support of Date Function
                                tempItemSetList.append(item) # Append every new element
                        elif(profitInDataframe): #Date available in Dataframe
                            if math.isnan(profit_sensitivity(row[profit_col-1][idx]/max_profit)) == False:
                                tempSupport.append(profit_sensitivity(row[profit_col-1][idx]/max_profit)) # Support of Profit Function
                                tempItemSetList.append(item) # Append every new element
                        else: # Simple Count as in the traditional Association Rules Algorithms
                            tempSupport.append(1) #Count 1
                            tempItemSetList.append(item) # Append every new element
                    except:
                        pass # Errors like not found date in index -> intentionally has to be skipped
        
        if tempSupport:
            itemSetList.append(tempItemSetList) #Shortened list every item only one time
            numTransaction+=max(tempSupport) # Support of each item is different, get max Support of highest item, instead of count 1
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

def updateTree(item, treeNode, headerTable, support):
    if item in treeNode.children:
        # If the item already exists, increment the count
        treeNode.children[item].increment(support)
    else:
        # Create a new branch
        newItemNode = Node(item, support, treeNode)
        treeNode.children[item] = newItemNode

    return treeNode.children[item]

def associationRule(assoc_rules, headerTable, minConf, minSupRatio, numTransaction):
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

        if(confidence == "NA" or (confidence >= minConf and percItemSetSup >= minSupRatio)):
            rules.append(
                    [antecedent,
                    supAntecedent,
                    consequent,
                    supConsequent,
                    antecedentConsequent,
                    supAntecedentConsequent,
                    #confidence,
                    #lift,
                    #improvement,
                    #bi_improvement,
                    #csa
                    ])
    return rules


##############################################################################


# Added by David Schmid
def fpgrowthFromDataFrame(data, minSupRatio=0.001, maxSupRatio=1, minConf=0, item_col=1, date_col=False, profit_col=False, max_date = False, date_range=False, date_sensitivity = lambda x: 1 / (1 + math.exp(-10*x+5)), max_profit = False, profit_sensitivity = lambda x : 1*x):
    itemSetList, support, numTransaction = getFromDataFrame(data, item_col, date_col, profit_col, max_date, date_range, date_sensitivity, max_profit, profit_sensitivity)
    minSup = numTransaction * minSupRatio
    maxSup = numTransaction * maxSupRatio
    fpTree, headerTable = constructTree(itemSetList, support, minSup, maxSup)
    if(fpTree == None):
        print('No frequent item set')
    else:
        assoc_rules = fpTree.create_association_rules(list())
        rules = associationRule(assoc_rules, headerTable, minConf, minSupRatio, numTransaction)
        rules_pd = pd.DataFrame(rules,columns=["antecedent","sup_antecedent","consequent","sup_consequent","antecedent&consequent","sup_antecedent&consequent"])
        return rules_pd

