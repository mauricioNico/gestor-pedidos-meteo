# Gestor de pedidos meteorológicos

MVP web para solicitar productos, ejecutar el motor existente por GitHub Actions y visualizarlos sin entrar a Actions.

## Flujo

```text
Navegador → Spring Boot → GitHub API → GitHub Actions
          → motor Java/Python → GitHub Pages → visor
```

Los productos se conservan **7 días**. Cada nuevo pedido incorpora sus PNG al historial, elimina pedidos vencidos y vuelve a publicar el catálogo. En esta etapa no se genera ZIP.

## Ejecutar Spring Boot localmente

PowerShell:

```powershell
$env:METEO_GITHUB_TOKEN="TOKEN"
mvn -f app/pom.xml spring-boot:run
```

Abrir:

```text
http://localhost:8080
```

El token debe poder disparar Actions en este repositorio y debe quedar únicamente en el backend, nunca en JavaScript.

## Variables

- `METEO_GITHUB_TOKEN`
- `METEO_GITHUB_OWNER` (default `mauricioNico`)
- `METEO_GITHUB_REPO` (default `gestor-pedidos-meteo`)
- `METEO_GITHUB_WORKFLOW` (default `pedido.yml`)
- `METEO_GITHUB_REF` (default `main`)
- `METEO_PAGES_BASE_URL` (default `https://mauricionico.github.io/gestor-pedidos-meteo`)
- `PORT` (default `8080`)

## MVP actual

- formulario responsive;
- backend Spring Boot;
- creación y seguimiento de pedidos;
- GitHub Actions oculto para el usuario final;
- visor por producto;
- navegación anterior/siguiente y loop;
- historial de pedidos;
- retención automática de 7 días;
- sin ZIP.

El motor meteorológico continúa sin cambios funcionales y permanece temporalmente empaquetado en `bootstrap/`.
