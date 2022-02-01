import os
import sys
import time
import random
import itertools
from collections import defaultdict
from mip import Model, xsum, maximize, BINARY, ConstrsGenerator, CutPool
from instance_heuristic import Instance
#from int_knapsack import Int_Knapsack
from solution_heuristic import Int_Solution

#from arguments_heuristic import Arguments
from Arguments import Arguments


import numpy as np

max_iterations = 30

seed = 2021

random.seed(seed)


def all_subsets(ss,l):
	subsets = itertools.chain(*map(lambda x: itertools.combinations(ss, x), range(0, len(ss) + 1)))
	return [S for S in subsets if len(S) == l]




class Int_Heuristic:
	""" 
	This class implement the new proposed model using gurobi 
	"""


	def __init__(self, inst):
		Sol = list()
		Flows_Crossing_Device  = defaultdict(list)
		Candidate_List = defaultdict(list)
		All_Cases_List = list()
		Restricted_Candidate_List = list()
		rcl_nb = int()

		self.Flows_Crossing_Device = Flows_Crossing_Device
		self.Candidate_List = Candidate_List
		self.Restricted_Candidate_List = Restricted_Candidate_List
		self.rcl_nb = rcl_nb
		self.All_Cases_List = All_Cases_List

	#def evaluate_objective(self,sol):


	
	def restricted_candidate_list(self, greediness_value = 0.5):
		##print("Sise of items : ", inst.Size)

		sol_collection = list()				# for the collected telemetry items
		#sol_collection_cost = int()			# total number of collected telemetry items
		sol_spatial = list()				# for the spatial dependencies 
		#sol_spatial_cost = int()			# total number of spatial dependencies
		sol_temporal = list()				# for the temporal dependencies
		#sol_temporal_cost = int()			# total number of tempral dependencies

		collected_items_d = defaultdict(set)
		satisfied_spatial_d = defaultdict(list)

		# flow routed through device d 
		for d in inst.D:
			for f in inst.F :
				if d in inst.path[f]:
					self.Flows_Crossing_Device[d].append(f)


		# generating the candidate list
		for d in inst.D:
			for i in range(len(inst.R)):
				#self.Candidate_List[d].append([d, inst.R[i], sum([inst.Size[k] for k in inst.R[i]])])
				self.Candidate_List[d].append([d, [t for t in inst.R[i] if t in inst.V_d[d]], sum([inst.Size[k] for k in [t for t in inst.R[i] if t in inst.V_d[d]]])])
		self.Candidate_List = sorted(self.Candidate_List.values(), reverse=True)
		
		# generating all cases
		for i in range(len(self.Candidate_List)):
			for j in range(len(self.Candidate_List[i])):
				if len(self.Candidate_List[i][j][1]) !=0:
					self.All_Cases_List.append(self.Candidate_List[i][j])
		# sorting the cases
		self.All_Cases_List.sort(key=lambda x:[x[2]])
		for i in inst.D:
			rand = int.from_bytes(os.urandom(8), byteorder = "big") / ((1 << 64) - 1)
			if (rand > greediness_value):
				#rest_list = self.All_Cases_List[:4] # grab the first five elements
				####
				while len(self.All_Cases_List) > 0:
					rest_list = self.All_Cases_List[:4] # grab the first five elements
					s = random.choice(rest_list)
					#for t in range(len(s)):
					for v in s[1]:
						for f in self.Flows_Crossing_Device[s[0]]:
							#if v in s[t][1] and f in self.Flows_Crossing_Device[s[t][0]]:
							if inst.Size[v] <= inst.Kf[f]:
								sol_collection.append([s[0],v,f])
								#seed[0].append([s[0],v,f])
								collected_items_d[s[0]].add(v)
								n_cap = inst.Kf[f] - inst.Size[v]
								n_Kf = {f:n_cap}
								inst.Kf.update(n_Kf)
								#print(inst.Kf[f])
								break
					self.All_Cases_List.pop(self.All_Cases_List.index(s))


				#####
			elif (rand <= greediness_value):
				#rest_list = random.sample(self.All_Cases_List, 4)   # select randomly four element
				####
				while len(self.All_Cases_List) > 4:
					rest_list = random.sample(self.All_Cases_List, 4)   # select randomly four element
					s = random.choice(rest_list)
					#for t in range(len(s)):
					for v in s[1]:
						for f in self.Flows_Crossing_Device[s[0]]:
							#if v in s[t][1] and f in self.Flows_Crossing_Device[s[t][0]]:
							if inst.Size[v] <= inst.Kf[f]:
								sol_collection.append([s[0],v,f])
								collected_items_d[s[0]].add(v)
								n_cap = inst.Kf[f] - inst.Size[v]
								n_Kf = {f:n_cap}
								inst.Kf.update(n_Kf)
								#print(inst.Kf[f])
								break
					self.All_Cases_List.pop(self.All_Cases_List.index(s))


		# the spatial dependencies 
		for m in inst.M:
			for d in inst.D:
				for P in range(len(inst.Rs[m])):
					if set(inst.Rs[m][P]).issubset(collected_items_d[d]):
						ss = (m,d,P, inst.Rs[m][P])
						satisfied_spatial_d[d].append(inst.Rs[m][P])
						sol_spatial.append(ss)

						#if inst.HH[P] > inst.TT[P]:
						#	tt = (m,P,inst.Rt[m][P])
						#	sol_temporal.append(tt)

		
		for m in inst.M:
			for P in range(len(inst.Rt[m])):
				if inst.HH[P] > inst.TT[P]:
					tt = (m,P,inst.Rt[m][P])
					sol_temporal.append(tt)


		# cost of the solution
		sol_collection_cost = len(sol_collection)				# total number of collected telemetry items
		sol_spatial_cost = len(sol_spatial)						# total number of spatial dependencies
		sol_temporal_cost = len(sol_temporal)					# total number of tempral dependencies
		sol_objective_value = sol_spatial_cost + sol_temporal_cost		# the value of the objective function
		heur_full_solution = [sol_objective_value, sol_spatial, sol_spatial_cost, sol_temporal, sol_temporal_cost, sol_collection, sol_collection_cost, collected_items_d, satisfied_spatial_d]
		heur_full_solution_save = [len(inst.D), len(inst.F), sol_collection_cost, sol_spatial_cost, sol_temporal_cost, sol_objective_value]

		return heur_full_solution, heur_full_solution_save

	#################
	# the local search
	def int_local_search(self, heur_full_solution):
		sol_objective_value_heur = heur_full_solution[0]
		sol_spatial_heur = heur_full_solution[1]				 
		sol_spatial_cost_heur = heur_full_solution[2]
		sol_temporal_heur = heur_full_solution[3]				
		sol_temporal_cost_heur = heur_full_solution[4]
		sol_collection_heur = heur_full_solution[5]
		sol_collection_cost_heur = heur_full_solution[6]		
		collected_items_d_heur = heur_full_solution[7]
		satisfied_spatial_d_heur = heur_full_solution[8] 

		sol_spatial_loc = list()
		sol_temporal_loc = list()
		satisfied_spatial_d_loc = defaultdict(list)


		#collected items from pairs and the missed ones
		collected_pairs = defaultdict(list)
		missed_pairs = defaultdict(list)
		for d in inst.D:
			for m in inst.M:
				for v in inst.R[m]:
					if v in collected_items_d_heur[d]:
						collected_pairs[d,m].append(v)
					if v not in collected_items_d_heur[d]:
						missed_pairs[d,m].append(v)

		devices_avilable = defaultdict(list)
		for d in inst.D:
			for m in inst.M:
				if len(collected_pairs[d,m]) != len(inst.R[m]):
					for v in collected_pairs[d,m]:
						devices_avilable[v].append(d)


		for d in inst.D:
			for m in inst.M:
				for ele in sol_collection_heur:
					if ele[0] == d:
						for v in missed_pairs[d,m]:
							if v in devices_avilable.keys():
								for d1 in devices_avilable[v]:
									if not set(collected_pairs[d,m]).issubset(collected_items_d_heur[d1]) and ele[2] in self.Flows_Crossing_Device[d]:
										##print("YES", "d1 : ", d1, "v : ", v)
										#collected_d[d1].remove(v)
										collected_items_d_heur[d].add(v)
									if v in collected_items_d_heur[d1]:
										collected_items_d_heur[d1].remove(v)


		for m in inst.M:
			for d in inst.D:
				for P in range(len(inst.Rs[m])):
					if set(inst.Rs[m][P]).issubset(collected_items_d_heur[d]):
						ss = (m,d,P, inst.Rs[m][P])
						satisfied_spatial_d_loc[d].append(inst.Rs[m][P])
						sol_spatial_loc.append(ss)

		sol_spatial_cost_loc = sum([len(satisfied_spatial_d_loc[t]) for t in satisfied_spatial_d_loc.keys()])
		sol_collection_cost_loc = sum([len(collected_items_d_heur[t]) for t in collected_items_d_heur.keys()])
		


		# evaluate temporal dependencies
		for m in inst.M:
			for P in range(len(inst.Rt[m])):
				if inst.HH[P] > inst.TT[P]:
					tt = (m,P,inst.Rt[m][P])
					sol_temporal_loc.append(tt)

		sol_temporal_cost_loc = len(sol_temporal_loc)

		sol_objective_value_loc = sol_spatial_cost_loc + sol_temporal_cost_loc

		loc_full_solution = [sol_objective_value_loc, sol_spatial_cost_loc, sol_temporal_cost_loc, sol_collection_cost_loc]
		loc_full_solution_save = [len(inst.D), len(inst.F), sol_collection_cost_loc, sol_spatial_cost_loc, sol_temporal_cost_loc, sol_objective_value_loc]

		##for d in collected_items_d_heur.keys():
		##	print("device : ", d, "--------> ", collected_items_d_heur[d])

		return loc_full_solution, loc_full_solution_save



if __name__ == "__main__":
	arg = Arguments()

	if not os.path.exists('solutions'):
		os.mkdir('solutions')

	
	spa_her = list()
	tempo_her = list()
	cost_her = list()

	spa_loc = list()
	tempo_loc = list()
	cost_loc = list()

	best = 0

	##for i in range(30):

	start_time = time.time()
	inst = Instance(path_data = arg.instance, num_nodes = arg.num_nodes, edges_to_attach = arg.edges_to_attach, num_flows = arg.num_flows, min_size = arg.min_size, max_size = arg.max_size, num_items = arg.num_items, num_mon_app = arg.num_mon_app)
	heuristic = Int_Heuristic(inst)
	#heuristic.Int_Greedy_Constructive()
	heur_full_solution, heur_full_solution_save = heuristic.restricted_candidate_list(greediness_value = 0.5)

	###############
	loc_full_solution, loc_full_solution_save = heuristic.int_local_search(heur_full_solution)




	print("------------------------------")
	print("Value of the Objecrive Function Heuristic : ", heur_full_solution[0])
	print("------------------------------")
	print("Number of Satisfied Spatial Dependencies Heuristic : ", heur_full_solution[2])
	print("------------------------------")
	print("Number of Satisfied Temporal Dependencies Heuristic : ", heur_full_solution[4])
	print("------------------------------")
	print("Number of Collected Items Heuristic : ", heur_full_solution[6])
	print("------------------------------")
	print("")
	print("")

	######
	print("Value of the Objecrive Function Local : ", loc_full_solution[0])
	print("------------------------------")
	print("Number of Satisfied Spatial Dependencies Local : ", loc_full_solution[1])
	print("------------------------------")
	print("Number of Satisfied Temporal Dependencies Local : ", loc_full_solution[2])
	print("------------------------------")
	print("Number of Collected Items Local : ", loc_full_solution[3])
	print("------------------------------")	



	solution = Int_Solution(inst)
	#solution.write(sol_info, path = arg.out)
	sol_info_heur = heur_full_solution_save + [round((time.time() - start_time),2)]
	solution.write_solution(sol_info_heur, path = arg.out_her)

	print("Total runtime: %.2f seconds" % (time.time() - start_time))

	def evaluate_objective(inst):
		print(len(inst.D))
		print(len(inst.F))
		print(len(inst.V))

	evaluate_objective(inst)
	print("size : ", inst.Kf)