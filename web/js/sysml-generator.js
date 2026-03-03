import { tree } from './state.js';
import { pad } from './utils.js';

// ============================================
// SYSML GENERATOR
// ============================================

function emitDims(name, d, indent) {
    let s = '';

    s += pad(indent) + `part ${name}_dims {\n`;
    s += pad(indent+1) + `attribute length = ${d.length || '0'};\n`;
    s += pad(indent+1) + `attribute width = ${d.width || '0'};\n`;
    s += pad(indent+1) + `attribute height = ${d.height || '0'};\n`;
    s += pad(indent) + `}\n\n`;

    return s;
}

function generateNode(node, indent) {
    let s = '';

    s += pad(indent) + `part ${node.name} {\n`;

    if (node.data) {
        s += emitDims(node.name, node.data, indent + 1);
    }

    if (node.children) {
        node.children.forEach(child => {
            s += generateNode(child, indent + 1);
        });
    }

    s += pad(indent) + `}\n`;
    return s;
}

export function buildSysML() {
    if (tree.length === 0) return '';

    let s = `package '${tree[0].name}' {\n\n`;

    tree.forEach(root => {
        s += generateNode(root, 1);
        s += '\n';
    });

    s += `}\n`;

    return s;
}