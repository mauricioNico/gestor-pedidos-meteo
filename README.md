# Gestor de pedidos meteorológicos

MVP para probar la generación remota de productos meteorológicos usando **GitHub Actions** y la publicación del último pedido mediante **GitHub Pages**.

## Objetivo de esta primera prueba

El flujo es:

```text
Formulario de GitHub Actions
        ↓
solicitud JSON
        ↓
motor existente Java + Python
        ↓
descarga GFS / ECMWF
        ↓
generación de PNG
        ↓
artefacto ZIP + visor web
```

No se sube ningún producto al sitio de FAA.

## Primera prueba recomendada

En la pestaña **Actions** abrir:

**Generar pedido meteorológico → Run workflow**

Usar:

```text
Modelo:       GFS
Productos:    SFC
Región:       Sudamerica
Norte:        15
Sur:          -60
Oeste:        -90
Este:         -20
H inicial:    0
H final:      24
Intervalo:    6
Corrida:      AUTO
```

Para esta prueba dejar vacías las coordenadas del punto.

Al finalizar correctamente:

1. El run tendrá un artefacto `pedido-meteorologico-N` descargable durante 7 días.
2. El ZIP contiene los productos generados.
3. El último pedido se prepara también para visualizarse mediante GitHub Pages.

## Activar GitHub Pages

Antes de probar la publicación web:

**Settings → Pages → Build and deployment → Source → GitHub Actions**

No elegir una rama como fuente. La publicación la realiza el workflow.

## Productos admitidos

- `SFC`: superficie.
- `500`: 500 hPa.
- `200`: 200 hPa.
- `SOND`: radiosondeo pronosticado; requiere punto.
- `MGRAM`: meteograma; requiere punto.

Se pueden combinar separados por coma, por ejemplo:

```text
SFC,500,200
```

## Estructura del MVP

El motor de esta primera versión se transporta dentro de `bootstrap/bundle.part*.b64`.
El workflow lo reconstruye en el runner de GitHub antes de ejecutarlo.

Esto es **temporal para la prueba inicial**. Una vez validado el circuito completo, la siguiente etapa será dejar el código Java/Python directamente visible en el repositorio y reemplazar el formulario de `Run workflow` por el formulario web responsive del gestor.

## Red

En GitHub Actions el proxy está deshabilitado. El motor usa la conexión directa del runner.

## Próxima etapa

Cuando la prueba GFS/SFC funcione de punta a punta:

- formulario web propio;
- identificación de pedido;
- estados Pendiente / Ejecutando / Finalizado;
- visor por modelo, producto y H+;
- descarga individual de PNG;
- descarga completa del pedido en ZIP;
- historial y vencimiento de pedidos.
