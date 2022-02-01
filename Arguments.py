import argparse
import os
import sys
import time

#from instance_heuristic import Instance
#from solution_heuristic import Int_Solution
#from int_ils import Int_Heuristic
#type=argparse.FileType('r')


def dir_path(path):
		if os.path.isdir(path):
			return path
		else:
			raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")


def file_path(file):
		if os.path.isfile(file):
			return file
		else:
			raise argparse.ArgumentTypeError(f"readable_file:{file} is not a valid path")

class Arguments:
	"""
	Let the user enter the argument via command line.
	"""
	def __init__(self):
		self.parser = argparse.ArgumentParser()
		#self.instance = self.parser.add_argument('instance', type=argparse.FileType('r'), default=sys.stdin, metavar='PATH', help="instances Directory")
		self.parser.add_argument('instance', type=dir_path,  help="instances Directory")
		self.parser.add_argument("num_nodes", type=int,  help="Number of Nodes")
		self.parser.add_argument("num_flows", type=int,  help="Number of Network Flows")
		self.parser.add_argument("num_items", type=int,  help="Number of Telemetry Items")
		self.parser.add_argument("num_mon_app", type=int,  help="Number of Monitoring Applications")
		self.parser.add_argument('num_given_flow', type=int, nargs='?', default=80, help="pourcentage of given network flows")
		self.parser.add_argument('min_size', type=int, nargs='?', default=10, help="minimum size of network flows")
		self.parser.add_argument('max_size', type=int, nargs='?', default=40, help="maximum size of network flows")
		# Optional positional argument
		
		self.parser.add_argument('max_route', type=int, nargs='?', default=9, help="Maximal hopes in a route")
		self.parser.add_argument('edges_to_attach', type=int, nargs='?', default=2, help="Edges to attach")
		#parser.add_argument('out', type=int, nargs='?', default=80, help='pourcentage of given network flows')
		#self.parser.add_argument("out", type=argparse.FileType('w'), nargs='?', default=sys.stdout, help="Output File path")
		#self.parser.add_argument("out", type=argparse.FileType('w'), nargs='?', default=os.path.join("./solutions",bbb), help="Output File path")
		#os.path.join("solutions", "heuristic" + prefix + os.path.basename(argv[2])) + "_" + str(self.edges_to_attach) + "_" + argv[4] + "_" + argv[5]
		#parser.add_argument("out", type=argparse.FileType('w',encoding=DEFAULT_ENCODING), nargs='?', default="./solutions", help="Output File path")
		self.args = self.parser.parse_args()
		self.instance = self.args.instance
		self.num_nodes = self.args.num_nodes
		self.num_flows = self.args.num_flows
		self.num_items = self.args.num_items
		self.num_mon_app = self.args.num_mon_app
		self.min_size = self.args.min_size
		self.max_size = self.args.max_size 
		self.num_given_flow = self.args.num_given_flow
		self.max_route = self.args.max_route
		self.edges_to_attach = self.args.edges_to_attach
		#self.out = self.args.out
		self.out_her = "./solutions/Heuristic" + "_" + str(self.edges_to_attach) + "_" + str(self.num_items) + "_" + str(self.num_mon_app)
		self.out_model = "./solutions/Model" + "_" + str(self.edges_to_attach) + "_" + str(self.num_items) + "_" + str(self.num_mon_app)
		self.out_mixte = "./solutions/Mixte" + "_" + str(self.edges_to_attach) + "_" + str(self.num_items) + "_" + str(self.num_mon_app) + "_" + str(self.num_given_flow)
		




	
	def dir_path(path):
		if os.path.isdir(path):
			return path
		else:
			raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")
		
		
	
# def Arguments() -> argparse.Namespace:
# 	parser = argparse.ArgumentParser()
# 	#parser.add_argument('instance', type=argparse.FileType('r'),  help="instances Directory")
# 	parser.add_argument('instance', type=dir_path,  help="instances Directory")
# 	parser.add_argument("num_nodes", type=int,  help="Number of Nodes")
# 	parser.add_argument("num_flows", type=int,  help="Number of Network Flows")
# 	parser.add_argument("num_items", type=int,  help="Number of Telemetry Items")
# 	parser.add_argument("num_mon_app", type=int,  help="Number of Monitoring Applications")
# 	parser.add_argument('min_size', type=int, nargs='?', default=10, help="minimum size of network flows")
# 	parser.add_argument('max_size', type=int, nargs='?', default=40, help="maximum size of network flows")
# 	# Optional positional argument
# 	#parser.add_argument('%', type=int, nargs='?', default=80, help="pourcentage of given network flows")
# 	#parser.add_argument('max_route', type=int, nargs='?', default=80, help="Maximal hopes in a route")
# 	parser.add_argument('edges_to_attach', type=int, nargs='?', default=2, help="Edges to attach")
# 	#parser.add_argument('out', type=int, nargs='?', default=80, help='pourcentage of given network flows')
# 	parser.add_argument("out", type=argparse.FileType('w'), nargs='?', default=sys.stdout, help="Output File path")
# 	#parser.add_argument("out", type=argparse.FileType('w',encoding=DEFAULT_ENCODING), nargs='?', default="./solutions", help="Output File path")
	







""" if __name__ == "__main__":
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



	solution = Int_Solution(inst)
	#solution.write(sol_info, path = arg.out)
	sol_info_heur = heur_full_solution_save + [round((time.time() - start_time),2)]
	solution.write_solution(sol_info_heur, path = arg.out)

	print("Total runtime: %.2f seconds" % (time.time() - start_time)) """
