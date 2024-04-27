CodeMirror.defineSimpleMode("ltl", {
    start: [
        {regex: /(?:F|G|X|U|W|R|M)\b/, token: "keyword"},
        {regex: /(?:true|false|tt|ff|0|1)\b/, token: "atom"},
        {regex: /&&|&|AND|\|\||\||OR|!|NOT|->|=>|IMP|<->|<=>|BIIMP|\^|XOR/, token: "operator"},
        {regex: /[a-z_][a-zA-Z_0-9]*/, token: "variable"},
        {regex: /\(|\)/, token: "bracket"}
    ]
});
CodeMirror.defineSimpleMode("traces", {
    start: [
        {regex: /\.|,|:|;/, token: "keyword"},
        {regex: /(?:true|false|tt|ff|0|1)\b/, token: "atom"},
        {regex: /&&|&|AND|\|\||\||OR|!|NOT/, token: "operator"},
        {regex: /[a-z_][a-zA-Z_0-9]*/, token: "variable"},
        {regex: /\(|\)/, token: "bracket"},
        {regex: /(?<=([a-zA-Z_0-9]+\ ?=\ *)).*/, token: "string"}
    ]
});
