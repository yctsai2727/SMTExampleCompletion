from aalpy.automata import MealyState, MealyMachine
import functools
from LTLsynthesis.utilities import *
from LTLsynthesis.completionUtilities import check_state_subsumed, check_state_mergeable, subsume_to_antichain_heads, subsume_to_antichain_head, sort_nodes, sort_list
import logging

logger = logging.getLogger('completion-phase-logger')

def completionStrategy(candidate_nodes, m, i_bdd, mealy_machine, UCBWrapper, addSpuriousEdge=True):
	# Checking if transition already exists
	i_str = bdd_to_str(i_bdd)
	logger.debug("Checking potential hole {}, {}".format(m.state_id, i_str))
	if i_str in m.transitions.keys():
		next_state = m.transitions[i_str]
		logger.debug("Transition already exists: {} , {} -> {}. Not a hole!".format(
			m.state_id, i_str, next_state.state_id))
		return next_state
	
	# Checking if there exists output where cf is subsumed by premachine state
	logger.debug("Checking if there exists output where cf is subsumed by premachine/newly created state state")
	for state in candidate_nodes:
		if check_state_subsumed(state, m, i_bdd, UCBWrapper):
			return state

	if addSpuriousEdge:
		# Checking if spurious edge to premachine state is possible
		logger.debug("Checking if spurious edge to premachine state is possible")
		for state in candidate_nodes:
			if check_state_mergeable(state, m, i_bdd, mealy_machine, UCBWrapper):
				return state
	return None

def createNewState(m, i_bdd, minimize_controller, UCBWrapper):
	# Initializing list of [counting functions, potential outputs].
	cf_o_list = []
	for o_bdd in UCBWrapper.bdd_outputs:
		cf = UCBWrapper.get_transition_state(m.counting_function, i_bdd & o_bdd)
		cf_o_list.append([o_bdd, cf])
	
	# Sorting list by counting functions 
	cf_o_list = sorted(cf_o_list, key=functools.cmp_to_key(sort_list))	
	
	for item in cf_o_list:
		o_bdd, cf = item
		if not UCBWrapper.is_safe(cf):
			continue
		i_str = bdd_to_str(i_bdd)
		o_str = bdd_to_str(o_bdd)
		
		next_state = MealyState("{}({}.{})".format(m.state_id, i_str, o_str))
		next_state.counting_function = cf
		next_state.special_node = False

		m.transitions[i_str] = next_state
		m.output_fun[i_str] = o_str

		# If minimize_controller flag is set, new state counting function abstracted 
		# to one of the antichain head which it is subsumed by
		if minimize_controller:
			subsume_to_antichain_head(next_state, UCBWrapper)

		logger.debug("Creating new state with state id: " + next_state.state_id)
		logger.debug("Counting function of transition: " + str(next_state.counting_function))
		logger.debug("Creating edge: {} + {}/{} -> {}".format(
			m.state_id,
			i_str,
			o_str,
			next_state.state_id))
		
		return next_state
	return None

def complete_mealy_machine(mealy_machine, UCBWrapper, minimize_controller=False, use_premachine_nodes=True):
	newly_created_nodes = []
	premachine_nodes = []

	if minimize_controller and use_premachine_nodes:
		subsume_to_antichain_heads(mealy_machine, UCBWrapper)
	
	logger.debug("Creating lists of premachine nodes")
	for state in mealy_machine.states:
		if state.special_node:
			premachine_nodes.append(state)
		else:
			newly_created_nodes.append(state)
	logger.info("# of premachine nodes: " + str(len(premachine_nodes)))
	# Sorting premachine nodes by their counting functions
	premachine_nodes = sorted(premachine_nodes, key=functools.cmp_to_key(sort_nodes))

	# State_Queue keeps track of list of states yet to be visited 
	# (unvisited states of current state's edges added to queue)
	state_queue = [mealy_machine.initial_state]

	# visited_states keeps track of list of states visited or in queue.
	visited_states = [mealy_machine.initial_state]

	# While loop visiting states of mealy machine breadth-first
	while len(state_queue) > 0:
		current_state = state_queue.pop(0) # dequeueing
		
		# initializing the transition state to None
		next_state = None

		logger.debug("Checking state: " + str(current_state.state_id))

		# checking for legitimate states (Maybe can be written better)
		if current_state == None:
			continue

		# checking for a (current_state, i_bdd) "hole"
		for i_bdd in UCBWrapper.bdd_inputs:
			logger.debug("Counting function of origin state: " + str(current_state.counting_function))
			candidate_nodes = premachine_nodes + newly_created_nodes
			
			if not use_premachine_nodes:
				candidate_nodes = newly_created_nodes
			
			next_state = completionStrategy(
				candidate_nodes,
				current_state,
				i_bdd,
				mealy_machine,
				UCBWrapper,
				not minimize_controller
			)

			if (next_state is not None):
				if (next_state not in visited_states):
					state_queue.append(next_state)
					visited_states.append(next_state)
				continue

			initialize_counting_function(mealy_machine, UCBWrapper)
			if not checkCFSafety(mealy_machine):
				logger.warning("This mealy machine is unsuitable")
				return mealy_machine

			logger.debug("Will have to create a new state")
			
			next_state = createNewState(current_state, i_bdd, minimize_controller, UCBWrapper)

			if next_state is None:
				current_state.color = "black"
				return None

			# Adding newly created state to mealy machine
			mealy_machine.states.append(next_state)

			# Adding newly created state to list of newly created nodes
			newly_created_nodes.append(next_state)

			# Adding newly created state to state queue and visited nodes
			state_queue.append(next_state)
			visited_states.append(next_state)
			
			# sorting the newly created nodes
			newly_created_nodes = sorted(newly_created_nodes, key=functools.cmp_to_key(sort_nodes))

