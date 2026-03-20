export async function triggerWorkflow(token, owner, repo, workflow, branch) {

    const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`;

    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/vnd.github+json'
        },
        body: JSON.stringify({ ref: branch })
    });

    if (res.status !== 204) {
        throw new Error("Failed to trigger workflow");
    }
}