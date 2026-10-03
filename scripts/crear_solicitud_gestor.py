# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

VALIDOS = {"SFC", "500", "200", "SOND", "MGRAM"}
PUNTUALES = {"SOND", "MGRAM"}


def numero(txt: str, nombre: str) -> float:
    try:
        return float(str(txt).strip().replace(",", "."))
    except Exception as exc:
        raise SystemExit(f"Valor inválido para {nombre}: {txt!r}") from exc


def entero(txt: str, nombre: str) -> int:
    try:
        return int(str(txt).strip())
    except Exception as exc:
        raise SystemExit(f"Valor inválido para {nombre}: {txt!r}") from exc


def verdadero(txt: str) -> bool:
    return str(txt).strip().lower() in {"1", "true", "si", "sí", "yes", "on"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--productos", required=True)
    ap.add_argument("--nombre-region", required=True)
    ap.add_argument("--norte", required=True)
    ap.add_argument("--sur", required=True)
    ap.add_argument("--oeste", required=True)
    ap.add_argument("--este", required=True)
    ap.add_argument("--nombre-punto", default="PUNTO_OPERATIVO")
    ap.add_argument("--lat-punto", default="")
    ap.add_argument("--lon-punto", default="")

    ap.add_argument("--ruta-habilitada", default="false")
    ap.add_argument("--ruta-nombre", default="")
    ap.add_argument("--origen-etiqueta", default="")
    ap.add_argument("--origen-lat", default="")
    ap.add_argument("--origen-lon", default="")
    ap.add_argument("--destino-etiqueta", default="")
    ap.add_argument("--destino-lat", default="")
    ap.add_argument("--destino-lon", default="")

    ap.add_argument("--f-inicio", required=True)
    ap.add_argument("--f-fin", required=True)
    ap.add_argument("--salto", required=True)
    ap.add_argument("--modo-corrida", default="AUTO")
    ap.add_argument("--fecha", default="")
    ap.add_argument("--ciclo", default="")
    args = ap.parse_args()

    modelo = args.modelo.strip().upper()
    if modelo not in {"GFS", "ECMWF"}:
        raise SystemExit("Modelo debe ser GFS o ECMWF")

    productos = [p.strip().upper() for p in args.productos.split(",") if p.strip()]
    desconocidos = [p for p in productos if p not in VALIDOS]
    if not productos or desconocidos:
        raise SystemExit(f"Productos inválidos: {desconocidos or productos}")

    norte = numero(args.norte, "norte")
    sur = numero(args.sur, "sur")
    oeste = numero(args.oeste, "oeste")
    este = numero(args.este, "este")
    if norte <= sur:
        raise SystemExit("Norte debe ser mayor que sur")

    f_inicio = entero(args.f_inicio, "f_inicio")
    f_fin = entero(args.f_fin, "f_fin")
    salto = entero(args.salto, "salto")
    if f_inicio < 0 or f_fin < f_inicio or salto <= 0:
        raise SystemExit("Período inválido")

    requiere_punto = any(p in PUNTUALES for p in productos)
    punto_habilitado = bool(args.lat_punto.strip() and args.lon_punto.strip())
    if requiere_punto and not punto_habilitado:
        raise SystemExit("SOND/MGRAM requieren latitud y longitud del punto")

    punto = {
        "habilitado": punto_habilitado,
        "nombre": args.nombre_punto.strip() or "PUNTO_OPERATIVO",
        "lat": numero(args.lat_punto, "lat_punto") if punto_habilitado else None,
        "lon": numero(args.lon_punto, "lon_punto") if punto_habilitado else None,
    }

    ruta_habilitada = verdadero(args.ruta_habilitada)
    if ruta_habilitada:
        requeridos = [args.origen_lat, args.origen_lon, args.destino_lat, args.destino_lon]
        if not all(str(x).strip() for x in requeridos):
            raise SystemExit("La ruta requiere coordenadas de origen y destino")
        ruta = {
            "dibujar": True,
            "nombre": args.ruta_nombre.strip(),
            "origen": {
                "lat": numero(args.origen_lat, "origen_lat"),
                "lon": numero(args.origen_lon, "origen_lon"),
                "etiqueta": args.origen_etiqueta.strip() or "Origen",
            },
            "destino": {
                "lat": numero(args.destino_lat, "destino_lat"),
                "lon": numero(args.destino_lon, "destino_lon"),
                "etiqueta": args.destino_etiqueta.strip() or "Destino",
            },
            "waypoints": [],
        }
    else:
        ruta = {
            "dibujar": False,
            "nombre": "",
            "origen": {"lat": None, "lon": None, "etiqueta": ""},
            "destino": {"lat": None, "lon": None, "etiqueta": ""},
            "waypoints": [],
        }

    modo = args.modo_corrida.strip().upper()
    if modo not in {"AUTO", "MANUAL"}:
        raise SystemExit("modo_corrida debe ser AUTO o MANUAL")
    if modo == "MANUAL" and (not args.fecha.strip() or not args.ciclo.strip()):
        raise SystemExit("Corrida MANUAL requiere fecha y ciclo")

    solicitud = {
        "modelo": modelo,
        "productos": productos,
        "region": {
            "nombre": args.nombre_region.strip() or "Region_solicitada",
            "norte": norte, "sur": sur, "oeste": oeste, "este": este,
        },
        "punto": punto,
        "corrida": {
            "modo": modo,
            "fecha": args.fecha.strip() or None,
            "ciclo": args.ciclo.strip() or None,
        },
        "periodo": {
            "f_inicio": f_inicio,
            "f_fin": f_fin,
            "salto": salto,
        },
        "ruta": ruta,
    }

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(solicitud, ensure_ascii=False, indent=2), encoding="utf-8")
    print(salida.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
