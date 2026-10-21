"""Build the self-contained explorer.html page."""
import html
import re

from plotly.offline import get_plotlyjs

PALETTES = ["Viridis", "Plasma", "Cividis", "Turbo", "Inferno", "Magma"]

TEMPLATE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<title>Explorer: __SOURCE__</title>
<style>
body { font-family: system-ui, sans-serif; margin: 0.8rem; }
.controls { display: flex; flex-wrap: wrap; gap: 0.6rem 1.2rem; align-items: center; }
label { white-space: nowrap; }
#status, #note { margin: 0.4rem 0; }
#note { color: #555; font-size: 0.85rem; }
#plot { width: 100%; height: 78vh; }
</style>
</head>
<body>
<div class="controls">
<label>X <select id="x">__COLUMN_OPTIONS__</select>
<input type="checkbox" id="logx"> log</label>
<label>Y <select id="y">__COLUMN_OPTIONS__</select>
<input type="checkbox" id="logy"> log</label>
<label>Z <select id="z">__NONE_OPTION____COLUMN_OPTIONS__</select>
<input type="checkbox" id="logz"> log</label>
<label>Colour <select id="colour">__NONE_OPTION____COLUMN_OPTIONS__</select>
<input type="checkbox" id="logc"> log</label>
<label>Palette <select id="palette">__PALETTE_OPTIONS__</select></label>
</div>
<div id="status"></div>
<div id="note">Rows with a missing value in a selected column are dropped, as are values
&le; 0 on a log scale (log axes and log colour). The count is shown above.</div>
<div id="plot"></div>
<script type="application/json" id="data">__DATA__</script>
<script>__PLOTLY__</script>
<script>
__SCRIPT__
</script>
</body>
</html>
"""

SCRIPT = r"""
const D = JSON.parse(document.getElementById('data').textContent);
const META = {};
D.columns.forEach(c => { META[c.name] = c; });
const $ = id => document.getElementById(id);
const withUnit = name => META[name].unit ? name + ' (' + META[name].unit + ')' : name;
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const LOGBOX = { x: 'logx', y: 'logy', z: 'logz', colour: 'logc' };

function applyLogDefault(selectId) {
  const col = $(selectId).value;
  $(LOGBOX[selectId]).checked = col !== 'none' && META[col].log;
}

function hoverText(i) {
  const lines = Object.keys(D.labels).map(k => '<b>' + esc(k) + '</b>: ' + esc(D.labels[k][i]));
  D.columns.forEach(c => {
    const v = D.rows[c.name][i];
    lines.push(esc(c.name) + ' = ' + (v === null ? 'missing' : String(Number(v.toPrecision(6)))) +
               (c.unit ? ' ' + esc(c.unit) : ''));
  });
  return lines.join('<br>');
}

function draw() {
  const sel = { x: $('x').value, y: $('y').value, z: $('z').value, colour: $('colour').value };
  const log = {
    x: $('logx').checked, y: $('logy').checked, z: $('logz').checked, colour: $('logc').checked
  };
  const used = Object.keys(sel).filter(k => sel[k] !== 'none');
  const is3d = sel.z !== 'none';
  const keep = [];
  let missing = 0, nonPositive = 0;
  for (let i = 0; i < D.n_written; i++) {
    let gap = false, bad = false;
    for (const k of used) {
      const v = D.rows[sel[k]][i];
      if (v === null) gap = true;
      else if (log[k] && v <= 0) bad = true;
    }
    if (gap) missing++;
    else if (bad) nonPositive++;
    else keep.push(i);
  }
  const pick = k => keep.map(i => D.rows[sel[k]][i]);
  const marker = { size: is3d ? 2 : 4, opacity: 0.8 };
  if (sel.colour !== 'none') {
    const cv = pick('colour');
    marker.color = log.colour ? cv.map(Math.log10) : cv;
    marker.colorscale = $('palette').value;
    marker.showscale = true;
    marker.colorbar = {
      title: { text: (log.colour ? 'log10 ' : '') + withUnit(sel.colour) }
    };
  } else {
    marker.color = '#1f77b4';
  }
  const trace = {
    type: is3d ? 'scatter3d' : 'scattergl',
    mode: 'markers',
    x: pick('x'),
    y: pick('y'),
    text: keep.map(hoverText),
    hovertemplate: '%{text}<extra></extra>',
    marker: marker
  };
  const axis = k => ({ title: { text: withUnit(sel[k]) }, type: log[k] ? 'log' : 'linear' });
  const layout = { margin: { l: 60, r: 20, t: 20, b: 50 } };
  if (is3d) {
    trace.z = pick('z');
    layout.scene = { xaxis: axis('x'), yaxis: axis('y'), zaxis: axis('z') };
  } else {
    layout.xaxis = axis('x');
    layout.yaxis = axis('y');
  }
  Plotly.react('plot', [trace], layout, { responsive: true });
  const dropped = missing + nonPositive;
  $('status').textContent = keep.length + ' plotted (' + dropped + ' dropped: ' + missing +
    ' missing, ' + nonPositive + ' not positive on a log scale); ' + D.n_written +
    ' rows loaded from ' + D.n_read + ' read';
}

Object.keys(LOGBOX).forEach(id => {
  $(id).addEventListener('change', () => { applyLogDefault(id); draw(); });
  $(LOGBOX[id]).addEventListener('change', draw);
});
$('palette').addEventListener('change', draw);
$('x').value = D.columns[0].name;
$('y').value = D.columns[Math.min(1, D.columns.length - 1)].name;
$('z').value = 'none';
$('colour').value = 'none';
Object.keys(LOGBOX).forEach(applyLogDefault);
draw();
"""


def option(value, text=None):
    """Return one <option> element with escaped value and text."""
    return (f'<option value="{html.escape(value, quote=True)}">'
            f'{html.escape(text or value)}</option>')


def build_page(payload, blob):
    """Return the complete HTML for a payload and its serialised JSON text."""
    names = [col["name"] for col in payload["columns"]]
    parts = {
        "__SOURCE__": html.escape(str(payload["source"])),
        "__COLUMN_OPTIONS__": "".join(option(name) for name in names),
        "__NONE_OPTION__": option("none", "none"),
        "__PALETTE_OPTIONS__": "".join(option(name) for name in PALETTES),
        "__DATA__": blob.replace("</", "<\\/"),
        "__PLOTLY__": get_plotlyjs(),
        "__SCRIPT__": SCRIPT,
    }
    return re.sub("|".join(parts), lambda m: parts[m.group(0)], TEMPLATE)
