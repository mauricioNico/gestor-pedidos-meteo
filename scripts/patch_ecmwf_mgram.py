#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amplia temporalmente las reglas MGRAM de DescargaECMWF.java después de
reconstruir el motor empaquetado. No modifica el bundle original.

Añade los campos necesarios para que el meteograma ECMWF tenga el mismo
diseño operativo que el GFS: perfil vertical, Z500, MUCAPE y omega 700.
"""

from __future__ import annotations

import sys
from pathlib import Path


BLOQUE = '''            case "MGRAM" -> List.of(
                    new Regla("msl", "msl", null, null),
                    new Regla("tp", "tp", null, null),
                    new Regla("tcc", "tcc", null, null),
                    new Regla("lcc", "lcc", null, null),
                    new Regla("mcc", "mcc", null, null),
                    new Regla("hcc", "hcc", null, null),
                    new Regla("10u", "10u", null, null),
                    new Regla("10v", "10v", null, null),
                    new Regla("10fg", "10fg", null, null),
                    new Regla("10fg3", "10fg3", null, null),
                    new Regla("2t", "2t", null, null),
                    new Regla("2d", "2d", null, null),
                    new Regla("cbh", "cbh", null, null),

                    new Regla("mucape", "mucape", null, null),
                    new Regla("gh500", "gh", "pl", "500"),
                    new Regla("w700", "w", "pl", "700"),

                    new Regla("t1000", "t", "pl", "1000"),
                    new Regla("t925", "t", "pl", "925"),
                    new Regla("t850", "t", "pl", "850"),
                    new Regla("t700", "t", "pl", "700"),
                    new Regla("t500", "t", "pl", "500"),
                    new Regla("t400", "t", "pl", "400"),

                    new Regla("r1000", "r", "pl", "1000"),
                    new Regla("r925", "r", "pl", "925"),
                    new Regla("r850", "r", "pl", "850"),
                    new Regla("r700", "r", "pl", "700"),
                    new Regla("r500", "r", "pl", "500"),
                    new Regla("r400", "r", "pl", "400"),

                    new Regla("u1000", "u", "pl", "1000"),
                    new Regla("u925", "u", "pl", "925"),
                    new Regla("u850", "u", "pl", "850"),
                    new Regla("u700", "u", "pl", "700"),
                    new Regla("u500", "u", "pl", "500"),
                    new Regla("u400", "u", "pl", "400"),

                    new Regla("v1000", "v", "pl", "1000"),
                    new Regla("v925", "v", "pl", "925"),
                    new Regla("v850", "v", "pl", "850"),
                    new Regla("v700", "v", "pl", "700"),
                    new Regla("v500", "v", "pl", "500"),
                    new Regla("v400", "v", "pl", "400")
            );'''


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: patch_ecmwf_mgram.py java/DescargaECMWF.java")
        return 2

    path = Path(sys.argv[1])
    texto = path.read_text(encoding="utf-8")

    inicio = texto.find('            case "MGRAM" -> List.of(')
    if inicio < 0:
        raise RuntimeError("No se encontró el bloque MGRAM en DescargaECMWF.java")

    marca_fin = '\n            case "SOND" -> List.of('
    fin = texto.find(marca_fin, inicio)
    if fin < 0:
        raise RuntimeError("No se encontró el final del bloque MGRAM")

    nuevo = texto[:inicio] + BLOQUE + texto[fin:]
    path.write_text(nuevo, encoding="utf-8")

    print("[ECMWF MGRAM] DescargaECMWF.java ampliado correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
