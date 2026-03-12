import { mkdir, writeFile } from 'node:fs/promises';
import { execSync } from 'node:child_process';

const now = new Date();
const stamp = now.toISOString().replace(/[:.]/g, '-');
const dir = 'docs/reports';
await mkdir(dir, { recursive: true });

const gitStatus = execSync('git status --short', { encoding: 'utf8' }).trim() || 'clean';
const lastCommit = execSync('git log -1 --oneline', { encoding: 'utf8' }).trim();

const content = `# Progress Report\n\n- Generated: ${now.toISOString()}\n- Last commit: ${lastCommit}\n\n## What changed\n- Fill this in\n\n## What was verified\n- Fill this in\n\n## Artifacts\n- Screenshots: artifacts/screenshots/\n- Playwright HTML report: artifacts/playwright-report/\n\n## Git status\n\n\`\`\`\n${gitStatus}\n\`\`\`\n\n## Next steps\n- Fill this in\n\n## Questions / blockers\n- Fill this in\n`;

const path = `${dir}/${stamp}-status-report.md`;
await writeFile(path, content, 'utf8');
console.log(path);
