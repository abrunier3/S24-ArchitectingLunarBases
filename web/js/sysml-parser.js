import { tree, makeId } from './state.js';

// ============================================
// SIMPLE SYSML PARSER (minimal version)
// ============================================

export function parseSysML(text) {
    tree.length = 0;

    const partRegex = /part\s+(\w+)\s*\{/g;
    let match;

    while ((match = partRegex.exec(text)) !== null) {
        tree.push({
            id: makeId(),
            name: match[1],
            children: [],
            data: {}
        });
    }
}