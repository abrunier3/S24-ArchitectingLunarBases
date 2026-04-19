// ============================================
// STATE MODULE
// ============================================

// ---------- Application State ----------

export let tree = [];
export let selectedNodeId = null;
export let modalParentId = null;
export let nodeCounter = 0;
export let attrCounter = 0;
export let dragSrcId = null;
export let collapsedNodes = new Set();
export let editingNodeId = null;


// ============================================
// STATE MUTATORS
// ============================================

export function setSelectedNode(id) {
    selectedNodeId = id;
}

export function setModalParent(id) {
    modalParentId = id;
}

export function setEditingNode(id) {
    editingNodeId = id;
}

export function incrementAttrCounter() {
    attrCounter += 1;
    return attrCounter;
}

export function resetAttrCounter() {
    attrCounter = 0;
}

export function resetTree() {
    tree = [];
    selectedNodeId = null;
    collapsedNodes.clear();
}


// ============================================
// TREE UTILITIES (PURE FUNCTIONS)
// ============================================

export function makeId() {
    return 'n' + (++nodeCounter);
}


export function findNode(id, nodes = tree) {
    for (const node of nodes) {
        if (node.id === id) return node;

        if (node.children) {
            const found = findNode(id, node.children);
            if (found) return found;
        }
    }
    return null;
}


export function findParentNode(id, nodes = tree, parent = null) {
    for (const node of nodes) {

        if (node.id === id) return parent;

        if (node.children && node.children.length > 0) {
            const found = findParentNode(id, node.children, node);
            if (found !== undefined) return found;
        }
    }
    return undefined;
}


export function removeFromTree(id, nodes = tree) {
    const idx = nodes.findIndex(n => n.id === id);

    if (idx !== -1) {
        nodes.splice(idx, 1);
        return true;
    }

    for (const n of nodes) {
        if (n.children && removeFromTree(id, n.children)) {
            return true;
        }
    }

    return false;
}


export function isDescendant(ancestorId, nodeId) {
    const ancestor = findNode(ancestorId);
    if (!ancestor) return false;

    function check(node) {
        if (!node.children) return false;

        for (const c of node.children) {
            if (c.id === nodeId || check(c)) return true;
        }

        return false;
    }

    return check(ancestor);
}