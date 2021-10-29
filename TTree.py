#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 17:43:29 2021

@author: linkv
"""
import numpy as np

class TTrees:
    def __init__(self, ts_object):
        self.trees = ts_object.trees()
        self.number = ts_object.num_trees
        
#     # def make(X):
#     #     X_ = (X+X.T)/2
#     #     np.fill_diagonal(X_, 0)
#     #     return X_

#     # def diff(y, N):
#     #     cols = np.tile(y, (N, 1))
#     #     rows = cols.T
#     #     buffer = cols - rows
#     #     return np.abs(buffer)
        


#     # def solving_function(array, tree):
#     #     covariance = trees_obj.TMRCA(0, N)
#     #     inv = np.linalg.inv(covariance)
#     #     np.dot(inv, array)

    
    

class TTree:
    def __init__(self, tree_iterator, N):
        self.tree = tree_iterator
        self.N = N
        self.tree_starts = -1
        self.index = tree_iterator.index
        self.height = -1
        
    def testPSD(self, A, tol=1e-8):
        E = np.linalg.eigvalsh(A)
        if np.all(E > -tol) == False:
            raise ValueError("Covariance matrix has negative eigenvalues")
        return np.all(E > -tol)
        
        
    def TMRCA(self, N):
        """
        see tskit to understand these classes: https://tskit.dev/tskit/docs/stable/python-api.html#the-tree-class
        
        - the goal of this function is to get pairwise branch lengths between all nodes of the tree
        - we go through all internal nodes and update the cells of all their descendants at once
        - the tree.time of a node gets larger backwards in time
        - the idea is to fill the TMRCA matrix with the total height of the tree and then to 
        deduct for all descendants of one node the branches from farther back in time
        for example, the terminal nodes will have all branch lengths that connect their ancestors deducted 
        -> they are only separated by the terminal branches
        Since the height of the tree can only be known by finding the oldest node, which we don't know a priori 
        we deduct the branch lengths from zero first, using the loop over nodes to find the height, and then add the height
    
        Parameters
        ----------
        tree : <class 'tskit.trees.Tree'>
            The tree for which distance between samples should be calculated.
        N : int
            number of samples.
    
        Returns
        -------
        tmrca : matrix of dim ? and type ?
            Time separating two samples.
    
        """
        tmrca = np.zeros([N, N])
        self.height = 0
        for c in self.tree.nodes():
            descendants = list(self.tree.samples(c))
            n = len(descendants)
            if(n == 0 or n == N or self.tree.time(c) == 0): #The branch length for a node that has no parent (e.g., a root) is defined as zero.
                continue
            t = self.tree.time(self.tree.parent(c)) - self.tree.time(c)
            tmrca[np.ix_(descendants, descendants)] -= t
            self.height = max(self.height, self.tree.time(self.tree.parent(c))) #time returns the time of a node
        tmrca += self.height
        np.fill_diagonal(tmrca, 0)
        tmrca = (tmrca + tmrca.T) / 2
        return tmrca
    
    def covariance(self, N):
        covariance = self.TMRCA(self.N)
        covariance = -covariance + self.height
        return(covariance)
    
    def print_something(self, something):
        raise ValueError("printing", something)

        
    def solving_function(self, array):   
        covariance = self.covariance(self.N)
        # covariance = (X+X.T)/2
        # np.fill_diagonal(covariance, 0)
        # print(np.diagonal(covariance))
        # print(np.shape(covariance))
        # print(covariance)
        self.testPSD(covariance)
        inv = np.linalg.inv(covariance)
        tmp = np.dot(inv, array)
        # print("shape of my dot product",np.shape(tmp))
        return(tmp)
        
        
        
        
        
        
        
        
        