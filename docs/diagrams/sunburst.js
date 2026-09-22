// sunburst.js: rendered into the #sun-* elements of index.html.
// The logical data structure: the record, how it is stored, and the views
// callers receive. Sources: docs/SCHEMA.md, domain/prompt_schema.py,
// domain/prompt.py, service.py, search/search_strategy.py, hooks/session_index.py.
(() => {
const { tip, untip, esc } = PL;

// Column facts for the record ring (prompt_schema.py + SCHEMA.md).
const COL = {
  id:         { by: "library", type: "scalar", note: "Slug from the title when not supplied. Immutable, and refused in updates." },
  title:      { by: "caller", type: "scalar", weight: 3, note: "Short descriptive name. Carries the most search weight." },
  prompt:     { by: "caller", type: "scalar", weight: 1, note: "The prompt text. Required and non-empty. {{variables}} are parsed from it." },
  tags:       { by: "caller", type: "list", weight: 2.5, note: "Retrieval tags. A facet filter for list and search." },
  category:   { by: "caller", type: "scalar", weight: 2, note: "Single grouping term. A facet filter." },
  model:      { by: "caller", type: "scalar", note: "Model the prompt is tuned for. A facet filter." },
  notes:      { by: "caller", type: "scalar", weight: 0.5, note: "Provenance, caveats, usage guidance." },
  source:     { by: "caller", type: "scalar", note: "Where the prompt came from." },
  version:    { by: "caller", type: "scalar", note: "Caller-managed revision label." },
  variables:  { by: "derived", type: "list", note: "The {{name}} placeholders, re-extracted from prompt on add and on every body update." },
  created_at: { by: "library", type: "scalar", note: "ISO-8601 UTC, set once." },
  updated_at: { by: "library", type: "scalar", note: "ISO-8601 UTC, set on every write." },
  extras:     { by: "open", type: "any", note: "Any undeclared field becomes a new CSV column, kept on every later write, in first-seen order." },
};
const col = (name) => ({ name, col: name });
const leaf = (name, note) => ({ name, note });
const grp = (name, note, children) => ({ name, note, children });

const data = grp("Prompt library data", "Everything the plugin keeps and returns.", [
  grp("Record", "One Prompt: one row of the single prompts table (domain/prompt.py).", [
    grp("Identity", "How a prompt is addressed.", [col("id")]),
    grp("Content", "What the prompt says.", [col("title"), col("prompt")]),
    grp("Facets", "What list and search filter on.", [col("tags"), col("category"), col("model")]),
    grp("Provenance", "Where it came from.", [col("notes"), col("source"), col("version")]),
    grp("Derived", "Computed from other columns, never set by hand.", [col("variables")]),
    grp("Lifecycle", "Library-managed timestamps.", [col("created_at"), col("updated_at")]),
    grp("Open columns", "The table is open: new facets cost a column, not a migration.", [col("extras")]),
  ]),
  grp("Storage", "How a record sits on disk (storage/).", [
    grp("prompts.csv", "The one table. Readable and editable without this plugin.", [
      leaf("Header row", "Declared columns first, in fixed order. Discovered columns follow."),
      leaf("One row per prompt", "Keyed by id."),
      leaf("Strings only", "Typing lives in the domain layer, not the file."),
      leaf("Comma-separated lists", "tags and variables."),
      leaf("No field-size ceiling", "csv.field_size_limit is raised, so long multi-line bodies round-trip exactly."),
    ]),
    grp("prompts.csv.lock", "Sidecar lock file.", [
      leaf("Exclusive flock", "Held for every read-modify-write. The CSV is re-read inside the lock, so sessions never clobber each other."),
    ]),
    grp("Write protocol", "AtomicFileWriter: an interrupted write leaves the previous file intact.", [
      leaf("Temp sibling file", "The whole table is rewritten beside the target."),
      leaf("fsync", "Flushed to disk before the swap."),
      leaf("os.replace", "Atomic rename over prompts.csv."),
    ]),
    grp("Location", "LibraryPaths.resolve (config.py).", [
      leaf("$PROMPT_LIBRARY_CSV", "Full path to the CSV. Checked first."),
      leaf("$PROMPT_LIBRARY_HOME", "Directory that holds prompts.csv."),
      leaf("~/.claude/prompt-library/", "Default. Outside the plugin, so reinstalling never touches your data."),
    ]),
  ]),
  grp("Views", "The shapes callers receive. The adapters format these; they never compute.", [
    grp("Full record", "Prompt.to_dict. Returned by get, add, update and delete.", [
      leaf("12 declared columns", "Lists as arrays."), leaf("extras", "Present only when discovered columns exist."),
    ]),
    grp("Summary", "Prompt.summary. Returned by list: no body.", [
      leaf("id"), leaf("title"), leaf("tags"), leaf("category"), leaf("model"),
      leaf("prompt_chars", "Body length instead of the body."), leaf("updated_at"),
    ]),
    grp("Search hit", "SearchHit.to_dict. Returned by search.", [
      leaf("summary or full record", "Full only with include_body."),
      leaf("score", "Weighted keyword score, rounded to 4 places."),
      leaf("matched_fields", "Which columns matched."),
    ]),
    grp("Render result", "service.render.", [
      leaf("text", "The body with values substituted."), leaf("substituted"),
      leaf("unfilled", "Placeholders left as {{name}}. With strict, a RenderError instead."),
      leaf("id"), leaf("title"), leaf("declared_variables"),
    ]),
    grp("Stats", "service.stats.", [
      leaf("csv_path"), leaf("count"), leaf("columns"), leaf("extra_columns"),
      leaf("tags", "Tag → count."), leaf("categories", "Category → count."), leaf("total_prompt_chars"), leaf("search_strategy"),
    ]),
    grp("Session index line", "hooks/session_index.py: always-on context, so kept minimal.", [
      leaf("id"), leaf("title", "Truncated to 60 characters."), leaf("tags"),
    ]),
  ]),
]);

const root = d3.hierarchy(data).sum((d) => (d.children ? 0 : 1));
const SIZE = 900, R = SIZE / 2 / (root.height + 1);
d3.partition().size([2 * Math.PI, root.height + 1])(root);
root.each((d) => (d.current = d));

// Neutral ink, stepped by section; identity is carried by the labels on the arcs,
// because the use-case hues above already own colour on this page.
const SECTION_OPACITY = { Record: 0.46, Storage: 0.32, Views: 0.2 };
const section = (d) => (d.depth === 0 ? null : d.ancestors().find((a) => a.depth === 1).data.name);
const baseOpacity = (d) => SECTION_OPACITY[section(d)] * (d.children ? 0.75 : 1);

const arc = d3.arc()
  .startAngle((d) => d.x0).endAngle((d) => d.x1)
  .padAngle((d) => Math.min((d.x1 - d.x0) / 2, 0.004)).padRadius(R * 1.5)
  .innerRadius((d) => d.y0 * R).outerRadius((d) => Math.max(d.y0 * R, d.y1 * R - 2));

const svg = d3.select("#sun-chart").append("svg")
  .attr("viewBox", [-SIZE / 2, -SIZE / 2, SIZE, SIZE])
  .attr("role", "img").attr("aria-label", "Sunburst of the prompt-library data model: record columns, storage, and the views returned to callers.");

const visible = (d) => d.y1 <= root.height + 1 && d.y0 >= 1 && d.x1 > d.x0;
const labelFits = (d) => visible(d) && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.035;

const path = svg.append("g").selectAll("path").data(root.descendants().slice(1)).join("path")
  .attr("class", "arc")
  .style("fill", "var(--node)")
  .attr("fill-opacity", (d) => (visible(d.current) ? baseOpacity(d) : 0))
  .attr("d", (d) => arc(d.current))
  .on("mousemove", (e, d) => { tip(e, describe(d, true)); hover(d); })
  .on("mouseleave", () => { untip(); hover(null); })
  .on("click", (e, d) => clicked(d.children ? d : d.parent));

const label = svg.append("g").attr("pointer-events", "none").attr("text-anchor", "middle")
  .selectAll("text").data(root.descendants().slice(1)).join("text")
  .attr("class", "halo").attr("dy", "0.35em")
  .style("font-size", (d) => (d.depth === 1 ? "14px" : "11.5px"))
  .style("font-weight", (d) => (d.depth < 3 ? 600 : 400))
  .attr("fill-opacity", (d) => +labelFits(d.current))
  .attr("transform", (d) => labelTransform(d.current))
  .text((d) => fit(d.data.name, R - 12, d.depth === 1 ? 14 : 11.5));

const center = svg.append("circle").attr("r", R).attr("fill", "transparent").style("cursor", "pointer")
  .on("click", () => clicked(focus.parent || root));
const centerText = svg.append("text").attr("text-anchor", "middle").attr("pointer-events", "none");

function fit(text, px, fs) {
  const max = Math.floor(px / (fs * 0.56));
  return text.length > max ? text.slice(0, max - 1) + "…" : text;
}
function labelTransform(d) {
  const x = ((d.x0 + d.x1) / 2) * 180 / Math.PI;
  const y = ((d.y0 + d.y1) / 2) * R;
  return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
}
function hover(d) {
  const trail = d ? new Set(d.ancestors()) : null;
  path.attr("fill-opacity", (p) => {
    if (!visible(p.current)) return 0;
    if (!trail) return baseOpacity(p);
    return trail.has(p) || p.ancestors().includes(d) ? Math.min(1, baseOpacity(p) + 0.15) : baseOpacity(p) * 0.35;
  });
}

let focus = root;
function clicked(p) {
  focus = p;
  root.each((d) => (d.target = {
    x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
    x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
    y0: Math.max(0, d.y0 - p.depth),
    y1: Math.max(0, d.y1 - p.depth),
  }));
  drawCenter();
  panel(p);
  if (PL.instant()) {
    path.interrupt(); label.interrupt();
    root.each((d) => (d.current = d.target));
    path.attr("fill-opacity", (d) => (visible(d.current) ? baseOpacity(d) : 0)).attr("d", (d) => arc(d.current));
    label.attr("fill-opacity", (d) => +labelFits(d.current)).attr("transform", (d) => labelTransform(d.current));
    return;
  }
  const t = svg.transition().duration(650);
  path.transition(t)
    .tween("data", (d) => { const i = d3.interpolate(d.current, d.target); return (tt) => (d.current = i(tt)); })
    .attr("fill-opacity", (d) => (visible(d.target) ? baseOpacity(d) : 0))
    .attrTween("d", (d) => () => arc(d.current));
  label.transition(t)
    .attr("fill-opacity", (d) => +labelFits(d.target))
    .attrTween("transform", (d) => () => labelTransform(d.current));
}
function drawCenter() {
  centerText.selectAll("tspan").remove();
  const lines = focus === root ? ["prompt-library", "data"] : [focus.data.name, "click to go back"];
  lines.forEach((l, i) => centerText.append("tspan").attr("x", 0).attr("dy", i === 0 ? "-0.2em" : "1.3em")
    .attr("class", i === 0 ? "" : "muted").style("font-size", i === 0 ? "15px" : "11px").style("font-weight", i === 0 ? 600 : 400)
    .text(fit(l, R * 1.7, i === 0 ? 15 : 11)));
}

function describe(d, short) {
  const trail = d.ancestors().reverse().slice(1, -1).map((a) => esc(a.data.name)).join(" › ");
  const c = d.data.col && COL[d.data.col];
  let html = `<b>${esc(d.data.name)}</b>${trail ? `<br><span class="k">${trail}</span>` : ""}`;
  if (c) html += `<br>${esc(c.note)}<br><span class="k">set by ${c.by} · ${c.type}${c.weight ? ` · search weight ×${c.weight}` : ""}</span>`;
  else if (d.data.note) html += `<br>${esc(d.data.note)}`;
  if (d.children && short) html += `<br><span class="k">${d.children.length} parts · click to zoom</span>`;
  return html;
}

function panel(d) {
  const el = d3.select("#sun-panel");
  const items = (d.children || []).map((c) => {
    const k = c.data.col && COL[c.data.col];
    const meta = k ? ` <span class="k">(${k.by}${k.weight ? `, ×${k.weight}` : ""})</span>` : c.children ? ` <span class="k">(${c.children.length})</span>` : "";
    return `<dt>${esc(c.data.name)}${meta}</dt><dd>${esc(k ? k.note : c.data.note || (c.children ? c.children.map((g) => g.data.name).join(", ") : "—"))}</dd>`;
  }).join("");
  el.html(`<div class="crumbs">${d.ancestors().reverse().map((a) => esc(a.data.name)).join(" › ")}</div>
    <h2>${esc(d.data.name)}</h2><div class="crumbs">${esc(d.data.note || "")}</div><dl>${items}</dl>`);
}

// table view: every leaf with its path
d3.select("#sun-table tbody").selectAll("tr").data(root.leaves()).join("tr").html((d) => {
  const [sec, grpName] = d.ancestors().reverse().slice(1).map((a) => a.data.name);
  const c = d.data.col && COL[d.data.col];
  return `<td>${esc(sec)}</td><td>${esc(grpName)}</td><td><code>${esc(d.data.name)}</code></td>
    <td>${esc(c ? `${c.note} (set by ${c.by}${c.weight ? `; search ×${c.weight}` : ""})` : d.data.note || "")}</td>`;
});

drawCenter();
panel(root);
})();
