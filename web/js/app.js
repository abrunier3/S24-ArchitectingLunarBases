    /* =====================================================
   S24 DEE — Application Orchestrator
   -----------------------------------------------------
   Connects:
   - State layer
   - Tree renderer
   - Form logic
   - SysML generator/parser
   - GitHub integration
   - Pipeline triggers
===================================================== */

import * as state from './state.js';
import * as tree from './tree.js';
import * as form from './form.js';
import * as parser from './sysml-parser.js';
import * as generator from './sysml-generator.js';
import * as github from './github-api.js';
import * as pipeline from './pipeline.js';
import * as modals from '../components/modals.js';
import * as notifications from '../components/notifications.js';


/* =====================================================
   APPLICATION BOOTSTRAP
===================================================== */

document.addEventListener('DOMContentLoaded', () => {

  console.log('S24 DEE initialized.');

  bindGlobalActions();
  initializeUI();

});


/* =====================================================
   GLOBAL ACTION DISPATCHER
   Uses data-action attributes
===================================================== */

function bindGlobalActions() {

  document.addEventListener('click', (e) => {

    const actionEl = e.target.closest('[data-action]');
    if (!actionEl) return;

    const action = actionEl.dataset.action;

    switch (action) {

      case 'clear':
        handleClear();
        break;

      case 'download':
        handleDownload();
        break;

      case 'preview':
        handlePreview();
        break;

      case 'copy':
        handleCopy();
        break;

      case 'close-preview':
        closePreview();
        break;

      case 'add-root':
        tree.openAddNodeModal(null);
        break;

      case 'add-part':
        form.addPartToTree();
        break;

      case 'save-edit':
        form.saveEdit();
        break;

      case 'cancel-edit':
        form.cancelEdit();
        break;

      case 'import':
        modals.openPasteModal();
        break;

      case 'open-github':
        modals.openGitHubModal();
        break;

      case 'open-pipeline':
        modals.openRunPipelineModal();
        break;

      case 'load-github':
        handleLoadFromGitHub();
        break;

      default:
        console.warn('Unhandled action:', action);
    }

  });

}


/* =====================================================
   INITIALIZATION
===================================================== */

function initializeUI() {
  tree.renderTree(state.getTree());
}


/* =====================================================
   HANDLERS
===================================================== */

function handleClear() {

  state.clearState();
  tree.renderTree(state.getTree());

  document.getElementById('btnExport').disabled = true;
  notifications.success('Assembly cleared.');

}


function handleDownload() {

  const sysml = generator.buildSysML(state.getTree());

  if (!sysml) {
    notifications.error('Tree is empty.');
    return;
  }

  const blob = new Blob([sysml], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = 'assembly.sysml';
  a.click();

  URL.revokeObjectURL(url);
}


function handlePreview() {

  const sysml = generator.buildSysML(state.getTree());

  if (!sysml) {
    notifications.error('Tree is empty.');
    return;
  }

  document.getElementById('sysmlOutput').textContent = sysml;
  document.getElementById('outputWrap').classList.add('visible');

}


function closePreview() {
  document.getElementById('outputWrap').classList.remove('visible');
}


function handleCopy() {

  const sysml = generator.buildSysML(state.getTree());

  if (!sysml) {
    notifications.error('Tree is empty.');
    return;
  }

  navigator.clipboard.writeText(sysml)
    .then(() => notifications.success('Copied to clipboard ✓'))
    .catch(() => notifications.error('Copy failed.'));

}


async function handleLoadFromGitHub() {

  const url = document.getElementById('repoUrl').value.trim();
  if (!url) return;

  try {
    notifications.info('Loading assembly...');
    const text = await github.fetchRawFile(url);

    const parsedTree = parser.parseSysML(text);
    state.setTree(parsedTree);

    tree.renderTree(state.getTree());
    notifications.success('Assembly loaded.');

  } catch (err) {
    notifications.error(err.message);
  }

}
