// Shared by the three diagrams: the use-case vocabulary (fixed categorical
// order, so a use case keeps its colour in every diagram) and the tooltip.
window.PL = (() => {
  const useCases = [
    { id: "save",    label: "Save a prompt",          slot: 1 },
    { id: "find",    label: "Find a prompt",          slot: 2 },
    { id: "reuse",   label: "Reuse a prompt",         slot: 3 },
    { id: "browse",  label: "Browse the library",     slot: 4 },
    { id: "edit",    label: "Edit or delete",         slot: 5 },
    { id: "inspect", label: "Inspect the library",    slot: 6 },
    { id: "session", label: "Session awareness",      slot: 7 },
    { id: "import",  label: "Bulk import",            slot: 8 },
  ];
  const byId = Object.fromEntries(useCases.map((u) => [u.id, u]));
  const color = (slot) => `var(--s${slot})`;

  const tipEl = () => document.getElementById("tip");
  function tip(event, html) {
    const el = tipEl();
    el.innerHTML = html;
    el.hidden = false;
    const pad = 14;
    const { innerWidth: w, innerHeight: h } = window;
    const r = el.getBoundingClientRect();
    let x = event.clientX + pad;
    let y = event.clientY + pad;
    if (x + r.width > w - 8) x = event.clientX - r.width - pad;
    if (y + r.height > h - 8) y = event.clientY - r.height - pad;
    el.style.left = `${Math.max(8, x)}px`;
    el.style.top = `${Math.max(8, y)}px`;
  }
  function untip() { tipEl().hidden = true; }

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const swatch = (slot) => `<span class="swatch" style="display:inline-block;width:10px;height:10px;border-radius:3px;background:${color(slot)}"></span>`;

  // Skip animation when the user asks for less motion, or when the page is hidden
  // (a background tab never runs animation frames, so a transition would stall).
  const instant = () => document.hidden || window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  return { useCases, byId, color, instant, tip, untip, esc, swatch };
})();
