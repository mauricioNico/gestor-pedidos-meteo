package ar.mil.meteo.gestor;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class GestorMeteoApplication {
    public static void main(String[] args) {
        SpringApplication.run(GestorMeteoApplication.class, args);
    }
}