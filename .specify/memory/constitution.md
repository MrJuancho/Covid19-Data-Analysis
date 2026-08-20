<!--
Sync Impact Report
- Version change: [TEMPLATE UNFILLED] → 1.0.0 (initial ratification)
- Modified principles: n/a (first concrete adoption from scaffold)
- Added sections:
  - I. Privacidad y Anonimización (PII First)
  - II. Arquitectura de Datos por Capas (Medallion Architecture)
  - III. Calidad de Código y Gates Obligatorios ("El Guantelete")
  - IV. Desarrollo Dirigido por Especificaciones (SDD Estricto)
  - Governance (amendment procedure, versioning policy, compliance review)
- Removed sections: [SECTION_2_NAME] / [SECTION_3_NAME] scaffold slots (no
  additional constraints beyond the four principles were supplied; omitted
  rather than filled with placeholder content)
- Templates requiring follow-up: none checked in this run — re-validate
  .specify/templates/plan-template.md, spec-template.md, and tasks-template.md
  against the Guantelete gates (mypy --strict, ruff, pytest --cov-fail-under=90)
  the next time those commands run.
- Deferred TODOs: RATIFICATION_DATE assumed as today (first formal adoption);
  confirm with project owner if an earlier informal ratification date applies.
-->

# COVID-19 Analytics (Hospital Gustavo Baz) Constitution

## Core Principles

### I. Privacidad y Anonimización (PII First)
- **Cero PII en capas Silver y Gold:** Ningún nombre completo, número de
  teléfono, dirección específica o CURP DEBE almacenarse en texto plano en
  las capas Silver o Gold del pipeline.
- **Seudonimización determinista:** Todo identificador de paciente DEBE
  generarse como un hash `SHA-256(Nombre_Normalizado + Folio + Sal)` durante
  la ingesta en la capa Bronze, antes de cualquier escritura a disco fuera de
  esa capa.
- **Aislamiento de artefactos:** Los logs de depuración, outputs de pruebas y
  datasets exportados NO DEBEN imprimir datos sensibles en consola ni en
  reportes intermedios. Cualquier fixture o ejemplo usado en documentación o
  pruebas DEBE ser sintético.
- **Rationale:** El dataset fuente contiene PII hospitalaria real (COVID-19,
  Hospital Gustavo Baz); una fuga de PII es el riesgo de mayor severidad del
  proyecto y no es negociable frente a conveniencia de desarrollo.

### II. Arquitectura de Datos por Capas (Medallion Architecture)
- **Bronze (`src/covid_analytics/ingestion/`):** Ingesta cruda de las 3 hojas
  del Excel, preservando los tipos originales sin mutar valores de origen;
  aquí ocurre la seudonimización de PII (Principio I).
- **Silver (`src/covid_analytics/cleaning/`):** Desanidado, normalización
  semántica, imputación controlada y cruces de entidades (merge por
  identificador seudonimizado). Tablas intermedias en memoria o Parquet.
- **Gold (`src/covid_analytics/analytics/`):** Agregaciones analíticas,
  series temporales y datasets estructurados para visualización y heatmaps,
  en formato columnar `.parquet`.
- **Rationale:** Separar responsabilidades por capa hace auditable el punto
  exacto donde el PII deja de existir en texto plano y evita que lógica de
  limpieza y lógica analítica se mezclen en el mismo módulo.

### III. Calidad de Código y Gates Obligatorios ("El Guantelete")
Ningún cambio se considera completado si no pasa el Guantelete en verde:
1. **Tipado estricto:** `uv run mypy --strict src` DEBE pasar sin errores
   (cero tolerancia a `Any` implícito).
2. **Linter y formato:** `uv run ruff check src tests` y
   `uv run ruff format --check src tests` DEBEN pasar sin hallazgos.
3. **Pruebas automatizadas y cobertura:** `uv run pytest --cov=src
   --cov-fail-under=90` DEBE pasar con al menos 90% de cobertura.
4. **Pruebas con datos sintéticos:** Las pruebas unitarias NO DEBEN depender
   del Excel real con PII; DEBEN usar fixtures sintéticos que cubran casos
   límite (fechas corruptas, caracteres especiales, valores nulos).
- **Rationale:** Un dataset de salud real exige que la validación técnica sea
  mecánica y repetible, no discrecional; los cuatro gates son el criterio
  objetivo de "terminado".

### IV. Desarrollo Dirigido por Especificaciones (SDD Estricto)
- **No hay código sin especificación previa:** Toda nueva funcionalidad
  DEBE tener `spec.md`, `plan.md` y `tasks.md` antes de implementarse.
- **TDD estricto:** Claude Code DEBE escribir primero las pruebas unitarias
  que fallen, antes de implementar la lógica de negocio correspondiente.
- **Auditoría dual:** Gemini DEBE validar que la arquitectura y los
  contratos de datos cumplan esta Constitución antes de la fusión a `main`.
- **Rationale:** Con dos agentes (Claude Code implementando, Gemini
  auditando) el flujo Spec-Driven Development es lo que mantiene a ambos
  agentes alineados sobre el mismo contrato en lugar de decisiones ad-hoc.

## Governance

- **Autoridad:** Esta Constitución tiene precedencia sobre cualquier otra
  guía de estilo, plantilla o preferencia individual dentro de este
  repositorio, incluyendo `GEMINI.md` y los skills en `.claude/skills/`.
- **Procedimiento de enmienda:** Cualquier cambio a esta Constitución DEBE
  proponerse mediante `/speckit-constitution`, documentarse en el Sync
  Impact Report al inicio de este archivo, y ser auditado por Gemini
  (Principio IV) antes de fusionarse a `main`.
- **Política de versionado (SemVer):**
  - **MAJOR:** eliminación o redefinición incompatible de un principio.
  - **MINOR:** adición de un principio o expansión material de una guía
    existente.
  - **PATCH:** aclaraciones, correcciones de redacción o refinamientos no
    semánticos.
- **Revisión de cumplimiento:** Todo PR DEBE pasar "El Guantelete"
  (Principio III) y la Auditoría Dual (Principio IV) antes de fusionarse.
  Cualquier complejidad que se desvíe de la Arquitectura por Capas
  (Principio II) DEBE justificarse explícitamente en el `plan.md` de la
  feature correspondiente.

**Version**: 1.0.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-19
