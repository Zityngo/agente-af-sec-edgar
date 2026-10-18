# A.Fundamental A — Primera auditoría de empresas reales
**Fecha de ejecución: 2026-10-18 (UTC)** · **Estado: ensayo interno, NO análisis totalmente certificado**

## Resultado reproducible

Ejecución CI: https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/39119957783

Repositorio: rama `agent/chatgpt-a`. Fuente primaria: SEC EDGAR (Companyfacts, Submissions y 10-K). Fuente complementaria: EODHD v1.1 con clave pública `demo`, exclusivamente para contraste no comercial.

- Pruebas automáticas Python: **39 aprobadas** (38 anteriores más la regla de EBIT Q4).
- SEC contra Form 10-K FY2025: **18 de 18 coincidencias**, seis campos por empresa: ventas, EBIT, resultado neto, CFO, CapEx bruto y EPS diluido.
- EODHD demo frente a cifras SEC del mismo FY: **15 de 15 campos disponibles coinciden**. El campo BPA anual no figura en la sección Income Statement de EODHD, por lo que quedan **3 como no disponibles**.
- Tres empresas descargadas/ingestadas en SQLite `af_core`; ningún error de descarga.
- **NO** se han certificado al completo: siguen pendientes resultados trimestrales, segmentos, notas, directiva/insiders, reexpresiones y comparables de valoración.

## Datos reales FY2025 (millones USD salvo BPA)

| Dato | Apple (2025-09-27) | Tesla (2025-12-31) | Amazon (2025-12-31) |
|:--|--:|--:|--:|
| Ventas | 416.161 | 94.827 | 716.924 |
| EBIT reportado | 133.050 | 4.355 | 79.975 |
| Beneficio atribuible / conciliado | 112.010* | 3.794 | 77.670* |
| Flujo operativo CFO | 111.482 | 14.747 | 139.514 |
| Compras brutas de inmovilizado | 12.715 | 8.527 | 131.819 |
| **FCF bruto** (CFO − CapEx bruto) | **98.767** | **6.220** | **7.695** |
| BPA diluido | 7,46 USD | 1,08 USD | 7,17 USD |
| ROIC calculado por motor | 83,1% PROXY | 4,7% PROXY | 19,5% PROXY |

*En Apple y Amazon el extractor SEC usa `NetIncomeLoss`: coincide con el 10-K, pero el motor conserva estado **PROXY** por la distinción entre resultado de matriz y beneficio disponible a ordinarios.

**Diferencia crítica Amazon:** FCF divulgado por la compañía **11.194 MUSD**, obtenido con CapEx neto de ventas e incentivos de **128.320 MUSD**. El FCF básico de nuestra fórmula con compras brutas es **7.695 MUSD**. **No intercambiarlos** al calcular valoración.

**Diferencia crítica Tesla:** beneficio consolidado 3.855 MUSD; beneficio atribuible a acciones ordinarias **3.794 MUSD**. La diferencia es **61 MUSD**, por intereses no controladores. Para PER, usar un BPA o resultado atribuible comparable.

### TTM aproximado basado en cuatro trimestres de SEC (no equivale a FY2025)

| Indicador | Apple | Tesla | Amazon |
|---|---:|---:|---:|
| Ventas TTM, MUSD | 466.823 | 103.619 | 775.680 |
| EBIT TTM, MUSD | 154.859 PROXY | 4.372 PROXY | 93.712 PROXY |
| FCF TTM (CapEx bruto), MUSD | 136.683 PROXY | 5.762 PROXY | −11.625 PROXY |
| BPA TTM | **NULL** | **NULL** | **NULL** |

El EBIT Q4 se reconstruye como **FY − nueve primeros meses** y se etiqueta `PROXY` con accession de ambos formularios. El FCF TTM combina CapEx trimestral derivado de acumulados, por lo que también se etiqueta `PROXY`. **No inferimos BPA Q4 restando BPA FY menos nueve meses**: las acciones medias ponderadas pueden variar. Los flujos TTM reflejan inversiones recientes y requieren conciliación con notas contables.

## Primera lectura fundamental (hipótesis de trabajo)

**Apple (AAPL):** altos márgenes operativos, generador de caja y poder de marca; efectos de ecosistema/costes de sustitución a verificar con retención, crecimiento y mix de Servicios. Un ROIC proxy del 83,1% puede resultar distorsionado por recompras que reducen patrimonio contable; **no interpretarlo como ventaja demostrada**. Riesgos prioritarios: concentración del iPhone, China/cadena de suministro, regulación y exigencia de valoración.

**Tesla (TSLA):** ventas 2025 inferiores a 2024 y EBIT claramente menor que las mega-cap tecnológicas; generación positiva de CFO/FCF en FY2025, pero el CapEx de autonomía, energía y computación cambia los escenarios. Hipótesis MOAT de marca/red de carga/escala aún no acreditadas cuantitativamente. Riesgos: competencia y precios de vehículos, ejecución de iniciativas de IA, asignación de capital y volatilidad de demanda.

**Amazon (AMZN):** crecimiento FY, EBIT consolidado cerca de 80.000 MUSD y relevancia de AWS; la gran expansión del gasto en infraestructura reduce el FCF, que depende mucho de **cómo se defina CapEx**. MOAT hipotético de escala logística y costes de sustitución en AWS, sujeto a contrastar crecimiento, retorno de inversión y márgenes por segmentos. Riesgos: inversión sostenida, competencia cloud, logística y regulación.

## Directiva, insiders, principales accionistas y catalizadores

Se han obtenido índices oficiales SEC Submissions y se han detectado secciones `InsiderTransactions` y `Holders` en el JSON de demostración EODHD. **Eso no significa que ya se haya verificado cada operación ni cada posición institucional.** Segunda etapa obligatoria:

1. Form 4 XML: P=compra, S=venta, A=concesión, M=ejercicio, F=retención fiscal; cotejar fecha, precio, propiedad y regla 10b5-1.
2. DEF 14A y 8-K: CEO/CFO, participación, remuneración, incentivos y cambios.
3. 13D/G y 13F: tenedores relevantes y cambios entre presentaciones; 13F tiene retardo y **no revela día de negociación**.
4. Noticias y 8-K: clasificar relevancia y verificar cada noticia, sin confundir índice de presentaciones con noticias verificadas.

**Valoración PER TTM, múltiplos de sector, DCF y margen de seguridad: PENDIENTES.** No publicar múltiplos sin precio/capitalización fechados, número de acciones coherente y definiciones compatibles, ni inventar una tesis final.

## Documentación oficial de referencia

- Apple 10-K FY2025: https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm
- Tesla 10-K FY2025: https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm
- Amazon 10-K FY2025: https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm

## Próximos bloqueos operativos

- Contrastación 10-Q por períodos continuos, cambios de criterios y reexpresiones.
- Completar ingresos de datos de directivos, insider trades, holders y noticias con evidencias y fechas.
- Resolver BPA Q4/TTM con fuente que aporte beneficio atribuible y dilución comparables; no forzar fórmulas.
- Identificar necesidad de licencia comercial solo después del prototipo privado.
- Publicar producto visual que lea `af_core` en modo consulta y muestre alertas `BLOCKED/PROXY`.
