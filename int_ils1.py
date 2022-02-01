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


def all_subsets(ss,l):
	subsets = itertools.chain(*map(lambda x: itertools.combinations(ss, x), range(0, len(ss) + 1)))
	return [S for S in subsets if len(S) == l]



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

def int_insert(inst, sol_collection, collected_items_d):
	#sol_collection.append([e])
	#collected items par device
	#collected_items_d = defaultdict(set)
	#for i in sol_collection:
	#	collected_items_d[i[0]].add(i[1])
	for f in inst.F:
		for v in inst.V:
			if inst.Kf[f] >= inst.Size[v] :
				for d in inst.path[f]:
					if v not in collected_items_d[d]:
						e = [d,v,f]
						sol_collection.append([e])
	return sol_collection

def int_remove(sol_collection, e):
	sol_collection.pop(sol_collection.index(e))




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
		

	
	""" is_feasable = True
	for f in flow_items_size.keys() :
		if sum(flow_items_size[f]) > inst.initial_Kf[f]:
			is_feasable = False
			print("capacite viole : ", is_feasable)

	#for i in sol_collection:
	#	if i[2] not in inst.FCD[i[0]]:
	#		is_feasable = False
	#		print("chemin viole : ", is_feasable)

	for i in sol_collection:
		if i[0] not in inst.path[i[2]]:
			is_feasable = False
			print("chemin viole : ", is_feasable) """
	return is_feasable



def int_greedy(inst, greediness_value = 0.3):
	#collected items par device
	##collected_items_d = defaultdict(set)
	collected_items_d = defaultdict(list)
	#satisfied_spatial_d = defaultdict(list)
	Candidate_List = defaultdict(list)
	All_Cases_List = list()

	sol_collection = list()
	
	# flows_cossing_d = defaultdict(list)
	# # flow routed through device d 
	# for d in inst.D:
	# 	for f in inst.F :
	# 		if d in inst.path[f]:
	# 			flows_cossing_d[d].append(f) 

	#print(flows_cossing_d[10])

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
		

	print(All_Cases_List)
	print(len(sol_collection))
	print(sol_objective_value)
	print(sol_spatial_cost)
	print(sol_temporal_cost)
	#print("Solution greedy : ", sol_collection)

	return sol_collection, sol_objective_value, sol_spatial_cost, sol_temporal_cost






def int_local_search(inst, sol_collection):
	best_obj, best_spa, best_tempo = evaluate_objective(inst, sol_collection)

	#collected items par device
	collected_items_d = defaultdict(set)
	for i in sol_collection:
		collected_items_d[i[0]].add(i[1])

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
				for v in collected_pairs[d,m]:
					devices_avilable[v].append(d)


	for d in inst.D:
		for m in inst.M:
			for ele in sol_collection:
				if ele[0] == d:
					for v in missed_pairs[d,m]:
						if v in devices_avilable.keys():
							for d1 in devices_avilable[v]:
								if not set(collected_pairs[d,m]).issubset(collected_items_d[d1]) and ele[2] in inst.FCD[d]:
									##print("YES", "d1 : ", d1, "v : ", v)
									#collected_d[d1].remove(v)
									collected_items_d[d].add(v)

								""" # evaluate candidate point
								cand_obj, cand_spa, cand_tempo = evaluate_objective(inst, collected_items_d)
								#candidte_eval = objective(candidate)
								# check if we should keep the new point
								if cand_obj >= best_obj:
									# store the new point
									#solution, solution_eval = candidate, candidte_eval
									best_obj, best_spa, best_tempo = cand_obj, cand_spa, cand_tempo """

								if v in collected_items_d[d1]:
									collected_items_d[d1].remove(v)


								# evaluate candidate point
								cand_obj, cand_spa, cand_tempo = evaluate_objective(inst, sol_collection)
								#candidte_eval = objective(candidate)
								# check if we should keep the new point
								if cand_obj >= best_obj:
									# store the new point
									#solution, solution_eval = candidate, candidte_eval
									best_obj, best_spa, best_tempo = cand_obj, cand_spa, cand_tempo

	#cand_obj, cand_spa, cand_tempo = evaluate_objective(inst, collected_items_d)

	print("best obj", best_obj)
	print("best spa", best_spa)
	print("best tempo", best_tempo)
	print("------------------------")
	#print("cand obj", cand_obj)
	#print("cand spa", cand_spa)
	#print("cand tempo", cand_tempo)


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
	
	print("-------------------------------")
	print("Set ttt : ", tt)
	#print("item AA : ", AA)
	#print("-------------------------------")
	#print("item BB : ", BB)
	
	#tt = [[[42, 0, 45], [33, 1, 40]], [[47, 0, 8], [43, 1, 7]]]
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
	

	return sol_collection, sol_par_d, devices_avilable


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


	print("Total runtime: %.2f seconds" % (time.time() - start_time))

	##print("bfore 3 :", inst.Kf)

	#evaluate_objective(inst)

	
	#int_greedy(inst)
	

	sol_collection, sol_objective_value, sol_spatial_cost, sol_temporal_cost = int_greedy(inst, greediness_value = 0.3)
	print("first : ", len(sol_collection))
	#int_local_search(inst, sol_collection, collected_items_d)
	#print("second : ",sol_collection)

	first_objective_value, first_spatial_cost, first_temporal_cost = evaluate_objective(inst, sol_collection)
	print("first cost : ", first_objective_value)
	print("first Spatial : ", first_spatial_cost)
	print("first temporal : ", first_temporal_cost)

	##is_feasable = is_feasable(inst, sol_collection)
	##print("flow items : ", flow_items)
	##print("flow item size : ", flow_items_size)
	##print("size 3 :", inst.Size)
	##print("after 3 :", inst.Kf)
	#a,b,c = is_feasable(inst,sol_collection)
	#print("initial : ", inst.initial_Kf)
	##print("State of the solution : ", is_feasable)
	#sol_collection1 = int_perturbation(sol_collection,1,1)
	#is_feasable = is_feasable(inst, sol_collection1)
	#T = is_feasable(inst, sol_collection1)
	#print("State of the solution perturbe : ", T)


	sol_collection, sol_par_d, devices_avilable = int_local_search1(inst, sol_collection)
	print("Size of items : ", inst.Size)
	#print("7 --> : ", inst.Kf[7], "8 --> : ", inst.Kf[8],  "140 --> : ",inst.Kf[140], "37 --> : ",inst.Kf[37], "55 --> : ", inst.Kf[55], "177 --> : ", inst.Kf[177])
	for i in sol_par_d.keys():
		print(i, " ------------> : ", sol_par_d[i])

	print("-------------------------------------------------")

	for i in devices_avilable.keys():
		print(i, "-------------> : ", devices_avilable[i])
	ele_sol = sol_par_d.values()

	values_list = list(ele_sol)
	bbb = 0
	for i in values_list:
		bbb = bbb + len(i)
	print("longueur : ", len(values_list), "---------------> ", bbb)

	print("second : ", len(sol_collection))

	is_feasable1 = is_feasable(inst, sol_collection)
	print("feasability : ", is_feasable1)
	if is_feasable:
		print("TH")
	else:
		print("Faux")

	best_objective_value, best_spatial_cost, best_temporal_cost = evaluate_objective(inst, sol_collection)
	print("cost : ", best_objective_value)
	print("Spatial : ", best_spatial_cost)
	print("temporal : ", best_temporal_cost)

	sol_collection, gen_sol = int_iterated_local_search(inst, sol_collection)
	print("feasable dans tout ca : ", len(gen_sol))



	#device by flow crossing it						
	sol_par_d = defaultdict(list)
	for i in sol_collection:
		if i[2] in inst.FCD[i[0]]:
			sol_par_d[i[0]].append(i)

	

	for i in sol_par_d.keys():
		print(i, " ------------> : ", sol_par_d[i])


	""" AA = list()
	BB = list()
	for i in range(1000):
		sol_collection = int_perturbation(sol_collection,1,1)
		best_objective_value, best_spatial_cost, best_temporal_cost = evaluate_objective(inst, sol_collection, collected_items_d)
		is_feasable1 = is_feasable(inst, sol_collection)
		if is_feasable1 == True:
			eval_objective_value, eval_spatial_cost, eval_temporal_cost = evaluate_objective(inst, sol_collection, collected_items_d)
			AA.append(eval_objective_value)
			if eval_objective_value > best_objective_value :
				best_objective_value = eval_objective_value
			#print("State of the solution perturbe : ", is_feasable1)
		if is_feasable1 == False:
			eval_objective_value, eval_spatial_cost, eval_temporal_cost = evaluate_objective(inst, sol_collection, collected_items_d)
			BB.append(eval_objective_value)

		#print("best : ", best_objective_value, "---------", eval_objective_value)
	print("Length AA : ", len(AA))
	if len(AA) != 0:
		print("min AA : ", min(AA))
		print("max AA : ", max(AA))

	print("Length BB : ", len(BB))
	if len(BB) != 0:
		print("min BB : ", min(BB))
		print("max BB : ", max(BB))


	#sol_collection = int_insert(inst, sol_collection)
	CC = list()
	DD = list()
	for i in range(10000):
		#sol_collection = int_perturbation(sol_collection,1,1)
		sol_collection = int_insert(inst, sol_collection, collected_items_d)
		best_objective_value, best_spatial_cost, best_temporal_cost = evaluate_objective(inst, sol_collection, collected_items_d)
		is_feasable1 = is_feasable(inst, sol_collection)
		if is_feasable1 == True:
			eval_objective_value, eval_spatial_cost, eval_temporal_cost = evaluate_objective(inst, sol_collection, collected_items_d)
			CC.append(eval_objective_value)
			if eval_objective_value > best_objective_value :
				best_objective_value = eval_objective_value
			#print("State of the solution perturbe : ", is_feasable1)
		if is_feasable1 == False:
			eval_objective_value, eval_spatial_cost, eval_temporal_cost = evaluate_objective(inst, sol_collection, collected_items_d)
			DD.append(eval_objective_value)

		#print("best : ", best_objective_value, "---------", eval_objective_value)
	print("Length CC : ", len(CC))
	if len(CC) != 0:
		print("min CC : ", min(CC))
		print("max CC : ", max(CC))

	print("Length DD : ", len(DD))
	if len(BB) != 0:
		print("min DD : ", min(DD))
		print("max DD : ", max(DD))
 """










