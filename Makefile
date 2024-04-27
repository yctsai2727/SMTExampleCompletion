init:
	conda create -n SynthLearn python=3.8
	conda activate SynthLearn
	conda install pip
	conda install -c conda-forge spot
	pip install -r requirements.txt

test:
	nosetests tests
