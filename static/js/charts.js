/* charts.js — Chart.js + D3 network graph for AgriSoc admin */

const PALETTE = {
  gold:   '#C8872A', leaf: '#2D5A27', sage: '#4A7A44', moss: '#7AAD72',
  rust:   '#A03820', sky:  '#3A6B8A', straw:'#E8C99A', wheat:'#C9956A',
  cream:  '#F5EDD8', soil: '#1E1208',
};

/* ── Monthly Revenue Line Chart ── */
async function initRevenueChart() {
  const canvas = document.getElementById('revenueChart');
  if (!canvas) return;
  const data = await fetch('/api/monthly-revenue').then(r => r.json());
  new Chart(canvas, {
    type: 'line',
    data: {
      labels: data.map(d => d.month_label),
      datasets: [{
        label: 'Revenue (KES)',
        data: data.map(d => d.total_revenue),
        borderColor: PALETTE.gold, backgroundColor: 'rgba(200,135,42,.12)',
        borderWidth: 2.5, pointBackgroundColor: PALETTE.gold,
        pointRadius: 4, fill: true, tension: 0.35
      }]
    },
    options: chartDefaults('Revenue (KES)')
  });
}

/* ── Members Growth Line Chart ── */
async function initGrowthChart() {
  const canvas = document.getElementById('growthChart');
  if (!canvas) return;
  const data = await fetch('/api/members-growth').then(r => r.json());
  new Chart(canvas, {
    type: 'line',
    data: {
      labels: data.map(d => d.month_label),
      datasets: [
        { label: 'New Members', data: data.map(d => d.new_members),
          borderColor: PALETTE.leaf, backgroundColor: 'rgba(45,90,39,.1)',
          borderWidth: 2, fill: true, tension: 0.3 },
        { label: 'Total Members', data: data.map(d => d.cumulative_members),
          borderColor: PALETTE.gold, borderWidth: 2, borderDash: [5,4],
          pointRadius: 3, tension: 0.3 }
      ]
    },
    options: chartDefaults('Members')
  });
}

/* ── Revenue by Category Doughnut ── */
async function initCategoryChart() {
  const canvas = document.getElementById('categoryChart');
  if (!canvas) return;
  const data = await fetch('/api/revenue-by-type').then(r => r.json());
  const colors = [PALETTE.gold, PALETTE.leaf, PALETTE.sky, PALETTE.rust, PALETTE.wheat, PALETTE.moss];
  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.paymenttype),
      datasets: [{ data: data.map(d => d.total_amount), backgroundColor: colors, borderWidth: 0 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { font: { family: 'DM Sans', size: 12 }, color: '#5C3D2E', boxWidth: 14 } },
        tooltip: { callbacks: { label: ctx => ` KES ${Number(ctx.raw).toLocaleString()}` } }
      },
      cutout: '60%'
    }
  });
}

/* ── Members per Branch Bar Chart ── */
async function initBranchChart() {
  const canvas = document.getElementById('branchChart');
  if (!canvas) return;
  const data = await fetch('/api/members-per-branch').then(r => r.json());
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: data.map(d => d.branchname),
      datasets: [{
        label: 'Members', data: data.map(d => d.totalmembers),
        backgroundColor: PALETTE.leaf, borderRadius: 6,
        hoverBackgroundColor: PALETTE.sage
      }]
    },
    options: chartDefaults('Members')
  });
}

/* ── Resource Usage Horizontal Bar ── */
async function initResourceChart() {
  const canvas = document.getElementById('resourceChart');
  if (!canvas) return;
  const data = await fetch('/api/resource-usage').then(r => r.json());
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: data.map(d => d.title.length > 28 ? d.title.slice(0,25)+'...' : d.title),
      datasets: [{
        label: 'Times Borrowed', data: data.map(d => d.timesborrowed),
        backgroundColor: PALETTE.gold, borderRadius: 4
      }]
    },
    options: { ...chartDefaults('Borrows'), indexAxis: 'y' }
  });
}

/* ── Revenue by Branch Bar ── */
async function initRevBranchChart() {
  const canvas = document.getElementById('revBranchChart');
  if (!canvas) return;
  const data = await fetch('/api/revenue-by-branch').then(r => r.json());
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: data.map(d => d.branchname),
      datasets: [{
        label: 'Revenue (KES)', data: data.map(d => d.total_revenue),
        backgroundColor: [PALETTE.gold, PALETTE.leaf, PALETTE.sky, PALETTE.rust],
        borderRadius: 6
      }]
    },
    options: chartDefaults('KES')
  });
}

/* ── D3 Network / Property Graph Visualisation ── */
async function initNetworkGraph() {
  const container = document.getElementById('networkGraph');
  if (!container || typeof d3 === 'undefined') return;
  const data = await fetch('/api/graph-data').then(r => r.json());

  const W = container.clientWidth || 600, H = 420;
  const svg = d3.select(container).append('svg').attr('width', W).attr('height', H)
    .style('background', '#1E1208').style('border-radius', '12px');

  const groupColors = { 'Nairobi Central': PALETTE.gold, 'Rift Valley Chapter': PALETTE.leaf,
    'Coast Branch': PALETTE.sky, 'Western Kenya': PALETTE.rust,
    'Book': PALETTE.wheat, 'Journal': PALETTE.moss, 'Manual': PALETTE.straw,
    'Seed Catalogue': PALETTE.sage, 'Video': PALETTE.wheat };

  const sim = d3.forceSimulation(data.nodes)
    .force('link', d3.forceLink(data.links).id(d => d.id).distance(60))
    .force('charge', d3.forceManyBody().strength(-120))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide(18));

  const link = svg.append('g').selectAll('line').data(data.links).enter().append('line')
    .attr('stroke', 'rgba(200,135,42,.35)').attr('stroke-width', 1.2);

  const node = svg.append('g').selectAll('circle').data(data.nodes).enter().append('circle')
    .attr('r', d => d.id > 999 ? 10 : 7)
    .attr('fill', d => groupColors[d.group_name] || PALETTE.wheat)
    .attr('stroke', '#fff').attr('stroke-width', 1.5).style('cursor','pointer')
    .call(d3.drag()
      .on('start', (e,d) => { if (!e.active) sim.alphaTarget(.3).restart(); d.fx=d.x;d.fy=d.y; })
      .on('drag',  (e,d) => { d.fx=e.x; d.fy=e.y; })
      .on('end',   (e,d) => { if (!e.active) sim.alphaTarget(0); d.fx=null;d.fy=null; }));

  const label = svg.append('g').selectAll('text').data(data.nodes).enter().append('text')
    .text(d => (d.label||'').slice(0,14))
    .attr('font-size', '9px').attr('fill', PALETTE.straw).attr('text-anchor','middle')
    .attr('dy', d => d.id > 999 ? 22 : 18).style('pointer-events','none');

  /* Tooltip */
  const tip = d3.select(container).append('div')
    .style('position','absolute').style('background','rgba(30,18,8,.92)')
    .style('color',PALETTE.straw).style('font-size','11px').style('padding','5px 9px')
    .style('border-radius','6px').style('pointer-events','none').style('opacity',0);

  node.on('mouseover', (e,d) => {
    tip.style('opacity',1).html(`<strong>${d.label}</strong><br>${d.group_name||''}`)
      .style('left',(e.offsetX+10)+'px').style('top',(e.offsetY-10)+'px');
  }).on('mouseout', () => tip.style('opacity',0));

  sim.on('tick', () => {
    link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y)
        .attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
    node.attr('cx',d=>d.x).attr('cy',d=>d.y);
    label.attr('x',d=>d.x).attr('y',d=>d.y);
  });

  /* Legend */
  const legendData = [...new Set(data.nodes.map(d=>d.group_name).filter(Boolean))].slice(0,6);
  const lg = svg.append('g').attr('transform','translate(12,14)');
  legendData.forEach((name,i) => {
    const g = lg.append('g').attr('transform',`translate(0,${i*18})`);
    g.append('circle').attr('r',5).attr('fill',groupColors[name]||PALETTE.wheat);
    g.append('text').text(name).attr('x',12).attr('dy','0.35em')
      .attr('fill',PALETTE.straw).attr('font-size','9px');
  });
}

/* ── Defaults ── */
function chartDefaults(yLabel) {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { labels: { font: { family: 'DM Sans', size: 12 }, color: '#5C3D2E', boxWidth: 12 } },
      tooltip: {
        backgroundColor: 'rgba(30,18,8,.92)', titleColor: '#E8C99A', bodyColor: '#C9956A',
        callbacks: { label: ctx => ` ${ctx.parsed.y?.toLocaleString() ?? ctx.raw}` }
      }
    },
    scales: {
      x: { grid:{ color:'rgba(0,0,0,.05)' }, ticks:{ color:'#8B7355', font:{size:11} } },
      y: { grid:{ color:'rgba(0,0,0,.07)' }, ticks:{ color:'#8B7355', font:{size:11} },
           title:{ display:!!yLabel, text:yLabel, color:'#8B7355', font:{size:11} } }
    }
  };
}

/* Init all charts on load */
document.addEventListener('DOMContentLoaded', () => {
  initRevenueChart();
  initGrowthChart();
  initCategoryChart();
  initBranchChart();
  initResourceChart();
  initRevBranchChart();
  initNetworkGraph();
});