# https://www.youtube.com/watch?v=ePxZDuQdnW4
# Implemented Algorithm by David Schmid (Not efficient and raw at current stage)

# Libraries
import pandas as pd
import itertools
from collections import defaultdict


def apriori(transactions_ungrouped, min_support_perc, min_confidence,min_lift):


    combinations = defaultdict(list)

    def get_combinations(old_combinations):
        new_combinations = defaultdict(list)
        elements = list(set().union(*old_combinations.keys()))
        for left in old_combinations.keys():
            for right in elements:
                if len(frozenset(list(left)+list(right))) == len(left)+1 and frozenset(list(left)+list(right)) not in combinations:
                    combinations[(frozenset(list(left)+list(right)))].append(left)
                    new_combinations[(frozenset(list(left)+list(right)))].append(left)
        return new_combinations



    # Initialize/ First run
    transactions_ungrouped.columns = ["transaction","item"]
    transactions = transactions_ungrouped.groupby('transaction')['item'].apply(frozenset)
    num_transactions = len(transactions.index)
    min_support = min_support_perc * num_transactions
    init_support = dict(transactions_ungrouped["item"].value_counts()[(transactions_ungrouped["item"].value_counts()>=min_support)])
    new_combinations = get_combinations(init_support)
    support_total = {}

    # Functions

    def get_support(combinations,min_support):
        count = dict()
        for combination in combinations.keys():
            for transaction in transactions:
                if combination.issubset(transaction):
                    count.setdefault(combination, 0)
                    count[combination] += 1
        return {k:v for k, v in count.items() if v >= min_support}
    
    def get_association_rules(combinations,min_confidence):
        rules = defaultdict(list)
        for parent, children in combinations.items():
            if support_total.get(parent):
                for child in children:
                    if support_total.get(child) and support_total[parent]/support_total[child]>min_confidence and (support_total[parent]/num_transactions)/((init_support[list(parent-child)[0]]/num_transactions)*(support_total[child]/num_transactions))>min_lift:
                        rules[parent].append([child,parent-child,support_total[child]/num_transactions,init_support[list(parent-child)[0]]/num_transactions,support_total[parent]/num_transactions,support_total[parent]/support_total[child],(support_total[parent]/num_transactions)/((init_support[list(parent-child)[0]]/num_transactions)*(support_total[child]/num_transactions))]) # "set antecedent","set antecedent_consequent","value support_antecedent","value support_consequent","value support_antecedent_consequent","rule confidence","lift"
        return rules
    
    def pandas_df_ruleset(rules):
        result = [["antecedent","consequent","antecedent_consequent","support_antecedent","support_consequent","support_antecedent&consequent","confidence","lift"]]
        for k,vs in rules.items():
            for v in vs:
                result.append([v[0],v[1],k,v[2],v[3],v[4],v[5],v[6]])
        df = pd.DataFrame(result)
        df.columns = df.iloc[0] 
        df = df[1:]
        return df


    while True: # Infinite Loop until break

        support = get_support(new_combinations,min_support)
        if not support:
            break
        support_total = {**support_total, **support}
        new_combinations = get_combinations(support)


    rules = get_association_rules(combinations,min_confidence)


    return pandas_df_ruleset(rules)


transactions= pd.read_csv("transactions.csv")

df_apriori = apriori(transactions,0.4,0.2,0.5)

print(df_apriori)