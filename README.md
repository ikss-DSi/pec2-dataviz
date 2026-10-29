# PEC 2 · Visualización de datos: calidad del aire en Barcelona

Tres visualizaciones interactivas sobre la calidad del aire en Barcelona, una por técnica asignada en la PEC 2 de la asignatura *Visualización de datos* (Máster universitario en Ciencia de datos, UOC, semestre 2026-1).

**Ver en línea:** https://ikss-dsi.github.io/pec2-dataviz/

| Técnica | Pregunta | Página | Código |
| --- | --- | --- | --- |
| Small multiples | ¿Cuánto NO₂ se respira al día en Barcelona? | [Multiple_small.html](https://ikss-dsi.github.io/pec2-dataviz/Multiple_small.html) | [Multiple_small.py](Multiple_small.py) |
| Icon chart | ¿Respira Barcelona el aire que recomienda la OMS? | [icon_chart.html](https://ikss-dsi.github.io/pec2-dataviz/icon_chart.html) | [icon_chart.py](icon_chart.py) |
| Violin plot | ¿Dónde hay más ozono en Barcelona? | [violin-plot.html](https://ikss-dsi.github.io/pec2-dataviz/violin-plot.html) | [violin-plot.py](violin-plot.py) |

## Datos

*Barcelona Virtual Sensor* (`bcn_virtual_sensor.parquet`), preparado por la UOC para la asignatura *Aprendizaje automático* (M2.891) a partir de datos abiertos del Ayuntamiento de Barcelona:

- [Calidad del aire, detalle](https://opendata-ajuntament.barcelona.cat/data/es/dataset/qualitat-aire-detall-bcn)
- [Estaciones de calidad del aire](https://opendata-ajuntament.barcelona.cat/data/es/dataset/qualitat-aire-estacions-bcn)
- [Estado del tráfico por tramos](https://opendata-ajuntament.barcelona.cat/data/es/dataset/trams)
- [Relación de tramos](https://opendata-ajuntament.barcelona.cat/data/dataset/transit-relacio-trams)

Contiene 138.063 registros horarios (2023-2026) de 7 estaciones de medición, con NO, NO₂, NOx y O₃ en µg/m³, un índice de congestión del tráfico en un radio de 1.250 m y variables de tiempo (hora, día, fin de semana, mes y año). Eixample solo tiene datos de 2023 y Navas solo de 2026; las visualizaciones lo señalan con un asterisco.

El archivo de datos no se incluye en el repositorio. Las páginas HTML son autónomas y ya llevan los datos agregados que necesitan.

## Técnicas

- **Small multiples:** perfil diario medio de NO₂ por hora en cada estación, día laborable frente a fin de semana, con la misma escala en todos los paneles y los promedios de las 7 estaciones como referencia. Botones para mostrar u ocultar series y deslizador de horario común.
- **Icon chart:** cada icono equivale al valor guía de la OMS (NO₂: 10 µg/m³ de media anual; O₃: 60 µg/m³ en temporada alta). El primero, en azul, es lo recomendado; los naranjas son exceso. El NO, sin guía de la OMS, se muestra en gris (1 icono = 5 µg/m³). Se puede reordenar por contaminante e incluye una tabla de datos accesible.
- **Violin plot:** distribución horaria de O₃ por estación, con las urbanas separadas de la suburbana. La densidad (kernel gaussiano) se recalcula en el navegador para el horario elegido, de modo que el bulto de ozono bajo nocturno aparece y desaparece.

## Cómo regenerar las páginas

```bash
pip install pandas pyarrow numpy plotly
# Copia bcn_virtual_sensor.parquet en esta carpeta (o en una superior)
python Multiple_small.py
python icon_chart.py
python violin-plot.py
```

Cada script guarda su página `.html` junto a él.

## Referencias

- Organización Mundial de la Salud (2021). *WHO global air quality guidelines*. https://www.who.int/publications/i/item/9789240034228
- Tufte, E. R. (1983). *The Visual Display of Quantitative Information*. Graphics Press.
- Neurath, O. (1936). *International Picture Language*. Kegan Paul.
- Hintze, J. L. y Nelson, R. D. (1998). Violin Plots: A Box Plot-Density Trace Synergism. *The American Statistician*, 52(2), 181-184.

## Autor

Iker Serrato · Visualización de datos, UOC.
=======
# pec2-dataviz
Práctica 2 de la matería Vizualización de datos
>>>>>>> 6aeb4180bbe951d6b92a28c37e8578bcd335b421
