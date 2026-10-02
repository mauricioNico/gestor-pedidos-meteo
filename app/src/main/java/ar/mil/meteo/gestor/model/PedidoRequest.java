package ar.mil.meteo.gestor.model;

import jakarta.validation.constraints.*;
import java.util.List;

public record PedidoRequest(
        @NotBlank String modelo,
        @NotEmpty List<String> productos,
        @NotBlank String nombreRegion,
        @NotNull @Min(-90) @Max(90) Double norte,
        @NotNull @Min(-90) @Max(90) Double sur,
        @NotNull @Min(-180) @Max(360) Double oeste,
        @NotNull @Min(-180) @Max(360) Double este,
        String nombrePunto,
        @Min(-90) @Max(90) Double latPunto,
        @Min(-180) @Max(360) Double lonPunto,
        @Min(0) Integer fInicio,
        @Min(0) Integer fFin,
        @Positive Integer salto,
        @NotBlank String modoCorrida,
        String fecha,
        String ciclo
) {}