package ar.mil.meteo.gestor.service;

import ar.mil.meteo.gestor.config.MeteoProperties;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestClient;
import java.util.Optional;

@Service
public class CatalogoService {
    private final RestClient client;
    private final MeteoProperties properties;
    public CatalogoService(RestClient.Builder builder,MeteoProperties properties){this.client=builder.build();this.properties=properties;}

    public Optional<JsonNode> obtenerPedido(String id){
        try{return Optional.ofNullable(client.get().uri(base()+"/pedidos/"+id+"/catalogo.json").retrieve().body(JsonNode.class));}
        catch(HttpClientErrorException.NotFound e){return Optional.empty();}
    }
    public JsonNode historial(){return client.get().uri(base()+"/catalogo.json").retrieve().body(JsonNode.class);}
    private String base(){String b=properties.pagesBaseUrl();return b.endsWith("/")?b.substring(0,b.length()-1):b;}
}