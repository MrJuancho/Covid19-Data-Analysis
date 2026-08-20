# Contrato de Datos (Enmienda Aditiva): `data/gold/metricas_demografia.parquet`

Enmienda aditiva al contrato original `specs/002-covid-gold/contracts/metricas_demografia_gold.md`
(FR-005a de `specs/003-dashboard-epidemiologico/spec.md`). El contrato original no se reescribe
aquí — solo se documenta la columna nueva y el cambio de grano de agregación. Cualquier
consumidor que ya tolere columnas adicionales no documentadas (norma de compatibilidad aditiva de
001-covid-etl) sigue funcionando sin cambios.

## Columna añadida

| Columna | Tipo lógico | Nulable | Restricción / Contrato |
|---|---|---|---|
| `grupo_edad_ui` | `string` | No | Uno de `<18`, `18-39`, `40-59`, `60+`, `SIN_DATO`. Calculado directamente desde `edad` (Silver) con cortes exactos `[0,18)`, `[18,40)`, `[40,60)`, `[60,∞)`; el sentinel `SIN_DATO` aplica bajo las mismas condiciones que en `grupo_edad` (`edad < 0` o nula) |

## Cambio de grano de agregación

- **Antes (002-covid-gold)**: `(grupo_edad, sexo, resultado_prueba, estatus_paciente)`.
- **Ahora (003-dashboard-epidemiologico)**: `(grupo_edad, grupo_edad_ui, sexo, resultado_prueba, estatus_paciente)`.

Esto **aumenta el número de filas** de la tabla (cada combinación válida de `grupo_edad` ×
`grupo_edad_ui` que exista en los datos se vuelve una fila independiente), pero preserva el
contrato de columnas original íntegramente — ningún consumidor de 002-covid-gold que dependa
solo de `(grupo_edad, sexo, resultado_prueba, estatus_paciente)` se rompe, siempre que agregue
(`sum`) sobre `grupo_edad_ui` si necesita el grano original.

## Regla de Integridad Añadida

- `grupo_edad = "SIN_DATO"` ⟺ `grupo_edad_ui = "SIN_DATO"` en toda fila (mismo sentinel de origen).
- Ninguna fila combina un `grupo_edad` y un `grupo_edad_ui` cuyos rangos numéricos no se
  intersecten (ej. `grupo_edad="0-1"` nunca aparece con `grupo_edad_ui="60+"`).
- La suma de `total_casos` agregada únicamente por `grupo_edad_ui` (colapsando `grupo_edad`) DEBE
  seguir sumando el total de filas de Silver (FR-007 de 002-covid-gold, ahora verificado también
  para esta dimensión).
