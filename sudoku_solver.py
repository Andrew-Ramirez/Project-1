#!/usr/bin/env python
# coding: utf-8

# In[11]:


import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import scipy.sparse as scs # sparse matrix construction 
import scipy.linalg as scl # linear algebra algorithms
import scipy.optimize as sco # for minimization use
import matplotlib.pylab as plt # for visualization
import os
from cvxopt import solvers, matrix
import time
solvers.options['show_progress'] = False


# In[12]:


def solver(data):
    #seed and choosing 1000 puzzles for the sake of this project
    np.random.seed(42)
    if len(data) > 1000:
        samples = np.random.choice(len(data), 1000)
    else:
        samples = range(len(data))
    #define the fixed constraints
    def fixed_constraints(N=9):
        rowC = np.zeros(N)
        rowC[0] =1
        rowR = np.zeros(N)
        rowR[0] =1
        row = scl.toeplitz(rowC, rowR)
        ROW = np.kron(row, np.kron(np.ones((1,N)), np.eye(N)))

        colR = np.kron(np.ones((1,N)), rowC)
        col  = scl.toeplitz(rowC, colR)
        COL  = np.kron(col, np.eye(N))

        M = int(np.sqrt(N))
        boxC = np.zeros(M)
        boxC[0]=1
        boxR = np.kron(np.ones((1, M)), boxC) 
        box = scl.toeplitz(boxC, boxR)
        box = np.kron(np.eye(M), box)
        BOX = np.kron(box, np.block([np.eye(N), np.eye(N) ,np.eye(N)]))

        cell = np.eye(N**2)
        CELL = np.kron(cell, np.ones((1,N)))

        return scs.csr_matrix(np.block([[ROW],[COL],[BOX],[CELL]]))
    
    #define given clue constraints for each matrix
    def clue_constraint(input_quiz, N=9):
        m = np.reshape([int(c) for c in input_quiz], (N,N))
        r, c = np.where(m.T)
        v = np.array([m[c[d],r[d]] for d in range(len(r))])

        table = N * c + r
        table = np.block([[table],[v-1]])

        CLUE = scs.lil_matrix((len(table.T), N**3))
        for i in range(len(table.T)):
            CLUE[i,table[0,i]*N + table[1,i]] = 1
        CLUE = CLUE.tocsr() 

        return CLUE
    
    corr_cnt = 0
    start = time.time()
    for i in range(len(samples)):
        #initial setup to get the quizzes and the solutions
        quiz = data["quizzes"][samples[i]]
        solu = data["solutions"][samples[i]]
        A0 = fixed_constraints()
        A1 = clue_constraint(quiz)

        # Formulate the matrix A and vector B (B is all ones).
        A = scs.vstack((A0,A1))
        A = A.toarray()
        B = np.ones(A.shape[0])

        #Necessary set up in order to use sco.linprog
        u, s, vh = np.linalg.svd(A, full_matrices=False)
        K = np.sum(s > 1e-12)
        S = np.block([np.diag(s[:K]), np.zeros((K, A.shape[0]-K))])
        A = S@vh
        B = u.T@B
        B = B[:K]

        c = np.block([ np.ones(A.shape[1]), np.ones(A.shape[1]) ])
        G = np.block([[-np.eye(A.shape[1]), np.zeros((A.shape[1], A.shape[1]))],                             [np.zeros((A.shape[1], A.shape[1])), -np.eye(A.shape[1])]])
        h = np.zeros(A.shape[1]*2)
        H = np.block([A, -A])
        b = B

        ret = sco.linprog(c, G, h, H, b, method='revised simplex', options={'tol':1e-6})
        x = ret.x[:A.shape[1]] - ret.x[A.shape[1]:]

        # map to board
        z = np.reshape(x, (81, 9))
        if np.linalg.norm(np.reshape(np.array([np.argmax(d)+1 for d in z]), (9,9) )                           - np.reshape([int(c) for c in solu], (9,9)), np.inf) >0:
            pass
        else:
            #print("CORRECT")
            corr_cnt += 1

        if (i+1) % 20 == 0:
            end = time.time()
            print("Aver Time: {t:6.2f} secs. Success rate: {corr} / {all} ".format(t=(end-start)/(i+1), corr=corr_cnt, all=i+1) )

    end = time.time()
    print("Aver Time: {t:6.2f} secs. Success rate: {corr} / {all} ".format(t=(end-start)/(i+1), corr=corr_cnt, all=i+1) )
    #return z ?

