// ============================================
// GITHUB API
// ============================================

export async function publishFile(token, owner, repo, path, content, branch) {

    const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;

    const encoded = btoa(unescape(encodeURIComponent(content)));

    const body = {
        message: "update assembly",
        content: encoded,
        branch: branch
    };

    const res = await fetch(apiUrl, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/vnd.github+json'
        },
        body: JSON.stringify(body)
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message);
    }

    return await res.json();
}