import os
import sys
import time
import random
import itertools
from collections import defaultdict
from instance_heuristic import Instance
from Arguments import Arguments


import numpy as np

max_iterations = 30

seed = 2021

random.seed(seed)


#generating subsets
def all_subsets(ss,l):
	subsets = itertools.chain(*map(lambda x: itertools.combinations(ss, x), range(0, len(ss) + 1)))
	return [S for S in subsets if len(S) == l]


#evalute the value of the objective
def evaluate_objective(inst, sol_collection):
	#collected items par device
	collected_items_d = defaultdict(list)
	for i in sol_collection:
		collected_items_d[i[0]].append(i[1])

	#satisfied spatil dependencies per device
	satisfied_spatial_d = defaultdict(list)

	#spatial dependencies
	sol_spatial = list()
	for m in inst.M:
		for d in inst.D:
			for P in range(len(inst.Rs[m])):
				if set(inst.Rs[m][P]).issubset(collected_items_d[d]):
					ss = (m,d,P, inst.Rs[m][P])
					satisfied_spatial_d[d].append(inst.Rs[m][P])
					sol_spatial.append(ss)

		
	# the temporal dependencies
	sol_temporal = list()
	for m in inst.M:
		for P in range(len(inst.Rt[m])):
			if inst.HH[P] > inst.TT[P]:
				tt = (m,P,inst.Rt[m][P])
				sol_temporal.append(tt)
		
	sol_spatial_cost = len(sol_spatial)	
	sol_temporal_cost = len(sol_temporal)					
	sol_objective_value = sol_spatial_cost + sol_temporal_cost

	return sol_objective_value, sol_spatial_cost, sol_temporal_cost


#swaping of items
def int_perturbation(sol_collection,i,j):
	a,b = random.sample(sol_collection, 2)
	#a,b = sol_collection[0], sol_collection[1]
	#print(a, b)
	#print(sol_collection.index(a))
	#print(sol_collection.index(b))
	
	c, d = a.copy(), b.copy()
	c[i], d[j] = d[j], c[i]
	sol_collection[sol_collection.index(a)] = c
	sol_collection[sol_collection.index(b)] = d
	return sol_collection

#inssertion of new element in the solution
def int_insert(inst, sol_collection, collected_items_d):
	for f in inst.F:
		for v in inst.V:
			if inst.Kf[f] >= inst.Size[v] :
				for d in inst.path[f]:
					if v not in collected_items_d[d]:
						e = [d,v,f]
						sol_collection.append([e])
	return sol_collection


#removing item from solution
def int_remove(sol_collection, e):
	sol_collection.pop(sol_collection.index(e))



#checking the feasability of a solution
def is_feasable(inst, sol_collection):
	# collected items
	collected_items_d = defaultdict(list)
	#items collected by each flow
	flow_items  = defaultdict(list)
	#sise of items collected by each flow
	flow_items_size = defaultdict(list)
	is_feasable = True
	for i in sol_collection:
		flow_items[i[2]].append(i[1])
		flow_items_size[i[2]].append(inst.Size[i[1]])
		collected_items_d[i[0]].append(i[1])

		#checking if capacity of flows are not excceded
		if sum(flow_items_size[i[2]]) > inst.initial_Kf[i[2]]:
			is_feasable = False
			#print("capacite viole : ", is_feasable)
			break

		#checking if the path of flow is not violated
		if i[0] not in inst.path[i[2]]:
			is_feasable = False
			#print("chemin viole : ", is_feasable)
			break

		#checking that no item is collected more than once
		if collected_items_d[i[0]].count(i[1]) > 1:
			is_feasable = False
			#print("multiple collection : ", is_feasable)
			break
			
	return is_feasable


#construction of the solution
def int_greedy(inst, greediness_value = 0.3):
	#collected items par device
	##collected_items_d = defaultdict(set)
	collected_items_d = defaultdict(list)
	#satisfied_spatial_d = defaultdict(list)
	Candidate_List = defaultdict(list)
	All_Cases_List = list()

	sol_collection = list()

	# generating the candidate list
	for d in inst.D:
		for i in range(len(inst.R)):
			#self.Candidate_List[d].append([d, inst.R[i], sum([inst.Size[k] for k in inst.R[i]])])
			Candidate_List[d].append([d, [t for t in inst.R[i] if t in inst.V_d[d]], sum([inst.Size[k] for k in [t for t in inst.R[i] if t in inst.V_d[d]]])])
	Candidate_List = sorted(Candidate_List.values(), reverse=True)
	
	# generating all cases
	for i in range(len(Candidate_List)):
		for j in range(len(Candidate_List[i])):
			if len(Candidate_List[i][j][1]) !=0:
				All_Cases_List.append(Candidate_List[i][j])
	# sorting the cases
	All_Cases_List.sort(key=lambda x:[x[2]])

	for i in inst.D:
		rand = int.from_bytes(os.urandom(8), byteorder = "big") / ((1 << 64) - 1)
		if (rand > greediness_value):
			#rest_list = self.All_Cases_List[:4] # grab the first five elements
			####
			while len(All_Cases_List) > 0:
				rest_list = All_Cases_List[:4] # grab the first five elements
				s = random.choice(rest_list)
				#for t in range(len(s)):
				for v in s[1]:
					for f in inst.FCD[s[0]]:
						#if v in s[t][1] and f in self.Flows_Crossing_Device[s[t][0]]:
						if inst.Size[v] <= inst.Kf[f]:
							sol_collection.append([s[0],v,f])
							#seed[0].append([s[0],v,f])
							##collected_items_d[s[0]].add(v)
							collected_items_d[s[0]].append(v)
							n_cap = inst.Kf[f] - inst.Size[v]
							n_Kf = {f:n_cap}
							inst.Kf.update(n_Kf)
							#print(inst.Kf[f])
							break
				All_Cases_List.pop(All_Cases_List.index(s))

	sol_objective_value, sol_spatial_cost, sol_temporal_cost = evaluate_objective(inst,sol_collection)
		

	#print(All_Cases_List)
	#print("Number of collected items : ", len(sol_collection))
	#print("Value of the objective : ", sol_objective_value)
	#print("Number of spatial dependencies : ", sol_spatial_cost)
	#print("Number of spatial dependencies : ", sol_temporal_cost)
	#print("Solution greedy : ", sol_collection)

	return sol_collection, sol_objective_value, sol_spatial_cost, sol_temporal_cost
	
	
	
# the local search 
def int_local_search1(inst, sol_collection):
	temp = sol_collection[:]

	#collected items par device
	collected_items_d = defaultdict(list)
	for i in sol_collection:
		collected_items_d[i[0]].append(i[1])

	#collected items by flows
	collected_items_f = defaultdict(list)
	for i in sol_collection:
		collected_items_f[i[2]].append(i[1])

	#flow crossing device in solution
	device_flow_d_f = defaultdict(list)
	for i in sol_collection:
		device_flow_d_f[i[0]].append(i[2])

	#collected items from pairs and the missed ones
	collected_pairs = defaultdict(list)
	missed_pairs = defaultdict(list)
	for d in inst.D:
		for m in inst.M:
			for v in inst.R[m]:
				if v in collected_items_d[d]:
					collected_pairs[d,m].append(v)
				if v not in collected_items_d[d]:
					missed_pairs[d,m].append(v)

	devices_avilable = defaultdict(list)
	for d in inst.D:
		for m in inst.M:
			if len(collected_pairs[d,m]) != len(inst.R[m]):
				#for f in inst.F:
					for v in collected_pairs[d,m]:
						#if f in device_flow_d_f[d]:
							devices_avilable[v].append(d)

	#Insertion part
	for d in inst.D:
		for v in inst.V:
			for f in inst.F:
				if d in inst.path[f] and inst.Kf[f] >= inst.Size[v]:
					#if inst.Kf[f] >= inst.Size[v]:
						if [d,v,f] not in sol_collection: #and v not in collected_items_d[d]:
							sol_collection.append([d,v,f])
							if is_feasable(inst, sol_collection) == True:
								collected_items_d[d].append(v)
							if is_feasable(inst, sol_collection) == False:
								sol_collection.pop(sol_collection.index([d,v,f]))


	

	#Replacement part
	AAA=list()
	for m in inst.M:
		for v in inst.R[m]:
			if v in devices_avilable.keys():
				for d in devices_avilable[v]:
					for i in sol_collection:
						if i[0] == d and i[1] == v:
							AAA.append(i)
		


	#device by flow crossing it						
	sol_par_d = defaultdict(list)
	for i in sol_collection:
		if i[2] in inst.FCD[i[0]]:
			sol_par_d[i[0]].append(i)

	AA=list()
	BB = list()
	for i in sol_collection:
		for m in inst.M:
			if not set(inst.R[m]).issubset(collected_items_d[i[0]]):
				if inst.R[m][0] in collected_items_d[i[0]] :
					AA.append(i)
				if inst.R[m][1] in collected_items_d[i[0]]:
					BB.append(i)
			
	tt = list()
	for i in AA:
		for j in BB:
			if j[2] in inst.FCD[i[0]]:
				tt.append([i,j])
				#print("On Peut : ", i,j)
				#print("On Peut : ", tt)
			if i[2] in inst.FCD[j[0]]:
				tt.append([i,j])
				#print("We can : ", i,j)
				#print("We can : ", tt)
	
	
	yy = list()
	for i in range(len(tt)):
		if tt[i][0] not in yy:
			a = [tt[i][0][0], tt[i][1][1], tt[i][1][2]]
			b = tt[i][1]
			yy.append(tt[i][0])
		#if b in sol_collection:
		#print("BBBBBBBBBB : ", b)
		
		if a not in sol_collection and b in sol_collection:
			sol_collection.append(a)
			sol_collection.remove(b)
			is_feasable1 = is_feasable(inst, sol_collection)
			print(is_feasable1)
		

		#sol_collection.append(b)
		#sol_collection.remove(i[1][1])
		#break
	

	return sol_collection, sol_par_d
	
	
	
def int_iterated_local_search(inst, sol_collection):
	gen_sol = list()
	for i in range(10000):
		sol_collection = int_perturbation(sol_collection,1,1)
		if is_feasable(inst, sol_collection) == True:
			gen_sol.append(sol_collection)

	return sol_collection, gen_sol
	
	


if __name__ == "__main__":
	arg = Arguments()

	if not os.path.exists('solutions'):
		os.mkdir('solutions')

	start_time = time.time()
	inst = Instance(path_data = arg.instance, num_nodes = arg.num_nodes, edges_to_attach = arg.edges_to_attach, num_flows = arg.num_flows, min_size = arg.min_size, max_size = arg.max_size, num_items = arg.num_items, num_mon_app = arg.num_mon_app)

	sol_collection, sol_objective_value, sol_spatial_cost, sol_temporal_cost = int_greedy(inst, greediness_value = 0.3)
	#print("first : ", len(sol_collection))
	
	print("Number of collected items : ", len(sol_collection))
	print("Value of the objective : ", sol_objective_value)
	print("Number of spatial dependencies : ", sol_spatial_cost)
	print("Number of spatial dependencies : ", sol_temporal_cost)
	
	
	sol_collection, sol_par_d = int_local_search1(inst, sol_collection)
	
	#for i in sol_par_d.keys():
	#	print(i, " ------------> : ", sol_par_d[i])
	
	
	print("Total runtime: %.2f seconds" % (time.time() - start_time))
