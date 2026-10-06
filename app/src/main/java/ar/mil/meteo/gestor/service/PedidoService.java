package ar.mil.meteo.gestor.service;

import ar.mil.meteo.gestor.model.*;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.stereotype.Service;
import java.security.SecureRandom;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class PedidoService {
    private static final DateTimeFormatter F=DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss").withZone(ZoneOffset.UTC);
    private final Map<String,Pedido> pedidos=new ConcurrentHashMap<>();
    private final SecureRandom random=new SecureRandom();
    private final GithubActionsService github;
    private final CatalogoService catalogo;

    public PedidoService(GithubActionsService github,CatalogoService catalogo){this.github=github;this.catalogo=catalogo;}

    public Pedido crear(PedidoRequest r){
        validar(r);
        String id="PED-"+F.format(java.time.Instant.now())+"-"+(1000+random.nextInt(9000));
        Pedido p=new Pedido(id,r); pedidos.put(id,p);
        try{github.disparar(p);p.actualizar(EstadoPedido.PENDIENTE,"Pedido enviado al motor meteorologico",null,null);}
        catch(RuntimeException ex){p.actualizar(EstadoPedido.ERROR,ex.getMessage(),null,null);throw ex;}
        return p;
    }

    public Optional<Pedido> obtener(String id){
        Pedido p=pedidos.get(id);
        if(p==null)return Optional.empty();
        refrescar(p); return Optional.of(p);
    }

    public Optional<JsonNode> productos(String id){return catalogo.obtenerPedido(id);}
    public JsonNode historial(){return catalogo.historial();}

    private void refrescar(Pedido p){
        if(p.getEstado()==EstadoPedido.FINALIZADO||p.getEstado()==EstadoPedido.ERROR)return;
        try{github.consultar(p.getId()).ifPresent(run->{
            if("completed".equalsIgnoreCase(run.status())){
                if("success".equalsIgnoreCase(run.conclusion()))p.actualizar(EstadoPedido.FINALIZADO,"Productos disponibles",run.id(),run.htmlUrl());
                else p.actualizar(EstadoPedido.ERROR,"La generacion finalizo con estado "+run.conclusion(),run.id(),run.htmlUrl());
            } else p.actualizar(EstadoPedido.EJECUTANDO,"Generando productos meteorologicos",run.id(),run.htmlUrl());
        });}
        catch(RuntimeException ex){p.actualizar(p.getEstado(),"No se pudo actualizar el estado: "+ex.getMessage(),p.getWorkflowRunId(),p.getWorkflowUrl());}
    }

    private static void validar(PedidoRequest r){
        if(r.norte()<=r.sur())throw new IllegalArgumentException("La latitud norte debe ser mayor que la latitud sur.");
        if(r.fFin()<r.fInicio())throw new IllegalArgumentException("H final debe ser mayor o igual que H inicial.");
        if((r.fFin()-r.fInicio())%r.salto()!=0)throw new IllegalArgumentException("El intervalo debe dividir exactamente el periodo solicitado.");

        boolean punto=r.productos().stream().map(String::toUpperCase).anyMatch(x->x.equals("SOND")||x.equals("MGRAM"));
        if(punto&&(r.latPunto()==null||r.lonPunto()==null))
            throw new IllegalArgumentException("SOND/MGRAM requieren latitud y longitud del punto.");

        if(r.rutaHabilitada()){
            boolean cartografico=r.productos().stream().map(String::toUpperCase)
                    .anyMatch(x->x.equals("SFC")||x.equals("500")||x.equals("200"));
            if(!cartografico)
                throw new IllegalArgumentException("La ruta se dibuja solamente en productos SFC, 500 y 200 hPa.");
            if(r.origenLat()==null||r.origenLon()==null||r.destinoLat()==null||r.destinoLon()==null)
                throw new IllegalArgumentException("La ruta requiere latitud y longitud de origen y destino.");
        }

        if("MANUAL".equalsIgnoreCase(r.modoCorrida())&&(r.fecha()==null||r.fecha().isBlank()||r.ciclo()==null||r.ciclo().isBlank()))
            throw new IllegalArgumentException("La corrida manual requiere fecha y ciclo.");

        validarPeriodoModelo(r);
    }

    private static void validarPeriodoModelo(PedidoRequest r){
        String modelo=r.modelo()==null?"":r.modelo().trim().toUpperCase();

        switch(modelo){
            case "GFS" -> validarPeriodoGfs(r);
            case "ECMWF" -> validarPeriodoEcmwf(r);
            default -> throw new IllegalArgumentException("Modelo no soportado: "+r.modelo());
        }
    }

    private static void validarPeriodoGfs(PedidoRequest r){
        if(r.fFin()>384)
            throw new IllegalArgumentException("GFS permite pronosticos hasta H+384.");

        for(int h=r.fInicio();h<=r.fFin();h+=r.salto()){
            boolean publicado = h<=120 || (h>120 && h%3==0);
            if(!publicado){
                throw new IllegalArgumentException(
                        "GFS publica pasos horarios hasta H+120 y luego cada 3 h hasta H+384. "
                        +"El pedido incluye H+"+h+", que no esta disponible.");
            }
        }
    }

    private static void validarPeriodoEcmwf(PedidoRequest r){
        boolean manual="MANUAL".equalsIgnoreCase(r.modoCorrida());
        String ciclo=r.ciclo()==null?"":r.ciclo().trim();

        if(manual && ("06".equals(ciclo)||"18".equals(ciclo))){
            if(r.fFin()>90)
                throw new IllegalArgumentException(
                        "ECMWF en las corridas 06/18 UTC permite el pronostico determinista hasta H+90.");
            for(int h=r.fInicio();h<=r.fFin();h+=r.salto()){
                if(h%3!=0){
                    throw new IllegalArgumentException(
                            "ECMWF 06/18 UTC publica pasos cada 3 h hasta H+90. "
                            +"El pedido incluye H+"+h+", que no esta disponible.");
                }
            }
            return;
        }

        if(r.fFin()>240)
            throw new IllegalArgumentException(
                    "ECMWF determinista en las corridas 00/12 UTC permite pronosticos hasta H+240.");

        for(int h=r.fInicio();h<=r.fFin();h+=r.salto()){
            boolean publicado = h<=144 ? h%3==0 : h%6==0;
            if(!publicado){
                throw new IllegalArgumentException(
                        "ECMWF publica cada 3 h hasta H+144 y luego cada 6 h hasta H+240. "
                        +"El pedido incluye H+"+h+", que no esta disponible.");
            }
        }
    }
}
