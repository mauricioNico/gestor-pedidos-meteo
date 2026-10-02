package ar.mil.meteo.gestor.controller;

import ar.mil.meteo.gestor.config.MeteoProperties;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
public class WebController {
    private final MeteoProperties properties;
    public WebController(MeteoProperties properties){this.properties=properties;}
    @GetMapping("/") public String inicio(){return "index";}
    @GetMapping("/pedido/{id}") public String pedido(@PathVariable String id,Model model){
        model.addAttribute("pedidoId",id);
        model.addAttribute("pagesBaseUrl",properties.pagesBaseUrl());
        return "pedido";
    }
}