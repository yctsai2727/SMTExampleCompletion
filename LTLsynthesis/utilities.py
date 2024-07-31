import spot, logging
from aalpy.automata import MealyState, MealyMachine
import buddy
import itertools
#from LTLsynthesis.algorithm import UCBwrapper
import time, re

logger = logging.getLogger('misc-logger')


def trace_to_int_function(trace, ordered_inputs):
	logger.debug("Trace to int function: " + str(trace))
	input_filtered_trace = list(filter(
		lambda proposition: proposition in ordered_inputs, trace))

	if len(input_filtered_trace) == 0:
		return 0
	return int(''.join(map(lambda input_proposition: str(
		ordered_inputs.index(input_proposition)+1),input_filtered_trace)))

def print_data(target_machine, mealy_machine, num_premachine_nodes, traces, k, UCBWrapper):
	print(''.join(['-']*20))
	print("DATA: ")
	if target_machine is not None:
		print("# of target nodes: " + str(len(target_machine.states)))
	print("# of Pre-machine nodes: " + str(num_premachine_nodes))
	print("# of states added by completion: " + str(len(mealy_machine.states) - num_premachine_nodes))
	print("Min k value: " + str(k))
	print("Final machine required traces: " + str(traces))
	print("# of traces required: " + str(len(traces)))
	cleaner_display(mealy_machine, UCBWrapper.ucb)
	if len(traces) > 1:
		traces = list(itertools.chain(*traces))
		print(traces)
		print("Sum of length of traces: " + str(len(".".join(traces))))
	elif len(traces) == 1:
		print("Sum of length of traces: " + str(len(".".join(traces[0]))))

def initialize_counting_function(mealy, UCBWrapper):
	for state in mealy.states:
		state.counting_function = [-1]*UCBWrapper.num_states
	mealy.initial_state.counting_function[UCBWrapper.ucb.get_init_state_number()] = 0

def checkCFSafety(mealy: MealyMachine,UCBWrapper):
	ts = time.time()
	#UCBWrapper = LTLsynthesis.algorithm.UCBWrapper
	# Checking CF Safety of the new Mealy Machine
	if not UCBWrapper.is_safe(mealy.initial_state.counting_function):
		return False
	
	edges_to_visit = []

	for i in mealy.initial_state.transitions.keys():
		edges_to_visit.append([mealy.initial_state, i, 
			i + "." + mealy.initial_state.output_fun[i]])
	
	count = 0
	while len(edges_to_visit) > 0:
		state, i, trace = edges_to_visit[0]
		target_state = state.transitions[i]
		edges_to_visit = edges_to_visit[1:]
		#logger.info(type(state))
		f1 = state.counting_function
		f2 = target_state.counting_function

		i_bdd = str_to_bdd(i, UCBWrapper.ucb)
		o_bdd = str_to_bdd(state.output_fun[i], UCBWrapper.ucb)

		f_ = lowestUpperBound(UCBWrapper.get_transition_state(f1, i_bdd & o_bdd), f2)

		if not UCBWrapper.is_safe(f_):
			logger.debug("checking safety took {} seconds".format(time.time()-ts))
			return False
		if contains(f2, f_) and f_ != f2:
			target_state.counting_function = f_;
			for j in target_state.transitions.keys():
				edges_to_visit.append([target_state, j, 
					"{}.{}.{}".format(trace, j, target_state.output_fun[j])])
	logger.debug("Checking safety took {} seconds".format(time.time()-ts))
	return True

def get_state_from_id(state_id, state_list):
	for state in state_list:
		if state.state_id == state_id:
			return state
	return None

def get_state_from_rank(rank, state_list):
	for state in state_list:
		logger.debug("State rank in states: " + str(state.rank))
		logger.debug("Equivalent rank states: " + str(state.equivalent_states))
		if rank in state.equivalent_states:
			return state
	return None

def get_index_from_id(state_id, state_list):
	for i, x in enumerate(state_list):
		if x.state_id == state_id:
			return i
	return None

def bdd_to_str(bdd_arg):
	return str(spot.bdd_to_formula(bdd_arg))

def str_to_bdd(bdd_str, ucb):
	return spot.formula_to_bdd(bdd_str, ucb.get_dict(), None)

def contains(vector_1, vector_2):
	if vector_1 == None or vector_2 == None:
		return False
	for i in range(len(vector_1)):
		if vector_1[i] > vector_2[i]:
			return False
	return True

def sort_counting_functions(cf_1, cf_2):
	if contains(cf_1, cf_2):
		return -1
	elif contains(cf_2, cf_1):
		return 1
	elif max(cf_1) < max(cf_2):
		return -1
	elif max(cf_1) > max(cf_2):
		return 1
	elif (sum(cf_1)) < (sum(cf_2)):
		return -1
	elif (sum(cf_1)) > (sum(cf_2)):
		return 1
	else:
		return 0

def lowestUpperBound(vector_1, vector_2):
	vector = []
	for i in range(len(vector_1)):
		if vector_1[i] > vector_2[i]:
			vector.append(vector_1[i])
		else:
			vector.append(vector_2[i])
	return vector

def mark_nodes(mealy_machine):
	for state in mealy_machine.states:
		state.special_node = True
		state.premachine_transitions = list(state.transitions.keys())
		logger.info(state.counting_function)

def cleaner_display(mealy_machine, ucb):
	for state in mealy_machine.states:
		grouped_transitions = {}
		for i, output_state in state.transitions.items():
			grouped_transitions[output_state] = [i] if output_state not in grouped_transitions.keys() else grouped_transitions[output_state] + [i]

		to_remove = []
		for output_state, input_set in grouped_transitions.items():
			for o in set(state.output_fun.values()):
				bdd_max = buddy.bddfalse
				str_inp = ""
				common_inp = []
				for i in input_set:
					if state.output_fun[i] == o:
						bdd_max = bdd_max | str_to_bdd(i, ucb)
						str_inp = str_inp + i + " + "
						common_inp.append(i)
				i_max = bdd_to_str(bdd_max)
				if i_max != "0" and len(common_inp) > 1:
					logger.debug("For the state, output {} {}: {} gives {}".format(
						state.state_id, o, '+'.join(common_inp), i_max))
					to_remove.extend(common_inp)
					state.transitions[i_max] = output_state
					state.output_fun[i_max] = o
		for i in to_remove:
			if i in state.transitions.keys():
				del state.transitions[i]

def shorten_traces(traces):
	traces = list(map(lambda trace: ".".join(trace), traces))
	traces.sort(key=lambda t: len(t))
	shortened_traces = []
	n = len(traces)
	for i in range(n):
		trace = traces[i]
		shouldAdd = True
		for j in range(i+1, n):
			if traces[j].startswith(trace):
				shouldAdd = False
				break
		if shouldAdd:
			shortened_traces.append(trace.split('.'))
	return shortened_traces

def sort_merge_cand_by_min_cf(node_pair_1, node_pair_2):
	node_1, node_2 = node_pair_1
	node_3, node_4 = node_pair_2

	if node_1 == node_3:
		return sort_counting_functions(node_2.counting_function, node_4.counting_function)
	logger.debug("Traces coming from sort merge cand: {} and {} where {} and {} are original".format(
		re.sub('[^A-Za-z0-9\.\&\!\ ]+', '.', node_1.state_id).split('.'),
		re.sub('[^A-Za-z0-9\.\&\!\ ]+', '.', node_3.state_id).split('.'),
		node_1.state_id, node_3.state_id))
	node_1_id = trace_to_int_function(filter(lambda x: len(x) > 0, 
		re.sub('[^A-Za-z0-9\.\&\!\ ]+', '.', node_1.state_id).split('.')), node_1.ordered_inputs)
	node_3_id = trace_to_int_function(filter(lambda x: len(x) > 0,
		re.sub('[^A-Za-z0-9\.\&\!\ ]+', '.', node_3.state_id).split('.')), node_3.ordered_inputs)
	if node_1_id == node_3_id:
		logger.error("What is happening?")
		return sort_counting_functions(node_2.counting_function, node_4.counting_function)
	elif node_1_id < node_3_id:
		return -1
	else:
		return 1

def is_excluded(pair, exclude_pairs):
	pair1 = '{}.{}'.format(pair[0].state_id, pair[1].state_id)
	pair2 = '{}.{}'.format(pair[1].state_id, pair[0].state_id)
	exclude_pairs = list(map(lambda x: '{}.{}'.format(x[0].state_id, x[1].state_id), exclude_pairs))
	return pair1 in exclude_pairs or pair2 in exclude_pairs