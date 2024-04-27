from aalpy.SULs import MealySUL
from aalpy.learning_algs import run_Lstar
from aalpy.oracles import RandomWalkEqOracle, StatePrefixEqOracle

def learning(mealy_machine):
	sul_mealy = MealySUL(mealy_machine)
	alphabet = mealy_machine.get_input_alphabet()
	state_origin_eq_oracle = StatePrefixEqOracle(alphabet, sul_mealy, walks_per_state=10, walk_len=15)
	learned_mealy, data = run_Lstar(alphabet, sul_mealy, state_origin_eq_oracle, return_data=True,
		automaton_type='mealy', cex_processing='longest_prefix', print_level=0)
	print("Number of membership queries: " + str(data['queries_learning']))
	print("Number of equivalence queries: " + str(data['queries_eq_oracle']))