import json
from ExampleCompletion.algorithm import ExampleCompletion
from LTLsynthesis.algorithm import build_mealy

if __name__ == "__main__":
    with open('examples/WeatherForcast/example1.json') as file:
        data = json.load(file)
    LTL_formula = "((" + ') & ('.join(data['assumptions']) + "))->((" + ') & ('.join(data['guarantees']) + "))"
    with open ('examples/WeatherForcast/sample.txt') as sample_file:
        samples = sample_file.readlines()

    C = 0
    C_min = -4
    examples = ExampleCompletion(LTL_formula,data['input_atomic_propositions'], data['output_atomic_propositions'],samples,"examples/WeatherForcast/reward.dot",-1)
    # while examples==None:
    #     if C>C_min:
    #         C-=1
    #         examples = ExampleCompletion(LTL_formula,data['input_atomic_propositions'], data['output_atomic_propositions'],samples,"examples/WeatherForcast/reward.dot",C)
    #     else:
    #         assert False
        
    traces = list(map(lambda x: x.replace('\r', '').split('.'), examples))
    #print(traces)
    #print(list(map(lambda x: list(map(lambda y:y.split('&')[0],x)), traces)))
    m,state = build_mealy(LTL_formula,data['input_atomic_propositions'], data['output_atomic_propositions'],traces,"Sample","",k=1)

    if m is None:
        print("Realization Failed")
    else:
        print("Realization Completed")