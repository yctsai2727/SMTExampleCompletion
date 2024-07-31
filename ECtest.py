import json
from ExampleCompletion.algorithm import ExampleCompletion
from LTLsynthesis.algorithm import build_mealy
from CustomAALpy.FileHandler import save_automaton_to_file

path = "examples/WeatherForcast/example_long/"

if __name__ == "__main__":
    with open("{}LTL.json".format(path)) as file:
        data = json.load(file)
    LTL_formula = "((" + ') & ('.join(data['assumptions']) + "))->((" + ') & ('.join(data['guarantees']) + "))"
    with open ("{}sample.txt".format(path)) as sample_file:
        samples = sample_file.readlines()

    C = 0
    C_min = -4
    while examples==None:
        if C>C_min:
            C-=1
            examples = ExampleCompletion(LTL_formula,data['input_atomic_propositions'], data['output_atomic_propositions'],samples,"{}reward.dot".format(path),C)
        else:
            assert False
        
    traces = list(map(lambda x: x.replace('\r', '').split('.'), examples))
    #print(traces)
    #print(list(map(lambda x: list(map(lambda y:y.split('&')[0],x)), traces)))
    m,state = build_mealy(LTL_formula,data['input_atomic_propositions'], data['output_atomic_propositions'],traces,"Sample","",k=1)
    
    save_automaton_to_file(m,"{}CompletedModel".format(path),"pdf")

    if m is None:
        print("Realization Failed")
    else:
        print("Realization Completed")