# Research: Pipeline ETL de COVID-19 (Bronze a Silver)

Todas las incógnitas de `Technical Context` quedan resueltas abajo. La especificación
(`spec.md`) y la Constitución (`.specify/memory/constitution.md`) ya fijan la mayoría de
las decisiones técnicas explícitamente (fórmula de hash, rutas de módulos, gates de
calidad); este documento formaliza las decisiones de herramientas concretas que la
especificación deja a nivel de "Assumptions" y resuelve los huecos de tooling que no
existen todavía en el repositorio (no hay `pyproject.toml`/`uv.lock`).

## 1. Gestor de proyecto y dependencias

- **Decision**: Bootstrapping del proyecto con `uv` (`uv init --package`), `pyproject.toml`
  como única fuente de dependencias, `uv.lock` versionado.
- **Rationale**: La Constitución (Principio III, "El Guantelete") invoca explícitamente
  `uv run mypy/ruff/pytest`; no existe hoy ningún `pyproject.toml` en el repo, así que la
  primera tarea de implementación debe crear el proyecto `uv` antes de escribir código de
  `src/covid_analytics/`.
- **Alternatives considered**: `pip` + `requirements.txt` (rechazado: la Constitución ya
  fija `uv` como el runner de los gates, no es una decisión abierta); `poetry` (rechazado
  por la misma razón).

## 2. Lectura de Excel (capa Bronze)

- **Decision**: `pandas.read_excel(..., engine="openpyxl")` con `usecols` explícito por
  hoja y detección de fila de encabezado por búsqueda de texto (no `skiprows` fijo),
  combinado con `nrows` acotado tras localizar la última fila con datos reales (columna
  clave no nula) para evitar materializar el rango fantasma de hasta 1,048,576 filas
  documentado en `docs/audit_legacy.md`.
- **Rationale**: `docs/audit_legacy.md` confirma que una lectura ingenua agota >50 GB de
  RAM por el rango usado inflado de Excel en 2 de las 3 hojas. `openpyxl` en modo
  `read_only=True` permite iterar fila por fila para detectar dónde termina el bloque de
  datos reales antes de pasarle `nrows` a `pandas.read_excel`.
- **Alternatives considered**: `pyexcel`/`xlrd` (rechazados: el archivo es `.xlsx`,
  `xlrd` ya no soporta ese formato; `openpyxl` es la dependencia estándar de pandas para
  `.xlsx`). Leer todo sin acotar (rechazado: ya demostrado que agota memoria).

## 3. Parseo de fechas polimórfico

- **Decision**: Función `parse_fecha_polimorfica(valor) -> datetime | pd.NaT` que:
  1. Si `valor` ya es `datetime`/`pd.Timestamp`, se devuelve tal cual.
  2. Si es `int`/`float` (serial de Excel), se convierte con el origen estándar de Excel
     `pd.Timestamp("1899-12-30") + pd.to_timedelta(valor, unit="D")`.
  3. Si es `str`, se extrae el primer patrón `DD/MM/YYYY` o `YYYY-MM-DD` vía regex antes de
     pasarlo a `pandas.to_datetime(..., dayfirst=True, errors="coerce")`, para tolerar
     sufijos de texto libre como `'24/03/2020  H. ZUMPANGO'`.
  4. Cualquier otro caso (texto puramente categórico como `"PENDIENTE"`) retorna `pd.NaT`.
- **Rationale**: Cubre los 3 formatos documentados en la auditoría (datetime nativo,
  string con ruido, serial de Excel) sin traer una dependencia extra (`dateutil` ya viene
  con pandas como dependencia transitiva, se usa indirectamente vía `to_datetime`).
- **Alternatives considered**: `dateutil.parser.parse` directo sobre el string completo
  (rechazado: falla o interpreta mal cuando hay texto adicional como el nombre del
  hospital pegado a la fecha; requiere el paso de extracción regex de todas formas).

## 4. Formato y engine de Parquet

- **Decision**: `pyarrow` como engine de escritura/lectura de Parquet
  (`df.to_parquet(path, engine="pyarrow", compression="snappy")`).
- **Rationale**: FR de Persistencia exige compresión Snappy explícita; `pyarrow` es el
  engine con mejor soporte de tipos lógicos de pandas (incluye metadata de esquema) y es
  el default recomendado por el propio proyecto pandas.
- **Alternatives considered**: `fastparquet` (mencionado como alternativa en
  `spec.md#Assumptions`; rechazado como elección primaria porque `pyarrow` preserva mejor
  los tipos nullable de pandas 2.x usados para `edad: float64` con nulos).

## 5. Contratos de datos (Bronze/Silver) y tipado estricto

- **Decision**: Modelos `pydantic.BaseModel` (`CasoBronze`, `CasoUnificadoSilver`,
  `ResumenCalidad`) como frontera de validación entre capas; las funciones de
  ingestión/limpieza reciben/devuelven listas de estos modelos (o `DataFrame` con
  conversión explícita `df.to_dict("records")` → lista de modelos) en los límites públicos
  de cada módulo, para que `mypy --strict` tenga tipos concretos en las firmas públicas en
  lugar de `DataFrame` sin tipar en las fronteras entre capas.
- **Rationale**: `mypy --strict` sobre `pandas.DataFrame` puro es notoriamente débil
  (columnas no tipadas); anclar los contratos de entrada/salida de cada módulo a modelos
  Pydantic explícitos permite cumplir el Principio III sin perder la ergonomía de pandas
  para el procesamiento interno vectorizado.
- **Alternatives considered**: Tipar únicamente con `pandas-stubs` sin capa Pydantic
  (rechazado: no captura las reglas de validación de dominio como rangos de edad o
  catálogos cerrados de `sexo`/`estatus`, que si son responsabilidad explícita del
  contrato según `spec.md#Key Entities`).

## 6. Sal de seudonimización (`COVID_PII_SALT`)

- **Decision**: Leer `COVID_PII_SALT` de entorno vía `os.environ.get`; si está ausente,
  usar un fallback constante documentado en código (no secreto real, solo para que el
  pipeline no se bloquee en desarrollo local) y emitir un `logging.warning` indicando que
  se está usando el fallback no seguro para producción.
- **Rationale**: Ya decidido en `spec.md#Assumptions`; este research solo fija el
  mecanismo (`os.environ.get` + warning) para que quede accionable como tarea.
- **Alternatives considered**: Fallar duro si la sal no está configurada (rechazado por el
  propio `spec.md`, que pide un fallback determinista documentado, no un error fatal).
