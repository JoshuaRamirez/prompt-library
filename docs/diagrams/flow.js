// flow.js: rendered into the #flow-* elements of index.html.
(() => {
const { useCases, byId, color, tip, untip, esc, swatch } = PL;

// ---- node catalogue: id -> label, role, source file -------------------------
const N = {};
const def = (id, label, role, file) => (N[id] = { id, label, role, file });

for (const u of useCases) def(`uc:${u.id}`, u.label, "Use case", "");

def("s:save", "/prompt-save", "Slash command", "commands/prompt-save.md");
def("s:find", "/prompt-find", "Slash command", "commands/prompt-find.md");
def("s:use",  "/prompt-use",  "Slash command", "commands/prompt-use.md");
def("s:list", "/prompt-list", "Slash command", "commands/prompt-list.md");
def("s:edit", "/prompt-edit", "Slash command", "commands/prompt-edit.md");
def("s:claude", "Claude, unprompted", "Skill-driven tool call", "SKILL.md · working rules; proactive save / reuse");
def("s:cli",  "promptlib (shell)", "CLI entry point", "bin/promptlib");
def("s:hook", "SessionStart hook", "Hook", "hooks/hooks.json");

def("a:mcp",  "MCP server", "Adapter", "shared_mcp.py gateway (127.0.0.1) → server/mcp_server.py → lib/promptlib/mcp/tool_registry.py");
def("a:cli",  "CLI adapter", "Adapter", "lib/promptlib/cli/main.py");
def("a:hook", "session_index.py", "Adapter", "hooks/session_index.py");

for (const m of ["search", "list", "get", "render", "stats", "add", "update", "delete", "import_rows"])
  def(`m:${m}`, `service.${m}()`, "Service method", "lib/promptlib/service.py");

def("c:filter",    "PromptFilter", "Domain", "lib/promptlib/domain/prompt_filter.py");
def("c:kw",        "KeywordSearchStrategy", "Search", "lib/promptlib/search/keyword_strategy.py");
def("c:renderer",  "TemplateRenderer", "Rendering", "lib/promptlib/rendering/template_renderer.py");
def("c:slugs",     "SlugFactory", "Identifiers", "lib/promptlib/identifiers.py");
def("c:repo",      "PromptRepository", "Domain", "lib/promptlib/domain/prompt_repository.py");
def("x:tokenizer", "Tokenizer", "Search", "lib/promptlib/search/tokenizer.py");
def("x:read",      "CsvTable.read_all", "Storage", "lib/promptlib/storage/csv_table.py");
def("x:lock",      "FileLock (flock)", "Storage", "lib/promptlib/storage/file_lock.py");
def("x:atomic",    "AtomicFileWriter", "Storage", "lib/promptlib/storage/atomic_writer.py");
def("f:csv",       "prompts.csv", "File", "~/.claude/prompt-library/prompts.csv");
def("f:lock",      "prompts.csv.lock", "File", "~/.claude/prompt-library/prompts.csv.lock");

const ADAPTER = { "s:cli": "a:cli", "s:hook": "a:hook" }; // everything else goes through MCP

// ---- what each service method calls (service.py + prompt_repository.py) ------
const READ = ["c:repo", "x:read", "f:csv"];
const WRITE = [["c:repo", "x:lock", "f:lock"], ["c:repo", "x:read", "f:csv"], ["c:repo", "x:atomic", "f:csv"]];
const CHAINS = {
  search:      [["c:filter"], ["c:kw", "x:tokenizer"], READ],
  list:        [["c:filter"], READ],
  get:         [READ],
  render:      [READ, ["c:renderer"]],
  stats:       [READ],
  add:         [["c:renderer"], ["c:slugs"], ...WRITE],
  update:      [["c:renderer"], ...WRITE],
  delete:      [...WRITE],
  import_rows: [["c:slugs"], ...WRITE],
};

// ---- which surfaces each use case enters through (commands/*.md, SKILL.md, cli/main.py) ----
const ROUTES = [
  ["save",    "s:save",   ["search", "stats", "add", "update"]],
  ["save",    "s:claude", ["search", "add"]],
  ["save",    "s:cli",    ["add"]],
  ["find",    "s:find",   ["search", "get", "list"]],
  ["find",    "s:claude", ["search", "get"]],
  ["find",    "s:cli",    ["search", "get"]],
  ["reuse",   "s:use",    ["get", "search", "render"]],
  ["reuse",   "s:claude", ["render"]],
  ["reuse",   "s:cli",    ["render"]],
  ["browse",  "s:list",   ["stats", "list"]],
  ["browse",  "s:cli",    ["list"]],
  ["edit",    "s:edit",   ["get", "search", "update", "delete"]],
  ["edit",    "s:cli",    ["update", "delete"]],
  ["inspect", "s:claude", ["stats"]],
  ["inspect", "s:cli",    ["stats"]],
  ["session", "s:hook",   ["list"]],
  ["import",  "s:cli",    ["import_rows"]],
];

// ---- expand into full paths, then aggregate links per (source, target, use case) ----
const paths = [];
for (const [uc, surface, methods] of ROUTES) {
  const adapter = ADAPTER[surface] || "a:mcp";
  for (const m of methods) for (const chain of CHAINS[m])
    paths.push({ uc, nodes: [`uc:${uc}`, surface, adapter, `m:${m}`, ...chain], method: m, surface, adapter, chain });
}
const linkMap = new Map();
const through = new Map(); // node id -> Set(path index)
paths.forEach((p, i) => {
  p.nodes.forEach((n) => (through.get(n) || through.set(n, new Set()).get(n)).add(i));
  for (let k = 0; k < p.nodes.length - 1; k++) {
    const key = `${p.nodes[k]}|${p.nodes[k + 1]}|${p.uc}`;
    const l = linkMap.get(key) || linkMap.set(key, { source: p.nodes[k], target: p.nodes[k + 1], uc: p.uc, value: 0, paths: new Set() }).get(key);
    l.value += 1;
    l.paths.add(i);
  }
});
const usedNodes = [...through.keys()].map((id) => ({ ...N[id] }));

// ---- layout ----
const W = 1420, H = 820, M = { top: 34, right: 150, bottom: 8, left: 8 };
const sankey = d3.sankey()
  .nodeId((d) => d.id)
  .nodeAlign(d3.sankeyLeft)
  .nodeWidth(10)
  .nodePadding(13)
  .iterations(64)
  .linkSort((a, b) => byId[a.uc].slot - byId[b.uc].slot)
  .extent([[M.left, M.top], [W - M.right, H - M.bottom]]);
const graph = sankey({ nodes: usedNodes, links: [...linkMap.values()].map((l) => ({ ...l })) });

const svg = d3.select("#flow-chart").append("svg").attr("viewBox", [0, 0, W, H]).attr("role", "img")
  .attr("aria-label", "Sankey diagram of control flow from eight use cases through entry points, adapters, service methods, components and storage.");

const COLS = ["Use case", "Entry point", "Adapter", "Service method", "Component", "Helper · storage", "File"];
const colX = d3.rollup(graph.nodes, (v) => d3.min(v, (d) => d.x0), (d) => d.depth);
svg.append("g").selectAll("text").data([...colX]).join("text")
  .attr("class", "col-head").attr("x", ([, x]) => x).attr("y", 14).text(([depth]) => COLS[depth] || "");

const linkG = svg.append("g").attr("fill", "none");
const link = linkG.selectAll("path").data(graph.links).join("path")
  .attr("d", d3.sankeyLinkHorizontal())
  .style("stroke", (d) => color(byId[d.uc].slot))
  .attr("stroke-width", (d) => Math.max(1.5, d.width))
  .attr("stroke-opacity", 0.42)
  .on("mousemove", (e, d) => {
    tip(e, `<div class="row">${swatch(byId[d.uc].slot)}<b>${esc(byId[d.uc].label)}</b></div>
      ${esc(d.source.label)} → ${esc(d.target.label)}<br><span class="k">${d.value} call path${d.value > 1 ? "s" : ""}</span>`);
    highlight(d.paths);
  })
  .on("mouseleave", () => { untip(); highlight(null); });

const node = svg.append("g").selectAll("g").data(graph.nodes).join("g");
node.append("rect")
  .attr("x", (d) => d.x0).attr("y", (d) => d.y0)
  .attr("width", (d) => d.x1 - d.x0).attr("height", (d) => Math.max(2, d.y1 - d.y0))
  .attr("rx", 2)
  .style("fill", (d) => (d.id.startsWith("uc:") ? color(byId[d.id.slice(3)].slot) : "var(--node)"));
node.append("text").attr("class", "halo")
  .attr("x", (d) => d.x1 + 6)
  .attr("y", (d) => (d.y0 + d.y1) / 2).attr("dy", "0.35em")
  .text((d) => d.label);
// wide invisible hit target, larger than the mark
node.append("rect")
  .attr("x", (d) => d.x0 - 4).attr("y", (d) => d.y0 - 3)
  .attr("width", (d) => d.x1 - d.x0 + 8 + 7 * d.label.length).attr("height", (d) => Math.max(10, d.y1 - d.y0 + 6))
  .attr("fill", "transparent")
  .on("mousemove", (e, d) => {
    const ids = through.get(d.id);
    const per = d3.rollups([...ids], (v) => v.length, (i) => paths[i].uc).sort((a, b) => byId[a[0]].slot - byId[b[0]].slot);
    tip(e, `<b>${esc(d.label)}</b> <span class="k">· ${esc(d.role)}</span>
      ${d.file ? `<br><code>${esc(d.file)}</code>` : ""}
      <br><span class="k">${ids.size} call paths pass through</span>
      ${per.map(([uc, n]) => `<div class="row">${swatch(byId[uc].slot)}${esc(byId[uc].label)} <span class="k">${n}</span></div>`).join("")}`);
    highlight(ids);
  })
  .on("mouseleave", () => { untip(); highlight(null); });

// ---- highlighting & isolation ----
const active = new Set(useCases.map((u) => u.id));
function highlight(pathIds) {
  link.attr("stroke-opacity", (d) => {
    if (!active.has(d.uc)) return 0.05;
    if (!pathIds) return 0.42;
    for (const i of d.paths) if (pathIds.has(i)) return 0.8;
    return 0.07;
  });
}
const legend = d3.select("#flow-legend");
legend.selectAll("button").data(useCases).join("button")
  .attr("type", "button").attr("aria-pressed", "true")
  .html((u) => `<span class="swatch" style="background:${color(u.slot)}"></span>${esc(u.label)}`)
  .on("click", function (e, u) {
    // first click isolates; clicking the only active one restores all
    if (active.size === useCases.length) { active.clear(); active.add(u.id); }
    else if (active.has(u.id) && active.size === 1) useCases.forEach((x) => active.add(x.id));
    else active.has(u.id) ? active.delete(u.id) : active.add(u.id);
    legend.selectAll("button").attr("aria-pressed", (x) => active.has(x.id));
    highlight(null);
  });
legend.append("span").attr("class", "hint").text("Click to isolate · click again to restore");

// ---- table view ----
d3.select("#flow-table tbody").selectAll("tr").data(paths).join("tr").html((p) => `
  <td>${esc(byId[p.uc].label)}</td><td>${esc(N[p.surface].label)}</td><td>${esc(N[p.adapter].label)}</td>
  <td><code>${esc(p.method)}</code></td><td>${p.chain.map((c) => esc(N[c].label)).join(" → ")}</td>`);
})();
