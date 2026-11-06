import { readFileSync, writeFileSync } from 'node:fs';
import { hasWall, mazeGridText, parseMazeText, type Edge, type Maze } from '/home/santi/Code/MicroMouse/Micras/worktrees/maze-studio-photo/src/maze';
import { recogniseMaze, type Recognition } from '/home/santi/Code/MicroMouse/Micras/worktrees/maze-studio-photo/src/photo/recognise';
import { scoreRecognition, wrongEdges } from '/home/santi/Code/MicroMouse/Micras/worktrees/maze-studio-photo/src/photo/score';

const ROOT = '/home/santi/.cache/maze-dataset/heldout/';
const V = '/home/santi/Code/MicroMouse/Micras/worktrees/maze-studio-photo/vendor/mazefiles/';
const index = JSON.parse(readFileSync(ROOT + 'index.json', 'utf8'));
const JITTER = 0.01;
const SEEDS = [1, 2, 3, 4];

type Pt = { x: number; y: number };
const pts = (c: number[][]) => c.map(([x, y]) => ({ x, y })) as [Pt, Pt, Pt, Pt];

function jitter(c: number[][], seed: number) {
  let s = seed * 7919;
  const rand = () => ((s = (s * 16807) % 2147483647) / 2147483647) * 2 - 1;
  return c.map(([x, y], k) => {
    const side = Math.hypot(c[(k + 1) % 4][0] - x, c[(k + 1) % 4][1] - y);
    return [x + rand() * JITTER * side, y + rand() * JITTER * side];
  });
}

const conf = (r: Recognition, e: Edge) => {
  const n = r.maze.width;
  return e.direction === 'horizontal' ? r.confidence.horizontal[e.y * n + e.x] : r.confidence.vertical[e.y * (n + 1) + e.x];
};

function internalEdges(n: number): Edge[] {
  const out: Edge[] = [];
  for (let y = 1; y < n; y++) for (let x = 0; x < n; x++) out.push({ direction: 'horizontal', x, y });
  for (let y = 0; y < n; y++) for (let x = 1; x < n; x++) out.push({ direction: 'vertical', x, y });
  return out;
}

function rules(found: Maze, truth: Maze) {
  const n = found.width;
  const goal = new Set(truth.goals.map((c) => c.y * n + c.x));
  const isGoal = (x: number, y: number) => x >= 0 && y >= 0 && x < n && y < n && goal.has(y * n + x);
  const wall = (d: 'horizontal' | 'vertical', x: number, y: number) =>
    x >= 0 && y >= 0 && (d === 'horizontal' ? x < n && y <= n : x <= n && y < n) && hasWall(found, { direction: d, x, y });
  const lonePost = (px: number, py: number) =>
    !(wall('horizontal', px - 1, py) || wall('horizontal', px, py) || wall('vertical', px, py - 1) || wall('vertical', px, py)) &&
    !(isGoal(px - 1, py - 1) && isGoal(px, py - 1) && isGoal(px - 1, py) && isGoal(px, py));
  const start = truth.start ?? { x: 0, y: 0 };
  const seen = new Uint8Array(n * n);
  const queue = [start];
  seen[start.y * n + start.x] = 1;
  while (queue.length) {
    const { x, y } = queue.pop()!;
    const go = (nx: number, ny: number, blocked: boolean) => {
      if (!blocked && nx >= 0 && ny >= 0 && nx < n && ny < n && !seen[ny * n + nx]) {
        seen[ny * n + nx] = 1;
        queue.push({ x: nx, y: ny });
      }
    };
    go(x, y + 1, wall('horizontal', x, y + 1));
    go(x, y - 1, wall('horizontal', x, y));
    go(x + 1, y, wall('vertical', x + 1, y));
    go(x - 1, y, wall('vertical', x, y));
  }
  const startOpen =
    [wall('horizontal', start.x, start.y + 1), wall('horizontal', start.x, start.y), wall('vertical', start.x + 1, start.y), wall('vertical', start.x, start.y)].filter((w) => !w).length > 1;
  return (e: Edge) => {
    const [a, b] = e.direction === 'horizontal' ? [{ x: e.x, y: e.y - 1 }, { x: e.x, y: e.y }] : [{ x: e.x - 1, y: e.y }, { x: e.x, y: e.y }];
    const [p, q] = e.direction === 'horizontal' ? [[e.x, e.y], [e.x + 1, e.y]] : [[e.x, e.y], [e.x, e.y + 1]];
    const broken: string[] = [];
    if (lonePost(p[0], p[1]) || lonePost(q[0], q[1])) broken.push('lonePost');
    if (!seen[a.y * n + a.x] || !seen[b.y * n + b.x]) broken.push('unreachable');
    if (startOpen && [a, b].some((c) => c.x === start.x && c.y === start.y)) broken.push('startOpen');
    if (hasWall(found, e) && isGoal(a.x, a.y) && isGoal(b.x, b.y)) broken.push('goalWall');
    return broken;
  };
}

const rows: unknown[] = [];
const wrongDump: Record<string, unknown> = {};
for (const a of index) {
  const data = new Uint8Array(readFileSync(ROOT + 'raw/' + a.id + '.rgba'));
  const photo = { width: a.width, height: a.height, data };
  const t0 = performance.now();
  const r = recogniseMaze(photo, { size: a.size, corners: pts(a.corners) });
  const ms = performance.now() - t0;
  if (a.role === 'unknown') {
    const walls = internalEdges(a.size).filter((e) => hasWall(r.maze, e));
    rows.push({ id: a.id, role: a.role, walls: walls.length, unsure: internalEdges(a.size).filter((e) => conf(r, e) < 0.3).length, ms: Math.round(ms) });
    wrongDump[a.id] = { corners: a.corners, size: a.size, proposal: walls.map((e) => [e.direction, e.x, e.y, +conf(r, e).toFixed(3)]), text: mazeGridText(r.maze) };
    continue;
  }
  const p = parseMazeText(readFileSync(V + a.mazeFile, 'utf8'), a.mazeFile);
  if (!p.ok) throw new Error('parse ' + a.mazeFile);
  const truth = p.value.maze;
  const wrong = wrongEdges(r.maze, truth);
  const broke = rules(r.maze, truth);
  const wrongInfo = wrong.map((e) => ({ ...e, truth: hasWall(truth, e), confidence: +conf(r, e).toFixed(3), rules: broke(e) }));
  const maxWrong = Math.max(0, ...wrongInfo.map((w) => w.confidence));
  const rightUnder = internalEdges(a.size).filter((e) => hasWall(r.maze, e) === hasWall(truth, e) && conf(r, e) <= maxWrong).length;
  const jit = SEEDS.map((s) => scoreRecognition(recogniseMaze(photo, { size: a.size, corners: pts(jitter(a.corners, s)) }).maze, truth));
  const img = a.cornersImage && a.distortion !== 'none' ? scoreRecognition(recogniseMaze(photo, { size: a.size, corners: pts(a.cornersImage) }).maze, truth) : null;
  const confs = internalEdges(a.size).map((e) => +conf(r, e).toFixed(3));
  rows.push({
    id: a.id, role: a.role, size: a.size, category: a.category, distortion: a.distortion, k1: a.k1, pxPerCell: a.pxPerCell,
    score: scoreRecognition(r.maze, truth), wrong: wrong.length, jitterMean: jit.reduce((x, y) => x + y) / jit.length, jitterMin: Math.min(...jit),
    imageCornersScore: img, maxWrongConfidence: maxWrong, rightUnderMax: rightUnder,
    wrongEdges: wrongInfo, ms: Math.round(ms), confidences: confs,
    rightConfidences: internalEdges(a.size).filter((e) => hasWall(r.maze, e) === hasWall(truth, e)).map((e) => +conf(r, e).toFixed(3)),
  });
  wrongDump[a.id] = { corners: a.corners, size: a.size, mazeFile: a.mazeFile, wrong: wrongInfo.map((w) => [w.direction, w.x, w.y, w.truth]) };
  console.error(a.id, (scoreRecognition(r.maze, truth) * 100).toFixed(2), wrong.length);
}
writeFileSync(ROOT + 'results.json', JSON.stringify(rows));
writeFileSync(ROOT + 'wrong.json', JSON.stringify(wrongDump));
