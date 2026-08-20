# Auditoría técnica del legacy (código + Excel)

Generado a partir de una inspección estática de `data_analysis.py` / `read.py` y de un script
temporal (`_tmp_audit_excel.py`, borrado al finalizar) que leyó el Excel solo para extraer
metadatos estructurales. **No contiene nombres de pacientes ni otros datos personales** —
únicamente nombres de columnas, tipos de dato, % de nulos, valores categóricos agregados
(conteos) y formatos de fecha de ejemplo (sin persona asociada).

> Nota de seguridad: el archivo `RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx`
> contiene columnas con PII real (nombre del paciente, calle, teléfono, colonia). El script de
> inspección nunca imprimió esos valores; solo los nombres de columna y estadísticas agregadas.

---

## 1. Inspección del código legacy (`data_analysis.py`, `read.py`)

### Imports

```python
from matplotlib import colors
import numpy as np
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import re
import tkinter as tk
from tkinter import filedialog, Button, Label, Text, messagebox as MessageBox
import os
```
`read.py` solo usa `pandas`.

### Funciones

- `data_analysis.py` define una única función, **`main()`** (línea 28), que contiene *todo* el
  pipeline (lectura, limpieza, transformación y ~25 gráficas) en un solo bloque de ~1420 líneas.
  No hay funciones auxiliares, ni separación entre carga/limpieza/graficado.
- El código de GUI con `tkinter` (`Error()`, `GUI()`) está comentado/deshabilitado; la ruta del
  archivo Excel está hardcodeada en el `main()`.
- `read.py` es un script exploratorio suelto (sin función), que solo hace `read_excel` +
  `.describe()`; no se usa en el flujo principal.
- Punto de entrada: `main()` se invoca directamente en la última línea del archivo (fuera de un
  bloque `if __name__ == "__main__":`).

### Lectura de datos

- Solo se lee **una hoja**: `"SEGUIMIENTO DE CASOS COVID 19"`, vía
  `pd.read_excel(archive, "SEGUIMIENTO DE CASOS COVID 19", usecols="A:T", skiprows=range(0,13))`.
- **Hallazgo relevante**: `skiprows=range(0,13)` salta las filas índice 0–12, lo que descarta la
  fila 12 (índice base 0) que contiene los **encabezados reales** (`NO. (consecutivo)`, `CASO...`,
  `SEXO...`, etc.). La fila que pandas termina usando como encabezado es la fila 13, que está casi
  vacía (solo tiene el valor `"Extradomiciliarios"` en la columna 17). Como consecuencia:
  - Los nombres de columna del DataFrame resultante son básicamente basura/posicionales.
  - El código **nunca usa los nombres de columna reales**: todo el acceso es posicional vía
    `df2.iloc[:, N]` (líneas 42–51), lo cual hace que el pipeline funcione "por accidente" a pesar
    del header roto, pero también lo vuelve **extremadamente frágil ante cualquier inserción o
    reordenamiento de columnas en el Excel** (un cambio de layout rompe silenciosamente el mapeo).
- Ni `NOMINAL DE HOSPITALIZADOS` ni `RED NEGATIVA` se leen en ningún punto del código actual.
- `Verificar.xlsx` se genera como salida de verificación (`DFCasos.to_excel('Verificar.xlsx')`,
  línea 160) — es un artefacto de depuración, no una fuente de datos.

### Columnas construidas (`DFCasos`, por posición de columna del Excel origen)

| Columna DFCasos | Origen (iloc) |
|---|---|
| Sexo | col 2 |
| Edad | col 3 |
| Residencia | col 4 |
| Derechohabiencia | col 7 |
| Fecha Notif | col 8 |
| Toma de muestra | col 10 |
| Resultado | col 12 |
| Fecha Result | col 13 |
| Estatus | col 14 |
| Pais Procedente | col 15 |

### Filtros y transformaciones (líneas 53–157)

Todas las columnas se limpian con `fillna` + cadenas de `replace(regex=[...])` (normalización por
coincidencia de prefijo/substring, sin catálogo canónico centralizado):

- **Pais Procedente**: null → `MÉXICO`; cualquier variante `MEX*`/`MÉX*` → `MÉXICO`.
- **Estatus**: colapsa decenas de variantes de texto libre a 3 categorías
  (`AMBULATORIO`, `DEFUNCION`, `HOSPITALIZADO`) vía prefijos regex.
- **Residencia**: ~35 reglas regex hardcodeadas mapean texto libre (con errores de captura,
  abreviaturas, acentos) a nombres de municipio/alcaldía normalizados (p. ej. `GAM`→
  `GUSTAVO A. MADERO`, `IZTAP*`→`IZTAPALAPA`). Muy propenso a falsos positivos por patrones
  amplios tipo `r'(^.*TLA.*$)'`.
- **Derechohabiencia**: solo `fillna('NINGUNO')`, sin normalización de variantes.
- **Toma de muestra**: null → `PENDIENTE`; luego colapsa a `PENDIENTE` / `NO SE TOMÓ`.
- **Resultado**: null → `SOSPECHOSO`; normaliza a `POSITIVO` / `NEGATIVO` / `SOSPECHOSO`; incluye
  un `np.where` final que fuerza cualquier valor no reconocido a `SOSPECHOSO`.
- **Fecha Result**: mezcla de reglas para texto (`PENDIENTE`, `NO SE TOMÓ`) y fechas; hay un
  intercambio explícito (línea 128–129) entre `Resultado` y `Fecha Result` cuando el valor de
  `Resultado` parece texto en vez de fecha (indicio de que en el Excel origen esas dos columnas a
  veces vienen invertidas).
- **Edad**: null → `-1`; normaliza edades en días/meses (`RN`, `D`, `ME`, etc.) a `0`;
  conversión final a numérico con `pd.to_numeric`.
- **Sexo**: normalización en dos pasadas (incluye un intercambio Sexo↔Edad, líneas 146–147, para
  el caso en que el valor de edad terminó en la columna de sexo o viceversa); colapsa a
  `F` / `M` / `OTRO`.

### Filtros derivados usados para graficar (repetidos ~15 veces con la misma forma)

Máscaras booleanas por combinación de `Resultado` × `Sexo`, `Estatus` × `Resultado`,
`Estatus` × `Sexo`, y rangos de `Edad` (0–1, 2–11, 12–17, 18–29, 30–39, 40–49, 50–59, 60–69, 70+,
sin dato) cruzados con `Resultado` y `Estatus`. El patrón se repite manualmente decenas de veces
en vez de usar `groupby`/`crosstab`, generando ~1300 líneas de código muy repetitivo (líneas
160–1450) que producen ~20 gráficas de barras guardadas en `img/`.

### Observaciones de calidad de código (no pedidas explícitamente, pero relevantes para una migración)

- Cero manejo de errores: si `Aux0[1]` no existe (categoría con 0 casos), el script revienta
  (ya hay parches manuales para ese caso puntual en líneas 449–450 y 511–513, pero no en todos
  los `Aux*[1]`).
- Sin tests, sin logging, sin separación de responsabilidades (lectura/limpieza/graficado todo en
  una función).
- La paleta de colores (`Colores`, línea 170) se reutiliza por índice fijo entre gráficas con
  distinto número de categorías, lo que puede desalinear colores/leyendas si cambia el conteo de
  categorías.

---

## 2. Inspección del Excel (`RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx`)

El libro tiene 5 hojas: `RED NEGATIVA`, `Gráfico1` (solo gráfico), `SEGUIMIENTO DE CASOS COVID 19`,
` NOMINAL DE HOSPITALIZADOS` (nota: nombre con espacio inicial), `Hoja1` (vacía). Las 3 hojas con
datos tabulares son las auditadas abajo.

> **Aviso técnico**: `SEGUIMIENTO DE CASOS COVID 19` y ` NOMINAL DE HOSPITALIZADOS` reportan un
> "rango usado" inflado por formato de Excel (hasta 1,048,576 filas × 16,382 columnas). Una
> lectura ingenua con `pandas.read_excel` sin `usecols`/`nrows` intenta materializar ese rango
> fantasma y agota la memoria (se observó un proceso `python.exe` creciendo a >50 GB de RAM antes
> de ser terminado). Cualquier script futuro que lea este archivo debe fijar explícitamente
> `usecols` y `nrows`/límite de filas, o usar `openpyxl` en modo `read_only` iterando manualmente.

Los encabezados reales de estas hojas están repartidos en 2–3 filas con celdas combinadas; para
esta auditoría se reconstruyeron concatenando las filas de encabezado con `|`. Por eso algunos
nombres de columna abajo se ven largos o con sufijos `(2)`/`(3)` — son artefactos de esa
reconstrucción, no nombres reales de una sola celda.

### Hoja: `RED NEGATIVA` (resumen agregado por hospital/día, no por paciente)

- 295 filas de datos, 14 columnas.

| # | Columna | Tipo pandas | % Nulos |
|---|---------|-------------|---------|
| 0 | *(columna A en blanco)* | float64 | 100.0% |
| 1 | FECHA 1 | str | 2.4% |
| 2 | HOSPITAL | str | 0.3% |
| 3 | INSTITUCIÓN | str | 2.4% |
| 4 | NUEVOS CASOS 2 | object | 2.4% |
| 5 | CASOS ACUMULADOS 3 | float64 | 2.4% |
| 6 | TOTAL CASOS 4 | float64 | 2.4% |
| 7 | ESTATUS 5 \| HOSPITALIZADOS | float64 | 4.1% |
| 8 | ESTATUS 5 \| AMBULATORIOS | float64 | 4.1% |
| 9 | BROTES 6 | str | 2.4% |
| 10 | POSITIVOS | float64 | 22.7% |
| 11 | NEGATIVOS | float64 | 22.7% |
| 12 | TOTAL DE PRUEBAS REALIZADAS | float64 | 22.7% |
| 13 | OBSERVACIONES | str | 97.6% |

- **Categóricas clave**: la única columna cuyo nombre coincide con `estatus` (`ESTATUS 5`) es en
  realidad un **conteo numérico** (hospitalizados/ambulatorios por fila), no una etiqueta de texto
  — se omite el top-10 por no ser categórica. Esta hoja no tiene columnas `derechohabiencia` ni
  `resultado` por registro (es un resumen agregado, no un listado nominal).
- **Fechas**: no se detectaron columnas de tipo fecha real; `FECHA 1` llegó como texto libre
  (formato dd.mm.aaaa, ej. `30.03.2020`) mezclado con algunos valores no parseables.

### Hoja: `SEGUIMIENTO DE CASOS COVID 19` (la que consume `data_analysis.py`)

- 5,986 filas de datos, 20 columnas (rango `A:T`, igual que usa el código legacy).

| # | Columna (reconstruida) | Tipo pandas | % Nulos |
|---|---------|-------------|---------|
| 0 | NO. (consecutivo) | int64 | 0.0% |
| 1 | CASO (nombre, apellido paterno, apellido materno) *(PII — no auditado en contenido)* | str | 0.0% |
| 2 | SEXO (M/F) | object | 0.1% |
| 3 | EDAD (ej: años: 3; meses-3M) | object | 0.4% |
| 4 | MUNICIPIO/PAÍS RESIDENCIA | str | 0.1% |
| 5 | UNIDAD NOTIFICANTE | str | 0.0% |
| 6 | JURISDICCIÓN | str | 0.0% |
| 7 | DERECHOHABIENCIA (IMSS, ISSSTE, ISSEMYM, SEDENA, NINGUNO) | str | 0.0% |
| 8 | FECHA DE NOTIFICACIÓN (dd/mm/aaaa) | datetime | 0.0% |
| 9 | SIGNOS Y SINTOMAS (SI/NO) | str | 0.1% |
| 10 | FECHA TOMA DE MUESTRA (dd/mm/aaaa) | datetime | 0.0% |
| 11 | LABORATORIO | str | 0.0% |
| 12 | RESULTADO (POSITIVO, NEGATIVO, PENDIENTE) | object | 0.0% |
| 13 | FECHA DE RESULTADO (dd/mm/aaaa) | datetime | 0.1% |
| 14 | ESTATUS | str | 0.0% |
| 15 | PAIS DE PROCEDENCIA | str | 0.0% |
| 16 | No. DE CONTACTOS | object | 0.1% |
| 17 | No. DE CONTACTOS (subcolumna "Extradomiciliarios") | object | 0.1% |
| 18–19 | OBSERVACIONES (texto libre; incluye a veces folio de captura) | object | 6.6–6.9% |

**Top-10 valores categóricos:**

- **DERECHOHABIENCIA**: `NINGUNO` — 5,985 (prácticamente el 100%; columna sin variación real,
  probablemente sin capturar en la práctica pese a existir en el formulario).
- **RESULTADO**: `NEGATIVO` 3,740 · `POSITIVO` 1,713 · `PENDIENTE` 243 · `RECHAZO` 105 ·
  `POSITIVA` 38 · `INDETERMINADO` 27 · `NO SE TOMO` 22 · **`2020-09-03 00:00:00`** 16 ·
  `NO SE TOMÓ` 15 · `RECHAZADA` 10.
  ⚠️ Nótese el valor `2020-09-03 00:00:00` entre los 10 más frecuentes: hay filas donde una fecha
  quedó capturada en la columna `RESULTADO` (consistente con el intercambio Resultado↔Fecha
  Result que el código legacy intenta corregir en tiempo de ejecución, líneas 128–132).
- **ESTATUS**: `AMBULATORIO` 4,710 · `ALTA` 176 · `DEFUNCION` 159 · `DEFUNCIÓN` 155 (nótese
  duplicado por acento) · `AMBULATORIO PEDIATRIA` 127 · `HOSPITALIZADO` 121 ·
  `AMBULATORIO GYO` 81 · `ALTA POR MEJORIA` 78 · `AMBULATORIO/` 47 · `AMBULATORIO G Y O` 46.

**Formatos de fecha (3 ejemplos, sin persona asociada):**

- `FECHA DE NOTIFICACIÓN`: `2020-03-18 00:00:00`, `2020-03-24 00:00:00`, `2020-03-25 00:00:00`
- `FECHA TOMA DE MUESTRA`: `2020-03-18 00:00:00`, `2020-03-24 00:00:00`, `2020-03-24 00:00:00`
- `FECHA DE RESULTADO`: `2020-03-20 00:00:00`, `2020-03-26 00:00:00`, `2020-03-26 00:00:00`

### Hoja: ` NOMINAL DE HOSPITALIZADOS`

- 5,992 filas de datos, 40 columnas (encabezado a 3 niveles: HOSPITAL/DATOS GENERALES/SERVICIO/
  LABORATORIO/FECHA Y ALTA POR/OBSERVACIONES/etc.). Contiene columnas de dirección y teléfono
  (PII) que **no se listan con contenido**, solo se reportan como nombre de columna + % nulos.

| # | Columna (reconstruida) | Tipo pandas | % Nulos |
|---|---------|-------------|---------|
| 0 | *(columna A en blanco)* | object | 99.9% |
| 1 | HOSPITAL | str | 0.0% |
| 2 | NO. | object | 0.0% |
| 3 | NOMBRE DEL PACIENTE *(PII — no auditado en contenido)* | str | 0.0% |
| 4 | EDAD \| F | object | 43.9% |
| 5 | EDAD \| M | object | 56.3% |
| 6–13 | DATOS GENERALES (CALLE, NO. EXT., NO. INT., COLONIA, LOCALIDAD, MUNICIPIO, C.P., TELÉFONO) *(PII — no auditado en contenido)* | object/str | 0.2%–5.4% |
| 14 | FECHA DE INICIO DE SÍNTOMAS | datetime | 0.0% |
| 15 | FECHA DE INGRESO O DE ATENCIÓN | datetime | 0.0% |
| 16 | FECHA DE INICIO TRATAMIENTO | datetime | 0.0% |
| 17–22 | SERVICIO (URGENCIAS/PISO AISLADOS/TERAPIA INTENSIVA × CON/SIN APOYO VENTILATORIO) | object/str | 5.7% |
| 23 | REPORTE DEL EDO. DE SALUD | object | 0.0% |
| 24 | DIAGNÓSTICO | str | 0.0% |
| 25 | TOMA DE MUESTRA FECHA | datetime | 0.1% |
| 26 | RESULTADO (laboratorio) | str | 0.0% |
| 27 | FECHA DE RESULTADO | datetime | 2.1% |
| 28–31 | FECHA Y ALTA POR (MEJORÍA/VOLUNTARIA/REFERENCIA/DEFUNCIÓN) | object/datetime | 94.5%–99.9% |
| 32–33 | OBSERVACIONES | str/datetime | 0.0%–100.0% |
| 34 | OCUPACIÓN PERSONAL DE SALUD | str | 86.6% |
| 35 | TIPO DE PACIENTE | str | 0.1% |
| 36 | RESULTADO (segunda columna, cerca de "DEFUNCIÓN") | str | 0.2% |
| 37–39 | CONSECUTIVO AMBULATORIO (3 sub-columnas, mayormente vacías) | object/float64 | 71.0%–100.0% |

**Top-10 valores categóricos — RESULTADO (laboratorio):**
`NEGATIVO` 3,693 · `POSITIVO` 1,698 · `PENDIENTE` 225 · `INDETERMINADO` 146 · `RECHAZADA` 125 ·
`NO SE TOMÓ` 38 · `POSITIVA` 24 · `NO SE TOMO` 7 · `PEDIENTE` 5 · `NEGATIVO - POSITIVO` 4.

No se encontraron columnas `derechohabiencia` ni `estatus` (estilo Seguimiento) en esta hoja.

**Formatos de fecha (ejemplos, sin persona asociada):**

- `FECHA DE INICIO DE SÍNTOMAS`: `2020-03-15 00:00:00`, `2020-03-22 00:00:00`, `2020-03-12 00:00:00`
- `FECHA DE INGRESO O DE ATENCIÓN`: `2020-03-18 00:00:00`, `2020-03-24 00:00:00`, `2020-03-24 00:00:00`
- `TOMA DE MUESTRA FECHA`: `2020-03-18 00:00:00`, `2020-03-24 00:00:00`, `2020-03-24 00:00:00`
- `FECHA DE RESULTADO`: `2020-03-20 00:00:00`, `2020-03-26 00:00:00`, `2020-03-26 00:00:00`
- Nótese que al menos un valor de fecha vino como **texto libre mezclado con otro dato**:
  `'24/03/2020  H. ZUMPANGO'` en la columna de referencia/unidad — otro indicio de captura poco
  estructurada, consistente con lo visto en la hoja de Seguimiento.

### 3. Verificación de la columna `folio`

- **`SEGUIMIENTO DE CASOS COVID 19`**: no existe una columna dedicada llamada `folio`. Existe una
  columna de `OBSERVACIONES` de texto libre donde, en el **0.3%** de las filas, aparece un patrón
  tipo `"FOLIO: COVID19-XXXX"` incrustado dentro de comentarios más largos.
- **` NOMINAL DE HOSPITALIZADOS`**: tampoco existe una columna dedicada `folio` ni un campo
  equivalente (consecutivo, id de caso, etc.) que sirva de llave clara hacia la otra hoja.
- **Conclusión**: no es posible calcular un porcentaje de coincidencia exacta de `folio` entre
  ambas hojas porque **ninguna tiene una columna estructurada para ese identificador**. El único
  candidato es el patrón de texto libre embebido en `OBSERVACIONES` de Seguimiento, presente en
  menos del 1% de los registros — insuficiente para usarlo como llave de unión confiable. Cualquier
  vinculación Seguimiento↔Nominal tendría que hacerse por combinación aproximada de otros campos
  (nombre, fecha, hospital), lo cual está fuera del alcance de esta auditoría por implicar PII.

---

## 4. Resumen de riesgos para una eventual migración/reescritura

1. El pipeline de `data_analysis.py` depende de **acceso posicional** (`iloc`) sobre una hoja cuyo
   header real es descartado por un `skiprows` que parece un bug — cualquier cambio de columnas en
   el Excel origen rompe el mapeo sin avisar.
2. La limpieza de categorías (`Residencia`, `Estatus`, `Resultado`, `Sexo`, `Edad`) se basa en
   decenas de reglas regex ad-hoc con patrones muy amplios (`.*X.*`), sin catálogo canónico ni
   tests — alto riesgo de falsos positivos/negativos silenciosos.
3. Los datos fuente tienen errores de captura conocidos y ya "vistos" por el propio código legado
   (fechas en columnas de resultado, sexo/edad intercambiados, acentos inconsistentes en
   categorías como `DEFUNCION`/`DEFUNCIÓN`).
4. No existe una llave `folio` estructurada para vincular `SEGUIMIENTO DE CASOS COVID 19` con
   ` NOMINAL DE HOSPITALIZADOS`; una futura integración de ambas fuentes requiere definir un nuevo
   mecanismo de vinculación (o solicitar que se capture un folio real en ambos formularios).
5. El archivo Excel reporta rangos de celdas usados artificialmente enormes en 2 de sus 3 hojas de
   datos — cualquier herramienta de lectura debe acotar explícitamente filas/columnas para evitar
   fallas de memoria.
