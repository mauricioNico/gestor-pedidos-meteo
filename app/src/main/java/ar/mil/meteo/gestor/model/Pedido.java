package ar.mil.meteo.gestor.model;

import java.time.Instant;

public class Pedido {
    private final String id;
    private final Instant creado;
    private final PedidoRequest solicitud;
    private volatile EstadoPedido estado = EstadoPedido.PENDIENTE;
    private volatile String mensaje = "Pedido recibido";
    private volatile Long workflowRunId;
    private volatile String workflowUrl;

    public Pedido(String id, PedidoRequest solicitud) {
        this.id=id; this.creado=Instant.now(); this.solicitud=solicitud;
    }
    public String getId(){return id;} public Instant getCreado(){return creado;}
    public PedidoRequest getSolicitud(){return solicitud;} public EstadoPedido getEstado(){return estado;}
    public String getMensaje(){return mensaje;} public Long getWorkflowRunId(){return workflowRunId;}
    public String getWorkflowUrl(){return workflowUrl;}
    public void actualizar(EstadoPedido e,String m,Long runId,String url){estado=e;mensaje=m;workflowRunId=runId;workflowUrl=url;}
}