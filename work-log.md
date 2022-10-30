## Work Log David Schmid
### 1. 22.09.2022 - 02.10.2022:
#### 1.1 Work done:
- I scanned through a number of papers with the topic "Association rules", but less than  30 papers for the moment. I will continue to find more later.
- My focus was to understand the new developments and possible shortcomings of the current implementations. Moreover I tried to fgind out, how deep learning can be implemented with association rules. I haven't found a satisfying answer yet. 
- I disvocered a paper "An-Improved-Evaluation-Methodology-for-Mining" (Published: 31 December 2021), which describes the improvement of the traditional association rule measures with "Bi-support, Bi-lift, Bi-improvement Bi-confidence".
#### 1.2 Papers scanned (30 papers) - Most important summarized:
#### 1.2.1 Mining-Association-Rules-between-Sets-of-Items-in-Large-Databases (1993, Rakesh Agrawal, Tomasz Imielinski, Arun Swami)<br>
It can be seen as the founding paper of the traditional association rule model. All further association rule reasearch is based on this paper as a fundament. It presents the formal model and a case study. <br>
"""Quote from paper"""<br>
The work reported in this paper could be viewed as a step towards enhancing databases with functionalities to process queries such as (we have omitted the confidence factor specification):
- Find all rules that have "Diet Coke" as consequent. These rules may help plan what the store should do to boost the sale of "Diet Coke".
- Find all rules that have "bagels" in the antecedent. These rules may help determine what products may be impacted if the store discontinues selling bagels.
- Find all rules that have "sausage" in the antecedent and "mustard" in the consequent. This query can be phrased alternatively as a request for the additional items that have to be sold together with sausage in order to make it highly likely that mustard will also be sold.
- Find all the rules relating items located on shelves A and B in the store. These rules may help shelf planning by determining if the sale of items on shelf. A is related to the sale of items on shelf B.
- Find the "best" k rules that have "bagels" in the consequent. Here, "best" can be formulated in terms of the confidence factors of the rules, or in terms of their support, i.e., the fraction of transactions satisfying the rule.

#### 1.2.2 Association-Rules-Mining-A-Recent-Overview (2006)<br/>
In year 2022, the "recent-overview" it is not that recent anymore. However considering the founding paper of 1993, at thatz time, some time passed and association rules matured.
Problems/Proposed Solutions discovered in time:
1. Problem: Redundant Association Rules<br>
-> Possible solution: Rules have been extracted based on user-defined templates or item constraints<br>
-> Possible solution: Researchers have developed interestingness measures to select only interesting rules<br>
-> Possible solution: Researchers have proposed inference rules or inference systems to prune redundant rules and thus present smaller,
and usually more understandable sets of association rules to the user<br>
-> Possible solution: New frameworks for mining association rule have been proposed that find association rules with different formats or properties<br>
2. Other measures as interestingness of an association<br>
-> Instead of getting the the association rules based on a user, it could be grouped by frequent items within a time intervall.<br>
-> The measure of significance of associations that is used could be the chi-squared test for correlation from classical statistics. 
-> Problem: Using a high support typically reduces the numberof rules mined but will eliminate the rules with rare items. -> Possible solution: This problem can be adressed by allowing users to specify different minimum supports for the various items in their mining algorithm. 
3. Negative association rules<br>
Instead of mining positiive association rules, it is possible to mine negative rules. However a general algorithm is hard to develop and it is based on domain knowledge.

#### 1.2.3 A brief overview of swarm intelligence-based algorithms for numerical association rule mining (2020)
In this paper there are some methods described how to not only consider associations between transactions, but how to
have numerical association rule mining. However, no implementation details are described. This paper is more of an overview.

#### 1.2.4 Efficient Analysis of Pattern and Association Rule Mining Approaches (2013)
In this paper, different association rule mining approaches and varaints are discussed. It's an older paper. However, it shows that research in the field of association rules is quite active.<br>
Methods listed are:<br>
- Apriori (1994)
- AprioriTID (1994)
- DHP (1995)
- FDM (1996)
- GSP (1996)
- DIC (1997)
- PincerSearch (1998)
- CARMA (1999)
- CHARM (1999)
- Depth-project (2000)
- Eclat (2000)
- SPAD (2001)
- SPAM (2002)
- Diffset (2003)
- FP-growth (2004)
- DSM-FI (2004)
- PRICES (2004)
- PrefixSpan (2004)
- Sporadic Rules (2005)
- IGB (2005)
- GenMax (2005)
- FPMax (2005)
- FHARM (2006)
- H-mine (2007)
- FHSAR (2008)
- Reverse Apriori (2008)
- DTFIM (2008)
- GIT-tree (2009)
- Scaling Apriori (2010)
- CMRules (2010)
- Minimum effort (2011)
- TopSeqRules (2011)
- FPG ARM (2012)
- TNR (2012)
- ClaSP (2013)

#### 1.2.5 An Innovative Approach for Association Rule Mining in Grocery Dataset Based On Non-Negative Matrix Factorization And Autoencoder (2022)
Interesting paper. Discusses the implementation of deep learning to get association rules. However the paper leaves many questions open. I would like to see the "code implementation" of the discussed method.

#### 1.2.6 An Improved Evaluation Methodology for Mining Association Rules (2022)
Quote<br>
Here, this paper first analyzes the advantages and disadvantages of common measurement indicators of association rules and then puts forward four new measure indicators (i.e., Bi-support, Bi-lift, Bi-improvement, and Bi-confidence) based on the analysis. At last, this paper proposes a novel Bi-directional interestingness measure framework to improve the traditional one. In conclusion, the bi-directional interestingness measure framework (Bi-support and Bi-confidence framework) is superior to the traditional ones in the aspects of the objective criterion, comprehensive definition, and practical application.<br>
For me this is a very practical/relevant paper. I would like to implement these new BI-measures and understand the advantages over the traditional evaluation measures.


#### 1.3. Next steps (proposed):
- I would to further optimize/clean the own implementation of the apiori-algorithm. It is really raw, but increases my understanding and let me experiment with variants.
- I would like to implement "Bi-support, Bi-lift, Bi-improvement Bi-confidence" and compare it to the traditional measure
- Experiment with the big dataset kz.csv for different methods (classical vs. Bi-measures)
- I would like to understand, how Assocation Rule Mining is possible with Deep Learning methods, as described in 1.2.5. For that reason I have tin explore some exemplatory code of a working implementation based on Tensorflow or Pytorch

#### 1.4. Questions:
- What do you think generally about my next steps? Do you have a specific guidance, where to move/ what to explore?
- In our first call, you mentioned that nowadays Association rules are developed by Deep Learning. I couldn't find a good example of such an approach, with working code. Maybe I was focused to much on the term "Association rules" and missed the term for the other modern approach.
- Personally I really like the simplicity and power of association rules. It is really a very practical, business-related method to find associations. I explored, that there are many variants and optimizations, however in PIP, only the most promiment classical algorithms like apriori, exclat, fp-growth can be found and there is generally a lack of working code examples in the papers. Can I get the underlying code of the experimental approaches of the papers somewhere or is it generally hidden in research papers?
- Are there any "must-read" papers for association rule topic, which you can recommend me?
- What is your recommendation to continue?

#### 1.5 Experiment with own implementation
![Alt text](Screenshot_2022-10-02.png?raw=true "apriori")

### 2. 03.10.2022 - 12.10.2022:
#### 2.1 Work done:
- Improved & corrected errors in algorithm, see in apriori_0_3.py with more optional parameters to get only wished associations from ... to ... length of associations back
- Implemented reverse support, bi-lift, bi-confidence as described in Paper "2022_An Improved Evaluation Methodology for Mining"
#### 2.2. Next steps (proposed):
- Implement rest of measures as desctribed in paper "2022_An Improved Evaluation Methodology for Mining"
- Upscale to kz_dataset and experiment / interprete results
- Study further papers and come up with own improvement or suggestion how to improve association mining rules

### 3 13.10.2022 - 30.10.2022
#### 3.1 Work done (Latest version of algorithm: fp_growth_run_V06)
- Based on apriori, experimented with  algorithm and implemented all metrics from paper "2022_An Improved Evaluation Methodology for Mining"
- However, I got into a crisis, as I realized how slow and inefficient the algorithm was
- I looked for the fastest popular association rule method, which is FP-Grwoth
- I took the basis of aa working implementation and modified it according to my needs
- On basis of the fp-growth algorithm, I develoiped a completely new concept, to adress the weaknesses I realized and found in paper
- 1. Problem: There was a question: Why is association rule methods rarely used in practice? - Main anwser: We don't consider mutiple items in one transaction
- 2. Problem: Counting the support tells something about the relations. But is that the major interest of Business? It is only a half-solution and the mined association rules need to be conencted to economic date, speak of price andf profit, that way is very cumbersome
- 3. Problem: Are transactions happened 1 year ago the same important as current transaction? A possible solution is to pre-clean only the rishful dates. But is there not a better smoother way?
- My newly developed considers all 3 problems and is very efficient. The main driver is profit. Because I didn't have profit per product or product category, for simplification I considered 0.1 * Price, which is not true in reality. Mostly more expensive products have less margin than cheaper products and depending on product category. I don't consider support anymore as simple count, but I weight the so called support according to chosen input factors.
For example max_profit has weight 3, 0 profit has weight 0. Then I make a linear distribution of each article in a transaction. If there are the same 5 articles
in a transaction I mutiply their weigth * 5, to represent the reality. Normally the cheaper products should havbe a higher revenue and thereforre make up the profit of
more rare expensive items. At the end it is a pure "profitability support" view. Moreover I can repesent the diferent dates with a date function. For example I weight
transactions which are 90 days old near zero and current transactions near 1.
at the end I multiple the time functiuon with the profit function to get the date based weighted profit support.
The results are interesting and give completely new insights in the key driver "proditability".
However, there have to be other metrics developed to really measure the success.
Moreover the date function, fopr which I currently take a modified sigmoid function need to be ajdusted to better represent reality.
#### 2.2. Next steps (proposed):
- Verify/Review correctness, therefore Simulation of simple example, which can be recalculated manually
- Analyse Rules tradtionally with big data set and the newly developed association rule algorithm
- Make a beautiful Juypter Notebook for analysis the different algorithms
- Check differences / Interprete Differences
- Explore the new algorithm
- Develop new metrics; Old metrics are too strict for interpretation, because Support can grow, because of "support as profit", has to be interpreted as "gained profit" through an association
- Describe advantages/ disadvantages of new algorithm