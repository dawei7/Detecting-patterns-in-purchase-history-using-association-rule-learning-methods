# An Improved Evaluation Methodology for Mining Association Rules (Fuguang Bao, Linghao Mao, Yiling Zhu, Cancan Xiao and Chonghuan Xu)
# Implemented Algorithm by David Schmid (Not efficient and raw at current stage)

# Libraries
import pandas as pd
import itertools
from collections import defaultdict
import math
from functools import reduce


def apriori(transactions_ungrouped, min_support_perc=0.5, min_confidence=0.5,min_lift=1,min_associations=2,max_associations=5):

    # Initialize
    combinations = defaultdict(list)
    transactions_ungrouped.columns = ["transaction","item"]
    transactions = transactions_ungrouped.groupby('transaction').agg({'item': list})
    num_transactions = len(transactions.index)
    min_support = min_support_perc * num_transactions
    init_support = dict(transactions_ungrouped["item"].value_counts()[(transactions_ungrouped["item"].value_counts()>=min_support)])
    support_total = {}
    anti_support = {}
    anti_support_total = {}
    counter = 1

    # Functions
    def get_combinations(old_combinations):
        new_combinations = defaultdict(list)
        elements = list(set().union(*old_combinations.keys()))
        for left in old_combinations.keys():
            for right in elements:
                if len(frozenset(list(left)+[right])) >= len(left)+1: #and frozenset(list(left)+list(right)) not in combinations:
                    combinations[frozenset(list(left)+[right])].append(left)
                    new_combinations[frozenset(list(left)+[right])].append(left)
        return new_combinations

    def get_support(combinations,min_support):
        count = dict()
        for combination in combinations.keys():
            for transaction in transactions.values:
                if combination.issubset(frozenset(transaction[0])):
                    count.setdefault(combination, 0)
                    count[combination] += 1

        return {k:v for k, v in count.items()}

    def get_anti_support(combinations,min_support):
        count = dict()
        for combination in combinations.keys():
            for transaction in transactions.values:
                count.setdefault(combination, 0)
                if combination.isdisjoint(frozenset(transaction[0])): # No common items, if 1 item is present, it is not disjoint
                    count[combination] += 1
        return {k:v for k, v in count.items()}

    def get_bi_lift(antecedent_consequent,antecedent,consequent):
        count_consequent = 0
        count_rev_antecedent = 0
        count_rev_antecedent_consequent = 0
        for transaction in transactions.values:
            if consequent.issubset(frozenset(transaction[0])):
                count_consequent += 1
            if antecedent.isdisjoint(frozenset(transaction[0])):
                count_rev_antecedent +=1
            if consequent.issubset(frozenset(transaction[0])) and antecedent.isdisjoint(frozenset(transaction[0])):
                count_rev_antecedent_consequent += 1

        if count_consequent *count_rev_antecedent == 0 or count_rev_antecedent_consequent == 0:
            return "NA"
        else:
            return \
            ((support_total[antecedent_consequent]/num_transactions)/((init_support[list(antecedent_consequent-antecedent)[0]]/num_transactions)*(support_total[antecedent]/num_transactions)))/\
            ((count_rev_antecedent_consequent/num_transactions)/((count_rev_antecedent/num_transactions)*(count_consequent/num_transactions)))

    
    def get_bi_confidence(antecedent_consequent,antecedent,consequent):
        count_rev_antecedent = 0
        count_rev_antecedent_consequent = 0
        for transaction in transactions.values:
            if antecedent.isdisjoint(frozenset(transaction[0])):
                count_rev_antecedent +=1
            if consequent.issubset(frozenset(transaction[0])) and antecedent.isdisjoint(frozenset(transaction[0])):
                count_rev_antecedent_consequent += 1

        if count_rev_antecedent == 0:
            return "NA"

        return \
            support_total[antecedent_consequent]/support_total[antecedent]-\
            (count_rev_antecedent_consequent/ count_rev_antecedent)

            
    
    def get_association_rules(combinations,min_confidence):
        rules = defaultdict(list)
        for parent, children in combinations.items():
            if support_total.get(parent):
                for child in children:
                    if support_total.get(child) and support_total[parent]/support_total[child]>=min_confidence and (support_total[parent]/num_transactions)/((init_support[list(parent-child)[0]]/num_transactions)*(support_total[child]/num_transactions))>=min_lift:
                        rules[parent].append([\
                            child, # "set antecedent"
                            parent-child, # set "antecedent_consequent"
                            support_total[child]/num_transactions, # set "value support_antecedent"
                            init_support[list(parent-child)[0]]/num_transactions, # set "value support_consequent"
                            support_total[parent]/num_transactions, # set "value support_antecedent_consequent"
                            anti_support_total[parent]/num_transactions, # set "value anti support_antecedent_consequent"
                            support_total[parent]/support_total[child], # set "rule confidence"
                            (support_total[parent]/num_transactions)/((init_support[list(parent-child)[0]]/num_transactions)*(support_total[child]/num_transactions)), #set "lift"
                            get_bi_lift(parent,child,parent-child), #set "bi-lift"
                            get_bi_confidence(parent,child,parent-child), #set "bi-confidence"
                            (support_total[parent]/support_total[child])-(init_support[list(parent-child)[0]]/num_transactions), #set improvement
                            ((support_total[parent]/num_transactions)-((init_support[list(parent-child)[0]]/num_transactions)*(support_total[child]/num_transactions)))/(1-support_total[child]/num_transactions), #set bi-improvement
                            ((support_total[parent]/support_total[child])-(init_support[list(parent-child)[0]]/num_transactions))/math.sqrt(((init_support[list(parent-child)[0]]/num_transactions)*(1-(init_support[list(parent-child)[0]])/num_transactions))/num_transactions) #set chi-square-analysis (csa)
                            ])
        return rules
    
    def pandas_df_ruleset(rules):
        result = [["antecedent","consequent","antecedent_consequent","support_antecedent","support_consequent","support_antecedent&consequent","anti-support_antecedent&consequent","confidence","lift","bi-lift","bi-confidence","improvement","bi-improvement","csa"]]
        for k,vs in rules.items():
            for v in vs:
                result.append([v[0],v[1],k,v[2],v[3],v[4],v[5],v[6],v[7],v[8],v[9],v[10],v[11],v[12]])
        df = pd.DataFrame(result)
        df.columns = df.iloc[0] 
        df = df[1:]
        return df

    # Loop
    while True and counter<=max_associations : # Infinite Loop until break
        if counter == 1:
            support = {frozenset([k]):v for k, v in init_support.items()}
        else:    
            support = get_support(new_combinations,min_support)
            anti_support = get_anti_support(new_combinations,min_support)

        if not support:
            break

        if counter<min_associations:
            support_total = support
            anti_support_total = anti_support
        else:
            support_total = {**support_total, **support}
            anti_support_total = {**anti_support_total, **anti_support}
        
        new_combinations = get_combinations(support)

        counter+=1


    rules = get_association_rules(combinations,min_confidence)


    return pandas_df_ruleset(rules)


#transactions= pd.read_csv("transactions_V2.csv")
transactions= pd.read_csv("kz_part_1 copy.csv",dtype={
    "order_id":"string",
    "product_id":"string"
    })
transactions = transactions[["order_id","product_id"]].rename(columns={
    "order_id":"transaction",
    "product_id":"item"
})

df_apriori = apriori(transactions, min_support_perc=0.008, min_confidence=0.2, min_lift=2,min_associations=2,max_associations=2)

print(df_apriori.to_string())
