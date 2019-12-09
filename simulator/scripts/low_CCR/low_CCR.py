#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 09:49:29 2019

Heuristics targeting low CCR/high-data DAGs for which HEFT (and HOFT) are likely to fail. 
Referred to in the conclusion of paper but this was not promising so we didn't pursue it any further.  

@author: Tom
"""

import os
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt 
import dill
from collections import defaultdict 
from timeit import default_timer as timer
import sys
sys.path.append('../../') # Quick fix to let us import modules from main directory. 
import Environment    # Node classes and functions.
from Static_heuristics import HEFT, HEFT_L

# Set some parameters for plots.
# See here: http://www.futurile.net/2016/02/27/matplotlib-beautiful-plots-with-style/
plt.style.use('ggplot')
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = 'Ubuntu'
plt.rcParams['font.monospace'] = 'Ubuntu Mono'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['axes.titlesize'] = 10
plt.rcParams['axes.titlepad'] = 0
plt.rcParams['xtick.labelsize'] = 8
plt.rcParams['ytick.labelsize'] = 8
plt.rcParams['legend.fontsize'] = 6
plt.rcParams['figure.titlesize'] = 12

####################################################################################################

# Define environments.

single = Environment.Node(7, 1, name="Single_GPU")
multiple = Environment.Node(28, 4, name="Multiple_GPU")

####################################################################################################

#######################################################################

"""Summarize failure information."""

#######################################################################

heuristics = ["HEFT-WM", "HOFT", "HOFT-WM"]

with open('../HOFT/data/rand_mkspans.dill', 'rb') as file:
    rand_mkspans = dill.load(file)
    
#for env in [single, multiple]:
#    env.print_info()
#    for acc in ["low_acc", "high_acc"]:
#        print("Acceleration: {}\n".format(acc))
#        
#        heft_failures = set()
#        for i, hft in enumerate(rand_mkspans[env.name][acc]["0_10"]["HEFT"]):
#            if rand_mkspans[env.name][acc]["0_10"]["MST"][i] < rand_mkspans[env.name][acc]["0_10"]["HEFT"][i]:
#                heft_failures.add(i)        
#        print("Number of HEFT failures: {}".format(len(heft_failures)))
#        
#        failures = defaultdict(int)
#        heft_corrections, new_failures = defaultdict(int), defaultdict(int)        
#        
#        for i, mst in enumerate(rand_mkspans[env.name][acc]["0_10"]["MST"]):
#            for h in heuristics:
#                if mst < rand_mkspans[env.name][acc]["0_10"][h][i]:
#                    failures[h] += 1
#                    if i not in heft_failures:
#                        new_failures[h] += 1
#                else:
#                    if i in heft_failures:
#                        heft_corrections[h] += 1
#        for h in heuristics:
#            print("Heuristic: {}".format(h))
#            print("Number of failures: {}".format(failures[h]))
#            print("Number of HEFT corrections: {}".format(heft_corrections[h]))
#            print("Number of new failures: {}\n".format(new_failures[h]))
            

#######################################################################

"""Sampling based lookahead."""

#######################################################################
            
start = timer()
samplings = ["1P"]
n_dags = 180
rand_speedups = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for env in [single, multiple]:
    env.print_info()
    for acc in ["low_acc", "high_acc"]:
        heft_failures = 0
        successes, ties, failures = defaultdict(int), defaultdict(int), defaultdict(int)
        with open("results/{}_{}.txt".format(env.name, acc), "w") as dest:            
            env.print_info(filepath=dest)
            count = 0
            for app in os.listdir('../../graphs/random/{}/{}/CCR_0_10'.format(env.name, acc)):
                count += 1
#                if count > 1: # REMEMBER TO REMOVE THIS BEFORE LEAVING TO RUN!
#                    break
                print("Starting DAG number {}...".format(count))
                dag = nx.read_gpickle('../../graphs/random/{}/{}/CCR_0_10/{}'.format(env.name, acc, app))
                dag.print_info(platform=env, filepath=dest)  
                mst = dag.minimal_serial_time(env) 
                
                heft_mkspan = HEFT(dag, platform=env)
                print("HEFT makespan: {}".format(heft_mkspan), file=dest)                  
                    
                for h in samplings:
                    mkspan = HEFT_L(dag, platform=env, weighted_average=True, child_sampling_policy=h)
                    print("HEFT-L with {} child sampling policy makespan: {}".format(h, mkspan), file=dest) 
                    rand_mkspans[env.name][acc]["0_10"][h].append(mkspan)     
                    
                    rand_speedups[env.name][acc][h].append(100 - (mkspan / heft_mkspan) * 100) 
                    
                    if mkspan > mst:
                        failures[h] += 1
                    elif mkspan == mst:
                        ties[h] += 1
                    elif mkspan < mst:
                        successes[h] += 1         
                                     
                print("--------------------------------------------------------\n", file=dest)                
               
                        
            print("--------------------------------------------------------", file=dest)
            print("SUMMARY", file=dest)
            print("--------------------------------------------------------", file=dest) 
            print("HEFT failures: {}\n".format(heft_failures), file=dest)
            for h in samplings:
                print("Sampling policy: {}.".format(h), file=dest)
                print("Average improvement compared to HEFT: {}%".format(np.mean(rand_speedups[env.name][acc][h])), file=dest)
                print("Number of times better than HEFT: {}/{}".format(sum(1 for s in rand_speedups[env.name][acc][h] if s >= 1.0), n_dags), file=dest) 
                print("Number of successes: {}/{}".format(successes[h], n_dags), file=dest) 
                print("Number of ties: {}/{}".format(ties[h], n_dags), file=dest) 
                print("Number of failures: {}/{}\n".format(failures[h], n_dags), file=dest)  
                    
## Save the speedups so can plot later...
with open('data/rand_speedups.dill', 'wb') as handle:
    dill.dump(rand_speedups, handle)
    
with open('data/rand_mkspans.dill', 'wb') as handle:
    dill.dump(rand_mkspans, handle)
    
elapsed = timer() - start
print("This took {} minutes.".format(elapsed / 60))

