import logging
import itertools
import buddy
from ExampleCompletion.ExamplePrefixTree import *
from LTLsynthesis.utilities import str_to_bdd
from LTLsynthesis.UCBBuilder import UCB,build_UCB
from pysmt.shortcuts import Symbol,And, Or, Equals,GE, LE, Plus, Minus, Implies, Times,Iff,Int
from pysmt.shortcuts import get_model, get_unsat_core, is_sat, is_unsat
from pysmt.rewritings import conjunctive_partition
from pysmt.typing import INT
from CustomAALpy.FileHandler import visualize_automaton,load_automaton_from_file


def ExampleCompletion(LTL_formula, I, O, samples, reward, C, k=1,debug=False):
    
    ###Build the K-co-Buchi Automata###
    UCBWrapper, k = build_UCB(LTL_formula,I,O,k)
    ucb = UCBWrapper.ucb
    #visualize_automaton(ucb,path="examples/WeatherForcast/")
    for antichain in UCBWrapper.antichain_heads:
        print("antichain: ",antichain)
    
    ###Build Prefix Tree and load reward machine###
    prefix_tree = PFT(samples)
    reward_machine = load_automaton_from_file(reward)
    
    ###Construct and Solve SMT instance###

    ###set up variables
    reward_state=reward_machine.states
    x_vso_list = list(itertools.product(range(1,prefix_tree.NodeCount),reward_state,O))
    name_var = lambda p:str(p[0])+str(p[1].state_id)+p[2]
    symb_x_vso = [Symbol(name_var(var),INT) for var in x_vso_list]
    y_vq_list = list(itertools.product(range(1,prefix_tree.NodeCount),range(0,ucb.num_states())))
    symb_y_vq = [Symbol(str(var),INT) for var in y_vq_list]
    
    ###Define the domain of variables
    domain_x_vst = And([Or(Equals(var,Int(0)),Equals(var,Int(1))) for var in symb_x_vso])
    domain_y_vq = And([And(GE(var,Int(-1)),LE(var,Int(k+1))) for var in symb_y_vq])
    domain = And(domain_x_vst,domain_y_vq)
    
    ###Ambiguity Constraint
    sum_st_list = []
    for v in range(1,prefix_tree.NodeCount):
        sum_so = Plus([symb_x_vso[idx] for idx,x in enumerate(x_vso_list) if x[0]==v])
        sum_st_list.append(Equals(sum_so,Int(1)))
    cst_Amb = And(sum_st_list)
    
    ###Initial Transition for reward machine
    init_state = reward_machine.initial_state
    Rew_Init_list = []
    for child in prefix_tree.root.child:
        sum_s0o = Plus([symb_x_vso[idx] for idx,x in enumerate(x_vso_list) if x[0]==child.id and x[1]==init_state])
        Rew_Init_list.append(Equals(sum_s0o,Int(1)))
    cst_RewInit = And(Rew_Init_list)
    
    ###Reward Transition
    trans_impl_list = []
    for idx,x in enumerate(x_vso_list):
        s_p = x[1].transitions.get(prefix_tree.lookup[x[0]].token.split('&')[0]+";"+x[2])
        for vp in prefix_tree.lookup[x[0]].child:
            sum_op = Plus([symb_x_vso[idxp] for idxp,xp in enumerate(x_vso_list) if xp[0]==vp.id and xp[1]==s_p])
            trans_impl_list.append(GE(Plus(Minus(Int(1),symb_x_vso[idx]),sum_op),Int(1)))
    cst_RewTrans = And(trans_impl_list)
    
    ###Counting Function, initial condition
    CF_init_list = []
    prev = None
    for idx,y in enumerate(y_vq_list):
        if not prefix_tree.root.hasChildByID(y[0]): #to be optimized
            continue
        if y[1] == ucb.get_init_state_number():
            if ucb.state_is_accepting(y[1]):
                CF_init_list.append(Equals(symb_y_vq[idx],Int(1)))
            else:
                CF_init_list.append(Equals(symb_y_vq[idx],Int(0)))
        else:
            CF_init_list.append(Equals(symb_y_vq[idx],Int(-1)))
    cst_CFInit = And(CF_init_list)

    ###Counting Function, transition
    CF_trans_list = []
    for i, x in enumerate(x_vso_list):
        next_node = list(filter(lambda y: prefix_tree.lookup[x[0]].hasChildByID(y[1][0]),enumerate(y_vq_list)))
        for j,y_p in next_node:
            i_bdd = str_to_bdd(prefix_tree.lookup[x[0]].token,ucb)
            #print(buddy.__dict__)
            # for ni in I:
            #     if ni==prefix_tree.lookup[x[0]].token:
            #         continue
            #     i_bdd = i_bdd & buddy.bdd_not(str_to_bdd(ni,ucb))
            o_bdd = str_to_bdd(x[2],ucb)
            for no in O:
                if no==x[2]:
                    continue
                o_bdd = o_bdd & buddy.bdd_not(str_to_bdd(no,ucb))
            q_ances_list = [e.src for e in ucb.edges() if e.dst == y_p[1] and e.cond&(i_bdd&o_bdd)!=buddy.bddfalse]
            # if prefix_tree.lookup[x[0]].token.split('&')[0]=='T1' and x[2]=='Off' and ucb.state_is_accepting(y_p[1]):
            #     print("Tree node:",x[0],"\nstate reachable from:",q_ances_list)
            if len(q_ances_list) == 0:
                continue
            sum_qqp = Plus([Plus(symb_y_vq[idk],Int(1)) for idk,y in enumerate(y_vq_list) if y[0]==x[0] and y[1] in q_ances_list])
            inner_imp = Iff(Equals(sum_qqp,Int(0)),Equals(symb_y_vq[j],Int(-1)))
            outer_imp = Implies(Equals(symb_x_vso[i],Int(1)),inner_imp)
            CF_trans_list.append(outer_imp)
            if ucb.state_is_accepting(y_p[1]):
                chi = 1
            else:
                chi = 0
            for q in q_ances_list:
                y_q_aces_list = [symb_y_vq[idk] for idk,y_vq in enumerate(y_vq_list) if y_vq[0]==x[0] and y_vq[1]==q]
                inner_imp_list = [Implies(GE(y_vq,Int(0)),GE(symb_y_vq[j],Plus(y_vq,Int(chi)))) for y_vq in y_q_aces_list]
                outer_imp_list = [Implies(Equals(symb_x_vso[i],Int(1)),inner) for inner in inner_imp_list]
                CF_trans_list.extend(outer_imp_list)
    cst_CFTrans = And(CF_trans_list)
    
    ###Counting Function, realizability
    CF_real_list = []
    for v in range(1,prefix_tree.NodeCount):
        y_v_list = [(idx,y_vq) for idx,y_vq in enumerate(y_vq_list) if y_vq[0]==v]
        v_list = []
        for antichain in UCBWrapper.antichain_heads:
            chain_list = []
            for idx,y in y_v_list:
                chain_list.append(LE(symb_y_vq[idx],Int(antichain[y[1]])))
            v_list.append(And(chain_list))
        CF_real_list.append(Or(v_list))
    cst_CFreal = And(CF_real_list)

    ###Optimality
    L = len(samples)
    sum_rew = Plus([Times(symb_x_vso[idx],Int(prefix_tree.lookup[x[0]].count*int(reward_machine.output_step(x[1],prefix_tree.lookup[x[0]].token.split('&')[0]+";"+x[2])))) for idx,x in enumerate(x_vso_list)])
    cst_opt = GE(sum_rew,Int(L*C))

    ###Solving the instance
    problem = And(cst_Amb,cst_RewInit,cst_RewTrans,cst_CFInit,cst_CFTrans,cst_CFreal,cst_opt)
    formula = And(domain, problem)

    if debug:
        print("Transformation of problem instance")
        print(formula)

    model = get_model(formula)
    if model:
        action_set = [str(solu[0]) for solu in model if solu[1].constant_value()==1]
        init_state = reward_machine.initial_state
        queue = list(map(lambda a:(a,init_state),prefix_tree.root.child))
        for (node,reward_state) in queue:
            node.action = list(filter(lambda a:"\'"+str(node.id)+reward_state.state_id in a,action_set))[0].split("\'"+str(node.id)+reward_state.state_id)[1].replace("\'","")
            extend = ""
            for o in O:
                if o != node.action:
                    extend += '&!'+o
            node.action += extend
            next_rew_state = reward_state.transitions.get(node.token.split('&')[0]+';'+node.action.split('&')[0])
            if len(node.child)!=0:
                queue.extend(list(map(lambda a:(a,next_rew_state),node.child)))
        examples = prefix_tree.synth()
        return examples
    else:
        # name_x_vso = list(map(name_var,x_vso_list))
        # id1 = name_x_vso.index("1s0Alarm")
        # id2 = name_x_vso.index("3s4Alarm")
        # sub_form = formula.substitute({symb_x_vso[id1]:Int(1),symb_x_vso[id2]:Int(1)})
        print("No solution found.")
        if debug:
            conj = conjunctive_partition(formula)
            ucore = get_unsat_core(conj)
            print("UNSAT-Core size '%d'" % len(ucore))
            for f in ucore:
                print(f.serialize())
        return None