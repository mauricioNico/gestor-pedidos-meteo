package ar.mil.meteo.gestor.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "meteo")
public record MeteoProperties(Github github, String pagesBaseUrl) {
    public record Github(String owner, String repo, String workflow, String ref, String token) {}
}