import time
import sys
import os
import numpy as np
import copy
import random
import csv
from collections import defaultdict

class Int_Solution:

	def __init__(self, inst, cost=None):
		self.inst = inst
		self.cost = cost
		self.gap_time = list()
		self.spatial = list()
		self.temporal = list()
		self.telemetry = list()
		#self.flow_items = defaultdict(list)
		self.flow_items = defaultdict(list)


	def add_gap_time(self, data):
		"""
		add the tuple (m,p) to the set of satisfied temporal requirements
		"""
		#data = [m,p]
		self.gap_time.append(data)

	def add_spatial(self, data):
		"""
		add the tuple (m,d,p) to the set of satisfied spatial requirements
		"""
		#data = [m,d,p] 
		self.spatial.append(data)


	def add_temporal(self, data):
		"""
		add the tuple (m,p) to the set of satisfied temporal requirements
		"""
		#data = [m,p]
		self.temporal.append(data)


	def add_telemetry(self, data):
		"""
		add the tuple (d,v.f) to the set of satisfied temporal requirements
		"""
		#data = [m,p]
		self.telemetry.append(data)

	def add_flow_items(self, dictio):
		self.flow_items = dictio



	def print_solution(self):
		print("--------------------------------------")
		print("    Solution cost = %.6f" % self.cost)

		print("")
		print("    Satisfied Spatial = %.6f" % len(self.spatial))

		print("")
		print("    Satisfied Temporal = %.6f" % len(self.temporal))


		print("")
		print("    Collected Items = %.6f" % len(self.telemetry))

		print("")
		print("    Relative Gap = %.6f" % float(self.gap_time[0]))

		print("")
		print("    Solution Runtime = %.2f" % self.gap_time[1])

		#print("")
		#print("    Flow Items = %s" % self.flow_items)


	"""
	def write(self, path):
		#inst = self.inst
		with open(path+".txt", "a") as f:
			f.write("Instance: %s\n" % os.path.basename(self.inst.path_data))
			f.write("Cost: %.6f\n" % self.cost)
			f.write("\n")


			# writing instance data
			f.write("Instance data:\n")
			f.write("\n")
			f.write("    %-7s\t%10.4f\n" % ("D :", len(self.inst.D)))
			f.write("    %-7s\t%10.4f\n" % ("F :", len(self.inst.F)))
			f.write("    %-7s\t%10.4f\n" % ("V :", len(self.inst.V)))
			f.write("    %-7s\t%10.4f\n" % ("M :", int(self.inst.num_mon_app)))
			f.write("    %-7s\t%10.4f\n" % ("Gap :", self.gap_time[0]))
			f.write("    %-7s\t%10.2f\n" % ("Solution runtime :", self.gap_time[1]))
			f.write("\n")

			# writing Solution detail
			f.write("Solution Information detail:\n")
			f.write("\n")
			f.write("    %-7s\t%10.2f\n" % ("Objective function : ", self.cost))
			f.write("    %-7s\t%10.2f\n" % ("Satisfied Spatial : ", len(self.spatial)))
			f.write("    %-7s\t%10.2f\n" % ("Satisfied Temporal : ", len(self.temporal)))
			f.write("    %-7s\t%10.2f\n" % ("Collected Items : ", len(self.telemetry)))
			f.write("    %-7s\t%10.2f\n" % ("Relative Gap : ", int(self.gap_time[0])))
			f.write("    %-7s\t%10.2f\n" % ("Solution Runtime : ", self.gap_time[1]))
			f.write("\n")
			f.write(" ---------------------------------------------------------------------\n" )
			f.write(" ---------------------------------------------------------------------\n" )
			f.write("\n")
			
	"""		
	def write(self, path):
		#inst = self.inst
		with open(path+".txt", "w") as f:
			f.write("Instance = %s\n" % os.path.basename(self.inst.path_data))
			f.write("Cost = %.6f\n" % self.cost)
			f.write("\n")


			# writing instance data
			f.write("Data instance Info:\n")
			f.write("\n")
			#f.write("    %-7s\t%10.4f\n" % ("D :", len(self.inst.D)))
			f.write("%s%s\n" % ("number of nodes = ", len(self.inst.D)))
			f.write("%s%s\n" % ("Number of flows = ", len(self.inst.F)))
			f.write("%s%s\n" % ("Number of items = ", len(self.inst.V)))
			f.write("%s%s\n" % ("Number of monitoring applications = ", int(self.inst.num_mon_app)))
			#f.write("%s%10.2f\n" % ("Gap = ", self.gap_time[0]))
			#f.write("%s%10.2f\n" % ("Solution runtime  = ", self.gap_time[1]))
			f.write("\n")
			# writing Solution detail
			f.write("Solution Information detail:\n")
			f.write("\n")
			f.write("%s%s\n" % ("Objective function = ", self.cost))
			f.write("%s%s\n" % ("Satisfied Spatial = ", len(self.spatial)))
			f.write("%s%s\n" % ("Satisfied Temporal = ", len(self.temporal)))
			f.write("%s%s\n" % ("Collected Items = ", len(self.telemetry)))
			f.write("%s%s\n" % ("Relative Gap = ", int(self.gap_time[0])))
			f.write("%s%s\n" % ("Solution Runtime = ", self.gap_time[1]))
			f.write("%s%s\n" % ("Item Flows = ", self.flow_items))
			#f.write("%s%s\n" % ("Item Flows = ", sum(self.flow_items[19])))
			f.write("\n")
			f.write(" ---------------------------------------------------------------------\n" )
			f.write(" ---------------------------------------------------------------------\n" )
			f.write("\n")

	
		
	def write_solution(self, sol_info, path):
		with open(path+".txt", "a") as f:
			writer = csv.writer(f, lineterminator='\n')
			#writer.writerow(list(range(len(sol_info))))
			writer.writerow(sol_info)
