"""Self-contained, network-free graph export. Note data never becomes executable HTML."""

from __future__ import annotations

import json
from typing import Any


def graph_html(graph: dict[str, Any]) -> str:
    data = (
        json.dumps(graph, ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return TEMPLATE.replace("__GRAPH_DATA__", data)


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'">
<title>Cortex / Knowledge map</title><style>
:root{color-scheme:dark;--bg:#111511;--panel:#1a201a;--line:#344334;--ink:#e4eadf;--dim:#9ca995;--lime:#d0ed97}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px system-ui,-apple-system,sans-serif}
header{height:92px;padding:24px 38px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between}
.brand{font-size:27px;font-weight:700;letter-spacing:5px}.brand span{color:var(--lime)}.tagline{color:var(--dim);font-size:11px;letter-spacing:2px;margin-top:7px}
main{display:grid;grid-template-columns:270px 1fr 300px;min-height:calc(100vh - 92px)}aside{padding:30px 25px;border-right:1px solid var(--line)}.right{border-right:0;border-left:1px solid var(--line)}
h1{font-size:28px;line-height:1.2;margin:6px 0 18px;font-weight:500}h2{font-size:11px;letter-spacing:2px;color:var(--dim);font-weight:500;margin:0 0 20px}p{color:var(--dim);line-height:1.65;font-size:13px}
input{width:100%;padding:12px;background:#121712;color:var(--ink);border:1px solid #465544;border-radius:6px;margin:12px 0 24px;outline:none}input:focus{border-color:var(--lime)}
.stat{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding:14px 0;color:var(--dim);font-size:13px}.stat b{color:var(--ink);font-size:19px;font-weight:400}.pill{border:1px solid #4d6048;color:var(--lime);font-size:10px;letter-spacing:1px;padding:8px 12px;border-radius:20px}
.canvas{position:relative;overflow:hidden;background-image:radial-gradient(#31402d 0.6px,transparent .6px);background-size:24px 24px}svg{width:100%;height:calc(100vh - 92px);min-height:560px;touch-action:none}.edge{stroke:#617957;stroke-width:1;opacity:.32}.node{cursor:pointer;outline:none}.node circle{stroke:#101510;stroke-width:4}.node:hover circle,.node:focus circle{stroke:#fff;stroke-width:2}.node text{fill:#c6d3be;font-size:10px;pointer-events:none}.node.dim{opacity:.09}.edge.dim{opacity:.03}
.key{display:flex;align-items:center;gap:9px;color:var(--dim);padding:7px 0;font-size:12px}.dot{height:8px;width:8px;border-radius:50%}.caption{position:absolute;bottom:23px;left:24px;color:var(--dim);font-size:11px;letter-spacing:1px}.detail{overflow-wrap:anywhere}.detail strong{color:var(--lime);font-weight:500}button{background:#d0ed97;color:#182014;border:0;border-radius:5px;padding:10px 15px;cursor:pointer;margin-top:20px}.muted{opacity:.7}.empty{position:absolute;top:35%;left:20%;max-width:350px}
@media(max-width:950px){main{grid-template-columns:210px 1fr}.right{grid-column:1/-1;border-top:1px solid var(--line)}header{padding:20px}.brand{font-size:22px}aside{padding:25px 18px}}
@media(max-width:600px){main{display:block}aside{border-bottom:1px solid var(--line)}svg{height:65vh}.tagline{letter-spacing:1px}}
</style></head><body>
<header><div><div class="brand">C<span>O</span>RTEX</div><div class="tagline">ONE BRAIN. EVERY MODEL.</div></div><span class="pill">LOCAL KNOWLEDGE MAP</span></header>
<main><aside><h2>YOUR CONNECTED CONTEXT</h2><h1>Ideas become<br>connections.</h1><p>A map of the actual Markdown files and wikilinks in this vault.</p><label for="search">Find a memory</label><input id="search" placeholder="Search titles…" type="search"><div class="stat">Memories <b id="count"></b></div><div class="stat">Resolved links <b id="links"></b></div><div class="stat">Stale memories <b id="stale"></b></div><div id="legend" style="margin-top:28px"></div><p class="muted">Static snapshot · No network calls<br>Markdown remains the source of truth.</p></aside>
<section class="canvas" aria-label="Knowledge graph"><svg id="map" viewBox="0 0 850 720" role="img" aria-label="Interactive knowledge map"></svg><div class="caption">SELECT A NODE TO INSPECT ITS SOURCE</div></section>
<aside class="right"><h2>MEMORY INSPECTOR</h2><div class="detail" id="detail"><h1>Follow a connection.</h1><p>Select any node to see its source, status and relationships. Use the search box to narrow the map.</p></div><button id="reset">Reset selection</button><p>Candidate memories are unconfirmed. Links indicate relationships, not proof.</p></aside></main>
<script type="application/json" id="graph-data">__GRAPH_DATA__</script><script>
const graph=JSON.parse(document.getElementById('graph-data').textContent);const svg=document.getElementById('map');const NS='http://www.w3.org/2000/svg';
const palette=['#d0ed97','#9cbddd','#e4c18b','#c2a9dc','#8cc8ac','#d69e97','#d9d9a0'];const groups=[...new Set(graph.nodes.map(n=>n.type))].sort();const colors=Object.fromEntries(groups.map((g,i)=>[g,palette[i%palette.length]]));
const points=new Map();const elements=new Map();const links=[];function el(tag,attrs){const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e}
function field(tag,text,parent){const e=document.createElement(tag);e.textContent=text;parent.append(e);return e}
document.getElementById('count').textContent=graph.nodes.length;document.getElementById('stale').textContent=graph.nodes.filter(n=>n.stale).length;
groups.forEach((g,i)=>{const row=document.createElement('div');row.className='key';const dot=document.createElement('i');dot.className='dot';dot.style.background=colors[g];row.append(dot);field('span',g,row);document.getElementById('legend').append(row);const members=graph.nodes.filter(n=>n.type===g);const angle=(i/Math.max(groups.length,1))*Math.PI*2-Math.PI/2;const cx=425+Math.cos(angle)*220,cy=350+Math.sin(angle)*220;members.forEach((n,j)=>{const a=j/members.length*Math.PI*2;const r=members.length===1?0:Math.min(115,40+members.length*7);points.set(n.path,{x:cx+Math.cos(a)*r,y:cy+Math.sin(a)*r})})});
for(const e of graph.edges){const a=points.get(e.source),b=points.get(e.target);if(!a||!b)continue;const line=el('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,class:'edge'});svg.append(line);links.push({line,...e})}document.getElementById('links').textContent=links.length;
function select(n){const box=document.getElementById('detail');box.replaceChildren();field('h1',n.title,box);field('strong',n.type.toUpperCase()+' / '+n.status.toUpperCase(),box);field('p','Source: '+n.path,box);field('p','Updated: '+n.updated.slice(0,10)+(n.stale?' · Stale':''),box);const neighbors=new Set([n.path]);links.forEach(e=>{if(e.source===n.path)neighbors.add(e.target);if(e.target===n.path)neighbors.add(e.source)});field('p',(neighbors.size-1)+' connected memories',box);for(const [path,node] of elements)node.classList.toggle('dim',!neighbors.has(path));links.forEach(e=>e.line.classList.toggle('dim',e.source!==n.path&&e.target!==n.path))}
for(const n of graph.nodes){const p=points.get(n.path);const g=el('g',{class:'node',tabindex:'0',role:'button','aria-label':n.title,transform:`translate(${p.x},${p.y})`});const degree=links.filter(e=>e.source===n.path||e.target===n.path).length;g.append(el('circle',{r:Math.min(23,9+degree*2.5),fill:colors[n.type]}));const label=el('text',{x:0,y:35,'text-anchor':'middle'});label.textContent=n.title.length>28?n.title.slice(0,27)+'…':n.title;g.append(label);g.addEventListener('click',()=>select(n));g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' ')select(n)});svg.append(g);elements.set(n.path,g)}
if(!graph.nodes.length){const empty=document.createElement('div');empty.className='empty';field('h1','Your map starts here.',empty);field('p','Create a note with cortex remember, then link it to another note with [[wikilinks]]. Export the graph again to see the connection.',empty);document.querySelector('.canvas').append(empty)}
document.getElementById('search').addEventListener('input',event=>{const q=event.target.value.toLowerCase();for(const n of graph.nodes)elements.get(n.path).classList.toggle('dim',!n.title.toLowerCase().includes(q));links.forEach(e=>e.line.classList.remove('dim'))});document.getElementById('reset').addEventListener('click',()=>{document.getElementById('search').value='';for(const node of elements.values())node.classList.remove('dim');links.forEach(e=>e.line.classList.remove('dim'))});
</script></body></html>"""
