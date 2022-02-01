import os
import sys
import time
from mip import Model, xsum, maximize, BINARY, ConstrsGenerator, CutPool
from collections import defaultdict


from Arguments import Arguments
from instances import Instance
#from instance_heuristic import Instance
from solutions import Int_Solution

# to save data
#from solution_heuristic import Int_Solution


class Compact_Formulation_Base:
	""" 
	This class implement the new proposed model using gurobi 
	"""

	def __init__(self, inst):
		# Creating the model
		model = Model("INT_Model_Base") # it choose automaticaly the model
		# Defining spatial and temporal dependencies variables
		s_b = [[[model.add_var(name='s_b({},{},{})'.format(m,d,P), var_type=BINARY) for P in range(len(inst.Rs[m]))] for d in inst.D] for m in inst.M]
		t_b = [[model.add_var(name='t_b({},{})'.format(m,P), var_type=BINARY) for P in range(len(inst.Rt[m]))] for m in inst.M]
		y = [[[model.add_var(name='y({},{},{})'.format(d,v,f), var_type=BINARY) for f in inst.F] for v in inst.V] for d in inst.D]
		s = [[[model.add_var(name='s({},{},{})'.format(m,d,P)) for P in range(len(inst.Rs[m]))] for d in inst.D] for m in inst.M]
		t = [[model.add_var(name='t({},{})'.format(m,P)) for P in range(len(inst.Rt[m]))] for m in inst.M]


		# objective function : maximise spatial and temporal dependencies
		model.objective = maximize(xsum(s_b[m][d][P] for m in inst.M for d in inst.D for P in range(len(inst.Rsd[m,d]))) + xsum(t_b[m][P] for m in inst.M for P in range(len(inst.Rt[m]))))

		# Constraints

		# each flow does not excced it capacity
		for f in inst.F :
			model += xsum(y[d][v][f]*inst.Size[v] for d in inst.path[f] for v in inst.V_d[d]) <= inst.Kf[f] 
			no_path_f = [j for j in inst.D if j not in inst.path[f]]
			model += xsum(y[d][v][f] for d in no_path_f for v in inst.V_d[d]) <= 0 


		# single telemetry is collected by a single flow
		for d in inst.D : #ori
			for v in inst.V :
				model += xsum(y[d][v][f] for f in inst.F) <= 1

		# counting the spatial dependency
		for m in inst.M :
			for d in inst.D :
				if len(inst.Rsd[m,d]) > 0:
					for p in range(len(inst.Rsd[m,d])) :
						model += s[m][d][p] == xsum(y[d][v][f] for v in inst.Rsd[m,d][p] for f in inst.F)

		# counting temporal dependency
		for m in inst.M :
			for P in range(len(inst.Rt[m])) :
				if inst.HH[P] > inst.TT[P] :
					print("encore")
					model += t[m][P] == xsum(y[d][v][f] for d in inst.D for v in inst.Rt[m][P] for f in inst.F)


		# satisfied spatial dependency
		for m in inst.M :
			for d in inst.D :
				if len(inst.Rsd[m,d]) > 0:
					for P in range(len(inst.Rsd[m,d])) :
						model += s_b[m][d][P] <= s[m][d][P]/len(inst.Rsd[m,d][P])


		# satisfied temporal dependency
		for m in inst.M :
			for P in range(len(inst.Rt[m])) :
				model += t_b[m][P] <= t[m][P]/len(inst.Rt[m][P])


		# creating class variables
		self.inst = inst
		self.model = model
		self.s_b = s_b
		self.t_b = t_b
		self.y = y
		self.solution = None


	def optimize(self):
		from mip import OptimizationStatus
		#model.max_gap = 0.05
		start_time = time.time()
		status = self.model.optimize(max_seconds=1000)
		end_time = time.time()
		if status == OptimizationStatus.OPTIMAL:
			print('optimal solution requirement {} found'.format(self.model.objective_value))
		elif status == OptimizationStatus.FEASIBLE:
			print('sol.requirement {} found, best possible: {}'.format(self.model.objective_value, self.model.objective_bound))
		elif status == OptimizationStatus.NO_SOLUTION_FOUND:
			print('no feasible solution found, lower bound is: {}'.format(self.model.objective_bound))

		"""
		if status == OptimizationStatus.OPTIMAL or status == OptimizationStatus.FEASIBLE:
			print('solution:')
			for v in self.model.vars:
				if abs(v.x) > 1e-6: # only printing non-zeros
					print('{} : {}'.format(v.name, v.x))
		"""

		Solution_Runtime = round((end_time - start_time),2)
		Gap = round((abs((self.model.objective_value - self.model.objective_bound)/self.model.objective_value)*100),2)
		UB = self.model.objective_bound
		Obj_value = self.model.objective_value

		# creting the final solution
		self.solution = Int_Solution(self.inst, cost=self.model.objective_value)


		self.solution.add_gap_time(Gap)
		self.solution.add_gap_time(Solution_Runtime)

		# spatial dependencies
		Sol1 = list()
		for m in self.inst.M:
			for d in self.inst.D:
				if len(inst.Rsd[m,d]) > 0:
					for P in range(len(self.inst.Rsd[m,d])):
						if self.s_b[m][d][P].x >= 0.99:
							data = [m,d,P]
							Sol1.append(data)
							self.solution.add_spatial(data)
		# number of spatial					
		Nb_spa = len(Sol1)

		# temporal dependencies
		Sol2 = list()
		for m in self.inst.M:
			for P in range(len(self.inst.Rt[m])):
				if self.t_b[m][P].x >= 0.99:
					data = [m,P]
					Sol2.append(data)
					self.solution.add_temporal(data)

		# number of temporal					
		Nb_tmp = len(Sol2)

		Sol = list()
		# collected telemtry items
		for d in self.inst.D:
			for v in self.inst.V_d[d]:
				for f in self.inst.F:
					if self.y[d][v][f].x >= 0.99:
						data = [d,v,f]
						Sol.append(data)
						self.solution.add_telemetry(data)

		# number of items
		Nb_items = len(Sol)

		#computing collected item by each flow
		sol_collection = list()
		collected_f = defaultdict(list)
		for d in self.inst.D:
			for v in self.inst.V_d[d]:
				for f in self.inst.F:
					if self.y[d][v][f].x >= 0.99:
						data = [v]
						sol_collection.append([d,v,f])
						#collected_f[f].append(v)
						collected_f[f].append(inst.Size[v])

		#self.solution.add_flow_items(collected_f)

		flow_collect = {}
		for f in inst.F:
			if f in collected_f.keys():
				flow_collect[f] = sum(collected_f[f])

		self.solution.add_flow_items(flow_collect)


		


		"""
		#print("Collected Items :", Sol)
		lista = defaultdict(list)
		for d in inst.D:
			for i in range(len(Sol)):
				if Sol[i][0] == d:
					lista[d].append(Sol[i])

		#print("spatial Items :", Sol1)
		lista1 = defaultdict(list)
		#for m in inst.M:
		for d in inst.D:
			for i in range(len(Sol1)):
				if Sol1[i][1] == d:
					lista1[d].append(Sol1[i])


		

		print("---------------------")
		print("collection at 5 :", lista[2])
		print("---------------------")
		print("spatial at 5 :", lista1[2])
		"""

		Sol_info = [len(inst.D),len(inst.F), Nb_spa, Nb_tmp, Nb_items, Obj_value, UB, Gap, Solution_Runtime]
		return Sol_info, sol_collection


if __name__ == "__main__":
	arg = Arguments()


	start_time = time.time()


	# creating folders 'logs' and 'solutions' if they don't exist already
	if not os.path.exists('logs'):
		os.makedirs('logs')
	if not os.path.exists('solutions'):
		os.makedirs('solutions')



	inst = Instance(path_data = arg.instance, num_nodes = arg.num_nodes, edges_to_attach = arg.edges_to_attach, num_flows = arg.num_flows, num_given_flow = arg.num_given_flow, max_route =arg.max_route, min_size = arg.min_size, max_size = arg.max_size, num_items = arg.num_items, num_mon_app = arg.num_mon_app)
	formulation = Compact_Formulation_Base(inst)
	Sol_info, sol_collection = formulation.optimize()


	solution = Int_Solution(inst)
	formulation.solution.print_solution()
	formulation.solution.write(path = arg.out_model)
	#solution.write_solution(Sol_info, path = arg.out_model)

	print("Total runtime: %.2f seconds" % (time.time() - start_time))
	#print("Sol collection : ", sol_collection)
