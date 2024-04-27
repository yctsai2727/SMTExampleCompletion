from flask import Flask
from flask import request
from flask import render_template, send_file, jsonify, session

from LTLsynthesis.algorithm import build_mealy
from LTLsynthesis.LStarLearning import learning
from LTLsynthesis.UCBBuilder import build_strix
import random
import logging
import json
import os

from aalpy.utils import load_automaton_from_file

import sys
sys.path.insert(0, 'sample/')

app = Flask(__name__)
app.secret_key = '97db21348530a03c3a836519c3d636b1f42d4fae7c98038349a9ea87a20dcc36'

ALLOWED_EXTENSIONS = {'dot'}
LOGGERS_LEVELS = [
('misc-logger', logging.DEBUG),
('prefix-tree-logger', logging.DEBUG),
('merge-phase-logger', logging.DEBUG), 
('completion-phase-logger', logging.DEBUG)]

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def setup_logging(name, level):
    # create formatter
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s - %(message)s')
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

for name, level in LOGGERS_LEVELS:
    setup_logging(name, level)

def parse_json(file_name, new_traces = [], k=1):
    with open('examples/' + file_name + ".json", "r") as read_file:
        data = json.load(read_file)
    LTL_formula = "((" + ') & ('.join(data['assumptions']) + "))->((" + ') & ('.join(data['guarantees']) + "))"
    if len(new_traces) == 0:
        traces = data['traces']
        traces = list(map(lambda trace: trace.split('.'), traces))
    else:
        traces = copy.deepcopy(new_traces)
    m = build_mealy(LTL_formula, data['input_atomic_propositions'], data['output_atomic_propositions'], traces, file_name, data['target'], k)
    learning(m)

@app.route('/', methods=['GET', 'POST'])
def execute():
    if request.method == 'POST':
        session['number'] = random.randint(100, 1000)
        target_file = None
        if 'target' in request.files:
            target_file = request.files['target']
        return execute_algorithm(request.form, target_file)
    else:
        return render_template('AcaciaSynth.html', LTL_formula="Nothing", type="acacia")

@app.route('/strix', methods=['GET', 'POST'])
def execute_strix():
    if request.method == 'POST':
        session['number'] = random.randint(100, 1000)
        return execute_strix(request.form)
    else:
        return render_template('StrixDemo.html', LTL_formula="Nothing", type="strix")

@app.route('/download/dot')
def download_dot():
    return send_file(
        'static/temp_model_files/LearnedModel_{}.dot'.format(session['number']), 
        as_attachment=True)

@app.route('/download/pdf')
def download_pdf():
    return send_file(
        'static/temp_model_files/LearnedModel_{}.pdf'.format(session['number']), 
        as_attachment=True)

@app.route('/download/target')
def download_target():
    return send_file('static/temp_model_files/TargetModel.pdf', as_attachment=True)

@app.route('/clear')
def clear_files():
    dir = 'static/temp_model_files'
    for file in os.scandir(dir):
        os.remove(file.path)
    return render_template('AcaciaSynth.html', type="acacia")


def execute_algorithm(data, target_file):
    target_filename = ""
    input_atomic_propositions = data['inputs']
    input_atomic_propositions = input_atomic_propositions.split(',')
    output_atomic_propositions = data['outputs']
    output_atomic_propositions = output_atomic_propositions.split(',')
    
    traces = data['traces']
    traces = traces.split('\n')
    k = int(data['k'])
    traces = list(map(lambda x: x.replace('\r', '').split('.'), traces))
    
    if (len(target_file.filename) > 0) and (allowed_file(target_file.filename)):
        target_filename = "static/temp_model_files/TargetModel_{}.dot".format(session['number'])
        target_file.save(target_filename)
    elif len(target_file.filename) > 0:
        print("Not a dot file!")
        target_file.save(os.path.join("static/temp_model_files", target_file.filename))

    m, stats = build_mealy(
        data['formula'],
        input_atomic_propositions,
        output_atomic_propositions,
        traces, "Sample",
        target_filename, k)
    if m is None:
        return stats, 400
    svg_file = open(
        'static/temp_model_files/LearnedModel_{}.svg'.format(session['number']), 
        'r', encoding = 'utf-8').read()
    svg_file = ''.join(svg_file.split('\n')[6:])
    return {
        'msg': 'success',
        'img': svg_file,
        'traces': stats['traces']
   }, 200

def execute_strix(data):
    input_atomic_propositions = data['inputs']
    input_atomic_propositions = input_atomic_propositions.split(',')
    output_atomic_propositions = data['outputs']
    output_atomic_propositions = output_atomic_propositions.split(',')

    m= build_strix(
        data['formula'],
        input_atomic_propositions,
        output_atomic_propositions)
    return jsonify({
        'msg': 'success',
        'img': m
   })

