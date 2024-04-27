import logging
import itertools
import buddy
from ExampleCompletion.ExamplePrefixTree import *
from LTLsynthesis.utilities import *
from LTLsynthesis.UCBBuilder import UCB
from LTLsynthesis.algorithm import build_ucb
from pysmt.shortcuts import Symbol,And, Or, Equals,GE, LE, Plus, Minus, Implies, Times, get_model
from pysmt.typing import INT
from CustomAALpy.FileHandler import load_automaton_from_file

def ExampleCompletion(LTL_formula, I, O, examples, reward, C, k=2):
    
    global ordered_inputs, bdd_inputs, ucb, UCBWrapper
    
    ###Build the K-co-Buchi Automata###
    build_ucb(LTL_formula,I,O)
    bdd_inputs = UCBWrapper.bdd_inputs
    ucb = UCBWrapper.ucb
    
    ###Build Prefix Tree and load reward machine###
    prefix_tree = PFT(examples)
    reward_machine = load_automaton_from_file(reward)
    
    ###Construct and Solve SMT instance###
    
    ###set up variables
    reward_state=reward_machine.states
    x_vso_list = itertools.product(range(0,prefix_tree.NodeCount),reward_state,O)
    symb_x_vso = [Symbol(var,INT) for var in x_vso_list]
    y_vq_list = itertools.product(range(0,prefix_tree.NodeCount),range(0,ucb.num_states()))
    symb_y_vq = [Symbol(var,INT) for var in y_vq_list]
    
    ###Define the domain of variables
    domain_x_vst = And([Or(Equals(var,0),Equals(var,1)) for var in symb_x_vso])
    domain_y_vq = And([And(GE(var,-1),LE(var,k+1)) for var in symb_y_vq])
    domain = And(domain_x_vst,domain_y_vq)
    
    ###Ambiguity Constraint
    sum_st_list = []
    for v in range(0,prefix_tree.NodeCount):
        sum_so = Plus([symb_x_vso[idx] for idx,x in enumerate(x_vso_list) if x[0]==v])
        sum_st_list.append(Equals(sum_so,1))
    cst_Amb = And(sum_st_list)
    
    ###Initial Transition for reward machine
    init_state = reward_machine.initial_state
    sum_s0o = Plus([symb_x_vso[idx] for idx,x in enumerate(x_vso_list) if x[0]==0 and x[1]==init_state])
    cst_RewInit = Equals(sum_s0o,1)
    
    ###Reward Transition
    trans_impl_list = []
    for idx,x in enumerate(x_vso_list):
        s_p = x[1].transitions.get(x[0].token+x[2])
        for vp in prefix_tree.lookup[x[0]].child:
            sum_op = Plus([symb_x_vso[idxp] for idxp,xp in enumerate(x_vso_list) if xp[0]==vp and xp[1]==s_p])
            trans_impl_list.append(GE(Plus(Minus(1,symb_x_vso[idx]),sum_op),1))
    cst_RewTrans = And(trans_impl_list)
    
    ###Counting Function, initial condition
    CF_init_list = []
    for idx,y in enumerate(y_vq_list):
        if y[0] != 0:
            continue
        if y[1] == ucb.get_init_state_number():
            if ucb.state_is_accepting(y[1]):
                CF_init_list.append(Equals(symb_y_vq[idx],1))
            else:
                CF_init_list.append(Equals(symb_y_vq[idx],0))
        else:
            CF_init_list.append(Equals(symb_y_vq[idx],-1))
    cst_CFInit = And(CF_init_list)
    
    ###Counting Function, transition
    CF_trans_list = []
    for i, x in enumerate(x_vso_list):
        for j,y_p in enumerate(filter(lambda y: y[0] in prefix_tree.lookup[x[0]].child,y_vq_list)):
            i_bdd = str_to_bdd(prefix_tree.lookup[x[0]].token,ucb)
            o_bdd = str_to_bdd(x[2],ucb)
            q_ances_list = [e.src for e in ucb.edges() if e.dst == y_p[1] and e.cond&(i_bdd&o_bdd)!=buddy.bddfalse]
            sum_qqp = Plus([Plus(symb_y_vq[k],1) for k,y in y_vq_list if y[0]==x[0] and y[1] in q_ances_list])
            inner_imp = Implies(Equals(sum_qqp,0),Equals(symb_y_vq[j],-1))
            outer_imp = Implies(Equals(symb_x_vso[i],1),inner_imp)
            CF_trans_list.append(outer_imp)
            for q in q_ances_list:
                y_q_aces_list = [symb_y_vq[k] for k,y_vq in y_vq_list if y_vq[0]==x[0] and y[1]==q]
                inner_imp_list = [Implies(GE(y_vq,0),GE(symb_y_vq[j],Plus(y_vq,int(ucb.state_is_accepting(y_p[1]))))) for y_vq in y_q_aces_list]
                outer_imp_list = [Implies(Equals(symb_x_vso[i],1),inner) for inner in inner_imp_list]
                CF_trans_list.extend(outer_imp_list)
    cst_CFTrans = And(CF_trans_list)
    
    ###Counting Function, realizability
    CF_real_list = []
    for idx,y in enumerate(y_vq_list):
        for antichain in ucb.antichain_heads:
            CF_real_list.append(LE(symb_y_vq[idx],antichain[y[1]]))
    cst_CFreal = And(CF_real_list)

    ###Optimality
    L = len(examples)
    sum_rew = Plus([Times(symb_x_vso[idx],prefix_tree.lookup[x[0]].count*reward_machine.output_step(x[1],prefix_tree.lookup[x[0]].token+x[2])/L) for idx,x in enumerate(x_vso_list)])
    cst_opt = GE(sum_rew,C)

    ###Solving the instance
    problem = And(cst_Amb,cst_RewInit,cst_RewTrans,cst_CFInit,cst_CFTrans,cst_CFreal,cst_opt)
    formula = And(domain, problem)

    print("Transformation of problem instance")
    print(formula)

    model = get_model(formula)
    if model:
        print(model)
    else:
        print("No solution found")