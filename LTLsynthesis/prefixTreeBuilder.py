from aalpy.automata import MealyState, MealyMachine
from LTLsynthesis.utilities import *
import LTLsynthesis.algorithm
import re

logger = logging.getLogger("prefix-tree-logger")

def expand_symbolic_traces(traces):
	new_traces = []
	for trace in traces:
		new_traces.extend(expand_trace(trace))
	return new_traces

def expand_trace(trace):
	bdd_inputs = LTLsynthesis.algorithm.bdd_inputs
	ucb = LTLsynthesis.algorithm.ucb
	expanded_traces = []
	for i in range(len(trace)-2, -1, -2):
		bdd_i = str_to_bdd(trace[i], ucb)
		new_traces = []
		for inp in bdd_inputs:
			if bdd_i & inp != buddy.bddfalse:
				str_i = bdd_to_str(inp)
				if len(expanded_traces) > 0:
					for t in expanded_traces:
						new_traces.append([str_i, trace[i+1]] + t)
				else:
					new_traces.append([str_i, trace[i+1]])
		expanded_traces = new_traces
	return expanded_traces

def generated_prefixes(traces):
	prefixes = []
	for trace in traces:
		for i in range(0, len(trace)-1, 2):
			prefixes.append(trace[0:(i+2)])
			logger.debug("Extended trace: " + str(trace[0:(i+2)]))
	return list(set(list(map(lambda trace: '.'.join(trace), prefixes))))

def build_prefix_tree(traces):
	# BDD inputs
	bdd_inputs = LTLsynthesis.algorithm.bdd_inputs
	# Expanding symbolic traces
	traces = expand_symbolic_traces(traces)
	# Generating prefix to make traces prefix-complete 
	traces = generated_prefixes(traces)
	# Sorting traces by input
	traces = list(map(lambda trace: trace.split('.'), traces))
	ordered_inputs = list(map(lambda prop: bdd_to_str(prop), bdd_inputs))
	traces = sorted(traces, key=lambda trace: trace_to_int_function(trace, ordered_inputs))
	
	# Building the prefix tree
	root = MealyState('()')
	# rank marks the position of the node in the prefix tree (BFS)
	root.rank = 0
	root.equivalent_states = {root.rank}
	# ordered list of inputs
	root.ordered_inputs = ordered_inputs
	
	list_nodes = [root]
	for trace in traces:
		current_node = root
		for i in range(0, len(trace)-1, 2):
			if trace[i] in current_node.transitions.keys():
				current_node = current_node.transitions[trace[i]]
			else:
				new_node = MealyState(current_node.state_id + \
					"({}.{})".format(trace[i],trace[i+1]))
				current_node.transitions[trace[i]] = new_node
				current_node.output_fun[trace[i]] = trace[i+1]
				current_node = new_node
				new_node.rank = len(list_nodes)
				new_node.equivalent_states = {new_node.rank}
				new_node.ordered_inputs = ordered_inputs
				list_nodes.append(new_node)
	mealyTree = MealyMachine(root, list_nodes)
	return mealyTree

def sort_nodes_by_cf_diff(node_1, node_2):
	return sum(list(abs(node_1.counting_function[i] - node_2.counting_function[i]) \
		for i in range(len(node_1.counting_function))))*-1

def sort_nodes_by_traces(node_1, node_2):
	logger.debug("Traces coming from sort nodes by traces: {} and {} where {} and {} are original".format(
		re.sub('[^A-Za-z0-9\.\&\!\ ]+', '', node_1.state_id).split('.'),
		re.sub('[^A-Za-z0-9\.\&\!\ ]+', '', node_2.state_id).split('.'),
		node_1.state_id, node_2.state_id))
	node_1_id = trace_to_int_function(
		re.sub('[^A-Za-z0-9\.\&\!\ ]+', '.', node_1.state_id).split('.'), node_1.ordered_inputs)
	node_2_id = trace_to_int_function(re.sub('[^A-Za-z0-9\.\&\!\ ]+', '.', node_2.state_id).split('.'), node_1.ordered_inputs)

	logger.debug("Traces converted to: {} and {}".format(node_1_id, node_2_id))

	if node_1_id < node_2_id:
		if node_1.rank > node_2.rank:
			logger.warning("Hypothesis is wrong")
		return -1
	elif node_1_id == node_2_id:
		logger.warning("Why is this happening?")
		return 0
	else:
		if node_1.rank < node_2.rank:
			logger.warning("Hypothesis is wrong")
		return 1
