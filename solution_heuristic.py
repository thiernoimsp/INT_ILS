import time
import sys
import os
import numpy as np
import copy
import random
import csv


class Int_Solution:

	def __init__(self, inst):
		self.inst = inst

	def write_solution(self, sol_info, path):
		with open(path+".txt", "a") as f:
			writer = csv.writer(f, lineterminator='\n')
			writer.writerow(sol_info)
