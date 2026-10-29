# Violin plot interactivo: distribución horaria de O3 por estación (PEC 2, Visualización de datos)
# Requisitos: pip install pandas pyarrow numpy
# Genera violin-plot.html junto a este script, una página autónoma lista para publicar en GitHub Pages.
# La forma de cada violín (densidad) se calcula en el navegador a partir de histogramas por hora,
# así el filtro de horario recalcula los violines sin incrustar las 138.000 mediciones.

from pathlib import Path
import json

import numpy as np
import pandas as pd

# El parquet se busca en la carpeta del script y en las superiores; la página se guarda junto al script
AQUI = Path(__file__).resolve().parent
RUTA_DATOS = next(p / 'bcn_virtual_sensor.parquet' for p in [AQUI, *AQUI.parents]
                  if (p / 'bcn_virtual_sensor.parquet').exists())
SALIDA = Path(__file__).resolve().with_suffix('.html')

# Tipografías (se cargan desde Google Fonts en la página)
TIT = "'Source Sans 3', 'Source Sans Pro', sans-serif"
DES = "'Noto Sans', sans-serif"

# Escala secuencial para título > subtítulo > descripción (igual que el small multiple)
C_TIT, C_SUB, C_DES = '#0d1b2a', '#33507a', '#6f8bb0'
# Escala cualitativa: azul urbanas, verde suburbana, naranja zona de O3 bajo
C_URB, C_SUB_EST, C_GUIA = '#1f5fbf', '#2a9d4b', '#e07b00'

UMBRAL = 12        # µg/m³: valle entre el bulto bajo y el cuerpo principal (KDE de las urbanas)

# --- Datos ---
df = pd.read_parquet(RUTA_DATOS)
df['est'] = df['station_name'].str.replace('Barcelona - ', '')
tipo = {'Traffic': 'tráfico', 'Urban Background': 'fondo urbano', 'Suburban': 'suburbana'}
df['tipo'] = df['station_type'].astype(str).map(tipo)
especiales = ('Eixample', 'Navas')            # estaciones con menos datos -> asterisco

mediana = df.groupby('est')['O3'].median()
urbanas = mediana[df.groupby('est')['tipo'].first() != 'suburbana'].sort_values().index.tolist()
suburbanas = ['Observatori Fabra']
orden = urbanas + suburbanas                                  # urbanas de menos a más ozono
pos = list(range(1, len(urbanas) + 1)) + [len(urbanas) + 2.2]  # hueco entre grupos

# Histograma de O3 (valores enteros en µg/m³) por estación y hora: base de los violines en el navegador
VMAX = int(df['O3'].max())
hist = {e: [np.bincount(d.loc[d['hour'] == h, 'O3'].astype(int), minlength=VMAX + 1).tolist()
            for h in range(24)] for e, d in df.groupby('est')}

info = {}
for e, d in df.groupby('est'):
    a, b = d['year'].min(), d['year'].max()
    info[e] = dict(nombre=e + ('*' if e in especiales else ''), tipo=d['tipo'].iloc[0],
                   anios=f'{a}' if a == b else f'{a}-{b}', sub=e in suburbanas)

# Cifras de los insights, calculadas (no escritas a mano)
pct = lambda x: (f'{x:.1%}' if x < .01 else f'{x:.0%}').replace('.', ',').replace('%', ' %')
bajo_est = df.groupby('est')['O3'].apply(lambda s: (s < UMBRAL).mean())
bajo = df[(df['tipo'] != 'suburbana') & (df['O3'] < UMBRAL)]['hour']
p_noche = ((bajo >= 20) | (bajo <= 5)).mean()
p_punta = ((bajo >= 6) & (bajo <= 9)).mean()
med_urb = mediana[urbanas]

# --- Página ---
datos = dict(orden=orden, pos=pos, info=info, hist=hist,
             ticks=[f"<b>{info[e]['nombre']}</b><br>({info[e]['tipo']})" for e in orden])

n = df.groupby('est').size()
fmt = lambda x: f'{x:,}'.replace(',', '.')
nota = (f'* Estaciones con menos datos: Eixample solo 2023 ({fmt(n["Eixample"])} registros horarios) y Navas solo 2026 '
        f'({fmt(n["Navas"])}); el resto, 2023-2026.<br>'
        'Urbanas ordenadas de menor a mayor mediana de O₃ (todo el día). Forma del violín: densidad estimada con un '
        'kernel gaussiano sobre las horas seleccionadas; cada violín se escala a su propio máximo.<br>'
        'Fuente: Ajuntament de Barcelona, Open Data BCN, calidad del aire (dataset preparado por la UOC, M2.891).')

presets = [('Todo el día', 0, 23), ('Noche (20-5 h)', 20, 5),
           ('Punta mañana (6-9 h)', 6, 9), ('Mediodía (11-17 h)', 11, 17)]
html_presets = ''.join(f'<button type="button" class="preset" data-a="{a}" data-b="{b}">{t}</button>'
                       for t, a, b in presets)
icono_caja = (f'<svg class="icono" viewBox="0 0 18 18" aria-hidden="true"><rect x="6" y="1" width="6" height="16" '
              f'fill="{C_TIT}"/><circle cx="9" cy="9" r="3.6" fill="#fff" stroke="{C_TIT}" stroke-width="1.5"/></svg>')

pagina = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ozono en Barcelona</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&family=Source+Sans+3:wght@400;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@3.0.1/plotly.min.js"></script>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #fff; color: {C_TIT}; font-family: {DES}; }}
  main {{ max-width: 1400px; margin: 0 auto; padding: 28px 16px 40px; }}
  h1 {{ font-family: {TIT}; font-size: clamp(1.6rem, 3.2vw, 2.4rem); margin: 0 0 6px; }}
  .sub {{ font-family: {TIT}; font-weight: 700; font-size: clamp(1rem, 1.6vw, 1.25rem); color: {C_SUB}; margin: 0 0 6px; }}
  .des {{ font-size: .9rem; color: {C_DES}; margin: 0 0 22px; }}
  .des b {{ color: {C_SUB}; }}
  .cuerpo {{ display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 20px; align-items: start; }}
  @media (max-width: 900px) {{ .cuerpo {{ grid-template-columns: 1fr; }} .controles {{ order: -1; max-width: none; }} }}
  .grafico {{ position: relative; min-width: 0; }}
  .lunar {{ display: inline-block; flex: none; width: 18px; height: 18px; border-radius: 50%; }}
  .icono {{ flex: none; width: 18px; height: 18px; }}
  .controles {{ display: flex; flex-direction: column; align-items: flex-start; gap: 8px;
               padding: 18px 20px; border: 2px solid {C_SUB}; }}
  .controles .tit {{ font-family: {TIT}; font-weight: 700; font-size: 1.1rem; color: {C_SUB}; margin-top: 6px; }}
  .controles .tit:first-child {{ margin-top: 0; }}
  .ley {{ display: flex; align-items: center; gap: 10px; font: 700 1rem {TIT}; }}
  button {{ cursor: pointer; font-family: {TIT}; color: {C_TIT}; transition: opacity .15s; }}
  button:focus-visible {{ outline: 3px solid {C_SUB}; outline-offset: 3px; }}
  .capa {{ display: inline-flex; align-items: center; gap: 10px; padding: 4px 0; text-align: left;
           font-weight: 700; font-size: 1rem; background: none; border: 0; }}
  .capa[aria-pressed="false"] {{ opacity: .35; text-decoration: line-through; }}
  .presets {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .preset {{ font-weight: 700; font-size: .85rem; padding: 3px 9px; background: #fff;
             border: 2px solid {C_SUB}; border-radius: 999px; }}
  .preset[aria-pressed="true"] {{ background: {C_SUB}; color: #fff; }}
  .rango {{ position: relative; width: 100%; height: 26px; }}
  .pista {{ position: absolute; left: 9px; right: 9px; top: 11px; height: 4px; border-radius: 2px; background: #d5dce6; }}
  .relleno {{ position: absolute; top: 0; bottom: 0; border-radius: 2px; background: {C_SUB}; }}
  .rango input {{ position: absolute; inset: 0; width: 100%; margin: 0; background: none;
                 pointer-events: none; -webkit-appearance: none; appearance: none; }}
  .rango input::-webkit-slider-thumb {{ pointer-events: auto; -webkit-appearance: none; width: 18px; height: 18px;
                 border-radius: 50%; background: #fff; border: 3px solid {C_SUB}; cursor: pointer; }}
  .rango input::-moz-range-thumb {{ pointer-events: auto; width: 12px; height: 12px;
                 border-radius: 50%; background: #fff; border: 3px solid {C_SUB}; cursor: pointer; }}
  .rango input:focus-visible::-webkit-slider-thumb {{ outline: 3px solid {C_SUB}; outline-offset: 2px; }}
  #txt-rango {{ font-family: {TIT}; font-weight: 700; }}
  .controles small {{ font-size: .75rem; color: {C_DES}; }}
  /* Pop-up flotante bajo el gráfico: no ocupa espacio, así la página no cambia de alto */
  .info {{ position: absolute; top: calc(100% - 6px); width: 250px; z-index: 5;
           padding: 8px 10px; font-size: .8rem; line-height: 1.5; color: {C_TIT}; background: #fff;
           border: 1px solid #d5dce6; border-radius: 6px; box-shadow: 0 4px 14px rgba(13,27,42,.15);
           pointer-events: none; }}
  .info:empty {{ display: none; }}
  .info strong {{ display: flex; align-items: center; gap: 6px; font-family: {TIT}; font-size: .95rem; }}
  .info .lunar {{ width: 11px; height: 11px; }}
  .info .det {{ color: {C_SUB}; }}
  .claves {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 26px; }}
  @media (max-width: 760px) {{ .claves {{ grid-template-columns: 1fr; }} }}
  .claves p {{ margin: 0; font-size: .92rem; line-height: 1.55; padding-left: 14px; border-left: 4px solid {C_SUB}; }}
  .claves b {{ font-family: {TIT}; font-size: 1.05rem; }}
  .claves .alerta {{ border-color: {C_GUIA}; }}
  .cierre {{ font-family: {TIT}; font-weight: 700; font-size: clamp(1.2rem, 2.2vw, 1.6rem); color: {C_SUB};
             text-align: center; margin: 30px 0 0; }}
  footer {{ font-size: .78rem; color: {C_DES}; line-height: 1.6; margin-top: 26px; }}
</style>
</head>
<body>
<main>
  <h1>¿Dónde hay más ozono en Barcelona?</h1>
  <p class="sub">Distribución horaria de O₃ por estación: las urbanas tienen un segundo bulto cerca de cero que la suburbana no tiene</p>
  <p class="des">Distribución de una variable <b>cuantitativa continua</b>: concentración <b>horaria de O₃ (µg/m³)</b>, agrupada por <b>estación de medición</b> y tipo de entorno.</p>
  <div class="cuerpo">
    <div class="grafico"><div id="violin"></div><div class="info" aria-live="polite"></div></div>
    <div class="controles" role="group" aria-label="Leyenda, capas y horario">
      <span class="tit">Leyenda:</span>
      <span class="ley"><i class="lunar" style="background:{C_URB}"></i>Estación urbana</span>
      <span class="ley"><i class="lunar" style="background:{C_SUB_EST}"></i>Estación suburbana</span>
      <span class="tit">Mostrar:</span>
      <button type="button" class="capa" data-capa="caja" aria-pressed="true">{icono_caja}Mediana y rango intercuartílico (25-75 %)</button>
      <button type="button" class="capa" data-capa="zona" aria-pressed="true"><i class="lunar" style="background:{C_GUIA}"></i>Zona de O₃ bajo (&lt; {UMBRAL} µg/m³) y % de horas</button>
      <span class="tit">Horario: <output id="txt-rango">00:00 – 23:00 hrs</output></span>
      <div class="presets">{html_presets}</div>
      <div class="rango"><div class="pista"><div class="relleno"></div><div class="relleno"></div></div>
        <input type="range" id="h-ini" min="0" max="23" step="1" value="0" aria-label="Hora inicial">
        <input type="range" id="h-fin" min="0" max="23" step="1" value="23" aria-label="Hora final"></div>
      <small>Si la hora inicial es posterior a la final, el rango cruza la medianoche.</small>
    </div>
  </div>
  <section class="claves">
    <p><b>La estación con más ozono es la más alejada del tráfico.</b><br>
    Observatori Fabra, en Collserola, tiene una mediana de {mediana['Observatori Fabra']:.0f} µg/m³, frente a
    {med_urb.min():.0f}-{med_urb.max():.0f} en las urbanas.</p>
    <p class="alerta"><b>Las urbanas tienen un segundo bulto cerca de cero.</b><br>
    En Ciutadella, el {pct(bajo_est['Ciutadella'])} de las horas está por debajo de {UMBRAL} µg/m³; en Observatori Fabra,
    solo el {pct(bajo_est['Observatori Fabra'])}. Más de la mitad de esas horas son de noche ({pct(p_noche)}) y un tercio,
    en la punta de la mañana ({pct(p_punta)}): el NO que emite el tráfico consume el ozono. Un boxplot no mostraría ese bulto.
    Prueba los horarios <i>Noche</i> y <i>Mediodía</i>: el bulto aparece y desaparece.</p>
  </section>
  <p class="cierre">«Alejarse del tráfico no significa respirar menos ozono.»</p>
  <footer>{nota}</footer>
</main>
<script>
  const D = {json.dumps(datos, ensure_ascii=False)};
  const U = {UMBRAL}, VMAX = {VMAX};
  const C = {{urb: '{C_URB}', sub: '{C_SUB_EST}', guia: '{C_GUIA}', tit: '{C_TIT}', azul: '{C_SUB}'}};
  const FUENTE = "{TIT}";
  const ver = {{caja: true, zona: true}};
  let horas = [...Array(24).keys()], R = {{}};
  const g = document.getElementById('violin'), info = document.querySelector('.info');
  const pct = x => (x < .01 ? (x * 100).toFixed(1) : Math.round(x * 100)) .toString().replace('.', ',') + ' %';
  const alfa = (hex, a) => `rgba(${{parseInt(hex.slice(1, 3), 16)}},${{parseInt(hex.slice(3, 5), 16)}},${{parseInt(hex.slice(5, 7), 16)}},${{a}})`;

  // Resumen de una estación en las horas elegidas: cuartiles, % bajo el umbral y densidad (KDE gaussiano)
  function resumen(e) {{
    const c = new Array(VMAX + 1).fill(0);
    horas.forEach(h => D.hist[e][h].forEach((k, v) => c[v] += k));
    let n = 0, s = 0, s2 = 0, lo = -1, hi = 0, bajo = 0;
    c.forEach((k, v) => {{ if (k) {{ n += k; s += k * v; s2 += k * v * v; if (lo < 0) lo = v; hi = v; if (v < U) bajo += k; }} }});
    const enPos = i => {{ let acc = 0; for (let v = 0; v <= VMAX; v++) {{ acc += c[v]; if (acc > i) return v; }} }};
    const q = p => {{ const t = p * (n - 1), f = Math.floor(t); return enPos(f) + (t - f) * (enPos(Math.ceil(t)) - enPos(f)); }};
    const sd = Math.sqrt(Math.max(s2 / n - (s / n) ** 2, 1)), bw = Math.max(1.5, 1.06 * sd * n ** -0.2);
    const ys = [], dens = [];
    for (let y = lo; y <= hi; y += 0.5) {{
      let d = 0;
      for (let v = Math.max(0, Math.floor(y - 4 * bw)); v <= Math.min(VMAX, y + 4 * bw); v++)
        if (c[v]) d += c[v] * Math.exp(-0.5 * ((y - v) / bw) ** 2);
      ys.push(y); dens.push(d);
    }}
    return {{n, q1: q(.25), med: q(.5), q3: q(.75), bajo: bajo / n, ys, dens}};
  }}

  function dibujar() {{
    D.orden.forEach(e => R[e] = resumen(e));
    const trazas = [], notas = [], formas = [];
    D.orden.forEach((e, i) => {{
      const r = R[e], x0 = D.pos[i], col = D.info[e].sub ? C.sub : C.urb, m = Math.max(...r.dens);
      const der = r.dens.map(d => x0 + .42 * d / m), izq = r.dens.map(d => x0 - .42 * d / m);
      trazas.push({{type: 'scatter', mode: 'lines', x: [...der, ...izq.reverse()], y: [...r.ys, ...[...r.ys].reverse()],
        fill: 'toself', fillcolor: alfa(col, .5), line: {{color: col, width: 1.2}}, hoverinfo: 'skip'}});
      if (ver.caja) {{
        trazas.push({{type: 'scatter', mode: 'lines', x: [x0, x0], y: [r.q1, r.q3], line: {{color: C.tit, width: 6}}, hoverinfo: 'skip'}});
        trazas.push({{type: 'scatter', mode: 'markers', x: [x0], y: [r.med], hoverinfo: 'skip',
          marker: {{size: 10, color: '#fff', line: {{color: C.tit, width: 2}}}}}});
      }}
      if (ver.zona) notas.push({{x: x0, y: U + 6, text: `<b>${{pct(r.bajo)}}</b>`, showarrow: false,
        font: {{family: FUENTE, size: 13, color: C.guia}}, bgcolor: 'rgba(255,255,255,.85)'}});
    }});
    // Zona invisible por estación para el pop-up
    trazas.push({{type: 'bar', x: D.pos, y: D.pos.map(() => 172), base: -2, width: .9,
      marker: {{color: 'rgba(0,0,0,0)'}}, hoverinfo: 'none', customdata: D.orden}});

    const fin = D.pos[D.pos.length - 1], corte = (D.pos[D.pos.length - 2] + fin) / 2;
    if (ver.zona) formas.push(
      {{type: 'rect', xref: 'paper', x0: 0, x1: 1, y0: 0, y1: U, fillcolor: alfa(C.guia, .10), line: {{width: 0}}, layer: 'below'}},
      {{type: 'line', xref: 'paper', x0: 0, x1: 1, y0: U, y1: U, line: {{color: C.guia, width: 1, dash: 'dash'}}}});
    formas.push({{type: 'line', x0: corte, x1: corte, yref: 'paper', y0: 0, y1: 1, line: {{color: '#c5cfdb', width: 1.2}}}});
    const cab = {{yref: 'paper', y: 1, yanchor: 'bottom', showarrow: false, font: {{family: FUENTE, size: 14}}}};
    notas.push({{...cab, x: (D.pos[0] + D.pos[D.pos.length - 2]) / 2, text: '<b>URBANAS (tráfico y fondo urbano)</b>', font: {{...cab.font, color: C.urb}}}},
               {{...cab, x: fin, text: '<b>SUBURBANA</b>', font: {{...cab.font, color: C.sub}}}},
               {{xref: 'paper', yref: 'paper', x: 0, y: 1, xanchor: 'right', yanchor: 'bottom', xshift: -6, showarrow: false,
                 text: 'µg/m³', font: {{family: FUENTE, size: 12, color: C.azul}}}});

    Plotly.react(g, trazas, {{
      height: 560, margin: {{l: 70, r: 16, t: 34, b: 64}}, showlegend: false, hovermode: 'closest',
      paper_bgcolor: 'white', plot_bgcolor: 'white', font: {{family: FUENTE, size: 12, color: '#333'}},
      xaxis: {{tickvals: D.pos, ticktext: D.ticks, range: [D.pos[0] - .7, fin + .7], fixedrange: true,
               showgrid: false, zeroline: false, ticks: '', tickfont: {{size: 12, color: C.tit}}}},
      yaxis: {{range: [-2, 172], dtick: 20, fixedrange: true, zeroline: false, showline: true, linecolor: '#bbb',
               gridcolor: 'rgba(0,0,0,.09)', tickfont: {{size: 13}},
               title: {{text: '<b>O₃, concentración horaria (µg/m³)</b>', font: {{size: 14, color: C.tit}}, standoff: 8}}}},
      shapes: formas, annotations: notas
    }}, {{displayModeBar: false, responsive: true}});
  }}

  // Pop-up con las cifras de la estación señalada, debajo del gráfico
  function enlazar() {{
    g.on('plotly_hover', ev => {{
      const p = ev.points.find(p => p.customdata);
      if (!p) return;
      const e = p.customdata, r = R[e], f = D.info[e], L = g._fullLayout;
      const cx = L._size.l + L.xaxis.l2p(p.x);
      info.style.left = Math.max(0, Math.min(g.clientWidth - 250, cx - 125)) + 'px';
      const n0 = x => x.toFixed(0);
      info.innerHTML = `<strong><i class="lunar" style="background:${{f.sub ? C.sub : C.urb}}"></i>${{f.nombre}}</strong>` +
        `<span class="det">${{f.tipo}}, ${{f.anios}}</span><br>Mediana: <b>${{n0(r.med)}} µg/m³</b><br>` +
        `Rango intercuartílico: <b>${{n0(r.q1)}}-${{n0(r.q3)}} µg/m³</b><br>` +
        `Horas con O₃ &lt; ${{U}} µg/m³: <b>${{pct(r.bajo)}}</b><br>Horas medidas en el horario: <b>${{r.n.toLocaleString('es-ES')}}</b>`;
    }});
    g.on('plotly_unhover', () => info.innerHTML = '');
  }}

  document.querySelectorAll('.capa').forEach(b => b.addEventListener('click', () => {{
    ver[b.dataset.capa] = !ver[b.dataset.capa];
    b.setAttribute('aria-pressed', ver[b.dataset.capa]);
    dibujar();
  }}));

  // Slider doble de horario; si el inicio supera al final, el rango cruza la medianoche
  const ini = document.getElementById('h-ini'), fin = document.getElementById('h-fin');
  const rellenos = document.querySelectorAll('.relleno'), txt = document.getElementById('txt-rango');
  const hh = h => String(h).padStart(2, '0') + ':00';
  const tramo = (el, a, b) => {{ el.style.left = (a / 23 * 100) + '%'; el.style.width = ((b - a) / 23 * 100) + '%'; }};
  function rango() {{
    const a = +ini.value, b = +fin.value;
    horas = a <= b ? Array.from({{length: b - a + 1}}, (_, i) => a + i)
                   : [...Array.from({{length: 24 - a}}, (_, i) => a + i), ...Array.from({{length: b + 1}}, (_, i) => i)];
    if (a <= b) {{ tramo(rellenos[0], a, b); tramo(rellenos[1], 0, 0); }}
    else {{ tramo(rellenos[0], a, 23); tramo(rellenos[1], 0, b); }}
    txt.textContent = `${{hh(a)}} – ${{hh(b)}} hrs`;
    document.querySelectorAll('.preset').forEach(p => p.setAttribute('aria-pressed', +p.dataset.a === a && +p.dataset.b === b));
    dibujar();
  }}
  ini.addEventListener('input', rango);
  fin.addEventListener('input', rango);
  document.querySelectorAll('.preset').forEach(p => p.addEventListener('click', () => {{
    ini.value = p.dataset.a; fin.value = p.dataset.b; rango();
  }}));
  rango();
  enlazar();
</script>
</body>
</html>
'''

SALIDA.write_text(pagina, encoding='utf-8')
print(f'Página generada: {SALIDA}')
for e in orden:
    print(f'{e:<18} mediana {mediana[e]:>4.0f}  O3 < {UMBRAL}: {pct(bajo_est[e])}')
print(f'Horas urbanas con O3 bajo: noche {pct(p_noche)}, punta mañana {pct(p_punta)}')
