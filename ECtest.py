import json
from ExampleCompletion.algorithm import ExampleCompletion
from LTLsynthesis.algorithm import build_mealy
from CustomAALpy.FileHandler import save_automaton_to_file

path_to_input = "examples/WeatherForcast/example_long/"

def CheckValidInput(s):
    counter = 0
    marker = None
    for comp in s.split(' | '):
        if len(list(comp.split(' & ')))>1:
            for sub in comp.split(' & '):
                if sub[0]!='!':
                    counter +=1
                    marker = sub
        else:
            for sub in comp.split('&'):
                if sub[0]!='!':
                    counter +=1
                    marker = sub
    if counter == 1:
        return True, marker
    else:
        return False, None

if __name__ == "__main__":
    with open("{}LTL.json".format(path_to_input)) as file:
        data = json.load(file)
    LTL_formula = "((" + ') & ('.join(data['assumptions']) + "))->((" + ') & ('.join(data['guarantees']) + "))"
    examples = None
    try:
        with open("{}examples.txt".format(path_to_input)) as file:
            examples = list(map(lambda a:a.split('\n')[0],file.readlines()))
    except:   
        with open ("{}sample.txt".format(path_to_input)) as sample_file:
            samples = sample_file.readlines()
        L = len(samples)
        k = len(samples[0])
        C = 0
        C_min = -1*k*L
        examples = ExampleCompletion(LTL_formula,data['input_atomic_propositions'], data['output_atomic_propositions'],samples,'{}reward.dot'.format(path_to_input),C)
        while examples==None:
            if C>C_min:
                C-= 1
                examples = ExampleCompletion(LTL_formula,data['input_atomic_propositions'], data['output_atomic_propositions'],samples,'{}reward.dot'.format(path_to_input),C)
            else:
                assert False
        print("Completion Done")
        with open("{}examples.txt".format(path_to_input),"w") as file:
            for example in examples:
                file.write(example+"\n")
    print(examples)
    for example in examples:
        for io in example.split('.'):
            _, tag = CheckValidInput(io)
            print(tag,end = '.')
        print('\n')
    traces = list(map(lambda x: x.replace('\r', '').split('.'), examples))
    m,state = build_mealy(LTL_formula,data['input_atomic_propositions'], data['output_atomic_propositions'],traces,"Sample","",k=1)
    
    if m is None:
        print("Realization Failed")
    else:
        print("Realization Completed")
        save_automaton_to_file(m,'{}CompletedModel'.format(path_to_input),'pdf')
        counter = 0
        # for st in m.states:
        #     st.state_id = 'q'+str(counter)
        #     counter +=1
        #     n_trans = {}
        #     n_outfunc = {}
        #     for i in st.transitions.keys():
        #         flag_i, inp = CheckValidInput(i)
        #         flag_o, oup = CheckValidInput(st.output_fun[i])
        #         if (flag_i and flag_o):
        #             print(i,st.output_fun[i],'->certified output:',inp,oup)
        #             n_trans[inp] = st.transitions[i]
        #             n_outfunc[inp] = oup
        #             #st.premachine_transitions.append(inp)
        #     st.transitions.clear()
        #     st.output_fun.clear()
        #     st.transitions = n_trans
        #     st.output_fun = n_outfunc    
        save_automaton_to_file(m,'{}CompletedModel'.format(path_to_input),'png')