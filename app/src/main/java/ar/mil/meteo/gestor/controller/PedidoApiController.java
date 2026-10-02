package ar.mil.meteo.gestor.controller;

import ar.mil.meteo.gestor.model.*;
import ar.mil.meteo.gestor.service.PedidoService;
import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.Valid;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/pedidos")
public class PedidoApiController {
    private final PedidoService service;
    public PedidoApiController(PedidoService service){this.service=service;}

    @PostMapping public ResponseEntity<Pedido> crear(@Valid @RequestBody PedidoRequest r){
        return ResponseEntity.status(HttpStatus.CREATED).body(service.crear(r));
    }
    @GetMapping("/{id}") public ResponseEntity<Pedido> obtener(@PathVariable String id){
        return service.obtener(id).map(ResponseEntity::ok).orElseGet(()->ResponseEntity.notFound().build());
    }
    @GetMapping("/{id}/productos") public ResponseEntity<JsonNode> productos(@PathVariable String id){
        return service.productos(id).map(ResponseEntity::ok).orElseGet(()->ResponseEntity.notFound().build());
    }
    @GetMapping("/historial") public JsonNode historial(){return service.historial();}

    @ExceptionHandler({IllegalArgumentException.class,IllegalStateException.class})
    public ResponseEntity<Map<String,String>> error(RuntimeException ex){
        return ResponseEntity.badRequest().body(Map.of("error",ex.getMessage()));
    }
}