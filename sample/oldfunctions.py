from UCBBuilder import UCB
from aalpy.automata import MealyState, MealyMachine
import spot
import buddy

class TrieNode(object):
	"""docstring for Node"""
	def __init__(self, input_word, output_word, parent=None, 
		isEndOfWord=False, counting_function=None):
		super(TrieNode, self).__init__()
		self.i = input_word
		self.o = output_word
		self.i_bdd = None
		self.o_bdd = None
		self.counting_function = counting_function
		self.isEndOfWord = False
		self.parent = parent
		self.children = []
		self.repr =  "[" + self.i + "].[" + self.o + "]"
		if self.parent != None:
			self.repr = str(self.parent) + "." + self.repr
			self.level = self.parent.level + 1
		else:
			self.level = 0
	
	def add_child(self, child):
		self.children.append(child)

	def __str__(self):
		return self.repr

	def __repr__(self):
		return self.repr

def bdd_to_str(bdd_arg):
	return str(spot.bdd_to_formula(bdd_arg))

def shorten_prefix_tree():
	for node_1 in nodes:
		for node_2 in nodes:
			if str(node_1) == str(node_2):
				continue
			if node_1.counting_function == node_2.counting_function:
				if check_node_compatibility(node_1, node_2):
					if node_2.level > node_1.level:
						print("Merging {} with {}".format(node_1, node_2)) 
						merge(node_label_dict[str(node_2)], 
							node_label_dict[str(node_1)])
					else:
						print("Merging {} with {}".format(node_2, node_1)) 
						merge(node_label_dict[str(node_1)], 
							node_label_dict[str(node_2)])


def merge(state_1, state_2):
	if state_1 == state_2:
		return
	for i in state_2.transitions.keys():
		if i in state_1.transitions.keys():
			merge(state_1.transitions[i], state_2.transitions[i])
		else:
			state_1.transitions[i] = state_2.transitions[i]
			state_1.output_fun[i] = state_2.output_fun[i]
	for state in states:
		for i in state.transitions.keys():
			if state.transitions[i] == state_2:
				state.transitions[i] = state_1
		
def build_prefix_tree(words):
	root = TrieNode('', '')
	list_nodes = [root]
	for word in words:
		current_node = root
		for index in range(0, len(word)-1, 2):
			foundChild = False
			for child in current_node.children:
				if child.i == word[index] and child.o == word[index+1]:
					current_node = child
					foundChild = True
					break
			if foundChild:
				continue
			else:
				new_node = TrieNode(word[index], word[index+1], current_node)
				current_node.add_child(new_node)
				current_node = new_node
				list_nodes.append(new_node)
		current_node.isEndOfWord = True
	return [root, list_nodes]

def build_mealy_prefix_tree(words):
	root = MealyState('')
	list_nodes = [root]
	for word in words:
		current_node = root
		for i in range(0, len(word)-1, 2):
			if word[i] in current_node.transitions.keys():
				current_node = current_node.transitions[word[i]]
			else:
				new_node = MealyState(current_node.state_id + word[i] + word[i+1])
				current_node.transitions[word[i]] = new_node
				current_node.output_fun[word[i]] = word[i+1]
				current_node = new_node
				list_nodes.append(new_node)
		current_node.isEndOfWord = True
	mealyTree = MealyMachine(root, list_nodes)
	return mealyTree

def set_counting_function(node, machine):
	for n in node.children:
		n.i_bdd = spot.formula_to_bdd(n.i, machine.ucb.get_dict(), None)
		n.o_bdd = spot.formula_to_bdd(n.o, machine.ucb.get_dict(), None)
		n.counting_function = machine.get_transition_state(
			node.counting_function, n.i_bdd & n.o_bdd)
		set_counting_function(n, machine)

def set_counting_function_to_mealy(mealyState, machine):
	for i in mealyState.transitions.keys():
		i_bdd = spot.formula_to_bdd(i, machine.ucb.get_dict(), None)
		o_bdd = spot.formula_to_bdd(mealyState.output_fun[i], 
			machine.ucb.get_dict(), None)
		transitionState = mealyState.transitions[i]
		transitionState.counting_function = machine.get_transition_state(
			mealyState.counting_function, i_bdd & o_bdd)
		set_counting_function_to_mealy(transitionState, machine)

def build_mealy_from_tree(root, machine):
	init_node = MealyState(str(root) + str(root.counting_function))
	init_node.counting_function = root.counting_function
	node_label_dict[str(root)] = init_node

	node_queue = [root]
	while(len(node_queue) > 0):
		curr_node = node_queue[0]
		visited_state_vectors.add(str(curr_node.counting_function))
		node_queue = node_queue[1:]
		mealy_parent = node_label_dict[str(curr_node)]

		for child in curr_node.children:
			node_queue.append(child)
			mealy_child = MealyState(str(child)+str(child.counting_function))
			mealy_child.counting_function = child.counting_function
			node_label_dict[str(child)] = mealy_child
			mealy_parent.transitions[child.i] = mealy_child
			mealy_parent.output_fun[child.i] = child.o
	states.extend(list(node_label_dict.values()))
	mealy = MealyMachine(init_node, states)
	return mealy


def check_node_compatibility(node_1, node_2):
	isCompatible = True
	for child_1 in node_1.children:
		for child_2 in node_2.children:
			if child_1.i_bdd & child_2.i_bdd == buddy.bddtrue:
				if child_1.o_bdd & child_2.o_bdd == buddy.bddtrue:
					isCompatible &= check_node_compatibility(child_1, child_2)
					break
				else:
					return False
			elif child_1.counting_function == child_2.counting_function:
				isCompatible &= check_node_compatibility(child_1, child_2)
	return isCompatible


class CustomMealyState(MealyState):
	"""docstring for CustomMealyState"""
	def __init__(self, state_id, counting_function=None):
		super().__init__(state_id)
		self.counting_function = counting_function

class CustomMealyMachine(MealyMachine):
	"""docstring for CustomMealyMachine"""
	def __init__(self, initial_state: CustomMealyState, states, ):
		super().__init__(initial_state, states)

def complete_mealy(state: MealyState, mealy_machine: MealyMachine, UCBObject: UCB, visited_states=[]):
	if len(visited_state_vectors) == 0:
		initialize_visited_state_vectors(mealy_machine)
	visited_states.append(state)
	for bdd_i in UCBObject.bdd_inputs:
		str_i = bdd_to_str(bdd_i)
		if str_i in state.transitions.keys():
			next_state = state.transitions[str_i]
		else:
			next_state_vector, output_choice = query(
				state.counting_function,
				bdd_i,
				UCBObject,
				state.state_id)
			if str(next_state_vector) in visited_state_vectors:
				next_state = get_state_from_counting_function(next_state_vector, mealy_machine.states)
			else:
				next_state = MealyState(state.state_id + \
					".[{}].[{}]".format(str_i, bdd_to_str(output_choice)))
				next_state.counting_function = next_state_vector
			state.transitions[str_i] = next_state
			state.output_fun[str_i] = bdd_to_str(output_choice)
		if next_state not in visited_states:
			complete_mealy(next_state, mealy_machine, UCBObject, visited_states)

class LearnMealyMachine(object):
	"""docstring for LearnMealyMachine"""

	def __init__(
			self, k, psi, input_atomic_propositions, 
			output_atomic_propositions, user_modifications=False):
		super(LearnMealyMachine, self).__init__()
		self.k = k
		self.compute_winning(psi, input_atomic_propositions, 
							 output_atomic_propositions)

		# universal co-buchi of formula
		self.ucb_num_states = self.ucb.num_states()
		
		# proposition list
		self.bdd_inputs = self.get_proposition_list(
			self.get_bdd_propositions(input_atomic_propositions))
		self.bdd_outputs = self.get_proposition_list(
			self.get_bdd_propositions(output_atomic_propositions))

		self.mealy_machine = None
		self.counting_function_to_state_map = {}
		self.visited_states = []

		self.queries = 0
		self.userQueries = 0
		self.user_modifications = user_modifications
	
	def build_mealy(self):
		k = 1
		waiting = []
		waiting.append([-1]*self.ucb_num_states)
		waiting[0][self.ucb.get_init_state_number()] = 0

		num_states = 0
		node_label_dict = dict()
		node_label_dict[num_states] = MealyState("[]")
		initial_node = node_label_dict[0]

		self.counting_function_to_state_map[str(waiting[0])] = initial_node
		self.visited_states.append(waiting[0])
		
		while len(waiting) > 0:
			from_count_fn = random.choice(waiting)
			waiting.remove(from_count_fn)
			
			from_state = self.counting_function_to_state_map[str(from_count_fn)]
			
			for i in self.bdd_inputs:
				dst_count_fn, o = self.query(from_count_fn, i)
				input_formula = str(spot.bdd_to_formula(i))
				output_formula = str(spot.bdd_to_formula(o))
				
				if dst_count_fn in self.visited_states:
					to_state = self.counting_function_to_state_map[str(dst_count_fn)]
				else:
					self.visited_states.append(dst_count_fn)
					waiting.append(dst_count_fn)
					
					num_states += 1
					node_label_dict[num_states] = MealyState( 
						from_state.state_id \
						+ ".[{}][{}]".format(input_formula, output_formula))

					to_state = node_label_dict[num_states]
					self.counting_function_to_state_map[str(dst_count_fn)] = to_state
				
				from_state.transitions[input_formula] = to_state
				from_state.output_fun[input_formula] = output_formula
		
		self.mealy_machine = MealyMachine(initial_node, list(node_label_dict.values()))
	
	def get_transition_state(self, state_vector, edge_formula):
		dst_state_vector = []
		for state in range(self.ucb_num_states):
			dst_state_possibilities = []
			for from_state in range(self.ucb_num_states):
				if state_vector[from_state] == -1:
					continue
				for edge in self.ucb.out(from_state):
					if edge.dst != state:
						continue
					if edge.cond & edge_formula != buddy.bddfalse:
						dst_state_possibilities.append(min(self.k+1, 
						(state_vector[from_state] + 
							1 if self.ucb.state_is_accepting(edge.dst)
							else 0)
						))
			if len(dst_state_possibilities) == 0:
				dst_state_vector.append(-1)
				continue
			dst_state_vector.append(max(dst_state_possibilities))
		return dst_state_vector

	def query(self, state_vector, i):
		self.queries += 1
		
		dst_state_vector = None
		output_choice = None
		
		unsafe_choice_list = []
		safe_choice_list = []
		best_choice_list = []
		visited_choice_list = []
		
		for o in self.bdd_outputs:
			current_state_vector = self.get_transition_state(state_vector, i & o)
			if not self.is_safe(current_state_vector):
				# print("Unsafe choice. Continuing...")
				unsafe_choice_list.append([current_state_vector, o])
				continue
			safe_choice_list.append([current_state_vector, o])
			
			if current_state_vector in self.visited_states:
				visited_choice_list.append([current_state_vector, o])
			
			if current_state_vector == dst_state_vector:
				best_choice_list.append([current_state_vector, o])
				continue
			
			if self.contains(current_state_vector, dst_state_vector):
				continue
			if (dst_state_vector == None \
			  or self.contains(dst_state_vector, current_state_vector) \
			  or current_state_vector in self.visited_states):
				dst_state_vector = current_state_vector
				output_choice = o
				best_choice_list = [[current_state_vector, o]]
				continue
			
			best_choice_list.append([current_state_vector, o])
		
		print("".join(["-"]*100))
		print("Action after sequence " 
			+ self.counting_function_to_state_map[str(state_vector)].state_id
			+ '.' + str(spot.bdd_to_formula(i))
			+ " is chosen as: " + str(spot.bdd_to_formula(output_choice)))
		
		self.print_choice_list(best_choice_list, "Best actions: ")
		self.print_choice_list(safe_choice_list, "Safe actions: ")
		self.print_choice_list(visited_choice_list,
								"Actions that lead to a visited state: ")
		self.print_choice_list(unsafe_choice_list, "Unsafe actions: ")
		
		if self.user_modifications:
			chooseToModify = input("Modify? (y/n): ")
			
			if chooseToModify in "yY":
				self.userQueries += 1
				while True:
					output_choice = input("Enter preferred action: ")
					for o in self.bdd_outputs:
						if output_choice == str(spot.bdd_to_formula(o)):
							output_choice = o
							dst_state_vector = self.get_transition_state(state_vector, i & o)
							return {"dst_state": dst_state_vector, "output": output_choice}
					print("Invalid action. Choose amongst: " \
						+ ", ".join(list(
							map(lambda x: str(spot.bdd_to_formula(x)),
							 self.bdd_outputs))))
		return [dst_state_vector, output_choice]

file_name = input("Enter name of json_file:")
with open('examples/' + file_name, "r") as read_file:
    data = json.load(read_file)

traces = data['traces']
traces = list(map(lambda x: x.split('.'), traces))
build_mealy(data['LTL'], data['input_atomic_propositions'],
	data['output_atomic_propositions'], traces, 2)