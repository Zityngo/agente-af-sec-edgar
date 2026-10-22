# Cotizaciones y acciones · diseño solo consulta · 22/10/2026
## Implementado
- `af_core/market_data.py`: interpreta snapshots de IBKR Client Portal Gateway, reconoce REALTIME/DELAYED/FROZEN/no suscrito, rechaza muestras caducadas (>15 min) y precios C/H, valida conid y timestamp.
- `sec_latest_shares`: usa `dei.EntityCommonStockSharesOutstanding` por fecha y accession SEC sin mezclar acciones medias diluidas de BPA.
- `validate_quote_and_shares`: capitalización con procedencia y diferencia de fecha de acciones.
- `tests/test_market_data.py`: datos sintéticos, sin cuenta personal, 7 pruebas.
## Seguridad y licencia
Uso particular; autenticación IBKR local previa, token jamás se guarda ni se mete en CI. Solo HTTPS localhost con certificado confiable: no desactivar validación TLS silenciosamente.
No existe todavía un servicio externo siempre encendido, ni se ofrece redistribución de precios a clientes.
Para automatizar precios a escala comercial se necesita proveedor y licencia expresa. Fallback: último cierre fechado, estado FROZEN, nunca presentado REALTIME.
La consulta IBKR conectada a ChatGPT es de solo lectura pero no una credencial portable al repositorio ni API de la aplicación.
Para datos SEC se prefiere 10-Q/10-K reciente; si SEC ha publicado Q3 antes de refrescar Companyfacts, marcar pendiente revisión del dato faltante en vez de reutilizar indefinidamente Q2.
