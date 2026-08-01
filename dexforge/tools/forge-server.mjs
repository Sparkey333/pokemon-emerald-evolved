// Indigo Dexforge forge server — zero dependency.
// Serves the dashboard AND gives it live write endpoints so the whole
// prompt -> art -> sheets -> dex loop runs in-app with no terminal.
//
//   node tools/forge-server.mjs [port]
//
//   POST /api/forge  {name, types[], evolvesFromName, method, theme, prompt, palette}
//   POST /api/map    {cell, slug}          assign a montage cell to an Evolved species
//   POST /api/rebuild                      rebuild data + regenerate a section
//   GET  /api/jobs                         job list + log tails
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { extname, join, normalize, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const PORT = Number(process.argv[2] || 8642);
const PY = 'python3';

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon', '.md': 'text/plain', '.csv': 'text/csv',
};

const jobs = [];
let nextId = 1;

function newJob(kind, label) {
  const job = { id: nextId++, kind, label, status: 'running', log: [], started: Date.now() };
  jobs.unshift(job);
  return job;
}

/** Run a queue of [cmd, args] serially, streaming output into the job log. */
function runSteps(job, steps) {
  const step = steps.shift();
  if (!step) {
    job.status = 'done';
    job.ended = Date.now();
    return;
  }
  job.log.push(`$ ${step[0]} ${step[1].join(' ')}`);
  const p = spawn(step[0], step[1], { cwd: ROOT });
  const take = (b) => {
    for (const line of String(b).split('\n')) if (line.trim()) job.log.push(line.trim());
    if (job.log.length > 400) job.log.splice(0, job.log.length - 400);
  };
  p.stdout.on('data', take);
  p.stderr.on('data', take);
  p.on('close', (code) => {
    if (code !== 0) {
      job.status = 'failed';
      job.ended = Date.now();
      job.log.push(`exited with code ${code}`);
      return;
    }
    runSteps(job, steps);
  });
  p.on('error', (e) => {
    job.status = 'failed';
    job.ended = Date.now();
    job.log.push(String(e));
  });
}

async function readJson(path, fallback) {
  try { return JSON.parse(await readFile(path, 'utf8')); } catch { return fallback; }
}

const slugify = (s) => String(s).toLowerCase().replace(/[^a-z0-9]/g, '');

function body(req) {
  return new Promise((resolve, reject) => {
    let d = '';
    req.on('data', (c) => {
      d += c;
      if (d.length > 1e6) reject(new Error('body too large'));
    });
    req.on('end', () => { try { resolve(JSON.parse(d || '{}')); } catch (e) { reject(e); } });
  });
}

const send = (res, code, obj) => {
  res.writeHead(code, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(obj));
};

createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');

  // ── API ───────────────────────────────────────────────────────────────
  if (url.pathname === '/api/jobs') {
    return send(res, 200, jobs.slice(0, 25));
  }

  if (url.pathname === '/api/forge' && req.method === 'POST') {
    let spec;
    try { spec = await body(req); } catch (e) { return send(res, 400, { error: String(e) }); }
    if (!spec.name || !String(spec.name).trim()) {
      return send(res, 400, { error: 'name is required' });
    }
    // Standing naming rule: no colour / jewel / gemstone / mineral names.
    const BANNED = /\b(garnet|cobalt|amethyst|obsidian|opal|jade|ruby|emerald|sapphire|topaz|onyx|indigo|crimson|azure|scarlet|violet|amber|pearl|quartz|malachite|celestine)\b/i;
    if (BANNED.test(spec.name)) {
      return send(res, 400, {
        error: `"${spec.name}" is a colour/gem name — the house rule bans those. ` +
               `Use a direct, characterful name drawn from what the creature does.`,
      });
    }
    const slug = slugify(spec.name);
    const file = join(ROOT, 'data', 'custom-species.json');
    const list = await readJson(file, []);
    if (list.some((s) => slugify(s.name) === slug)) {
      return send(res, 409, { error: `${spec.name} already exists in the forge` });
    }
    list.push({
      slug,
      name: String(spec.name).trim(),
      types: (spec.types || []).filter(Boolean).map((t) => String(t).toLowerCase()),
      evolvesFromName: spec.evolvesFromName || null,
      method: spec.method || 'Lv 50',
      theme: spec.theme || '',
      prompt: spec.prompt || '',
      palette: spec.palette || '',
      created: new Date().toISOString(),
    });
    await mkdir(join(ROOT, 'data'), { recursive: true });
    await writeFile(file, JSON.stringify(list, null, 1));

    const job = newJob('forge', spec.name);
    runSteps(job, [[PY, [join('tools', 'forge_species.py'), '--slug', slug]]]);
    return send(res, 200, { ok: true, slug, jobId: job.id });
  }

  if (url.pathname === '/api/map' && req.method === 'POST') {
    let spec;
    try { spec = await body(req); } catch (e) { return send(res, 400, { error: String(e) }); }
    const { cell, slug } = spec;
    if (!cell || !slug) return send(res, 400, { error: 'cell and slug are required' });
    if (!existsSync(join(ROOT, 'vault', 'evolved', 'montage', `${cell}-normal.png`))) {
      return send(res, 404, { error: `unknown montage cell ${cell}` });
    }
    const file = join(ROOT, 'data', 'montage-map.json');
    const map = await readJson(file, {});
    map[slug] = cell;
    await writeFile(file, JSON.stringify(map, null, 1));

    const job = newJob('map', `${cell} → ${slug}`);
    runSteps(job, [
      [PY, [join('tools', 'build_species.py')]],
      [PY, [join('tools', 'gen_sheets.py'), '--slug', slug]],
    ]);
    return send(res, 200, { ok: true, jobId: job.id });
  }

  if (url.pathname === '/api/rebuild' && req.method === 'POST') {
    const spec = await body(req).catch(() => ({}));
    const args = [join('tools', 'gen_sheets.py')];
    if (spec.section) args.push('--only', spec.section);
    const job = newJob('rebuild', spec.section || 'all');
    runSteps(job, [[PY, [join('tools', 'build_species.py')]], [PY, args]]);
    return send(res, 200, { ok: true, jobId: job.id });
  }

  // ── static ────────────────────────────────────────────────────────────
  try {
    let path = normalize(decodeURIComponent(url.pathname)).replace(/^(\.\.[/\\])+/, '');
    if (path === '/' || path === '\\') path = '/dashboard.html';
    const file = await readFile(join(ROOT, path));
    res.writeHead(200, {
      'Content-Type': MIME[extname(path)] || 'application/octet-stream',
      'Cache-Control': 'no-store',
    });
    res.end(file);
  } catch {
    res.writeHead(404);
    res.end('not found');
  }
}).listen(PORT, () => console.log(`Indigo Dexforge forge server on http://localhost:${PORT}`));
