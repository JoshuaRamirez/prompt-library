// pack.js: rendered into the #pack-* elements of index.html.
(() => {
const { useCases, byId, color, tip, untip, esc } = PL;

// kind: main | alt | fail. Sources noted per scenario.
const S = (name, kind, src, steps) => ({ name, kind, src, children: steps.map((s) => ({ name: s })) });
const DECOMP = {
  save: [
    S("Save new material", "main", "commands/prompt-save.md", [
      "Select material: the argument, or the latest prompt-shaped text (say which)",
      "prompt_search the gist to check for a near-duplicate",
      "Turn reusable specifics into {{placeholders}}",
      "Give a title and 2–5 retrieval tags",
      "Reuse an existing category from prompt_stats",
      "prompt_add: id slugged from title, variables derived from body",
      "Locked read-modify-write, atomic replace of prompts.csv",
      "Report id, title, tags and detected variables",
    ]),
    S("Near-duplicate exists", "alt", "commands/prompt-save.md · SKILL.md rule 1", [
      "Propose prompt_update on the existing record",
      "Stop for the user's decision",
    ]),
    S("Proactive offer", "alt", "SKILL.md description", [
      "Notice a substantial reusable instruction in the conversation",
      "Offer to save it, then follow ‘Save new material’",
    ]),
    S("Save from the shell", "alt", "cli/main.py · SKILL.md CLI", [
      "promptlib add --title … --prompt - (body on stdin)",
      "--set COLUMN=VALUE adds open columns",
    ]),
    S("Explicit id already taken", "fail", "domain/prompt_repository.py", [
      "DuplicatePromptError raised inside the lock",
      "Nothing is written",
    ]),
  ],
  find: [
    S("Ranked search", "main", "commands/prompt-find.md · search/keyword_strategy.py", [
      "prompt_search with the query (limit 10)",
      "Facets filter the corpus before ranking",
      "Weighted score: title ×3, tags ×2.5, category ×2, body ×1, notes ×0.5",
      "Present id, title, tags, score",
      "Point to /prompt-use <id>",
    ]),
    S("One dominant hit", "alt", "commands/prompt-find.md", [
      "prompt_get the top hit",
      "Show its body",
    ]),
    S("No hits", "alt", "commands/prompt-find.md", [
      "Retry once with the most distinctive term",
      "Fall back to prompt_list to show what exists",
    ]),
    S("Recognised from the session index", "alt", "SKILL.md description", [
      "Request resembles an indexed prompt",
      "Search and offer reuse instead of re-deriving",
    ]),
  ],
  reuse: [
    S("Resolve by id", "main", "commands/prompt-use.md", [
      "Treat the first token as an id",
      "prompt_get it",
    ]),
    S("Resolve by search", "alt", "commands/prompt-use.md", [
      "prompt_get fails, so prompt_search the whole argument",
      "Take the top hit and name it",
    ]),
    S("Fill and apply", "main", "commands/prompt-use.md · rendering/template_renderer.py", [
      "Collect name=value pairs from the arguments",
      "prompt_render substitutes {{name}} placeholders",
      "Show the rendered prompt",
      "Act on it as this turn's instruction",
    ]),
    S("Placeholders left unfilled", "alt", "commands/prompt-use.md", [
      "Infer the unambiguous ones from the conversation",
      "Ask one consolidated question for the rest",
    ]),
    S("Strict render", "fail", "rendering/template_renderer.py", [
      "strict=true with missing values",
      "RenderError lists the missing names",
    ]),
  ],
  browse: [
    S("List everything", "main", "commands/prompt-list.md", [
      "prompt_stats for the tag and category vocabulary",
      "prompt_list",
      "Table grouped by category: id, title, tags, updated",
      "Report total count and CSV path",
    ]),
    S("Filtered list", "alt", "commands/prompt-list.md", [
      "Match the argument against the tag/category vocabulary",
      "prompt_list with tags or category",
    ]),
  ],
  edit: [
    S("Update fields", "main", "commands/prompt-edit.md · domain/prompt.py", [
      "prompt_get the id and show the current record",
      "prompt_update with only the changed fields",
      "New facets become new CSV columns",
      "variables re-derived if the body changed",
      "Show the result and its new updated_at",
    ]),
    S("Id doesn't resolve", "alt", "commands/prompt-edit.md", [
      "prompt_search for candidates",
      "Confirm the target before changing anything",
    ]),
    S("Delete", "main", "commands/prompt-edit.md · SKILL.md rule 6", [
      "State the id and title",
      "Wait for explicit confirmation",
      "prompt_delete returns the removed record",
    ]),
    S("Managed column in an update", "fail", "docs/SCHEMA.md · Prompt.merged_with", [
      "id, created_at, updated_at are dropped from the changes",
    ]),
  ],
  inspect: [
    S("Library stats", "main", "service.py · stats()", [
      "Count, CSV path, search strategy",
      "Declared plus discovered columns",
      "Tag and category distributions",
      "Total prompt characters",
    ]),
    S("Locate the file", "alt", "SKILL.md CLI", [
      "promptlib path",
    ]),
  ],
  session: [
    S("Inject the index", "main", "hooks/session_index.py", [
      "SessionStart hook runs session_index.py",
      "service.list() reads every prompt",
      "One line each: id, title (≤60 chars), tags",
      "Past 60 entries, state the overflow",
    ]),
    S("Empty library", "alt", "hooks/session_index.py", [
      "Print nothing, so an unused plugin costs no context",
    ]),
    S("Any error", "fail", "hooks/session_index.py", [
      "Swallow it and exit 0; never block the session",
    ]),
  ],
  import: [
    S("Upsert a batch", "main", "cli/main.py · PromptRepository.upsert_many", [
      "promptlib import file.json (array of records)",
      "Match on id, replacing existing records",
      "No id: slug from the title",
      "One locked, atomic write for the whole batch",
      "Report the written count and ids",
    ]),
  ],
};

const KIND = { main: { label: "Main scenario", dash: null }, alt: { label: "Alternate", dash: "5 3" }, fail: { label: "Failure / guard", dash: "1.5 3" } };

const data = { name: "prompt-library", children: useCases.map((u) => ({ name: u.label, uc: u.id, children: DECOMP[u.id] })) };
const root = d3.hierarchy(data).count().sort((a, b) => b.value - a.value);
root.each((d) => { d.uc = d.depth === 0 ? null : (d.depth === 1 ? d.data.uc : d.ancestors().find((a) => a.depth === 1).data.uc); });

const SIZE = 900;
d3.pack().size([SIZE, SIZE]).padding((d) => (d.depth === 0 ? 14 : d.depth === 1 ? 8 : 3))(root);

const svg = d3.select("#pack-chart").append("svg").attr("viewBox", `-${SIZE / 2} -${SIZE / 2} ${SIZE} ${SIZE}`)
  .attr("role", "img").attr("aria-label", "Circle packing: eight use cases, each containing its scenarios, each containing its steps.")
  .style("cursor", "pointer").on("click", (e) => zoom(e, root));

const fillFor = (d) => {
  if (d.depth === 0) return "transparent";
  const c = color(byId[d.uc].slot);
  return c;
};
const circle = svg.append("g").selectAll("circle").data(root.descendants().slice(1)).join("circle")
  .style("fill", fillFor)
  .attr("fill-opacity", (d) => (d.depth === 1 ? 0.12 : d.depth === 2 ? 0.2 : 0.85))
  .style("stroke", (d) => color(byId[d.uc].slot))
  .attr("stroke-width", (d) => (d.depth === 3 ? 0 : 1.5))
  .attr("stroke-dasharray", (d) => (d.depth === 2 ? KIND[d.data.kind].dash : null))
  .on("mousemove", (e, d) => {
    const trail = d.ancestors().reverse().slice(1).map((a) => esc(a.data.name)).join(" › ");
    const extra = d.depth === 2 ? `<br><span class="k">${KIND[d.data.kind].label} · ${d.value} steps · ${esc(d.data.src)}</span>`
      : d.depth === 1 ? `<br><span class="k">${d.children.length} scenarios · ${d.value} steps</span>` : "";
    tip(e, `<b>${esc(d.data.name)}</b>${d.depth > 1 ? `<br><span class="k">${trail}</span>` : ""}${extra}`);
  })
  .on("mouseleave", untip)
  .on("click", (e, d) => { e.stopPropagation(); zoom(e, d.children ? d : d.parent); });

const label = svg.append("g").attr("pointer-events", "none").attr("text-anchor", "middle")
  .selectAll("text").data(root.descendants().slice(1)).join("text").attr("class", "halo");

let focus = root, view;
function zoomTo(v) {
  const k = SIZE / v[2];
  view = v;
  circle.attr("transform", (d) => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`).attr("r", (d) => d.r * k);
  label.attr("transform", (d) => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`);
  drawLabels(k);
}
// Labels for the focus's children only, wrapped to fit their circle.
function drawLabels(k) {
  label.each(function (d) {
    const t = d3.select(this);
    t.selectAll("tspan").remove();
    const show = d.parent === focus;
    t.style("display", show ? null : "none");
    if (!show) return;
    const r = d.r * k;
    const fs = d.depth === 1 ? 15 : d.depth === 2 ? 13 : 12;
    t.style("font-size", `${fs}px`).style("font-weight", d.depth < 3 ? 600 : 400);
    const maxChars = Math.max(8, Math.floor((r * 1.6) / (fs * 0.55)));
    const words = d.data.name.split(/\s+/);
    const lines = [];
    let line = "";
    for (const w of words) {
      if ((line + " " + w).trim().length > maxChars && line) { lines.push(line); line = w; } else line = (line + " " + w).trim();
    }
    if (line) lines.push(line);
    const maxLines = Math.max(1, Math.floor((r * 1.5) / (fs * 1.2)));
    const shown = lines.slice(0, maxLines);
    if (lines.length > maxLines) shown[maxLines - 1] = shown[maxLines - 1].replace(/.{0,1}$/, "…");
    shown.forEach((l, i) => t.append("tspan").attr("x", 0).attr("dy", i === 0 ? `${-(shown.length - 1) * 0.6 + 0.35}em` : "1.2em").text(l));
  });
}
function zoom(event, d) {
  focus = d;
  panel(d);
  const target = [focus.x, focus.y, focus.r * 2 + 8];
  if (PL.instant()) { svg.interrupt(); zoomTo(target); return; }
  svg.transition().duration(event && event.altKey ? 2500 : 650)
    .tween("zoom", () => { const i = d3.interpolateZoom(view, target); return (t) => zoomTo(i(t)); });
}

// ---- side panel: what's in focus ----
function panel(d) {
  const el = d3.select("#pack-panel");
  if (d.depth === 0) {
    el.html(`<h2>8 use cases · ${root.leaves().length} steps</h2><div class="crumbs">Click a use case to open it.</div>
      <ol>${root.children.map((c) => `<li>${esc(c.data.name)} <span class="k">(${c.children.length} scenarios, ${c.value} steps)</span></li>`).join("")}</ol>`);
  } else if (d.depth === 1) {
    el.html(`<h2>${esc(d.data.name)}</h2><div class="crumbs">${d.children.length} scenarios · ${d.value} steps</div>
      ${d.children.map((s) => `<div class="kind" style="margin-top:10px">${KIND[s.data.kind].label}</div><b>${esc(s.data.name)}</b>
      <ol>${s.children.map((l) => `<li>${esc(l.data.name)}</li>`).join("")}</ol>`).join("")}`);
  } else {
    el.html(`<div class="crumbs">${esc(d.parent.data.name)}</div><h2>${esc(d.data.name)}</h2>
      <div class="kind">${KIND[d.data.kind].label}</div><div class="crumbs"><code>${esc(d.data.src)}</code></div>
      <ol>${d.children.map((l) => `<li>${esc(l.data.name)}</li>`).join("")}</ol>`);
  }
}

// ---- legend: use cases + scenario kinds (dash pattern, so kind is never colour-alone) ----
const legend = d3.select("#pack-legend");
for (const u of useCases)
  legend.append("span").attr("class", "key").html(`<span class="swatch" style="background:${color(u.slot)}"></span>${esc(u.label)}`);
for (const [k, v] of Object.entries(KIND))
  legend.append("span").attr("class", "key").html(`<svg width="22" height="14" aria-hidden="true"><circle cx="11" cy="7" r="5.5" fill="none" stroke="var(--text-secondary)" stroke-width="1.5" ${v.dash ? `stroke-dasharray="${v.dash}"` : ""}/></svg>${v.label}`);

d3.select("#pack-table tbody").selectAll("tr").data(root.descendants().filter((d) => d.depth === 2)).join("tr")
  .html((s) => `<td>${esc(s.parent.data.name)}</td><td>${esc(s.data.name)}</td><td>${KIND[s.data.kind].label}</td>
    <td>${s.children.map((l) => esc(l.data.name)).join("; ")}</td>`);

zoomTo([root.x, root.y, root.r * 2 + 8]);
panel(root);
})();
