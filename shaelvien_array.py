"""
ShaelvienOS • Phase 23.8 • shaelvien_array
-------------------------------------------
Lightweight numeric array engine (pure Python) replacing NumPy.
Handles resonance, signal energy, and normalization.
"""

import math
import random
from typing import List

class Array(list):
    """Minimal 1-D numeric array wrapper."""

    # ---- creation ----
    @staticmethod
    def zeros(n: int):  return Array([0.0]*n)
    @staticmethod
    def ones(n: int):   return Array([1.0]*n)
    @staticmethod
    def random(n: int): return Array([random.random() for _ in range(n)])

    # ---- arithmetic ----
    def _binary_op(self, other, op):
        if isinstance(other, (int,float)):
            return Array([op(x,other) for x in self])
        return Array([op(x,y) for x,y in zip(self,other)])

    def __add__(self, other): return self._binary_op(other, lambda a,b:a+b)
    def __sub__(self, other): return self._binary_op(other, lambda a,b:a-b)
    def __mul__(self, other): return self._binary_op(other, lambda a,b:a*b)
    def __truediv__(self, other): return self._binary_op(other, lambda a,b:a/b)

    # ---- aggregates ----
    def sum(self): return float(sum(self))
    def mean(self): return self.sum()/len(self) if self else 0.0
    def max(self): return float(max(self)) if self else 0.0
    def min(self): return float(min(self)) if self else 0.0
    def dot(self, other): return float(sum(a*b for a,b in zip(self,other)))
    def magnitude(self): return math.sqrt(self.dot(self))

# ---- matrix helpers ----
def matrix_multiply(A:List[List[float]],B:List[List[float]]):
    rows_A,cols_A=len(A),len(A[0])
    rows_B,cols_B=len(B),len(B[0])
    if cols_A!=rows_B: raise ValueError("matrix dimension mismatch")
    result=[[0.0]*cols_B for _ in range(rows_A)]
    for i in range(rows_A):
        for j in range(cols_B):
            result[i][j]=sum(A[i][k]*B[k][j] for k in range(cols_A))
    return result

# ---- signal helpers ----
def fourier_amplitude(samples:List[float])->float:
    n=len(samples)
    if n==0: return 0.0
    energy=sum(x*x for x in samples)/n
    return math.sqrt(energy)

def normalize(values:List[float])->List[float]:
    if not values: return []
    vmin,vmax=min(values),max(values)
    if vmax==vmin: return [0.5]*len(values)
    return [(v-vmin)/(vmax-vmin) for v in values]

if __name__=="__main__":
    a=Array.random(5)
    b=Array.ones(5)
    print("[shaelvien_array] a=",a)
    print("[shaelvien_array] dot=",a.dot(b),"mean=",a.mean())
    print("normalized:",normalize(a))
