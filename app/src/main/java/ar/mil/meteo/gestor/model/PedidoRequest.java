package ar.mil.meteo.gestor.model;

import jakarta.validation.constraints.*;
import java.util.List;

public record PedidoRequest(
        @NotBlank String modelo,
        @NotEmpty List<String> productos,
        @NotBlank String nombreRegion,
        @NotNull @DecimalMin("-90") @DecimalMax("90") Double norte,
        @NotNull @DecimalMin("-90") @DecimalMax("90") Double sur,
        @NotNull @DecimalMin("-180") @DecimalMax("360") Double oeste,
        @NotNull @DecimalMin("-180") @DecimalMax("360") Double este,
        String nombrePunto,
        @DecimalMin("-90") @DecimalMax("90") Double latPunto,
        @DecimalMin("-180") @DecimalMax("360") Double lonPunto,
        @NotNull @Min(0) Integer fInicio,
        @NotNull @Min(0) Integer fFin,
        @NotNull @Positive Integer salto,
        @NotBlank String modoCorrida,
        String fecha,
        String ciclo
) {}
