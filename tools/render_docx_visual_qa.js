const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const { chromium } = require("playwright-core");

const workspace = path.resolve(__dirname, "..");
const sourceDir = path.join(workspace, "题库解析SOP_DOCX");
const outputDir = path.join(os.tmpdir(), "cams_sop_visual_qa_20260729", "browser");
const bundlePath = path.join(os.tmpdir(), "cams_docx_preview_runtime", "node_modules", "docx-preview", "dist", "docx-preview.min.js");
const runtimeNodeModules = path.join(os.tmpdir(), "cams_docx_preview_runtime", "node_modules");

function resolveJsZipBundle() {
  const directPath = path.join(runtimeNodeModules, "jszip", "dist", "jszip.min.js");
  if (fs.existsSync(directPath)) return directPath;

  const pnpmStore = path.join(runtimeNodeModules, ".pnpm");
  if (fs.existsSync(pnpmStore)) {
    const packageDir = fs.readdirSync(pnpmStore).find(name => name.startsWith("jszip@"));
    if (packageDir) {
      const pnpmPath = path.join(pnpmStore, packageDir, "node_modules", "jszip", "dist", "jszip.min.js");
      if (fs.existsSync(pnpmPath)) return pnpmPath;
    }
  }

  throw new Error(`Unable to locate jszip.min.js under ${runtimeNodeModules}`);
}

const jszipPath = resolveJsZipBundle();
const browserPath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";

if (!outputDir.startsWith(path.resolve(os.tmpdir()))) {
  throw new Error(`Refusing to write outside temp: ${outputDir}`);
}
fs.rmSync(outputDir, { recursive: true, force: true });
fs.mkdirSync(outputDir, { recursive: true });

const documents = ["新教材新题库解析撰写SOP.docx", "新题加入处理SOP.docx"];
let currentDocument = null;

const html = `<!doctype html>
<html><head><meta charset="utf-8"><style>
html,body{margin:0;background:#cfd3d7;font-family:Arial,"Microsoft YaHei",sans-serif}
#container{padding:24px 0}
.docx-wrapper{background:#cfd3d7!important;padding:0!important}
section.docx{margin:0 auto 24px!important;box-shadow:0 2px 10px rgba(0,0,0,.18)!important}
</style></head><body><div id="container"></div>
<script src="/jszip.js"></script><script src="/docx-preview.js"></script><script>
async function render(){
  const response=await fetch('/document.docx');
  const buffer=await response.arrayBuffer();
  await docx.renderAsync(buffer, document.getElementById('container'), null, {
    className:'docx', inWrapper:true, breakPages:true, ignoreWidth:false,
    ignoreHeight:false, ignoreFonts:false, renderHeaders:true, renderFooters:true
  });
  window.__renderDone=true;
}
render().catch(error=>{window.__renderError=String(error);});
</script></body></html>`;

const server = http.createServer((request, response) => {
  if (request.url === "/") {
    response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    response.end(html);
  } else if (request.url === "/docx-preview.js") {
    response.writeHead(200, { "Content-Type": "application/javascript" });
    response.end(fs.readFileSync(bundlePath));
  } else if (request.url === "/jszip.js") {
    response.writeHead(200, { "Content-Type": "application/javascript" });
    response.end(fs.readFileSync(jszipPath));
  } else if (request.url === "/document.docx" && currentDocument) {
    response.writeHead(200, { "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
    response.end(fs.readFileSync(currentDocument));
  } else {
    response.writeHead(404);
    response.end();
  }
});

(async () => {
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  const browser = await chromium.launch({ headless: true, executablePath: browserPath });
  try {
    for (const filename of documents) {
      currentDocument = path.join(sourceDir, filename);
      const stem = path.parse(filename).name;
      const docDir = path.join(outputDir, stem);
      fs.mkdirSync(docDir, { recursive: true });
      const page = await browser.newPage({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 1.25 });
      await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "networkidle" });
      await page.waitForFunction(() => window.__renderDone || window.__renderError, null, { timeout: 30000 });
      const renderError = await page.evaluate(() => window.__renderError || null);
      if (renderError) throw new Error(`${filename}: ${renderError}`);
      const pages = page.locator("section.docx");
      const count = await pages.count();
      for (let index = 0; index < count; index += 1) {
        await pages.nth(index).screenshot({ path: path.join(docDir, `page-${String(index + 1).padStart(2, "0")}.png`) });
      }
      fs.writeFileSync(path.join(docDir, "page-count.txt"), String(count), "utf8");
      console.log(`${filename}: ${count} pages`);
      await page.close();
    }
  } finally {
    await browser.close();
    server.close();
  }
})().catch(error => {
  console.error(error);
  server.close();
  process.exitCode = 1;
});
