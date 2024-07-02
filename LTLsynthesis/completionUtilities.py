import logging
from LTLsynthesis.utilities import bdd_to_str, contains, initialize_counting_function, checkCFSafety, sort_counting_functions

logger = logging.getLogger('completion-logger')

def subsume_to_antichain_heads(mealy_machine, UCBWrapper):
	for state in mealy_machine.states:
		subsume_to_antichain_head(state, UCBWrapper)

def subsume_to_antichain_head(state, UCBWrapper):
	for head in UCBWrapper.antichain_heads:
		if contains (state.counting_function, head):
			state.counting_function = head
			break

def sort_list(item_1, item_2):
	return sort_counting_functions(item_1[1], item_2[1])

def sort_nodes(node_1, node_2):
	return sort_counting_functions(node_1.counting_function, node_2.counting_function)

def check_state_subsumed(state, current_state, i_bdd, UCBWrapper):
	i_str = bdd_to_str(i_bdd)
	for o_bdd in UCBWrapper.bdd_outputs:
		cf = UCBWrapper.get_transition_state(current_state.counting_function, i_bdd & o_bdd)
		o_str = bdd_to_str(o_bdd)
		if contains(cf, state.counting_function):
			logger.debug("CF subsumed by node..")
			logger.debug("Counting function of transition: " + str(cf))
			logger.debug("Counting function of next state: " + str(state.counting_function))
			logger.debug("Creating edge: {} + {}/{} -> {}".format(
				current_state.state_id,
				i_str,
				o_str,
				state.state_id))
			current_state.transitions[i_str] = state
			current_state.output_fun[i_str] = o_str
			return True
	return False

def check_state_mergeable(state, current_state, i_bdd, mealy_machine, UCBWrapper):
	i_str = bdd_to_str(i_bdd)
	for o_bdd in UCBWrapper.bdd_outputs:
		o_str = bdd_to_str(o_bdd)
		current_state.transitions[i_str] = state
		current_state.output_fun[i_str] = o_str
		initialize_counting_function(mealy_machine, UCBWrapper)
		if checkCFSafety(mealy_machine,UCBWrapper):
			cf = UCBWrapper.get_transition_state(current_state.counting_function, i_bdd & o_bdd)
			logger.debug("Merging with node..")
			logger.debug("Counting function of transition: " + str(cf))
			logger.debug("Counting function of next state: " + str(state.counting_function))
			logger.debug("Creating edge: {} + {}/{} -> {}".format(
				current_state.state_id,
				i_str,
				o_str,
				state.state_id))
			return True
		del current_state.transitions[i_str]
		del current_state.output_fun[i_str]
	return False