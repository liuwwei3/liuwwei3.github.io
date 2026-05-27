/**
 * Pre-render LaTeX math to KaTeX HTML before Jekyll/kramdown processes markdown.
 * Run: node build-math.js
 *
 * Reads .md files from blogs/, replaces $...$ and $$...$$ with KaTeX HTML,
 * writes back. Jekyll then sees already-rendered math that kramdown won't touch.
 */
const fs = require('fs');
const path = require('path');
const katex = require('katex');

const BLOGS_DIR = path.join(__dirname, 'blogs');

function renderMath(md) {
  // State machine: track whether we're inside display math ($$...$$)
  const result = [];
  let i = 0;

  while (i < md.length) {
    // Check for display math $$...$$
    if (md[i] === '$' && md[i + 1] === '$') {
      const end = md.indexOf('$$', i + 2);
      if (end === -1) {
        result.push(md.slice(i));
        break;
      }
      const latex = md.slice(i + 2, end).trim();
      try {
        const html = katex.renderToString(latex, { displayMode: true, throwOnError: false });
        result.push(html);
      } catch (e) {
        result.push(md.slice(i, end + 2)); // keep original on error
      }
      i = end + 2;
      continue;
    }

    // Check for inline math $...$
    // Must NOT be preceded by $ (avoid $$ confusion) and NOT followed by $
    if (md[i] === '$' && md[i - 1] !== '$' && md[i + 1] !== '$') {
      // Skip escaped \$
      if (md[i - 1] === '\\') {
        result.push('$');
        i++;
        continue;
      }
      const end = md.indexOf('$', i + 1);
      if (end === -1) {
        result.push(md.slice(i));
        break;
      }
      const latex = md.slice(i + 1, end).trim();
      if (latex.length === 0) {
        // Empty $$ — could be a stray $
        result.push('$');
        i++;
        continue;
      }
      try {
        const html = katex.renderToString(latex, { displayMode: false, throwOnError: false });
        result.push(html);
      } catch (e) {
        result.push(md.slice(i, end + 1)); // keep original on error
      }
      i = end + 1;
      continue;
    }

    result.push(md[i]);
    i++;
  }

  return result.join('');
}

// Process all .md files in blogs/
const files = fs.readdirSync(BLOGS_DIR).filter(f => f.endsWith('.md'));
let total = 0;

for (const file of files) {
  const filePath = path.join(BLOGS_DIR, file);
  const original = fs.readFileSync(filePath, 'utf-8');
  const rendered = renderMath(original);

  if (rendered !== original) {
    fs.writeFileSync(filePath, rendered);
    const formulaCount = (original.match(/\$\$/g) || []).length / 2 + (original.match(/(?<!\$)\$(?!\$)/g) || []).length / 2;
    total += Math.round(formulaCount);
    console.log(`  ${file}: ~${Math.round(formulaCount)} formulas rendered`);
  } else {
    console.log(`  ${file}: no math found`);
  }
}

console.log(`Done — ${files.length} files, ~${total} formulas`);
