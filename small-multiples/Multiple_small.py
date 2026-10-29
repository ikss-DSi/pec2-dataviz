# Small multiples interactivos: perfil diario de NO2 por estación (PEC 2, Visualización de datos)
# Requisitos: pip install pandas pyarrow plotly
# Genera Multiple_small.html junto a este script, una página autónoma lista para publicar en GitHub Pages.

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# El parquet se busca en la carpeta del script y en las superiores; la página se guarda junto al script
AQUI = Path(__file__).resolve().parent
RUTA_DATOS = next(p / 'bcn_virtual_sensor.parquet' for p in [AQUI, *AQUI.parents]
                  if (p / 'bcn_virtual_sensor.parquet').exists())
SALIDA = Path(__file__).resolve().with_suffix('.html')

# Tipografías (se cargan desde Google Fonts en la página)
TIT = "'Source Sans 3', 'Source Sans Pro', sans-serif"
DES = "'Noto Sans', sans-serif"

# Escala secuencial para título > subtítulo > descripción
C_TIT, C_SUB, C_DES = '#0d1b2a', '#33507a', '#6f8bb0'
# Series: azul laborable, verde fin de semana; versiones claras para los promedios
C_LAB, C_FDS = '#1f5fbf', '#2a9d4b'
C_PROM_LAB, C_PROM_FDS = '#74E4F7', '#81F774'

# --- Datos ---
df = pd.read_parquet(RUTA_DATOS)
df['est'] = df['station_name'].str.replace('Barcelona - ', '')

tipo = {'Traffic': 'tráfico', 'Urban Background': 'fondo urbano', 'Suburban': 'suburbana'}
especiales = ('Eixample', 'Navas')            # estaciones con menos datos -> asterisco
periodo = df.groupby('est')['year'].agg(['min', 'max'])
tipo_est = df.groupby('est')['station_type'].first().astype(str)
nombre, detalle = {}, {}                      # título en dos líneas: estación / (tipo, años)
for e, (a, b) in periodo.iterrows():
    anios = f'{a}' if a == b else f'{a}-{b}'
    nombre[e] = e + ('*' if e in especiales else '')
    detalle[e] = f'({tipo[tipo_est[e]]}, {anios})'

orden = ['Eixample', 'Gràcia', 'Navas', 'Ciutadella', 'Palau Reial', 'Vall Hebron', 'Observatori Fabra']

# Media de NO2 por estación, hora y tipo de día
perfil = df.groupby(['est', 'hour', 'is_weekend'])['NO2'].mean().unstack()
perfil.columns = ['Laborable', 'Fin de semana']
perfil = perfil.reset_index()

# Promedios: media simple de los perfiles de las 7 estaciones, por tipo de día
prom_lab = perfil.groupby('hour')['Laborable'].mean()
prom_fds = perfil.groupby('hour')['Fin de semana'].mean()

# Registros por estación para la nota al pie
n = df.groupby('est').size()
resto = n.drop(list(especiales))

# --- Gráficos: una figura por estación, colocadas en una rejilla que se adapta a la pantalla ---
# Cada traza lleva meta = [tipo de día, es promedio] para que los botones la encuentren.
# hoverinfo='none' oculta la etiqueta de Plotly; los valores se muestran debajo del eje X (ver script).
def linea(x, y, nom, color, dia, es_prom):
    return go.Scatter(
        x=x, y=y, name=nom, mode='lines', meta=[dia, es_prom], hoverinfo='none',
        line=dict(color=color, width=3 if es_prom else 2.2, dash='dash' if es_prom else 'solid'))

def figura(e):
    s = perfil[perfil['est'] == e].sort_values('hour')
    fig = go.Figure([
        linea(prom_lab.index, prom_lab.values, 'Promedio laborable', C_PROM_LAB, 'lab', True),
        linea(prom_fds.index, prom_fds.values, 'Promedio fin de semana', C_PROM_FDS, 'fds', True),
        linea(s['hour'], s['Fin de semana'], 'Fin de semana', C_FDS, 'fds', False),
        linea(s['hour'], s['Laborable'], 'Laborable', C_LAB, 'lab', False),
    ])
    fig.update_layout(
        height=270, margin=dict(l=52, r=34, t=22, b=44), showlegend=False,
        paper_bgcolor='white', plot_bgcolor='white', hovermode='x',
        font=dict(family=TIT, size=12, color='#444'))
    fig.update_xaxes(range=[-0.5, 23.5], tickvals=[0, 6, 12, 18, 23],
                     title=dict(text='Hora del día', font=dict(size=12, color=C_SUB), standoff=6),
                     showgrid=False, showline=True, linecolor='#bbb', fixedrange=True,
                     showspikes=True, spikemode='across', spikecolor='#999', spikethickness=1, spikedash='solid')
    fig.update_yaxes(range=[0, 58], gridcolor='rgba(0,0,0,.09)', zeroline=False,
                     title=dict(text='NO₂ medio (µg/m³)', font=dict(size=12, color=C_SUB), standoff=4),
                     showline=True, linecolor='#bbb', fixedrange=True)
    # Unidades al final de cada eje
    unidad = dict(xref='paper', yref='paper', showarrow=False, font=dict(size=11, color=C_SUB))
    fig.add_annotation(text='µg/m³', x=0, y=1, xanchor='center', yanchor='bottom', yshift=2, **unidad)
    fig.add_annotation(text='hrs', x=1, y=0, xanchor='left', yanchor='middle', xshift=4, **unidad)
    return fig

config = {'displayModeBar': False, 'responsive': True}
paneles = []
for i, e in enumerate(orden):
    html = figura(e).to_html(full_html=False, include_plotlyjs=False, config=config, div_id=f'g{i}')
    paneles.append(f'<figure class="panel"><figcaption><strong>{nombre[e]}</strong>'
                   f'<span>{detalle[e]}</span></figcaption>{html}'
                   f'<div class="info" aria-live="polite"></div></figure>')

# Casilla 8: botones que encienden y apagan las series en los 7 paneles a la vez
mitades = f'linear-gradient(90deg, {C_PROM_LAB} 50%, {C_PROM_FDS} 50%)'
botones = [('lab', 'Laborable', C_LAB),
           ('fds', 'Fin de semana', C_FDS),
           ('prom', 'Promedios de las 7 estaciones', mitades)]
html_botones = ''.join(
    f'<button type="button" aria-pressed="true" data-serie="{k}">'
    f'<i class="lunar" style="background:{c}"></i>{t}</button>'
    for k, t, c in botones)
# Slider doble para el rango horario (afecta a todos los gráficos)
html_rango = ('<span>Horario: <output id="txt-rango">00:00 – 23:00 hrs</output></span>'
              '<div class="rango"><div class="pista"><div class="relleno"></div></div>'
              '<input type="range" id="h-ini" min="0" max="23" step="1" value="0" aria-label="Hora inicial">'
              '<input type="range" id="h-fin" min="0" max="23" step="1" value="23" aria-label="Hora final">'
              '</div>')
paneles.append(f'<div class="panel controles" role="group" aria-label="Series visibles y rango horario">'
               f'<span>Mostrar:</span>{html_botones}{html_rango}</div>')

# Nota al pie
fmt = lambda x: f'{x:,}'.replace(',', '.')
nota = (f'* Estaciones con menos datos: Eixample solo tiene 2023 ({fmt(n["Eixample"])} registros horarios) '
        f'y Navas solo 2026 ({fmt(n["Navas"])}); el resto cubre 2023-2026 con entre '
        f'{fmt(resto.min())} y {fmt(resto.max())} registros cada una.<br>'
        'Entre paréntesis: tipo de estación y años con datos. Misma escala en todos los paneles. '
        'Promedios: media simple de los perfiles de las 7 estaciones para cada tipo de día.<br>'
        'Fuente: Ajuntament de Barcelona, Open Data BCN, calidad del aire (dataset preparado por la UOC, M2.891).')

pagina = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NO₂ diario en Barcelona</title>
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
  .lunar {{ display: inline-block; flex: none; width: 14px; height: 14px; border-radius: 50%; }}
  .controles {{ display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 10px;
               padding: 20px; border: 2px solid {C_SUB}; align-self: center; justify-self: center;
               width: 100%; max-width: 320px; }}
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
  #txt-rango {{ color: {C_TIT}; }}
  .controles > span {{ font-family: {TIT}; font-weight: 700; font-size: 1.1rem; color: {C_SUB}; }}
  button {{ display: inline-flex; align-items: center; gap: 10px; padding: 4px 0; cursor: pointer; text-align: left;
            font: 700 1rem {TIT}; color: {C_TIT}; background: none; border: 0; transition: opacity .15s; }}
  button .lunar {{ width: 18px; height: 18px; }}
  button[aria-pressed="false"] {{ opacity: .35; text-decoration: line-through; }}
  button:focus-visible {{ outline: 3px solid {C_SUB}; outline-offset: 3px; }}
  .rejilla {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px 14px; }}
  @media (max-width: 1100px) {{ .rejilla {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
  @media (max-width: 800px)  {{ .rejilla {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
  @media (max-width: 520px)  {{ .rejilla {{ grid-template-columns: 1fr; }} }}
  .panel {{ margin: 0; min-width: 0; position: relative; }}
  figcaption {{ font-family: {TIT}; text-align: center; line-height: 1.2; }}
  figcaption strong {{ display: block; font-size: 1.1rem; }}
  figcaption span {{ display: block; font-size: .9rem; color: {C_SUB}; }}
  /* Pop-up flotante bajo el gráfico: no ocupa espacio, así la página no cambia de alto */
  .info {{ position: absolute; top: calc(100% - 8px); left: 40px; right: 8px; z-index: 5;
           padding: 8px 10px; font-size: .78rem; color: {C_TIT}; background: #fff;
           border: 1px solid #d5dce6; border-radius: 6px; box-shadow: 0 4px 14px rgba(13,27,42,.15);
           display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 2px 10px;
           pointer-events: none; }}
  .info:empty {{ display: none; }}
  .info .hora {{ grid-column: 1 / -1; font-weight: 700; color: {C_SUB}; }}
  .info span {{ display: flex; align-items: center; gap: 5px; }}
  .info .lunar {{ width: 10px; height: 10px; }}
  footer {{ font-size: .78rem; color: {C_DES}; line-height: 1.6; margin-top: 18px; }}
</style>
</head>
<body>
<main>
  <h1>¿Cuánto NO₂ se respira al día en Barcelona?</h1>
  <p class="sub">Perfil diario de NO₂ en 7 estaciones de medición, día laborable frente a fin de semana, comparado con el promedio</p>
  <p class="des">Serie temporal <b>cuantitativa</b>: concentración media de <b>NO₂ (µg/m³)</b> por <b>hora del día</b>, agrupada por estación de medición y tipo de día.</p>
  <div class="rejilla">{''.join(paneles)}</div>
  <footer>{nota}</footer>
</main>
<script>
  const activo = {{lab: true, fds: true, prom: true}};
  const graficos = [...document.querySelectorAll('.js-plotly-plot')];
  const ordenInfo = [3, 2, 0, 1];   // Laborable, Fin de semana, Promedio laborable, Promedio fin de semana

  function aplicar() {{
    graficos.forEach(g => {{
      const vis = g.data.map(t => activo[t.meta[0]] && (!t.meta[1] || activo.prom));
      Plotly.restyle(g, {{visible: vis}});
    }});
  }}
  document.querySelectorAll('button[data-serie]').forEach(b => b.addEventListener('click', () => {{
    const k = b.dataset.serie;
    activo[k] = !activo[k];
    b.setAttribute('aria-pressed', activo[k]);
    aplicar();
  }}));

  // Valores de la hora señalada, debajo del eje X del gráfico activo
  graficos.forEach(g => {{
    const info = g.closest('.panel').querySelector('.info');
    g.on('plotly_hover', ev => {{
      const y = {{}};
      ev.points.forEach(p => y[p.curveNumber] = p.y);
      const hora = String(ev.points[0].x).padStart(2, '0') + ':00 hrs';
      info.innerHTML = `<span class="hora">${{hora}}</span>` + ordenInfo.filter(i => i in y).map(i =>
        `<span><i class="lunar" style="background:${{g.data[i].line.color}}"></i>` +
        `${{g.data[i].name}}: <b>${{y[i].toFixed(1)}}</b></span>`).join('');
    }});
    g.on('plotly_unhover', () => info.innerHTML = '');
  }});

  // Slider doble: rango horario común a todos los gráficos
  const ini = document.getElementById('h-ini'), fin = document.getElementById('h-fin');
  const relleno = document.querySelector('.relleno'), txt = document.getElementById('txt-rango');
  const hh = h => String(h).padStart(2, '0') + ':00';
  function rango(ev) {{
    let a = +ini.value, b = +fin.value;
    if (a > b) {{ if (ev && ev.target === ini) ini.value = a = b; else fin.value = b = a; }}
    relleno.style.left = (a / 23 * 100) + '%';
    relleno.style.width = ((b - a) / 23 * 100) + '%';
    txt.textContent = `${{hh(a)}} – ${{hh(b)}} hrs`;
    const paso = b - a <= 6 ? 1 : b - a <= 12 ? 2 : 6;
    const marcas = [];
    for (let h = Math.ceil(a / paso) * paso; h <= b; h += paso) marcas.push(h);
    if (marcas[marcas.length - 1] !== b) marcas.push(b);
    graficos.forEach(g => Plotly.relayout(g, {{'xaxis.range': [a - 0.5, b + 0.5], 'xaxis.tickvals': marcas}}));
  }}
  ini.addEventListener('input', rango);
  fin.addEventListener('input', rango);
  rango();
</script>
</body>
</html>
'''

SALIDA.write_text(pagina, encoding='utf-8')
print(f'Página generada: {SALIDA.resolve()}')
