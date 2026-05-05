/**
 * Cloudflare Worker: Newsletter Subscriber Webhook
 *
 * Receives FormSubmit.co webhook POSTs and appends new subscriber emails
 * directly to newsletter_subscribers.csv in the GitHub repo via the
 * GitHub Contents API — enabling near-instant CSV updates (seconds, not minutes).
 *
 * ── SETUP ──────────────────────────────────────────────────────────────────
 *
 * 1. Go to https://dash.cloudflare.com → Workers & Pages → Create Worker.
 * 2. Paste this file as the Worker source and deploy.
 * 3. Add two encrypted secrets via Settings → Variables → Secrets:
 *
 *      GITHUB_TOKEN   Fine-grained personal access token with:
 *                     - Contents: Read & Write
 *                     - Scoped ONLY to the MinDatabase repository.
 *                     Create at: https://github.com/settings/personal-access-tokens
 *
 *      GITHUB_REPO    Repository in "owner/repo" format.
 *                     Example: "xkkxsn56sn-bot/MinDatabase"
 *
 * 4. Copy the Worker URL (e.g. https://subscriber-webhook.YOUR-NAME.workers.dev).
 * 5. Paste it as the value of the `_webhook` hidden input in both:
 *      - index.html             (newsletter-form)
 *      - _layouts/scholars.html (scholars-newsletter-form)
 *
 * ── HOW IT WORKS ───────────────────────────────────────────────────────────
 *
 * FormSubmit → Worker (validates + dedupes) → GitHub API → CSV updated
 *
 * The 5-minute IMAP sync workflow remains active as a fallback safety net.
 *
 * ── SECURITY ───────────────────────────────────────────────────────────────
 *
 * - Honeypot field (_honey) rejects bots.
 * - Subject filter ensures only newsletter signups are processed.
 * - Email is validated and deduplicated before writing.
 * - GITHUB_TOKEN is stored as an encrypted Cloudflare secret (never in source).
 */

const CSV_PATH = "newsletter_subscribers.csv";
const SUBJECT_FILTER = "medieval visions newsletter registration";
const EXCLUDE = new Set([
    "contact@medievalvisions.com",
    "noreply@formsubmit.co",
    "no-reply@formsubmit.co",
]);

export default {
    async fetch(request, env) {
        if (request.method !== "POST") {
            return new Response("OK", { status: 200 });
        }

        // Parse both JSON and form-encoded payloads (FormSubmit supports both modes)
        let fields = {};
        const contentType = request.headers.get("content-type") || "";
        try {
            if (contentType.includes("application/json")) {
                fields = await request.json();
            } else {
                const fd = await request.formData();
                for (const [k, v] of fd.entries()) fields[k] = v;
            }
        } catch {
            return new Response("OK", { status: 200 });
        }

        // Reject bots via honeypot
        if (fields["_honey"]) return new Response("OK", { status: 200 });

        // Only process newsletter registration submissions
        const subject = (fields["_subject"] || "").toLowerCase();
        if (!subject.includes(SUBJECT_FILTER)) {
            return new Response("OK", { status: 200 });
        }

        const email = (fields["email"] || "").toLowerCase().trim();
        if (!email || !email.includes("@") || !email.includes(".") || EXCLUDE.has(email)) {
            return new Response("OK", { status: 200 });
        }

        const githubToken = env.GITHUB_TOKEN;
        const githubRepo = env.GITHUB_REPO;
        if (!githubToken || !githubRepo) {
            console.error("Worker secrets GITHUB_TOKEN or GITHUB_REPO not configured.");
            return new Response("Worker not configured", { status: 500 });
        }

        const apiUrl = `https://api.github.com/repos/${githubRepo}/contents/${CSV_PATH}`;
        const ghHeaders = {
            Authorization: `token ${githubToken}`,
            "User-Agent": "subscriber-webhook/1.0",
            Accept: "application/vnd.github+json",
        };

        // Read current CSV from GitHub
        const getResp = await fetch(apiUrl, { headers: ghHeaders });
        if (!getResp.ok) {
            console.error(`GitHub read failed: ${getResp.status}`);
            return new Response("GitHub read failed", { status: 502 });
        }
        const fileData = await getResp.json();
        const currentContent = atob(fileData.content.replace(/\s/g, ""));

        // Deduplicate — skip if email already exists
        if (currentContent.toLowerCase().includes(email)) {
            return new Response("OK", { status: 200 });
        }

        // Append new row
        const now = new Date().toISOString().split(".")[0] + "+00:00";
        const newRow = `${email},yes,formsubmit_webhook,${now},\n`;
        const updatedContent = currentContent.endsWith("\n")
            ? currentContent + newRow
            : currentContent + "\n" + newRow;

        // Write updated CSV back to GitHub
        const putResp = await fetch(apiUrl, {
            method: "PUT",
            headers: { ...ghHeaders, "Content-Type": "application/json" },
            body: JSON.stringify({
                message: `chore: add subscriber via webhook`,
                content: btoa(updatedContent),
                sha: fileData.sha,
            }),
        });

        if (!putResp.ok) {
            const errText = await putResp.text();
            console.error(`GitHub write failed: ${putResp.status} — ${errText}`);
            return new Response("GitHub write failed", { status: 502 });
        }

        console.log(`Subscriber added: ${email}`);
        return new Response("OK", { status: 200 });
    },
};
