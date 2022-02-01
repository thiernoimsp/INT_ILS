import os
import sys
import time
from mip import Model, xsum, maximize, BINARY, ConstrsGenerator, CutPool
#from arguments import Arguments
from Arguments import Arguments
from instances import Instance
from solutions import Int_Solution


class Compact_Formulation_Mixte:
	""" 
	This class implement the new proposed model using gurobi 
	"""
	def __init__(self, inst):
		# Creating the model
		model = Model("INT_Mixte") # it choose automaticaly the model
		# Defining spatial and temporal dependencies variables
		s_b = [[[model.add_var(name='s_b({},{},{})'.format(m,d,P), var_type=BINARY) for P in range(len(inst.Rs[m]))] for d in inst.D] for m in inst.M]
		t_b = [[model.add_var(name='t_b({},{})'.format(m,P), var_type=BINARY) for P in range(len(inst.Rt[m]))] for m in inst.M]
		x = [[[model.add_var(name='x({},{},{})'.format(i,j,f), var_type=BINARY) for f in inst.F] for j in inst.D] for i in inst.D]
		y = [[[model.add_var(name='y({},{},{})'.format(d,v,f), var_type=BINARY) for f in inst.F] for v in inst.V] for d in inst.D]
		s = [[[model.add_var(name='s({},{},{})'.format(m,d,P)) for P in range(len(inst.Rs[m]))] for d in inst.D] for m in inst.M]
		t = [[model.add_var(name='t({},{})'.format(m,P)) for P in range(len(inst.Rt[m]))] for m in inst.M]
		ttt = [[model.add_var(name='ttt({},{})'.format(i,f)) for f in inst.F] for i in inst.D]


		# objective function : maximise spatial and temporal dependencies
		model.objective = maximize(xsum(s_b[m][d][P] for m in inst.M for d in inst.D for P in range(len(inst.Rs[m]))) + xsum(t_b[m][P] for m in inst.M for P in range(len(inst.Rt[m]))))

		# Constraints
		# each flow does not excced it capacity
		"""
		for f in inst.GF :
			model += xsum(y[d][v][f]*inst.Size[v] for d in inst.path_mixte[f] for v in inst.G.nodes[d]['Items']) <= inst.Kf[f] #, 'bad_const_'+ str(f)    #2
			no_path_f = [j for j in inst.D if j not in inst.path_mixte[f]]
			model += xsum(y[d][v][f] for d in no_path_f for v in inst.G.nodes[d]['Items']) <= 0 #, 'god_const_'+ str(f)
		"""
		# each flow does not excced it capacity
		for f in inst.GF :
			model += xsum(y[d][v][f]*inst.Size[v] for d in inst.path[f] for v in inst.G.nodes[d]['Items']) <= inst.Kf[f] 
			no_path_f = [j for j in inst.D if j not in inst.path[f]]
			model += xsum(y[d][v][f] for d in no_path_f for v in inst.G.nodes[d]['Items']) <= 0 


		#starting of the flow
		for f in inst.FF:
			model += xsum(x[inst.S[f]][j][f] for j in inst.G.neighbors(inst.S[f])) == 1  #3

		#ending of the flow
		for f in inst.FF :
			model += xsum(x[i][inst.E[f]][f] for i in inst.G.neighbors(inst.E[f])) == 1  #4


		#flow conservation
		for f in inst.FF :
			for n in inst.D :
				if (n!= inst.S[f] and n!=inst.E[f]) :
					model += xsum(x[i][n][f] for i in inst.G.neighbors(n)) - xsum(x[n][j][f] for j in inst.G.neighbors(n)) == 0

		# removing subtours
		for i in inst.D:
			for j in inst.D:
				for f in inst.F:
					model += ttt[j][f] >= ttt[i][f]+1 - len(inst.D)*(1-x[i][j][f]), "mtz_"+str(i)+"_"+str(j)+"_"+str(f)

		# removing tours of size two
		for f in inst.F:
			for (i,j) in list(inst.G.edges):
				model += x[i][j][f] + x[j][i][f] <=1


		#limiting the lenght of routes
		for f in inst.FF:
			model += xsum(x[i][j][f] for i in inst.D for j in inst.D) <= inst.max_route - 1  #7

		# collected items must belong to the path of the network flow f
		for d in inst.D : #ori
			for v in inst.G.nodes[d]['Items'] :
				for f in inst.FF:
					model += y[d][v][f] <= xsum(x[i][d][f] for i in inst.G.neighbors(d)) #ori   #8


		# single telemetry is collected by a single flow
		for d in inst.D:
			for v in inst.G.nodes[d]['Items']:
				model += xsum(y[d][v][f] for f in inst.F) <= 1, "single_Item_Flow_"+str(d)+"_"+str(v)


		# each flow does not excced it capacity
		for f in inst.FF :
			model += xsum(y[d][v][f]*inst.Size[v] for d in inst.D for v in inst.G.nodes[d]['Items']) <= inst.Kf[f]   #10


		# counting spatial dependencies
		for m in inst.M:
			for d in inst.D:
				for P in range(len(inst.Rs[m])):
					model += s[m][d][P] == xsum(y[d][v][f] for v in inst.Rs[m][P] for f in inst.F)

		# satisfied spatial dependencies
		for m in inst.M:
			for d in inst.D:
				for P in range(len(inst.Rs[m])):
					model += s_b[m][d][P] <= s[m][d][P]/len(inst.Rs[m][P])

		# counting temporal dependency
		for m in inst.M:
			for P in range(len(inst.Rt[m])):
				if inst.HH[P] > inst.TT[P]:
					print("encore")
					model += t[m][P] == xsum(y[d][v][f] for d in inst.D for v in inst.Rt[m][P] for f in inst.F)

		# satisfied temporal dependency
		for m in inst.M:
			for P in range(len(inst.Rt[m])):
				model += t_b[m][P] <= t[m][P]/len(inst.Rt[m][P])


		# creating class variables
		self.inst = inst
		self.model = model
		self.s_b = s_b
		self.t_b = t_b
		self.x = x
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
		self.model.write("INT.lp")
		#self.model.optimize(max_seconds=timelimit)
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
		for m in inst.M:
			for d in inst.D:
				for P in range(len(inst.Rs[m])):
					if self.s_b[m][d][P].x >= 0.99:
						data = [m,d,P]
						Sol1.append(data)
						self.solution.add_spatial(data)

		# number of spatial					
		Nb_spa = len(Sol1)

		# temporal dependencies
		Sol2 = list()
		for m in inst.M:
			for P in range(len(inst.Rt[m])):
				if self.t_b[m][P].x >= 0.99:
					data = [m,P]
					Sol2.append(data)
					self.solution.add_temporal(data)

		# number of temporal					
		Nb_tmp = len(Sol2)

		# collected telemtry items
		Sol = list()
		for d in inst.D:
			for v in inst.V:
				for f in inst.F:
					if self.y[d][v][f].x >= 0.99:
						data = [d,v,f]
						Sol.append(data)
						self.solution.add_telemetry(data)
		# number of items
		Nb_items = len(Sol)

		Sol_info = [len(inst.D), len(inst.F), Nb_spa, Nb_tmp, Nb_items, Obj_value, UB, Gap, Solution_Runtime]
		return Sol_info


if __name__ == "__main__":
	arg = Arguments()


	start_time = time.time()

	# creating folders 'logs' and 'solutions' if they don't exist already
	if not os.path.exists('logs'):
		os.makedirs('logs')
	if not os.path.exists('solutions'):
		os.makedirs('solutions')



	inst = Instance(path_data = arg.instance, num_nodes = arg.num_nodes, edges_to_attach = arg.edges_to_attach, num_flows = arg.num_flows, num_given_flow = arg.num_given_flow, max_route =arg.max_route, min_size = arg.min_size, max_size = arg.max_size, num_items = arg.num_items, num_mon_app = arg.num_mon_app)
	formulation = Compact_Formulation_Mixte(inst)
	Sol_info = formulation.optimize()


	solution = Int_Solution(inst)
	formulation.solution.print_solution()
	#formulation.solution.write(path = arg.out)

	solution.write_solution(Sol_info, path = arg.out_mixte)

	print("Total runtime: %.2f seconds" % (time.time() - start_time))
