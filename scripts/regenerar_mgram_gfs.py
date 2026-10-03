#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenera MGRAM GFS con el meteograma operativo de productosMetCloud.

Flujo:
1) lee config/solicitud_workflow.json;
2) detecta fecha/ciclo GFS ya seleccionados por el motor;
3) descarga un recorte pequeño alrededor del punto con los campos adicionales
   que necesita el meteograma completo;
4) ejecuta scripts/meteograma_gfs_referencia.py;
5) reemplaza el PNG MGRAM simplificado por el producto completo.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"

VARS = [
    "PRMSL", "TMP", "RH", "UGRD", "VGRD", "GUST",
    "APCP", "ACPCP", "CAPE", "CIN", "LFTX", "VVEL",
    "HGT", "REFC", "LCDC", "VIS", "SNOD", "WEASD",
]


def cargar_solicitud(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def buscar_corrida_gfs(root: Path) -> tuple[str, str, list[int]]:
    patron = re.compile(r"(?i)gfs.*?(20\d{6}).*?_(00|06|12|18).*?f(\d{3})")
    encontrados: list[tuple[str, str, int]] = []

    for p in root.rglob("*.grib2"):
        m = patron.search(p.name)
        if m:
            encontrados.append((m.group(1), m.group(2), int(m.group(3))))

    if not encontrados:
        raise RuntimeError("No se pudo detectar fecha/ciclo GFS en los GRIB descargados.")

    # El motor usa una sola corrida por pedido. Elegimos la combinación con más pasos.
    conteo: dict[tuple[str, str], list[int]] = {}
    for fecha, ciclo, fh in encontrados:
        conteo.setdefault((fecha, ciclo), []).append(fh)

    (fecha, ciclo), fhs = max(conteo.items(), key=lambda kv: len(set(kv[1])))
    return fecha, ciclo, sorted(set(fhs))


def construir_url(fecha: str, ciclo: str, fh: int, lat: float, lon: float) -> str:
    margen = 0.75
    top = min(90.0, lat + margen)
    bottom = max(-90.0, lat - margen)

    lon360 = lon % 360.0
    left = (lon360 - margen) % 360.0
    right = (lon360 + margen) % 360.0

    # En el caso extremadamente raro de cruzar 0°, ampliamos a una caja simple
    # alrededor de la longitud equivalente negativa/positiva. Para los puntos
    # operativos sudamericanos habituales no se activa.
    if left > right:
        left = max(0.0, lon360 - 1.5)
        right = min(360.0, lon360 + 1.5)

    params = [
        ("file", f"gfs.t{ciclo}z.pgrb2.0p25.f{fh:03d}"),
        ("all_lev", "on"),
    ]
    params.extend((f"var_{v}", "on") for v in VARS)
    params.extend([
        ("subregion", ""),
        ("leftlon", f"{left:.2f}"),
        ("rightlon", f"{right:.2f}"),
        ("toplat", f"{top:.2f}"),
        ("bottomlat", f"{bottom:.2f}"),
        ("dir", f"/gfs.{fecha}/{ciclo}/atmos"),
    ])
    return BASE_URL + "?" + urllib.parse.urlencode(params)


def descargar(url: str, destino: Path, intentos: int = 6) -> None:
    if destino.exists() and destino.stat().st_size > 10_000:
        print(f"[MGRAM] Ya existe: {destino.name}")
        return

    espera = 3
    for intento in range(1, intentos + 1):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "gestor-pedidos-meteo/1.0",
                "Accept": "application/octet-stream,*/*",
            },
        )
        try:
            print(f"[MGRAM] Descargando {destino.name} (intento {intento}/{intentos})")
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                ctype = (resp.headers.get("Content-Type") or "").lower()

            if len(data) < 10_000 or b"<html" in data[:500].lower():
                raise RuntimeError(
                    f"Respuesta NOMADS no valida ({len(data)} bytes, Content-Type={ctype})"
                )

            tmp = destino.with_suffix(destino.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(destino)
            print(f"[MGRAM] OK {destino.name}: {len(data)/1024:.1f} KiB")
            return

        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry = exc.headers.get("Retry-After")
                try:
                    espera = max(espera, int(retry)) if retry else espera
                except Exception:
                    pass
            print(f"[MGRAM] HTTP {exc.code}: {exc.reason}")
        except Exception as exc:
            print(f"[MGRAM] {type(exc).__name__}: {exc}")

        if intento < intentos:
            time.sleep(espera)
            espera = min(60, espera * 2)

    raise RuntimeError(f"No se pudo descargar {destino.name}")


def carpeta_operativo(salidas: Path) -> Path:
    carpetas = [p for p in salidas.iterdir() if p.is_dir()]
    if not carpetas:
        raise RuntimeError("No se encontro la carpeta operativa en salidas/")
    return max(carpetas, key=lambda p: p.stat().st_mtime)


def main() -> int:
    solicitud_path = Path(sys.argv[1] if len(sys.argv) > 1 else "config/solicitud_workflow.json")
    solicitud = cargar_solicitud(solicitud_path)

    if str(solicitud.get("modelo", "")).upper() != "GFS":
        print("[MGRAM] Modelo distinto de GFS: se conserva el generador actual.")
        return 0

    productos = {str(x).upper() for x in solicitud.get("productos", [])}
    if "MGRAM" not in productos:
        print("[MGRAM] Pedido sin MGRAM: no se requiere postproceso.")
        return 0

    punto = solicitud.get("punto") or {}
    if not punto.get("habilitado"):
        raise RuntimeError("MGRAM requiere un punto habilitado.")

    lat = float(punto["lat"])
    lon = float(punto["lon"])
    nombre = str(punto.get("nombre") or "PUNTO_OPERATIVO")

    fecha, ciclo, fhs_existentes = buscar_corrida_gfs(Path("gribs"))

    periodo = solicitud.get("periodo") or {}
    f_ini = int(periodo.get("f_inicio", min(fhs_existentes)))
    f_fin = int(periodo.get("f_fin", max(fhs_existentes)))
    salto = int(periodo.get("salto", 3))

    # Mantenemos exactamente la resolución temporal solicitada en el gestor.
    fhs = list(range(f_ini, f_fin + 1, salto))
    if not fhs:
        raise RuntimeError("No hay forecast hours para construir el meteograma.")

    print(
        f"[MGRAM] Corrida GFS detectada: {fecha} {ciclo}Z | "
        f"punto={nombre} ({lat:.3f}, {lon:.3f}) | pasos={fhs}"
    )

    gribs_ref = Path("gribs") / "mgram_referencia"
    gribs_ref.mkdir(parents=True, exist_ok=True)

    for fh in fhs:
        destino = gribs_ref / f"gfs_{fecha}_{ciclo}_f{fh:03d}_mgram_ref.grib2"
        descargar(construir_url(fecha, ciclo, fh, lat, lon), destino)
        time.sleep(1.2)

    operativo = carpeta_operativo(Path("salidas"))
    salida_mgram = operativo / "MGRAM"
    salida_mgram.mkdir(parents=True, exist_ok=True)

    # Retiramos el MGRAM simplificado para que el visor muestre una sola versión.
    for png in salida_mgram.glob("*.png"):
        png.unlink()

    datos_taf = salida_mgram / "datos_taf_mgram.csv"

    cmd = [
        sys.executable,
        "scripts/meteograma_gfs_referencia.py",
        str(gribs_ref),
        str(salida_mgram),
        str(lat),
        str(lon),
        nombre,
        str(datos_taf),
    ]
    print("[MGRAM] Ejecutando meteograma de referencia...")
    subprocess.run(cmd, check=True)

    generados = list(salida_mgram.glob("meteograma_*.png"))
    if not generados:
        raise RuntimeError("El meteograma de referencia no genero PNG.")

    print(f"[MGRAM] Producto final: {generados[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
