# Icon chart: contaminación por estación frente a las guías de la OMS (PEC 2, Visualización de datos)
# Requisitos: pip install pandas pyarrow
# Genera icon_chart.html junto a este script, una página autónoma lista para publicar en GitHub Pages.

from pathlib import Path
import json

import numpy as np
import pandas as pd

# El parquet se busca en la carpeta del script y en las superiores; la página se guarda junto al script
AQUI = Path(__file__).resolve().parent
RUTA_DATOS = next(p / 'bcn_virtual_sensor.parquet' for p in [AQUI, *AQUI.parents]
                  if (p / 'bcn_virtual_sensor.parquet').exists())
SALIDA = Path(__file__).resolve().with_suffix('.html')

# Guías de la OMS 2021 (WHO global air quality guidelines, tabla de niveles AQG)
GUIA_NO2 = 10      # µg/m³, media anual
GUIA_O3 = 60       # µg/m³, temporada alta: media de los máximos diarios de la media móvil de 8 h
                   # en los 6 meses consecutivos con más ozono
UNIDAD_NO = 5      # µg/m³ por icono para el NO (la OMS no fija guía para el NO)

TIT = "'Source Sans 3', 'Source Sans Pro', sans-serif"
DES = "'Noto Sans', sans-serif"
C_TIT, C_SUB, C_DES = '#0d1b2a', '#33507a', '#6f8bb0'
# Azul y naranja se distinguen también con daltonismo (verde y rojo no)
C_OK, C_EXCESO, C_NO = '#1f5fbf', '#e07b00', '#8a99ad'   # dentro de la guía, exceso, NO sin guía

MESES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
         'September', 'October', 'November', 'December']
MESES_ES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

# --- Datos ---
df = pd.read_parquet(RUTA_DATOS)
df['est'] = df['station_name'].str.replace('Barcelona - ', '')
tipo = {'Traffic': 'tráfico', 'Urban Background': 'fondo urbano', 'Suburban': 'suburbana'}
especiales = ('Eixample', 'Navas')            # menos de un año de datos -> asterisco
df['m'] = df['month'].map({m: i for i, m in enumerate(MESES)})

# Las filas están en orden temporal: cada cambio de day_name es un día nuevo
df['dia'] = df.groupby('est')['day_name'].transform(lambda s: (s != s.shift()).cumsum())
# Media móvil de 8 h dentro de cada día (al menos 6 horas con dato) y su máximo diario
df['o3_8h'] = df.groupby(['est', 'dia'])['O3'].transform(lambda s: s.rolling(8, min_periods=6).mean())
diario = df.groupby(['est', 'dia']).agg(o3max=('o3_8h', 'max'), m=('m', 'first')).dropna()

def temporada_alta(d):
    """Media de los máximos diarios de 8 h en los 6 meses consecutivos con más ozono."""
    por_mes = d.groupby('m')['o3max'].mean().reindex(range(12))
    mejor = max((por_mes[[(s + k) % 12 for k in range(6)]].mean(), s) for s in range(12)
                if por_mes[[(s + k) % 12 for k in range(6)]].notna().any())
    meses = [(mejor[1] + k) % 12 for k in range(6)]
    return d[d['m'].isin(meses)]['o3max'].mean(), f'{MESES_ES[meses[0]]}-{MESES_ES[meses[-1]]}'

filas = []
for e, d in df.groupby('est'):
    o3, meses = temporada_alta(diario.loc[e])
    a, b = d['year'].min(), d['year'].max()
    filas.append(dict(
        est=e, ast='*' if e in especiales else '',
        tipo=tipo[str(d['station_type'].iloc[0])], anios=f'{a}' if a == b else f'{a}-{b}',
        no2=round(d['NO2'].mean(), 1), o3=round(o3, 1), meses=meses, no=round(d['NO'].mean(), 1)))
filas.sort(key=lambda f: -f['no2'])            # orden inicial: de más a menos NO₂

# --- Página ---
fmt = lambda x: f'{x:.1f}'.replace('.', ',')
nota = ('* Eixample (solo 2023) y Navas (solo 2026) tienen menos de un año de datos: su temporada alta de O₃ '
        'es una estimación con los meses disponibles.<br>'
        'NO₂ y NO: media de todas las horas del periodo 2023-2026, no de un año natural. '
        'O₃: media de los máximos diarios de la media móvil de 8 h en los 6 meses consecutivos con más ozono, '
        'calculada a partir de los datos horarios.<br>'
        'Guías: OMS (2021), <a href="https://www.who.int/publications/i/item/9789240034228">WHO global air quality '
        'guidelines</a>: NO₂ media anual 10 µg/m³; O₃ temporada alta 60 µg/m³. La OMS no fija valor guía para el NO.<br>'
        'Datos: Ajuntament de Barcelona, Open Data BCN, calidad del aire (dataset preparado por la UOC, M2.891).')

pagina = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aire de Barcelona y OMS</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&family=Source+Sans+3:wght@400;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #fff; color: {C_TIT}; font-family: {DES}; }}
  main {{ max-width: 1300px; margin: 0 auto; padding: 28px 16px 40px; }}
  h1 {{ font-family: {TIT}; font-size: clamp(1.6rem, 3.2vw, 2.4rem); margin: 0 0 6px; }}
  .sub {{ font-family: {TIT}; font-weight: 700; font-size: clamp(1rem, 1.6vw, 1.25rem); color: {C_SUB}; margin: 0 0 6px; }}
  .des {{ font-size: .9rem; color: {C_DES}; margin: 0 0 18px; }}
  .des b {{ color: {C_SUB}; }}
  .barra {{ display: flex; flex-wrap: wrap; gap: 14px 28px; align-items: center; margin-bottom: 14px;
            font-family: {TIT}; font-weight: 700; color: {C_TIT}; }}
  .leyenda {{ display: flex; flex-wrap: wrap; gap: 6px 18px; padding: 8px 14px; border: 2px solid {C_SUB}; }}
  .leyenda span {{ display: inline-flex; align-items: center; gap: 6px; }}
  .leyenda svg {{ width: 16px; height: 22px; }}
  .orden button {{ font: 700 .95rem {TIT}; color: {C_SUB}; background: #fff; border: 2px solid {C_SUB};
                   padding: 4px 10px; cursor: pointer; }}
  .orden button[aria-pressed="true"] {{ background: {C_SUB}; color: #fff; }}
  .orden button:focus-visible {{ outline: 3px solid {C_SUB}; outline-offset: 2px; }}
  .tabla {{ display: grid; grid-template-columns: minmax(150px, 1.1fr) repeat(3, minmax(0, 1.3fr)); }}
  .cab {{ font-family: {TIT}; font-weight: 700; color: {C_SUB}; padding: 6px 8px 10px; border-bottom: 2px solid {C_SUB};
          line-height: 1.25; }}
  .cab small {{ display: block; font-weight: 400; color: {C_DES}; font-family: {DES}; font-size: .78rem; }}
  .fila {{ display: contents; }}
  .fila > div {{ padding: 10px 8px; border-bottom: 1px solid #e3e8ef; display: flex; align-items: center; min-width: 0; }}
  .fila:hover > div {{ background: #f4f7fb; }}
  .est strong {{ display: block; font-family: {TIT}; font-size: 1.05rem; }}
  .est span {{ display: block; font-size: .8rem; color: {C_SUB}; }}
  .est {{ flex-direction: column; align-items: flex-start !important; justify-content: center; }}
  .iconos {{ display: flex; flex-wrap: wrap; gap: 4px; }}
  .iconos svg {{ width: 24px; height: 35px; flex: none; }}
  .valor {{ font-family: {TIT}; font-weight: 700; font-size: 1.05rem; margin-left: 12px; white-space: nowrap; }}
  .valor small {{ display: block; font-weight: 400; font-size: .75rem; color: {C_DES}; }}
  details {{ margin-top: 20px; font-size: .85rem; }}
  summary {{ cursor: pointer; font-family: {TIT}; font-weight: 700; color: {C_SUB}; }}
  table {{ border-collapse: collapse; margin-top: 8px; }}
  th, td {{ padding: 4px 10px; border-bottom: 1px solid #e3e8ef; text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  footer {{ font-size: .78rem; color: {C_DES}; line-height: 1.6; margin-top: 18px; }}
  footer a {{ color: {C_SUB}; }}
  @media (max-width: 760px) {{
    .tabla {{ grid-template-columns: 1fr; }}
    .cab:not(:first-child) {{ display: none; }}
    .fila > div {{ border-bottom: 0; padding: 4px 8px; }}
    .fila > .est {{ border-top: 1px solid #c5cfdb; padding-top: 12px; }}
    .fila > div[data-etq]::before {{ content: attr(data-etq); width: 3.2em; flex: none; font-family: {TIT};
                                     font-weight: 700; color: {C_SUB}; }}
  }}
</style>
</head>
<body>
<main>
  <h1>¿Respira Barcelona el aire que recomienda la OMS?</h1>
  <p class="sub">Donde hay menos NO₂ hay más ozono: ninguna estación cumple a la vez las dos guías de la OMS</p>
  <p class="des">Cada icono equivale al <b>valor guía de la OMS</b>: lo que pasa del primer icono es <b>exceso</b>.
  Para el NO, que la OMS no regula, cada icono son 5 µg/m³.</p>
  <div class="barra">
    <div class="leyenda" aria-label="Leyenda">
      <span><svg viewBox="0 0 18 26"><use href="#persona" fill="{C_OK}"/></svg>Dentro de la guía OMS</span>
      <span><svg viewBox="0 0 18 26"><use href="#persona" fill="{C_EXCESO}"/></svg>Exceso sobre la guía</span>
      <span><svg viewBox="0 0 18 26"><use href="#persona" fill="{C_NO}"/></svg>NO: 5 µg/m³ (sin guía)</span>
    </div>
    <div class="orden" role="group" aria-label="Ordenar estaciones">Ordenar por:
      <button type="button" data-k="no2" aria-pressed="true">NO₂</button>
      <button type="button" data-k="o3" aria-pressed="false">O₃</button>
      <button type="button" data-k="no" aria-pressed="false">NO</button>
    </div>
  </div>
  <svg width="0" height="0" style="position:absolute" aria-hidden="true">
    <symbol id="persona" viewBox="0 0 18 26"><circle cx="9" cy="5" r="4.5"/>
      <path d="M2 26V15a7 7 0 0 1 14 0v11z"/></symbol>
  </svg>
  <div class="tabla" id="tabla">
    <div class="cab">Estación<small>tipo y años con datos</small></div>
    <div class="cab">NO₂ · veces la guía<small>guía OMS: 10 µg/m³ de media anual</small></div>
    <div class="cab">O₃ · veces la guía<small>guía OMS: 60 µg/m³ en temporada alta</small></div>
    <div class="cab">NO · µg/m³<small>sin guía OMS; 1 icono = 5 µg/m³</small></div>
  </div>
  <details>
    <summary>Ver los datos en una tabla</summary>
    <table>
      <thead><tr><th>Estación</th><th>NO₂ (µg/m³)</th><th>Veces guía NO₂</th><th>O₃ temporada alta (µg/m³)</th>
      <th>Meses</th><th>Veces guía O₃</th><th>NO (µg/m³)</th></tr></thead>
      <tbody>{''.join(
        f"<tr><td>{f['est']}{f['ast']}</td><td>{fmt(f['no2'])}</td><td>{fmt(f['no2'] / GUIA_NO2)}</td>"
        f"<td>{fmt(f['o3'])}</td><td>{f['meses']}</td><td>{fmt(f['o3'] / GUIA_O3)}</td><td>{fmt(f['no'])}</td></tr>"
        for f in filas)}</tbody>
    </table>
  </details>
  <footer>{nota}</footer>
</main>
<script>
  const filas = {json.dumps(filas, ensure_ascii=False)};
  const G = {{no2: {GUIA_NO2}, o3: {GUIA_O3}}}, U_NO = {UNIDAD_NO};
  const C = {{ok: '{C_OK}', ex: '{C_EXCESO}', no: '{C_NO}'}};
  const coma = x => x.toFixed(1).replace('.', ',');

  // Un icono por unidad; el último se recorta según la fracción
  function iconos(valor, colorDe) {{
    let html = '';
    for (let i = 0; i < Math.ceil(valor - 1e-9); i++) {{
      const f = Math.min(1, valor - i), id = 'c' + Math.random().toString(36).slice(2);
      html += `<svg viewBox="0 0 18 26" aria-hidden="true"><defs><clipPath id="${{id}}"><rect width="${{18 * f}}" height="26"/></clipPath></defs>` +
              `<use href="#persona" fill="#e3e8ef"/><use href="#persona" fill="${{colorDe(i)}}" clip-path="url(#${{id}})"/></svg>`;
    }}
    return html;
  }}
  const guia = i => i < 1 ? C.ok : C.ex;

  function pintar(k) {{
    const t = document.getElementById('tabla');
    t.querySelectorAll('.fila').forEach(n => n.remove());
    [...filas].sort((a, b) => b[k] / (G[k] || 1) - a[k] / (G[k] || 1)).forEach(f => {{
      const v2 = f.no2 / G.no2, v3 = f.o3 / G.o3, vn = f.no / U_NO;
      t.insertAdjacentHTML('beforeend', `<div class="fila">
        <div class="est"><strong>${{f.est}}${{f.ast}}</strong><span>(${{f.tipo}}, ${{f.anios}})</span></div>
        <div data-etq="NO₂" title="NO₂: ${{coma(f.no2)}} µg/m³ = ${{coma(v2)}} veces la guía OMS">
          <div class="iconos" role="img" aria-label="NO₂ ${{coma(v2)}} veces la guía">${{iconos(v2, guia)}}</div>
          <div class="valor">${{coma(v2)}}×<small>${{coma(f.no2)}} µg/m³</small></div></div>
        <div data-etq="O₃" title="O₃ temporada alta (${{f.meses}}): ${{coma(f.o3)}} µg/m³ = ${{coma(v3)}} veces la guía OMS">
          <div class="iconos" role="img" aria-label="O₃ ${{coma(v3)}} veces la guía">${{iconos(v3, guia)}}</div>
          <div class="valor">${{coma(v3)}}×<small>${{coma(f.o3)}} µg/m³</small></div></div>
        <div data-etq="NO" title="NO: ${{coma(f.no)}} µg/m³ (la OMS no fija guía)">
          <div class="iconos" role="img" aria-label="NO ${{coma(f.no)}} microgramos">${{iconos(vn, () => C.no)}}</div>
          <div class="valor">${{coma(f.no)}}<small>µg/m³</small></div></div>
      </div>`);
    }});
  }}
  document.querySelectorAll('.orden button').forEach(b => b.addEventListener('click', () => {{
    document.querySelectorAll('.orden button').forEach(x => x.setAttribute('aria-pressed', x === b));
    pintar(b.dataset.k);
  }}));
  pintar('no2');
</script>
</body>
</html>
'''

SALIDA.write_text(pagina, encoding='utf-8')
print(f'Página generada: {SALIDA.resolve()}')
for f in filas:
    print(f"{f['est']:<18} NO2 {f['no2']:>5} ({f['no2'] / GUIA_NO2:.1f}x)  O3 {f['o3']:>5} {f['meses']} "
          f"({f['o3'] / GUIA_O3:.1f}x)  NO {f['no']}")
