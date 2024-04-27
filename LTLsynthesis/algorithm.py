from CustomAALpy.FileHandler import visualize_automaton, save_automaton_to_file, load_automaton_from_file
import logging
from flask import session
from functools import reduce
from LTLsynthesis.prefixTreeBuilder import build_prefix_tree, checkCFSafety
from LTLsynthesis.mealyMachineBuilder import isCrossProductCompatible, generalization_algorithm
from LTLsynthesis.completion_phase import complete_mealy_machine
from LTLsynthesis.utilities import *
from LTLsynthesis.UCBBuilder import UCB,build_UCB

import time

logger = logging.getLogger("misc-logger")

# def build_ucb(LTL_formula, I, O,k):
# 	global ucb, UCBWrapper
# 	logger.debug("Checking if K is appropriate...")
# 	logger.debug("Checking if K is appropriate for LTL")
# 	ts = time.time()
# 	UCBWrapper = UCB(k, LTL_formula, I, O)
# 	k_max = max(int(k * 1.5), 10)
# 	while UCBWrapper.ucb is None:
# 		if k == k_max:
# 			return None, {'msg': 'Specification unsafe for k={}'.format(k), 'retry': True, 'k': k}
# 		if UCBWrapper.internal_error:
# 			return None, {
# 				'msg': 'Internal Server Error: ' + UCBWrapper.error_msg,
# 				'retry': False,
# 				'k': k
# 			}
# 		if UCBWrapper.formula_error:
# 			return None, {
# 				'msg': 'Parsing Formula Error: ' + UCBWrapper.error_msg,
# 				'retry': False,
# 				'k': k
# 			}
# 		logger.debug("LTL Specification is unsafe for k=" + str(k))
# 		k = k + 1
# 		UCBWrapper = UCB(k, LTL_formula, I, O)
# 	logger.debug("LTL Specification is safe for k=" + str(k))

def build_mealy(LTL_formula, I, O, traces, file_name, target, k = 2):	
	global ordered_inputs, bdd_inputs, ucb, UCBWrapper

	### STEP 1 ###

	# Check if K is appropriate
	logger.debug("Checking if K is appropriate...")

	logger.debug("Checking if K is appropriate for LTL")
	ts = time.time()
	k_unsafe = True
	UCBWrapper = UCB(k, LTL_formula, I, O)
	k_max = max(int(k * 1.5), 10)
	while UCBWrapper.ucb is None:
		if k == k_max:
			return None, {'msg': 'Specification unsafe for k={}'.format(k), 'retry': True, 'k': k}
		if UCBWrapper.internal_error:
			return None, {
				'msg': 'Internal Server Error: ' + UCBWrapper.error_msg,
				'retry': False,
				'k': k
			}
		if UCBWrapper.formula_error:
			return None, {
				'msg': 'Parsing Formula Error: ' + UCBWrapper.error_msg,
				'retry': False,
				'k': k
			}
		logger.debug("LTL Specification is unsafe for k=" + str(k))
		k = k + 1
		UCBWrapper = UCB(k, LTL_formula, I, O)
	
	logger.debug("LTL Specification is safe for k=" + str(k))
	bdd_inputs = UCBWrapper.bdd_inputs
	ucb = UCBWrapper.ucb

	# Build Prefix Tree Mealy Machine
	logger.info("Building Prefix Tree...")
	mealy_machine = build_prefix_tree(traces)
	logger.info("Prefix Tree Mealy built")

	# Check if K is appropriate for traces
	logger.debug("Checking if K is appropriate for traces")
	while k_unsafe:
		if k == k_max:
			return None, {'msg': 'Traces unsafe', 'retry': True, 'k': k}
		initialize_counting_function(mealy_machine, UCBWrapper)
		if checkCFSafety(mealy_machine):
			logger.info("Traces is safe for k=" + str(k))
			k_unsafe = False
			break
		k = k + 1
		logger.debug("Traces is unsafe for k=" + str(k))
		UCBWrapper = UCB(k, LTL_formula, I, O)

	logger.info("Choosing K as " + str(k))

	# Loading the target machine if it exists
	target_machine = None
	if len(target) > 0:
		target_machine = load_automaton_from_file(target)
		k_unsafe = True
		while k_unsafe:
			if k == k_max:
				return None, {'msg': 'Target unsafe', 'retry': True, 'k': k}
			initialize_counting_function(target_machine, UCBWrapper)
			if checkCFSafety(target_machine):
				logger.info("Target is safe for k=" + str(k))
				k_unsafe = False
				break
			k = k + 1
			logger.info("Target is unsafe for k=" + str(k))
			UCBWrapper = UCB(k, LTL_formula, I, O)
	
	### STEP 2 ###
	# Merge compatible nodes
	logger.info("Phase 1: Merging compatible nodes in prefix tree...")
	mealy_machine = generalization_algorithm(mealy_machine, sort_merge_cand_by_min_cf, UCBWrapper)
	logger.info("Phase 1: Merge phase is complete")

	save_mealy_machile(mealy_machine, "static/temp_model_files/PreMachine", ['pdf'])
	### STEP 2.5 ###
	# Mark nodes in "pre-machine"
	mark_nodes(mealy_machine)

	logger.info("Phase 2: Completion Phase begins...")
	num_premachine_nodes = len(mealy_machine.states)
	### STEP 3 ###
	# Complete mealy machine
	complete_mealy_machine(mealy_machine, UCBWrapper)
	logger.info("Took {} seconds to complete.".format(time.time() - ts))
	logger.info("Phase 2: Completion Phase done")
	if target_machine is not None:
		isComp, cex = isCrossProductCompatible(target_machine, mealy_machine)
		if not isComp:
			logger.info('Counter example: ' + ".".join(cex))
			traces.append(cex)
			logger.info("Traces: "+ str(traces))

			return build_mealy(
				LTL_formula, 
				I, 
				O, traces, 
				file_name, target, k)
	if target_machine is not None:
		save_mealy_machile(target_machine, "static/temp_model_files/TargetModel", ['svg', 'pdf'])
	save_mealy_machile(mealy_machine, "static/temp_model_files/LearnedModel", ['dot'])
	cleaner_display(mealy_machine, UCBWrapper.ucb)
	save_mealy_machile(mealy_machine, "static/temp_model_files/LearnedModel", ['svg', 'pdf'])
	traces = shorten_traces(traces)
	print_data(target_machine, mealy_machine, num_premachine_nodes, traces, k, UCBWrapper)
	return mealy_machine, {'traces': traces, 'num_premachine_nodes': num_premachine_nodes, 'k': k}

def display_mealy_machine(mealy_machine, file_name, file_type="pdf"):
	visualize_automaton(
		mealy_machine,
		path="examples/" + file_name + '_' + str(session['number']),
		file_type="pdf"
	)
def save_mealy_machile(mealy_machine, file_name, file_type = ['dot']):
	for type in file_type:
		save_automaton_to_file(
			mealy_machine,
			file_type=type,
			path=file_name + '_' + str(session['number'])
		)