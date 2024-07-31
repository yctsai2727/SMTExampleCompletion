import os
import sys
import traceback

from pydot import Dot, Node, Edge, graph_from_dot_file

from aalpy.automata import MealyState, MealyMachine

file_types = ['dot', 'png', 'svg', 'pdf', 'string']


def _get_node(state):
    if 'special_node' in state.__dict__.keys():
        return Node(state.state_id, fillcolor="#ff000075", color="black", label=state.state_id, style="filled")
    elif 'color' in state.__dict__.keys():
        return Node(state.state_id, fillcolor=state.color, color="white", label=state.state_id, style="filled")
    return Node(state.state_id, label=state.state_id)


def _add_transition_to_graph(graph, state, display_same_state_trans):
    for i in state.transitions.keys():
        new_state = state.transitions[i]
        try:
            if i in state.premachine_transitions:
                graph.add_edge(Edge(
                    state.state_id,
                    new_state.state_id,
                    label=f'{i}/{state.output_fun[i]}',
                    color="red"))
            else:
                graph.add_edge(Edge(
                    state.state_id,
                    new_state.state_id,
                    label=f'{i}/{state.output_fun[i]}'))
        except:
            graph.add_edge(Edge(
                state.state_id,
                new_state.state_id,
                label=f'{i}/{state.output_fun[i]}'))

def visualize_automaton(automaton, path="LearnedModel", file_type='pdf', display_same_state_trans=True):
    """
    Create a graphical representation of the automaton.
    Function is round in the separate thread in the background.
    If possible, it will be opened by systems default program.
    Args:
        automaton: automaton to be visualized
        path: file in which visualization will be saved (Default value = "Model_Visualization")
        file_type: type of file/visualization. Can be ['png', 'svg', 'pdf'] (Default value = 'pdf')
        display_same_state_trans: if True, same state transitions will be displayed (Default value = True)
    """
    print('Visualization started in the background thread.')

    if len(automaton.states) >= 25:
        print(f'Visualizing {len(automaton.states)} state automaton could take some time.')

    import threading
    visualization_thread = threading.Thread(target=save_automaton_to_file, name="Visualization",
                                            args=(automaton, path, file_type, display_same_state_trans, True))
    visualization_thread.start()


def save_automaton_to_file(automaton, path="LearnedModel", file_type='dot',
                           display_same_state_trans=True, visualize=False):
    """
    The Standard of the automata strictly follows the syntax found at: https://automata.cs.ru.nl/Syntax/Overview.
    For non-deterministic and stochastic systems syntax can be found on AALpy's Wiki.
    Args:
        automaton: automaton to be saved to file
        path: file in which automaton will be saved (Default value = "LearnedModel")
        file_type: Can be ['dot', 'png', 'svg', 'pdf'] (Default value = 'dot')
        display_same_state_trans: True, should not be set to false except from the visualization method
            (Default value = True)
        visualize: visualize the automaton
    Returns:
    """
    assert file_type in file_types
    if file_type == 'dot' and not display_same_state_trans:
        print("When saving to file all transitions will be saved")
        display_same_state_trans = True

    graph = Dot(path, graph_type='digraph')
    for state in automaton.states:
        graph.add_node(_get_node(state))

    for state in automaton.states:
        _add_transition_to_graph(graph, state, display_same_state_trans)

    # add initial node
    graph.add_node(Node('__start0', shape='none', label=''))
    graph.add_edge(Edge('__start0', automaton.initial_state.state_id, label=''))

    if file_type == 'string':
        return graph.to_string()
    else:
        try:
            graph.write(path=f'{path}.{file_type}', format=file_type if file_type != 'dot' else 'raw')
            print(f'Model saved to {path}.{file_type}.')
        except OSError:
            traceback.print_exc()
            print(f'Could not write to the file {path}.{file_type}.', file=sys.stderr)


def _process_label(label, source, destination):
    inp = label.split('/')[0]
    out = label.split('/')[1]
    inp = int(inp) if inp.isdigit() else inp
    out = int(out) if out.isdigit() else out
    source.transitions[inp] = destination
    source.output_fun[inp] = out

def _process_node_label(node, label, node_label_dict):
    node_name = node.get_name()
    node_label_dict[node_name] = MealyState(label)

def _strip_label(label: str) -> str:
    label = label.strip()
    if label[0] == '\"' and label[-1] == label[0]:
        label = label[1:-1]
    if label[0] == '{' and label[-1] == '}':
        label = label[1:-1]
    return label


def load_automaton_from_file(path, compute_prefixes=False):
    """
    Loads the automaton from the file.
    Standard of the automatas strictly follows syntax found at: https://automata.cs.ru.nl/Syntax/Overview.
    For non-deterministic and stochastic systems syntax can be found on AALpy's Wiki.
    Args:
        path: path to the file
        compute_prefixes: it True, shortest path to reach every state will be computed and saved in the prefix of
            the state. Useful when loading the model to use them as a equivalence oracle. (Default value = False)
    Returns:
      automaton
    """
    graph = graph_from_dot_file(path)[0]

    node_label_dict = dict()
    for n in graph.get_node_list():
        if n.get_name() == '__start0' or n.get_name() == '' or n.get_name() == '"\\n"':
            continue
        label = None
        if 'label' in n.get_attributes().keys():
            label = n.get_attributes()['label']
            label = _strip_label(label)

        _process_node_label(n, label, node_label_dict)

    initial_node = None
    for edge in graph.get_edge_list():
        if edge.get_source() == '__start0':
            initial_node = node_label_dict[edge.get_destination()]
            continue

        source = node_label_dict[edge.get_source()]
        destination = node_label_dict[edge.get_destination()]

        label = edge.get_attributes()['label']
        label = _strip_label(label)
        _process_label(label, source, destination)

    if initial_node is None:
        print("No initial state found. \n"
              "Please follow syntax found at: https://github.com/DES-Lab/AALpy/wiki/"
              "Loading, Saving, Syntax and Visualization of Automata ")
        assert False

    automaton = MealyMachine(initial_node, list(node_label_dict.values()))
    if compute_prefixes:
        for state in automaton.states:
            state.prefix = automaton.get_shortest_path(automaton.initial_state, state)
    return automaton