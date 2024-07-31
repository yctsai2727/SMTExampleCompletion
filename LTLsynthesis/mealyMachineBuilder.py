from aalpy.automata import MealyState, MealyMachine
from LTLsynthesis.utilities import *
from LTLsynthesis.prefixTreeBuilder import *
import copy, functools, logging

logger = logging.getLogger("merge-phase-logger")

def isCrossProductCompatible(m1: MealyMachine, m2: MealyMachine):
	# Building Cross Product
	ts = time.time()

	root = (m1.initial_state, m2.initial_state)
	state_queue = [(root, [])]
	visited_states = set()
	while len(state_queue) > 0:
		state, trace = state_queue[0]
		state_queue = state_queue[1:]
		s1, s2 = state
		visited_states.add(s1.state_id + " & " + s2.state_id)
		for i in s1.transitions.keys():
			if i in s2.transitions.keys():
				trace_ = trace + [i, s1.output_fun[i]]
				transition_state = (s1.transitions[i], s2.transitions[i])
				s3, s4 = transition_state
				if s3.state_id + " & " + s4.state_id not in visited_states:
					if s1.output_fun[i] != s2.output_fun[i]:
						logger.debug("Checking compatibilty takes: " + str(time.time() - ts))
						logger.debug("Obtained counter-example: " + str(trace_))
						return [False, trace_]
					state_queue.append((transition_state, trace_))
	logger.debug("Checking compatibilty takes : " + str(time.time() - ts))
	return [True, []]

def generalization_algorithm(premealy_machine, merging_strategy, UCBWrapper):
	states = premealy_machine.states
	states.sort(key=lambda s: s.rank)

	rank_state_dict = {}
	for s in states:
		rank_state_dict[s.rank] = s.rank
	exclude_pairs = []
	i = 0
	for i in range(len(states)):
		s = get_state_from_rank(rank_state_dict[i], states)
		logger.debug("Rant state dict: " + str(rank_state_dict))
		merge_pairs = get_compatible_nodes(states, s, exclude_pairs)
		merge_pairs = sorted(merge_pairs, key=functools.cmp_to_key(merging_strategy))

		while (len(merge_pairs) > 0):
			merge_pair = merge_pairs[0]
			merge_pairs = merge_pairs[1:]
			if is_excluded(merge_pair, exclude_pairs):
				continue
			ts = time.time()
			premealy_machine, exclude_pairs, rank_state_dict, isMerged = merge_compatible_nodes(
				merge_pair, exclude_pairs, 
				rank_state_dict, premealy_machine, UCBWrapper)
			logger.debug("Merge took {} time".format(time.time()-ts))
			if isMerged:
				logger.debug("Merged {} into {}".format(merge_pair[1].state_id, 
					merge_pair[0].state_id))
				logger.debug("Merged {} into {}".format(merge_pair[1].rank, 
					merge_pair[0].rank))
				states = premealy_machine.states
				states.sort(key=lambda s: s.rank)
				logger.debug("# of states: {}".format(len(states)))
				break
			logger.debug("Merge {} and {} failed".format(merge_pair[0].state_id,
				merge_pair[1].state_id))
			logger.debug("Merge {} and {} failed".format(merge_pair[0].rank,
				merge_pair[1].rank))
	return premealy_machine

def get_compatible_nodes(states, s, exclude=[]):
	pair_nodes = []
	for s_ in states:
		logger.debug("Checking compatibilty with " + s.state_id)
		if s == s_:
			continue
		if is_excluded([s, s_], exclude):
			logger.debug("Excluding {} and {}".format(s, s_))
			continue
		if s.rank < min(s_.equivalent_states):
			continue
		m1 = MealyMachine(s, states)
		m2 = MealyMachine(s_, states)
		isComp, cex = isCrossProductCompatible(m1, m2)
		if isComp:
			pair_nodes.append([s, s_])
		else:
			logger.debug("Counter example for merge: " + ".".join(cex))
	logger.debug("Returning {} pairs of potentially mergeable nodes".format(len(pair_nodes)))
	# pair_nodes = sorted(pair_nodes, key=lambda x: sort_nodes_by_cf_diff(x[0], x[1]))
	return pair_nodes

def merge_compatible_nodes(pair, exclude_pairs, rank_state_dict,
	mealy_machine, UCBWrapper):
	old_mealy_machine = copy.deepcopy(mealy_machine)
	for st in old_mealy_machine.states:
		st.counting_function = get_state_from_id(st.state_id,mealy_machine.states).counting_function
		st.rank = get_state_from_id(st.state_id,mealy_machine.states).rank
		st.equivalent_states = get_state_from_id(st.state_id,mealy_machine.states).equivalent_states
	old_rank_state_dict = copy.deepcopy(rank_state_dict)
	merged = False
	pair[0] = get_state_from_rank(
		rank_state_dict[pair[0].rank],
		mealy_machine.states)
	pair[1] = get_state_from_rank(
		rank_state_dict[pair[1].rank],
		mealy_machine.states)
	mealy_machine = mergeAndPropogate(
		pair[0], pair[1], rank_state_dict, mealy_machine)
	if mealy_machine is None:
		rank_state_dict = old_rank_state_dict
		mealy_machine = old_mealy_machine
		exclude_pairs.append(pair)
	else:
		initialize_counting_function(mealy_machine, UCBWrapper)
		if not checkCFSafety(mealy_machine,UCBWrapper):
			mealy_machine = old_mealy_machine
			rank_state_dict = old_rank_state_dict
			exclude_pairs.append(pair)
		else:
			exclude_pairs = []
			merged = True
	return [mealy_machine, exclude_pairs, rank_state_dict, merged]

def mergeAndPropogate(m1: MealyState, m2: MealyState,
	rank_state_dict, mealy_machine: MealyMachine):
	propogate_queue = [[m1, m2]]
	while len(propogate_queue) > 0:
		s1, s2 = propogate_queue[0]
		logger.debug("Commence merge of {} and {}:".format(s1.state_id, s2.state_id))
		logger.debug("Commence merge of {} and {}:".format(s1.rank, s2.rank))
		propogate_queue = propogate_queue[1:]
		while s1 not in mealy_machine.states:
			logger.debug(s1.state_id + " has been deleted.")
			logger.debug(str(s1.rank )+ " has been deleted.")
			s1 = get_state_from_rank(rank_state_dict[s1.rank],
				mealy_machine.states)
		while s2 not in mealy_machine.states:
			logger.debug(s2.state_id + " has been deleted.")
			logger.debug(str(s2.rank) + " has been deleted.")
			s2 = get_state_from_rank(rank_state_dict[s2.rank],
				mealy_machine.states)
		if s1.rank == s2.rank:
			logger.debug("Merge of the same states should be skipped")
			continue
		logger.debug("Commence merge of {} and {}:".format(s1.rank, s2.rank))
		mergedStuff = mergeOperation(s1, s2, mealy_machine)
		if mergedStuff is not None:
			logger.debug("Adding to queue:")
			for pair in mergedStuff:
				logger.debug("[{}, {}]".format(pair[0].state_id, pair[1].state_id))
				logger.debug("[{}, {}]".format(pair[0].rank, pair[1].rank))
			propogate_queue.extend(mergedStuff)
			rank_state_dict[s2.rank] = s1.rank
			equivalent_states = s1.equivalent_states.union(s2.equivalent_states)
			s1.equivalent_states = equivalent_states
			s2.equivalent_states = equivalent_states
			logger.debug("Deleting node " + str(s2.rank))
			mealy_machine.states.remove(s2)
		else:
			logger.debug("Merge failed! Exiting..")
			return None
		if s2 == mealy_machine.initial_state:
			mealy_machine.initial_state = s1
	return mealy_machine


def mergeOperation(s1: MealyState, s2: MealyState, mealy_machine: MealyMachine):
	merge_next = []
	for state in mealy_machine.states:
		for i in state.transitions.keys():
			if state.transitions[i] == s2:
				state.transitions[i] = s1
	for i in s2.transitions.keys():
		if i in s1.transitions.keys():
			if s1.output_fun[i] == s2.output_fun[i]:
				merge_next.append([s1.transitions[i], s2.transitions[i]])
			else:
				logger.debug("Output of transition differs here: {} ->{}/{} and {} ->{}/{}".format(
					s1.state_id, i, s1.output_fun[i], s2.state_id, i, s2.output_fun[i]))
				return None
		else:
			s1.transitions[i] = s2.transitions[i]
			s1.output_fun[i] = s2.output_fun[i]
	return merge_next
