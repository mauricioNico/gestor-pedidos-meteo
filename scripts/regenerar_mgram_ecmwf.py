#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reemplaza el MGRAM ECMWF simplificado por el producto operativo completo.
Los campos extra ya fueron incorporados a DescargaECMWF.java por el patch
aplicado antes de ejecutar el motor.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def carpeta_operativo(salidas: Path) -> Path:
    carpetas = [p for p in salidas.iterdir() if p.is_dir()]
    if not carpetas:
        raise RuntimeError("No se encontro la carpeta operativa en salidas/")
    return max(carpetas, key=lambda p: p.stat().st_mtime)


def main() -> int:
    solicitud_path = Path(sys.argv[1] if len(sys.argv) > 1 else "config/solicitud_workflow.json")
    solicitud = json.loads(solicitud_path.read_text(encoding="utf-8"))

    if str(solicitud.get("modelo", "")).upper() != "ECMWF":
        return 0

    productos = {str(x).upper() for x in solicitud.get("productos", [])}
    if "MGRAM" not in productos:
        return 0

    punto = solicitud.get("punto") or {}
    if not punto.get("habilitado"):
        raise RuntimeError("MGRAM requiere un punto habilitado.")

    lat = float(punto["lat"])
    lon = float(punto["lon"])
    nombre = str(punto.get("nombre") or "PUNTO_OPERATIVO")

    operativo = carpeta_operativo(Path("salidas"))
    salida_mgram = operativo / "MGRAM"
    salida_mgram.mkdir(parents=True, exist_ok=True)

    tmp = salida_mgram / "_ecmwf_ref_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    cmd = [
        sys.executable,
        "scripts/meteograma_ecmwf_referencia.py",
        "gribs/ecmwf",
        str(tmp),
        str(lat),
        str(lon),
        nombre,
    ]

    print("[MGRAM ECMWF] Generando meteograma operativo...", flush=True)
    proceso = subprocess.run(cmd, check=False)

    generados = [
        p for p in tmp.glob("meteograma_*.png")
        if p.is_file() and p.stat().st_size > 10_000
    ]

    if proceso.returncode != 0:
        if proceso.returncode in (-11, 139) and generados:
            print(
                "[MGRAM ECMWF][WARN] SIGSEGV al cerrar librerias nativas, "
                "pero el PNG fue generado correctamente.",
                flush=True,
            )
        else:
            raise RuntimeError(
                f"El generador MGRAM ECMWF termino con codigo {proceso.returncode} "
                "y no produjo un PNG valido."
            )

    if not generados:
        raise RuntimeError("El meteograma ECMWF de referencia no genero PNG valido.")

    for png in salida_mgram.glob("*.png"):
        png.unlink()

    final = salida_mgram / generados[0].name
    shutil.move(str(generados[0]), final)
    shutil.rmtree(tmp, ignore_errors=True)

    print(f"[MGRAM ECMWF] Producto final: {final} ({final.stat().st_size} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
