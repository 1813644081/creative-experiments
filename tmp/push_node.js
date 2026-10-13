// Push the whole working tree to origin/main in small batches.
// All path/hash data flows through git stdio (no shell quoting, no codepage loss).
const { execFileSync, execFile } = require('child_process');
const fs = require('fs');
const path = require('path');

const repo = process.argv[2];
process.chdir(repo);

const GIT = (args, opts = {}) =>
  execFileSync('git', args, { maxBuffer: 1 << 30, encoding: opts.encoding ?? 'utf8', ...opts });

const env = {
  ...process.env,
  GIT_TERMINAL_PROMPT: '0',
  GIT_SSH_COMMAND: 'ssh -F C:/dsh-ssh/config',
};
const G = (args, opts = {}) => execFileSync('git', args, { maxBuffer: 1 << 30, encoding: 'utf8', env, ...opts });

const SKIP = new Set([
  'tmp/push_batches.log',
  'tmp/probe_post.js',
  'tmp/probe_slow.js',
  'tmp/probe_rate.js',
  'tmp/push_batches.ps1',
  'tmp/push_direct.ps1',
  'tmp/recover_blobs.js',
]);

function listPaths() {
  const out = G(['ls-files', '-z', '-o', '-c', '--exclude-standard'], { encoding: 'buffer' });
  return out.toString('utf8').split('\u0000').filter(Boolean).filter((p) => !SKIP.has(p));
}

function blobSizes(paths) {
  // One hash-object call for every path, then one batch-check for every size.
  const inBuf = Buffer.from(paths.join('\n') + '\n', 'utf8');
  const shas = G(['hash-object', '-w', '--stdin-paths'], { input: inBuf }).trim().split('\n').filter(Boolean);
  if (shas.length !== paths.length) throw new Error(`hash count ${shas.length} != ${paths.length}`);
  const sizeOut = G(['cat-file', '--batch-check=%(objectsize)'], { input: Buffer.from(shas.join('\n') + '\n', 'utf8') })
    .trim().split('\n').map((s) => parseInt(s.trim(), 10));
  if (sizeOut.length !== shas.length) throw new Error(`size count ${sizeOut.length} != ${shas.length}`);
  return shas.map((sha, i) => ({ sha, size: sizeOut[i] }));
}

function runPush(args) {
  const r = require('child_process').spawnSync('git', args, { env, encoding: 'utf8' });
  return { code: r.status, out: (r.stdout || '') + (r.stderr || '') };
}

function main() {
  const paths = listPaths();
  const blobs = blobSizes(paths);
  const totalRaw = blobs.reduce((a, b) => a + b.size, 0);
  console.log(`files=${paths.length} rawBufferMB=${(totalRaw / 1048576).toFixed(2)}`);

  // Fresh root history, then append one commit per small batch.
  try { G(['update-ref', '-d', 'refs/heads/main']); } catch { /* branch may not exist */ }

  const LIMIT = 96 * 1024;
  let idx = 0;
  let batch = 0;
  let failures = 0;

  while (idx < blobs.length) {
    const start = idx;
    let bytes = 0;
    const chunks = [];
    while (idx < blobs.length && (bytes < LIMIT || bytes === 0)) {
      chunks.push(Buffer.from(`100644 ${blobs[idx].sha}\t${paths[idx]}\u0000`, 'utf8'));
      bytes += blobs[idx].size;
      idx++;
    }
    G(['update-index', '-z', '--add', '--index-info'], { input: Buffer.concat(chunks) });
    const tree = G(['write-tree']).trim();
    const parentLine = (() => {
      try { return G(['rev-parse', '--verify', 'HEAD']).trim(); } catch { return null; }
    })();
    batch++;
    const commitArgs = ['commit-tree', tree];
    if (parentLine) commitArgs.push('-p', parentLine);
    const commitSha = G(commitArgs, { input: Buffer.from(`Add content batch ${batch}\n`, 'utf8') }).trim();
    G(['update-ref', 'refs/heads/main', commitSha]);

    let r = runPush(['push', 'origin', 'main']);
    if (r.code !== 0) r = runPush(['push', 'origin', 'main']);
    if (r.code !== 0) r = runPush(['push', '--force', 'origin', 'main']);
    if (r.code === 0) {
      console.log(`OK batch ${batch} ${commitSha.slice(0, 7)} bytes=${bytes} idx=${idx}/${blobs.length}`);
    } else {
      failures++;
      console.log(`FAIL batch ${batch} bytes=${bytes} :: ${r.out.trim().split('\n').slice(-2).join(' | ')}`);
      break;
    }
  }

  const localHead = G(['rev-parse', 'HEAD']).trim();
  const remote = G(['ls-remote', 'origin', 'refs/heads/main'], { encoding: 'utf8', env }).trim();
  console.log(`localHead=${localHead}`);
  console.log(`remote=${remote}`);
  console.log(`batches=${batch} failures=${failures}`);
  const tracked = G(['ls-tree', '-r', '--name-only', 'HEAD']).trim().split('\n').filter(Boolean).length;
  console.log(`trackedInCommit=${tracked}`);
}

main();
