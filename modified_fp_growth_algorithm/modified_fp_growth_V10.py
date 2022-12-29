from collections import defaultdict
import pandas as pd
import math
import datetime
import copy
from itertools import combinations



class Node:
    def __init__(self, itemName, support, parentNode):
        self.itemName = itemName
        self.count = support
        self.parent = parentNode
        self.children = {}
        self.next = None

    def increment(self, support, profit=1, weight_date=1):
        self.count += support

    
    def create_association_rules(self,assoc_rules,path=""):
        assoc_rules.append((self.itemName,self.count,path))
        for child in list(self.children.values()):
            child.create_association_rules(assoc_rules,path+","+str(self.itemName))
        else: # After Recursion, return list
            return assoc_rules


def sort_dict_by_value(d, reverse = False):
    return dict(sorted(d.items(), key = lambda x: x[1], reverse = reverse))

def getFromDataFrame(data, item_col, date_col, profit_col, max_date, date_range, date_sensitivity, max_profit, profit_sensitivity):

    dateSupportDict = dict()

    itemSetList = []
    dict_profit_per_item = defaultdict(list)
    support = []
    numTransaction = 0

    dateInDataframe = True if date_col and max_date and date_range and date_sensitivity else False # Flag: True/False is here date data
    profitInDataframe = True if profit_col and max_profit and profit_sensitivity else False # Flag: True/False Is there profit data

    # Date based mofidier
    if dateInDataframe:
        for i in range(date_range):
            dateSupportDict[max_date-datetime.timedelta(days = i)]=date_sensitivity((date_range-i)/date_range) # Create time support dictionary for every date in range

    
    for row in data.values:
        tempSupport = []
        tempItemSetList = []

        for idx, item in enumerate(row[item_col-1]):
                try: # Solve problem of multiple items per transaction
                    idx_multi = tempItemSetList.index(str(item)) # If not double, it will fail
                    if(profitInDataframe): #Date & Profit available in Dataframe
                        dict_profit_per_item[str(item)][0] += row[profit_col-1][idx] # If there are mutiple items, don't add to the count, but to the profit, to get higher average profit per item
                    else: # Simple Count but without consideration of multiple items per Transactions as in the Association Rules Algorithms, therefore pass
                        pass # Therefore in this case pass
                        
                except:
                    try:
                        if(dateInDataframe and profitInDataframe): #Date & Profit available in Dataframe
                            if math.isnan(dateSupportDict[row[date_col-1][idx]]*profit_sensitivity(row[profit_col-1][idx]/max_profit)*max_profit) == False:
                                # Add the end of the loop, we will divide sum profit of each item / count of each item. If there are multiple items, count once, but add up profit
                                # In this way, we can weight the mutiple items, without destroying the equivalence of the principle of association rules
                                # However, this method is only possible if we have profit on each item, or assumed profit at least dervived from prices/revenue
                                if item not in dict_profit_per_item:
                                    dict_profit_per_item[str(item)] += [0,0,0] #If there doesn't exist a dictionay, create one
                                dict_profit_per_item[str(item)][1]+=1 #One normal counter needed for average at the end
                                dict_profit_per_item[str(item)][0]+= profit_sensitivity(row[profit_col-1][idx]/max_profit)*max_profit #Add up profit
                                dict_profit_per_item[str(item)][2]+= dateSupportDict[row[date_col-1][idx]] #Support of Date Function only for diluted profit

                                tempSupport.append(dateSupportDict[row[date_col-1][idx]]) # Support of Date Function
                                tempItemSetList.append(str(item)) #Append every new element
                        elif(dateInDataframe): #Date available in Dataframe
                            if math.isnan(dateSupportDict[row[date_col-1][idx]]) == False:
                                tempSupport.append(dateSupportDict[row[date_col-1][idx]]) # Support of Date Function
                                tempItemSetList.append(str(item)) # Append every new element
                        elif(profitInDataframe): #Date available in Dataframe
                            if math.isnan(profit_sensitivity(row[profit_col-1][idx]/max_profit)*max_profit) == False:
                                if str(item) not in dict_profit_per_item:
                                    dict_profit_per_item[str(item)] += [0,0] #If there doesn't exist a dictionay, create one
                                dict_profit_per_item[str(item)][1]+=1 #One normal counter needed for average at the end
                                dict_profit_per_item[str(item)][0]+= profit_sensitivity(row[profit_col-1][idx]/max_profit)*max_profit #Add up profit

                                tempSupport.append(1) # Support of Profit Function
                                tempItemSetList.append(str(item)) # Append every new element         
                        else: # Simple Count as in the traditional Association Rules Algorithms
                            tempSupport.append(1) #Count 1
                            tempItemSetList.append(str(item)) # Append every new element
                    except:
                        pass # Errors like not found date in index -> intentionally has to be skipped
        
        if tempSupport:
            itemSetList.append(tempItemSetList) #Shortened list every item only one time
            if dateInDataframe:
                numTransaction+=tempSupport[0] # Support of transaction by after date decay function, just take the first value, all values are the same
            else:
                numTransaction+=1
            support.append(tempSupport) # Add List to List representing each item has individual support, however in our case it is the same because of Association Rule equivalence

    return itemSetList, support, numTransaction, dict_profit_per_item, profitInDataframe, dateInDataframe


def constructTree(itemSetList, support, minSup, maxSup, dict_profit_per_item, profitInDataframe, minProfit):
    headerTable = defaultdict(int)

    # Counting support and create header table
    for idx, itemSet in enumerate(itemSetList):
        for idx2, item in enumerate(itemSet):
            headerTable[item] += support[idx][idx2]

    # Deleting items below minSup
    # Even with profit
    if profitInDataframe:
        headerTable = dict((item, sup) for item, sup in headerTable.items() if (dict_profit_per_item[item][0] > minProfit))
    else:
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

        # In our case, all items have the same support, therefore it doesn't matter, therefore a more general approach here, where it could matter in future
        itemSet_zipped = list(zip(itemSet, support[idx]))
        itemSet = [item for item in itemSet_zipped if item[0] in headerTable]
        itemSet.sort(key=lambda item: headerTable[item[0]][0], reverse=True)
        # Traverse from root to leaf, update tree with given item
        currentNode = fpTree
        for idx2, item in enumerate(itemSet):
            currentNode = updateTree(item[0], currentNode, headerTable, item[1])

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


def associationRule(assoc_rules, headerTable, minConf, minSup, minTransactionLength, maxTransactionLength, numTransaction, dict_profit_per_item, profitInDataframe,diluted_total_profit,minProfit):
    dict_assoc_rules = dict()
    rules = []
    list_itemsets = []
    list_itemsets_support = []

    for elements in assoc_rules:
        consequent,support_antecedent_consequent,antecedent = elements
        if consequent != "Null":
            antecedent = antecedent[1:].split(",") #Split by comma, delete first ","
            antecedent.pop(0) #Pop Root Null Element
            antecedent_consequent = copy.deepcopy(antecedent)
            antecedent_consequent.append(str(consequent))


            list_itemsets.append(antecedent_consequent)
            list_itemsets_support.append(support_antecedent_consequent)

            # dict_assoc_rules[frozenset(antecedent_consequent)]=[antecedent,consequent,headerTable[consequent][0],support_antecedent_consequent]
    
    headerTable_keys = list(headerTable.keys())
    headerTable_keys.sort(key=lambda item: headerTable[item][0], reverse=False)

    

    for item in headerTable_keys:
        my_temp_sets = []
        my_temp_support = []
        my_combinations = []
        for idx, itemset in enumerate(list_itemsets):
            if item == itemset[len(itemset)-1]:
                my_temp_sets.append(itemset)
                my_temp_support.append(list_itemsets_support[idx]) # get support of last added item
        
                my_temp_combinations = sum([list(map(list, combinations(itemset[0:len(itemset)-1], i))) for i in range(len(itemset)-1 + 1)], [])
                for my_temp_combination in my_temp_combinations:
                    my_temp_combination.append(item)
                    if my_temp_combination not in my_combinations:
                        my_combinations.append(my_temp_combination)

        for my_combination in my_combinations:
            support = 0
            for idx, my_temp_set in enumerate(my_temp_sets):
                if set(my_combination) <= set(my_temp_set): # Check if combination is subset of the subtree set
                    support+= my_temp_support[idx]
            if support >= 0 and support != 0:
                dict_assoc_rules[frozenset(my_combination)]=[list(set(my_combination)-set([item])),item,headerTable[item][0],support]
            
                
    
    for key, value in dict_assoc_rules.items():
        
        # Support
        antecedentConsequent = list(key)
        antecedent = value[0]
        consequent = [str(value[1])]
        supAntecedentConsequent = value[3]
        supConsequent = value[2]


        # profit metrics
        profit_associated = 0
        profit_associated_prev = 0
        profit_last_item = 0
        loss_by_change = 0
        net_change = 0

        if profitInDataframe:
            profit_last_item = dict_profit_per_item[consequent[0]][0]/dict_profit_per_item[consequent[0]][1]*supAntecedentConsequent
            for item in antecedentConsequent:
                profit_associated += dict_profit_per_item[item][0]/dict_profit_per_item[item][1]*supAntecedentConsequent
            perc_of_total_profit = profit_associated / diluted_total_profit

        if antecedent != []:
            supAntecedent = dict_assoc_rules[frozenset(value[0])][3]
            if profitInDataframe:
                for item in antecedent:
                    profit_associated_prev += dict_profit_per_item[item][0]/dict_profit_per_item[item][1]*supAntecedent
                
                net_change = profit_associated - profit_associated_prev
                loss_by_change = net_change - profit_last_item

            # Percentage measures
            percItemSetSup = supAntecedentConsequent / numTransaction #in %
            percSupAntecedent = supAntecedent / numTransaction #in %
            percSupConsequent = supConsequent / numTransaction #in %

            # Success metrics
            confidence = supAntecedentConsequent / supAntecedent
            lift = percItemSetSup/(percSupAntecedent * percSupConsequent)
            improvement = confidence - percSupConsequent
        else:
            supAntecedent = "NA"
            percSupAntecedent = "NA"
            confidence = "NA"
            lift = "NA"
            improvement = "NA"
            percItemSetSup = supAntecedentConsequent / numTransaction #in %
            percSupConsequent = supConsequent / numTransaction #in %
            net_change = profit_associated - 0

        if profitInDataframe and (confidence == "NA" or confidence >= minConf) and profit_associated >= minProfit and len(antecedentConsequent)>=minTransactionLength and len(antecedentConsequent)<=maxTransactionLength:
            rules.append([
                antecedent,
                supAntecedent,
                percSupAntecedent,
                consequent,
                supConsequent,
                percSupConsequent,
                antecedentConsequent,
                supAntecedentConsequent,
                percItemSetSup,
                confidence,
                lift,
                improvement,
                profit_associated,
                perc_of_total_profit,
                profit_associated_prev,
                net_change,
                profit_last_item,
                loss_by_change
                ])
        elif not profitInDataframe and (confidence == "NA" or confidence >= minConf) and supAntecedentConsequent >= minSup and len(antecedentConsequent)>=minTransactionLength and len(antecedentConsequent)<=maxTransactionLength:
            rules.append([
                antecedent,
                supAntecedent,
                percSupAntecedent,
                consequent,
                supConsequent,
                percSupConsequent,
                antecedentConsequent,
                supAntecedentConsequent,
                percItemSetSup,
                confidence,
                lift,
                improvement
                ])
    return rules


##############################################################################


def fpgrowthFromDataFrame(data, minSupRatio=0.001, maxSupRatio=1, minTransactionLength=1, maxTransactionLength=100, minConf=0, item_col=1, date_col=False, profit_col=False, max_date = False, date_range=False, date_sensitivity = lambda x: 1 / (1 + math.exp(-10*x+5)), max_profit = False, profit_sensitivity = lambda x : 1*x):
    itemSetList, support, numTransaction, dict_profit_per_item, profitInDataframe, dateInDataframe = getFromDataFrame(data, item_col, date_col, profit_col, max_date, date_range, date_sensitivity, max_profit, profit_sensitivity)
    minSup = numTransaction * minSupRatio
    maxSup = numTransaction * maxSupRatio
    diluted_total_profit = 0
    minProfit = 0
    if profitInDataframe:
        total_profit = sum([float(v[0]) for v in dict_profit_per_item.values()])
        total_simple_count = sum([float(v[1]) for v in dict_profit_per_item.values()])
        if dateInDataframe:
            total_date_dependent_count = sum([float(v[2]) for v in dict_profit_per_item.values()])
            diluted_total_profit = total_profit/total_simple_count*total_date_dependent_count # If date decay function function is present it needs a correction
        else:
            diluted_total_profit = total_profit # Without date function, no change needed - cleaner approach
        minProfit = minSupRatio*diluted_total_profit

    fpTree, headerTable = constructTree(itemSetList, support, minSup, maxSup, dict_profit_per_item, profitInDataframe,minProfit)
    if(fpTree == None):
        print('No frequent item set')
    else:
        assoc_rules = fpTree.create_association_rules(list())
        rules = associationRule(assoc_rules, headerTable, minConf, minSup, minTransactionLength, maxTransactionLength, numTransaction, dict_profit_per_item, profitInDataframe,diluted_total_profit,minProfit)
        if profitInDataframe:
            rules_pd = pd.DataFrame(rules,columns=["antecedent","sup_antecedent","percSupAntecedent","consequent","sup_consequent","percSupConsequent","antecedent&consequent","sup_ant&cons","sup_perc_ant&cons","confidence","lift","improvement","profit_associated","perc_of_total_profit","profit_associated_prev","net_change","profit_last_item","loss_by_change"]).sort_values("profit_associated",ascending=False).reset_index(drop=True)
        else:
            rules_pd = pd.DataFrame(rules,columns=["antecedent","sup_antecedent","percSupAntecedent","consequent","sup_consequent","percSupConsequent","antecedent&consequent","sup_ant&cons","sup_perc_ant&cons","confidence","lift","improvement"]).sort_values("sup_perc_ant&cons",ascending=False).reset_index(drop=True)
        return rules_pd




"""
data = pd.read_csv("Analysis/datasets/ecommerce_purchase_history_from_electronic_store/kz_part_1 copy 2.csv")
data["date"] = pd.to_datetime(data['event_time']).dt.date
max_date = data["date"].max()
data["margin"] = 0.1
data["profit"] = data["price"] * data["margin"]
max_profit = data["profit"].max()

data = data.groupby("order_id",dropna=True)["product_id","date","price","margin"].agg(lambda x: list(x))

rules = fpgrowthFromDataFrame(\
    data,
    minSupRatio=0.001,
    maxSupRatio=1,
    minConf=0,
    item_col=1,
    profit_col=3,
    max_profit = 100,
    profit_sensitivity = lambda x : 1 * x
    ) #Only Date

print(rules)
rules.to_excel("fp_groth_out.xlsx",index=False) 
"""

"""
T = pd.read_csv("Analysis/datasets/proof_of_concept/transactions.csv")
T = T.groupby("transaction",dropna=True)["item"].agg([lambda x: list(x),"count"])
rules = fpgrowthFromDataFrame(T, minSupRatio=0.5, maxSupRatio=1, minConf=0, item_col=1) #Traditional Association Rules

print(rules)
"""

"""
T = pd.read_csv("Analysis/datasets/proof_of_concept/transactions.csv")
T["date"] = pd.to_datetime(T["date"],format='%Y-%m-%d')
T = T.groupby("transaction",dropna=True)["item","date"].agg([lambda x: list(x)])

rules = fpgrowthFromDataFrame(\
    T,
    minSupRatio=0.5,
    maxSupRatio=1,
    minConf=0,
    item_col=1,
    date_col=2,
    max_date=datetime.datetime(2022, 11, 10),
    date_range=10,
    date_sensitivity = lambda x: 1 / (1 + math.exp(-10*x+5))
    ) #Only Date
"""

"""
T = pd.read_csv("Analysis/datasets/proof_of_concept/transactions.csv")
T = T.groupby("transaction",dropna=True)["item","profit"].agg([lambda x: list(x)])

rules = fpgrowthFromDataFrame(\
    T,
    minSupRatio=0.1,
    maxSupRatio=1,
    minConf=0,
    item_col=1,
    profit_col=2,
    max_profit = 100,
    profit_sensitivity = lambda x : 1 * x
    ) #Only Profit
rules

print(rules)
"""


T = pd.read_csv("Datasets/proof_of_concept/transactions.csv")
T["date"] = pd.to_datetime(T["date"],format='%Y-%m-%d')
T = T.groupby("transaction",dropna=True)["item","date","profit"].agg([lambda x: list(x)])

import math
import datetime

rules = fpgrowthFromDataFrame(\
    T,
    # General parameters
    minSupRatio=0.01,
    maxSupRatio=1,
    minTransactionLength = 2,
    maxTransactionLength = 2,
    minConf=0,
    item_col=1,
    # Date parameters
    date_col=2,
    max_date=datetime.datetime(2022, 11, 10),
    date_range=10,
    date_sensitivity = lambda x: 1 / (1 + math.exp(-10*x+5)),
    # Profit parameters
    profit_col=3,
    max_profit = 100,
    profit_sensitivity = lambda x : 1 * x
    )

rules.to_excel("fp_groth_out.xlsx",index=False)