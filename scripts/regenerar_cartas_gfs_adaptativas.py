#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenera las cartas GFS SFC/500/200 con los generadores operativos.

Se ejecuta DESPUES del motor del gestor. De esta forma no altera la descarga
ni el resto del flujo; solamente reemplaza los PNG finales de SFC/500/200
por las versiones generadas con productosMetCloud/master.

La selección de proyección queda a cargo de mapa_proyeccion_adaptativa.py.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


MAPAS = {
    "SFC": Path("python/mapa_mslp.py"),
    "500": Path("python/mapa_500.py"),
    "200": Path("python/mapa_200.py"),
}

TOKENS = {
    "SFC": ("_sfc_f",),
    "500": ("_500_f", "_500hpa_f"),
    "200": ("_200_f", "_200hpa_f"),
}


def slug_region(nombre: str) -> str:
    s = (nombre or "Region").strip().replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_") or "Region"


def paso_desde_nombre(path: Path):
    m = re.search(r"_f(\d{3})(?:\D|$)", path.name, re.IGNORECASE)
    return int(m.group(1)) if m else None


def buscar_gribs(base: Path, producto: str, productos_mapa):
    todos = sorted(base.rglob("*.grib2"))
    tokens = TOKENS[producto]
    filtrados = [p for p in todos if any(t in p.name.lower() for t in tokens)]

    if filtrados:
        return filtrados

    # Algunos motores usan GRIB unificado sin nombre de producto. El fallback
    # solo se permite si se pidió una única carta para evitar mezclar datasets.
    if len(productos_mapa) == 1:
        return [p for p in todos if paso_desde_nombre(p) is not None]

    return []


def buscar_directorio_salida(producto: str):
    candidatos = sorted(Path("salidas").glob(f"*_GFS/{producto}"))
    if not candidatos:
        raise FileNotFoundError(f"No se encontró directorio de salida para {producto}.")
    return candidatos[-1]


def salida_para_paso(outdir: Path, producto: str, region_slug: str, paso: int):
    existentes = sorted(outdir.glob(f"*f{paso:03d}.png"))
    if existentes:
        return existentes[0]
    return outdir / f"GFS_{producto}_{region_slug}_f{paso:03d}.png"


def copia_segura_sfc(grib: Path):
    """mapa_mslp.py puede reorganizar GRIBs; se le pasa una copia descartable."""
    m = re.search(r"(20\d{6})", grib.name)
    fecha = m.group(1) if m else "temporal"
    tmpdir = Path("gribs") / fecha
    tmpdir.mkdir(parents=True, exist_ok=True)
    copia = tmpdir / grib.name

    if grib.resolve() == copia.resolve():
        return grib, False

    shutil.copy2(grib, copia)
    return copia, True


def main():
    if len(sys.argv) != 2:
        print("Uso: regenerar_cartas_gfs_adaptativas.py config/solicitud_workflow.json")
        return 2

    solicitud_path = Path(sys.argv[1])
    solicitud = json.loads(solicitud_path.read_text(encoding="utf-8"))

    if str(solicitud.get("modelo", "")).upper() != "GFS":
        print("No es un pedido GFS. No se regeneran cartas.")
        return 0

    productos = [str(p).upper() for p in solicitud.get("productos", [])]
    productos_mapa = [p for p in productos if p in MAPAS]

    if not productos_mapa:
        print("El pedido no contiene SFC/500/200. No hay nada que regenerar.")
        return 0

    region = solicitud.get("region", {})
    nombre_region = str(region.get("nombre") or "Region")
    region_slug = slug_region(nombre_region)

    top = float(region["norte"])
    bottom = float(region["sur"])
    left = float(region["oeste"])
    right = float(region["este"])

    # Los GRIB GFS descargados por el gestor usan longitudes 0..360.
    # Los generadores operativos recortan el xarray antes de proyectar, por
    # lo que deben recibir el mismo sistema de longitudes que el GRIB.
    left_data = left % 360.0
    right_data = right % 360.0

    print(
        f"Regeneración cartográfica GFS: {nombre_region} | "
        f"N={top} S={bottom} W={left} E={right} | "
        f"GRIB lon={left_data}..{right_data}"
    )

    base_gribs = Path("gribs/gfs")
    if not base_gribs.exists():
        base_gribs = Path("gribs")

    total = 0

    for producto in productos_mapa:
        script = MAPAS[producto]
        if not script.exists():
            raise FileNotFoundError(f"Falta generador {script}")

        gribs = buscar_gribs(base_gribs, producto, productos_mapa)
        if not gribs:
            raise FileNotFoundError(
                f"No se encontraron GRIBs compatibles para {producto} en {base_gribs}"
            )

        outdir = buscar_directorio_salida(producto)
        print(f"[{producto}] {len(gribs)} GRIB(s) -> {outdir}")

        for grib in gribs:
            paso = paso_desde_nombre(grib)
            if paso is None:
                continue

            salida = salida_para_paso(outdir, producto, region_slug, paso)
            entrada = grib
            borrar_entrada = False

            if producto == "SFC":
                entrada, borrar_entrada = copia_segura_sfc(grib)

            cmd = [
                sys.executable,
                str(script),
                str(entrada),
                str(salida),
                str(top),
                str(bottom),
                str(left_data),
                str(right_data),
            ]

            print(f"[{producto}] f{paso:03d} -> {salida.name}", flush=True)
            try:
                subprocess.run(cmd, check=True)
            finally:
                if borrar_entrada:
                    try:
                        entrada.unlink()
                    except FileNotFoundError:
                        pass

            total += 1

    print(f"Regeneración adaptativa completada: {total} carta(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
