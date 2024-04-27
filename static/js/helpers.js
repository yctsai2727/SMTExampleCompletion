$(document).ready(function() {
	$('.alert').alert()
	let count=0
	let exampleReference = {
		'SimpleArbiter2': {
			'assumptions': [],
			'guarantees': ['G (p -> F (gp))', 'G (q -> F (gq))', 'G (!gp | !gq)'],
			'inputs': 'p, q',
			'outputs': 'gp, gq',
			'traces': ['p & q.gp & !gq']
		},
		'SimpleArbiter3': {
			'assumptions': [],
			'guarantees': 
				['G (p -> F (gp))',
				'G (r -> F (gr))',
				'G (q -> F (gq))',
				'G (!(gp & gq) & !(gp & gr) & !(gr & gq))'],
			'inputs': 'p, q, r',
			'outputs': 'gp, gq, gr',
			'traces': ['p & q & r.gp & !gq & !gr']
		},
		'LiftFloor3': {
			'assumptions': [
				'G(b0 -> (b0 W (f0 & serve)))',
				'G(b1 -> (b1 W (f1 & serve)))'],
			'guarantees' :
				['G (b0 -> F (f0 & serve))',
				'G (b1 -> F (f1 & serve))',
				'G ((f0 & !f1) | (!f0 & f1))',
				'G ((f0 & serve) -> X (!f1))',
				'G ((f1 & serve) -> X (!f0))',
				'f0'],
			'inputs': 'b0, b1',
			'outputs': 'f0, f1, serve',
			'traces': [
				'!b0 & b1.f0 & !f1 & !serve.!b0 & b1.!f0 & f1 & serve.!b0 & !b1.!f0 & f1 & !serve.!b0 & !b1.!f0 & f1 & !serve',
				'!b0 & !b1.f0 & !f1 & !serve.!b0 & !b1.f0 & !f1 & !serve']
		},
		'PrioritizedArbiter': {
			'assumptions': ['G F !m'],
			'guarantees' : ['G (p1 -> F (g1))',
				'G (p2 -> F (g2))',
				'G (m -> gm)',
				'G (g1 -> (!g2 & !gm))',
				'G (g2 -> (!g1 & !gm))',
				'G (gm -> (!g1 & !g2))'],
			'inputs': 'p1, p2, m',
			'outputs': 'g1, g2, gm',
			'traces': ["!m & !p1 & !p2.!g1 & !g2 & !gm",
			"m & p1 & p2.!g1 & !g2 & gm.!m & !p1 & !p2.g1 & !g2 & !gm",
			"!m & p1 & p2.g1 & !g2 & !gm.!m & !p1 & !p2.!g1 & g2 & !gm",
			"!m & p1 & !p2.g1 & !g2 & !gm.!m & !p1 & !p2.!g1 & !g2 & !gm",
			"m & !p1 & p2.!g1 & !g2 & gm.!m & !p1.!g1 & g2 & !gm.!m & !p1 & !p2.!g1 & !g2 & !gm",
			"m & p1 & !p2.!g1 & !g2 & gm.!m & p2.g1 & !g2 & !gm.!m & !p1 & !p2.!g1 & g2 & !gm",
			"m & !p1 & p2.!g1 & !g2 & gm.!m & !p1 & p2.!g1 & g2 & !gm.!m & !p1 & !p2.!g1 & !g2 & !gm",
			"m & p1 & !p2.!g1 & !g2 & gm.!m & p1 & !p2.g1 & !g2 & !gm.!m & !p1 & !p2.!g1 & !g2 & !gm"]
		}
	}

	let variable_set = {}
	
	let initEditor = function(id, mode="ltl") {
		return CodeMirror.fromTextArea(document.getElementById(id), {
			lineNumbers: true,
			lineWrapping: true,
			mode: mode,
			theme: "3024-day",
			matchBrackets: true,
			autoCloseBrackets: true,
			extraKeys: { "Tab": false, "Shift-Tab": false }
		});
	};
	let initLineEditor = function(id) {
		return CodeMirror.fromTextArea(document.getElementById(id), {
			mode: "ltl",
			theme: "3024-day",
			lineWrapping: true,
			extraKeys: { "Tab": false, "Shift-Tab": false }
		});
	};
	
	let assumptionsEditor = initEditor("assumptions_textarea");
	let guaranteesEditor = initEditor("guarantees_textarea");
	let inputsEditor = initLineEditor("inputs_textarea");
	let outputsEditor = initLineEditor("outputs_textarea");
	let tracesEditor = initEditor("traces_textarea", "traces");
	
	let process_variable = str => {
		str = str.split('=').map(s => s.trim());
		variable_set[str[0]] = str[1];
		return '';
	}
	let make_formula = str => "((" + str.split(/\r|\n/).map(s => s.trim()).filter(s => s.length > 0).join(") & (") + "))";
	let make_propositions = str => str.split(/\r|\n|,| /).filter(s => s.length > 0).map(s => s.trim()).join(',');
	let make_traces = str => str.split(/\r|\n/).map(
		s => s.includes('=')? 
		process_variable(s):
		s.trim().split(/\.|,|:|;|\#/).map(t => t in variable_set? variable_set[t]: t).join(".")).filter(
		s => s.length > 0).join('\n');

	let setData =  function (exampleName) {
		assumptionsEditor.setValue(exampleReference[exampleName]['assumptions'].join('\n'));
		guaranteesEditor.setValue(exampleReference[exampleName]['guarantees'].join('\n'));
		inputsEditor.setValue(exampleReference[exampleName]['inputs']);
		outputsEditor.setValue(exampleReference[exampleName]['outputs']);
		tracesEditor.setValue(exampleReference[exampleName]['traces'].join('\n'));
	};

	let addAlert = function(message, isError) {
		$('<div>', {
			class: 'alert alert-dismissible d-flex align-items-center ' + (isError?'alert-danger':'alert-warning'),
			role: 'alert'
		}).appendTo('form').html(
		"<i class=\"bi bi-exclamation-triangle-fill\"></i> &nbsp;"
		+ message
		+ "<button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\" aria-label=\"Close\"></button>");
		$('.alert').alert();
	}
	
	$('#submit').click(function(){
		document.querySelector('svg').innerHTML = "";
		$('.downloader').addClass('visually-hidden');
		$('.submit-text').addClass('visually-hidden');
		$('ul.list-group').addClass('visually-hidden').html("");
		$('.loading').removeClass('visually-hidden');
		
		let data = new FormData($('#acacia-form')[0]);

		let showTarget = data.get('target').size > 0;
		
		let assumptions = assumptionsEditor.getValue().trim();
		let guarantees = guaranteesEditor.getValue().trim();
		if (!guarantees) {
			$("#image-container").text("Guarantees not specified");
			return;
		}

		let k = parseInt(data.get('kvalue'));
		k = k > 0? k : 1;

		formula = "";
		if (assumptions) {
			formula += make_formula(assumptions);
			formula += " -> ";
		}
		formula += make_formula(guarantees);

		data.append('formula', formula.trim());

		let inputs = inputsEditor.getValue().trim();
		let outputs = outputsEditor.getValue().trim();
		if (!inputs && !outputs) {
			addAlert("No input or output symbols specified");
			return;
		}
		inputs = make_propositions(inputs);
		outputs = make_propositions(outputs);

		data.set('inputs', inputs);
		data.set('outputs', outputs);
		data.set('k', k);

		let traces = tracesEditor.getValue().trim();
		data.set('traces', make_traces(traces));	
		
		$.ajax({
			type: 'POST',
			url: '/',
			enctype: 'multipart/form-data',
			processData: false,
			contentType: false,
			cache: false,
			data: data, 
			success: function(data) {
				$('.submit-text').html("Submit");
				$('.downloader').removeClass('visually-hidden');
				$('.submit-text').removeClass('visually-hidden');
				$('.loading').addClass('visually-hidden');
				if (!showTarget) {
					$('.downloader.target').addClass('visually-hidden');
				}
				document.querySelector('svg').innerHTML = data.img;
				$('.figure .svg svg').attr('height', $('.figure .svg').attr('height'));
				$('.figure-caption').html("");
				let ul = $('ul.list-group');
				ul.removeClass('visually-hidden');
				data.traces.forEach((item) => {
					ul.append(`<li class="list-group-item">${item.join('.')}</li>`);
				});
			},
			error: function(error) {
				data = error.responseJSON
				$('.downloader').removeClass('visually-hidden');
				$('.submit-text').removeClass('visually-hidden');
				$('.loading').addClass('visually-hidden');
				if (!showTarget) {
					$('.downloader.target').addClass('visually-hidden');
				}
				addAlert(data.msg, !data.retry);
				if (data.retry) {
					$('.submit-text').html("Retry?");
					$('input[name="kvalue"').val(data.k + 1);
				}
			}
		});
	});

	$('#submitstrix').click(function(){
		document.getElementById('img').src = "";
		$('.downloader').addClass('visually-hidden');
		$('.submit-text').addClass('visually-hidden');
		$('ul.list-group').addClass('visually-hidden').html("");
		$('.loading').removeClass('visually-hidden');
		
		let data = new FormData($('#strix-form')[0]);
		
		let assumptions = assumptionsEditor.getValue().trim();
		let guarantees = guaranteesEditor.getValue().trim();
		if (!guarantees) {
			$("#image-container").text("Guarantees not specified");
			return;
		}

		formula = "";
		if (assumptions) {
			formula += make_formula(assumptions);
			formula += " -> ";
		}
		formula += make_formula(guarantees);

		data.append('formula', formula.trim());

		let inputs = inputsEditor.getValue().trim();
		let outputs = outputsEditor.getValue().trim();
		if (!inputs && !outputs) {
			$("#image-container").text("No input or output symbols specified")
			return;
		}
		inputs = make_propositions(inputs);
		outputs = make_propositions(outputs);

		data.set('inputs', inputs);
		data.set('outputs', outputs);	
		
		$.ajax({
			type: 'POST',
			url: '/strix',
			enctype: 'multipart/form-data',
			processData: false,
			contentType: false,
			cache: false,
			data: data, 
			success: function(data) {
				count += 1
				$('.downloader').removeClass('visually-hidden');
				$('.submit-text').removeClass('visually-hidden');
				$('.loading').addClass('visually-hidden');
				document.getElementById('img').src = "/static/temp_model_files/StrixModel.svg?count=" + count;
				$('.figure-caption').html("");
			}
		});
	});

	$('#SimpleArbiter2').click(() => {setData('SimpleArbiter2')});
	$('#SimpleArbiter3').click(() => {setData('SimpleArbiter3')});
	$('#LiftFloor3').click(() => {setData('LiftFloor3')});
});