package ar.mil.meteo.gestor.service;

import ar.mil.meteo.gestor.config.MeteoProperties;
import ar.mil.meteo.gestor.model.Pedido;
import ar.mil.meteo.gestor.model.PedidoRequest;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClient;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

@Service
public class GithubActionsService {
    public record WorkflowEstado(Long id, String status, String conclusion, String htmlUrl) {}

    private final RestClient client;
    private final MeteoProperties properties;

    public GithubActionsService(RestClient.Builder builder, MeteoProperties properties) {
        this.properties=properties;
        this.client=builder.baseUrl("https://api.github.com")
                .defaultHeader(HttpHeaders.ACCEPT,"application/vnd.github+json")
                .defaultHeader("X-GitHub-Api-Version","2022-11-28").build();
    }

    public void disparar(Pedido pedido) {
        validarToken();
        PedidoRequest s=pedido.getSolicitud();
        Map<String,String> in=new LinkedHashMap<>();
        in.put("pedido_id",pedido.getId());
        in.put("modelo",s.modelo());
        in.put("productos",String.join(",",s.productos()));
        in.put("nombre_region",s.nombreRegion());
        in.put("norte",s.norte().toString()); in.put("sur",s.sur().toString());
        in.put("oeste",s.oeste().toString()); in.put("este",s.este().toString());
        in.put("nombre_punto",nvl(s.nombrePunto()));
        in.put("lat_punto",s.latPunto()==null?"":s.latPunto().toString());
        in.put("lon_punto",s.lonPunto()==null?"":s.lonPunto().toString());
        in.put("f_inicio",String.valueOf(s.fInicio())); in.put("f_fin",String.valueOf(s.fFin()));
        in.put("salto",String.valueOf(s.salto())); in.put("modo_corrida",s.modoCorrida());
        in.put("fecha",nvl(s.fecha())); in.put("ciclo",nvl(s.ciclo()));

        client.post().uri("/repos/{o}/{r}/actions/workflows/{w}/dispatches",
                        properties.github().owner(),properties.github().repo(),properties.github().workflow())
                .header(HttpHeaders.AUTHORIZATION,"Bearer "+properties.github().token())
                .contentType(MediaType.APPLICATION_JSON)
                .body(Map.of("ref",properties.github().ref(),"inputs",in))
                .retrieve().toBodilessEntity();
    }

    public Optional<WorkflowEstado> consultar(String pedidoId) {
        validarToken();
        JsonNode root=client.get().uri(uriBuilder->uriBuilder
                        .path("/repos/{o}/{r}/actions/workflows/{w}/runs")
                        .queryParam("event","workflow_dispatch").queryParam("per_page","50")
                        .build(properties.github().owner(),properties.github().repo(),properties.github().workflow()))
                .header(HttpHeaders.AUTHORIZATION,"Bearer "+properties.github().token())
                .retrieve().body(JsonNode.class);
        if(root==null||!root.has("workflow_runs")) return Optional.empty();
        for(JsonNode run:root.get("workflow_runs")){
            String title=run.path("display_title").asText("");
            if(title.contains(pedidoId)){
                return Optional.of(new WorkflowEstado(run.path("id").asLong(),run.path("status").asText(""),
                        run.path("conclusion").isNull()?null:run.path("conclusion").asText(null),
                        run.path("html_url").asText("")));
            }
        }
        return Optional.empty();
    }

    private void validarToken(){
        if(!StringUtils.hasText(properties.github().token()))
            throw new IllegalStateException("METEO_GITHUB_TOKEN no configurado en el servidor.");
    }
    private static String nvl(String v){return v==null?"":v;}
}