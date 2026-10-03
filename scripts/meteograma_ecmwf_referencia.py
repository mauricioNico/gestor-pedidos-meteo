#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Meteograma operativo ECMWF IFS 0.25° con diseño equivalente al producto GFS.

Usa únicamente campos presentes en ECMWF Open Data:
- perfil vertical: T, RH, U/V entre 1000 y 400 hPa;
- MSLP + Z500;
- MUCAPE;
- viento 10 m + ráfaga;
- T2m + Td2m;
- omega 700 hPa;
- precipitación por intervalo.

No inventa Lifted Index: ECMWF Open Data no expone el LFTX usado por GFS.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

from meteograma_gfs_referencia import (
    abrir_con_filtros_posibles,
    abrir_por_shortname,
    calcular_precipitacion_intervalo,
    color_cape,
    extraer_dataarray_punto,
    extraer_escalar_desde_ds,
    extraer_escalar_isobarico,
    extraer_perfil_isobarico,
    fijar_escala_cape,
    fijar_escala_omega,
    fijar_escala_precipitacion,
    fijar_escala_viento_rafagas,
    interp_perfil,
    leer_tiempo_archivo,
    normalizar_mslp,
    normalizar_porcentaje,
    normalizar_precip_mm_desde_da,
    normalizar_t_kelvin,
    normalizar_velocidad_kt_desde_da,
    normalizar_z500,
)


def sanitize(nombre: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]", "_", nombre)


def abrir_gust(archivo: Path):
    return abrir_con_filtros_posibles(
        archivo,
        [
            {"shortName": "10fg3"},
            {"shortName": "10fg"},
        ],
    )


def main() -> int:
    if len(sys.argv) < 6:
        print(
            "Uso: meteograma_ecmwf_referencia.py "
            "carpeta_gribs carpeta_salidas lat lon nombre_punto"
        )
        return 2

    carpeta_gribs = Path(sys.argv[1])
    carpeta_salidas = Path(sys.argv[2])
    lat = float(sys.argv[3])
    lon = float(sys.argv[4])
    nombre_punto = sys.argv[5]

    carpeta_salidas.mkdir(parents=True, exist_ok=True)

    archivos = sorted(carpeta_gribs.glob("ecmwf_*_mgram_f*.grib2"))
    if not archivos:
        archivos = sorted(carpeta_gribs.glob("*mgram*.grib2"))
    if not archivos:
        raise RuntimeError(f"No se encontraron GRIB ECMWF MGRAM en {carpeta_gribs}")

    niveles_verticales = np.array([1000, 950, 925, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400], dtype=float)

    tiempos = []
    lead_h = []
    mslp_list = []
    z500_list = []
    mucape_list = []
    omega700_list = []
    t2m_list = []
    td2m_list = []
    u10_list = []
    v10_list = []
    gust_list = []
    tp_list = []
    perfiles_t = []
    perfiles_rh = []
    perfiles_u = []
    perfiles_v = []

    for archivo in archivos:
        print(f"\n[ECMWF MGRAM] Procesando {archivo.name}", flush=True)

        tiempo = leer_tiempo_archivo(archivo)
        if tiempo is None:
            print("  [WARN] No se pudo determinar el tiempo válido.")
            continue

        ds_msl = abrir_por_shortname(archivo, "msl")
        ds_tp = abrir_por_shortname(archivo, "tp")
        ds_mucape = abrir_por_shortname(archivo, "mucape")
        ds_2t = abrir_por_shortname(archivo, "2t")
        ds_2d = abrir_por_shortname(archivo, "2d")
        ds_10u = abrir_por_shortname(archivo, "10u")
        ds_10v = abrir_por_shortname(archivo, "10v")
        ds_gust = abrir_gust(archivo)

        ds_gh = abrir_por_shortname(
            archivo, "gh", {"typeOfLevel": "isobaricInhPa"}
        )
        if ds_gh is None:
            ds_gh = abrir_por_shortname(
                archivo, "z", {"typeOfLevel": "isobaricInhPa"}
            )

        ds_w = abrir_por_shortname(
            archivo, "w", {"typeOfLevel": "isobaricInhPa"}
        )
        ds_t = abrir_por_shortname(
            archivo, "t", {"typeOfLevel": "isobaricInhPa"}
        )
        ds_r = abrir_por_shortname(
            archivo, "r", {"typeOfLevel": "isobaricInhPa"}
        )
        ds_u = abrir_por_shortname(
            archivo, "u", {"typeOfLevel": "isobaricInhPa"}
        )
        ds_v = abrir_por_shortname(
            archivo, "v", {"typeOfLevel": "isobaricInhPa"}
        )

        mslp = normalizar_mslp(extraer_escalar_desde_ds(ds_msl, lat, lon))
        z500 = normalizar_z500(extraer_escalar_isobarico(ds_gh, lat, lon, 500))
        mucape = extraer_escalar_desde_ds(ds_mucape, lat, lon)
        omega700 = extraer_escalar_isobarico(ds_w, lat, lon, 700)

        t2m = normalizar_t_kelvin(extraer_escalar_desde_ds(ds_2t, lat, lon))
        td2m = normalizar_t_kelvin(extraer_escalar_desde_ds(ds_2d, lat, lon))
        u10 = extraer_escalar_desde_ds(ds_10u, lat, lon)
        v10 = extraer_escalar_desde_ds(ds_10v, lat, lon)
        gust_kt = normalizar_velocidad_kt_desde_da(
            extraer_dataarray_punto(ds_gust, lat, lon)
        )
        tp = normalizar_precip_mm_desde_da(
            extraer_dataarray_punto(ds_tp, lat, lon)
        )

        lev_t, val_t = extraer_perfil_isobarico(ds_t, lat, lon)
        lev_r, val_r = extraer_perfil_isobarico(ds_r, lat, lon)
        lev_u, val_u = extraer_perfil_isobarico(ds_u, lat, lon)
        lev_v, val_v = extraer_perfil_isobarico(ds_v, lat, lon)

        perfil_t = interp_perfil(lev_t, val_t, niveles_verticales)
        perfil_t = np.where(perfil_t > 100, perfil_t - 273.15, perfil_t)

        perfil_rh = interp_perfil(lev_r, val_r, niveles_verticales)
        perfil_rh = np.array([normalizar_porcentaje(x) for x in perfil_rh])

        perfil_u = interp_perfil(lev_u, val_u, niveles_verticales)
        perfil_v = interp_perfil(lev_v, val_v, niveles_verticales)

        m = re.search(r"_f(\d{3})", archivo.name)
        fh = int(m.group(1)) if m else len(tiempos) * 3

        tiempos.append(pd.to_datetime(tiempo))
        lead_h.append(fh)
        mslp_list.append(mslp)
        z500_list.append(z500)
        mucape_list.append(mucape)
        omega700_list.append(omega700)
        t2m_list.append(t2m)
        td2m_list.append(td2m)
        u10_list.append(u10)
        v10_list.append(v10)
        gust_list.append(gust_kt)
        tp_list.append(tp)
        perfiles_t.append(perfil_t)
        perfiles_rh.append(perfil_rh)
        perfiles_u.append(perfil_u)
        perfiles_v.append(perfil_v)

        print(
            f"  MSLP={mslp:.1f} hPa | Z500={z500:.0f} m | "
            f"MUCAPE={mucape:.0f} J/kg | Omega700={omega700:.3f} Pa/s | "
            f"T2m={t2m:.1f} C | Td2m={td2m:.1f} C | "
            f"GUST={gust_kt:.1f} kt | TPacum={tp:.2f} mm",
            flush=True,
        )

    if not tiempos:
        raise RuntimeError("No se pudieron construir series ECMWF.")

    orden = np.argsort(np.asarray(tiempos, dtype="datetime64[ns]"))
    x = pd.to_datetime(np.asarray(tiempos)[orden])

    df = pd.DataFrame({
        "lead_h": np.asarray(lead_h)[orden],
        "mslp": np.asarray(mslp_list, dtype=float)[orden],
        "z500": np.asarray(z500_list, dtype=float)[orden],
        "mucape": np.asarray(mucape_list, dtype=float)[orden],
        "omega700": np.asarray(omega700_list, dtype=float)[orden],
        "t2m": np.asarray(t2m_list, dtype=float)[orden],
        "td2m": np.asarray(td2m_list, dtype=float)[orden],
        "u10": np.asarray(u10_list, dtype=float)[orden],
        "v10": np.asarray(v10_list, dtype=float)[orden],
        "gust10_kt": np.asarray(gust_list, dtype=float)[orden],
        "tp_acum": np.asarray(tp_list, dtype=float)[orden],
    })

    perfiles_t = np.asarray(perfiles_t, dtype=float)[orden]
    perfiles_rh = np.asarray(perfiles_rh, dtype=float)[orden]
    perfiles_u = np.asarray(perfiles_u, dtype=float)[orden]
    perfiles_v = np.asarray(perfiles_v, dtype=float)[orden]

    df["wind10_kt"] = np.sqrt(df["u10"] ** 2 + df["v10"] ** 2) * 1.94384
    df["tp_intervalo"] = calcular_precipitacion_intervalo(df["tp_acum"].values)

    if len(x) >= 2:
        difs = np.diff(mdates.date2num(x))
        difs = difs[np.isfinite(difs)]
        ancho_barra = max(0.03, float(np.min(difs) * 0.65)) if len(difs) else 0.12
    else:
        ancho_barra = 0.12

    fig, axes = plt.subplots(
        7, 1, figsize=(14, 12), sharex=True,
        gridspec_kw={
            "height_ratios": [4.8, 1.0, 1.35, 1.55, 1.25, 1.0, 1.15],
            "hspace": 0.08,
        },
    )

    fig.suptitle(
        f"Meteograma para {nombre_punto} basado en ECMWF IFS 0.25°",
        fontsize=17, fontweight="bold", y=0.985,
    )

    # 1) Perfil vertical: HR, temperatura y viento
    ax0 = axes[0]
    niveles_hr = [40, 50, 60, 70, 80, 90, 100]
    colores_hr = ["#f3fff3", "#d6ffd6", "#aaffaa", "#6cff6c", "#00e000", "#00a000"]
    cmap_hr = ListedColormap(colores_hr)
    norm_hr = BoundaryNorm(niveles_hr, cmap_hr.N)

    cf = ax0.contourf(
        x, niveles_verticales, perfiles_rh.T,
        levels=niveles_hr, cmap=cmap_hr, norm=norm_hr, extend="max",
    )

    niveles_temp = np.arange(-40, 31, 5)
    try:
        cs_temp = ax0.contour(
            x, niveles_verticales, perfiles_t.T,
            levels=niveles_temp, linewidths=1.0, cmap="cool",
        )
        ax0.clabel(cs_temp, fontsize=8, inline=True, fmt="%d")
    except Exception:
        pass

    try:
        cs0 = ax0.contour(
            x, niveles_verticales, perfiles_t.T,
            levels=[0], colors=["#ff1493"], linewidths=1.5,
        )
        ax0.clabel(cs0, fontsize=8, inline=True, fmt={0: "0"})
    except Exception:
        pass

    paso_t = max(1, len(x) // 35)
    ax0.barbs(
        mdates.date2num(x)[::paso_t],
        niveles_verticales,
        (perfiles_u * 1.94384)[::paso_t, :].T,
        (perfiles_v * 1.94384)[::paso_t, :].T,
        length=5, linewidth=0.45,
    )
    ax0.set_ylim(1000, 400)
    ax0.set_ylabel("Presión\n(hPa)")
    ax0.grid(True, linestyle="--", alpha=0.45)
    ax0.set_title("HR en altura, temperatura y viento", loc="left", fontsize=10)

    cax = fig.add_axes([0.93, 0.66, 0.012, 0.22])
    cbar = plt.colorbar(cf, cax=cax, orientation="vertical")
    cbar.set_label("HR (%)", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    # 2) MSLP + Z500
    ax1 = axes[1]
    ax1.plot(x, df["mslp"], linewidth=1.8, color="#004cff")
    ax1.set_ylabel("SLP\n(hPa)")
    ax1.grid(True, linestyle="--", alpha=0.45)
    ax1b = ax1.twinx()
    ax1b.plot(x, df["z500"], linestyle="--", linewidth=1.3, color="#00bcd4")
    ax1b.set_ylabel("Z500\n(m)")

    # 3) MUCAPE
    ax2 = axes[2]
    colores_cape = [color_cape(v) for v in df["mucape"].values]
    ax2.bar(
        x, df["mucape"], width=ancho_barra * 0.75,
        color=colores_cape, alpha=0.95, edgecolor="white", linewidth=0.3,
    )
    ax2.set_ylabel("MUCAPE\n(J/kg)")
    fijar_escala_cape(ax2, df["mucape"].values)
    ax2.grid(True, linestyle="--", alpha=0.45)
    ax2.legend(
        handles=[
            Patch(facecolor="#8b00a8", label="> 2000"),
            Patch(facecolor="#ff2d2d", label="1500 - 2000"),
            Patch(facecolor="#ff9d00", label="1000 - 1500"),
            Patch(facecolor="#fff000", label="500 - 1000"),
            Patch(facecolor="#1fc83a", label="0 - 500"),
        ],
        loc="upper left", fontsize=6, framealpha=0.85, ncol=5,
    )
    ax2.text(
        0.995, 0.93, "ECMWF: MUCAPE (sin LI nativo en Open Data)",
        transform=ax2.transAxes, ha="right", va="top", fontsize=7,
    )

    # 4) Viento 10 m + ráfagas + barbas
    ax3 = axes[3]
    ax3.bar(
        x, df["gust10_kt"], width=ancho_barra * 0.78,
        color="#f2b66d", alpha=0.55, edgecolor="#c97820",
        linewidth=0.45, label="Ráfaga", zorder=1,
    )
    ax3.plot(
        x, df["wind10_kt"], color="#ff7f00",
        linewidth=1.7, label="Viento 10 m", zorder=4,
    )
    _, franja = fijar_escala_viento_rafagas(
        ax3, df["wind10_kt"].values, df["gust10_kt"].values
    )
    ybarb = np.full(len(df), -franja * 0.48)
    paso_barbas = max(1, len(df) // 32)
    ax3.barbs(
        mdates.date2num(x)[::paso_barbas],
        ybarb[::paso_barbas],
        (df["u10"].values * 1.94384)[::paso_barbas],
        (df["v10"].values * 1.94384)[::paso_barbas],
        length=5.4, linewidth=0.60, color="#5f4a3a",
        pivot="middle", barb_increments={"half": 5, "full": 10, "flag": 50},
        zorder=6, clip_on=True,
    )
    ax3.set_ylabel("Viento / ráfaga\n10 m (kt)")
    ax3.grid(True, linestyle="--", alpha=0.40)
    ax3.legend(loc="upper right", fontsize=7, ncol=2, framealpha=0.85)

    # 5) T2m + Td2m
    ax4 = axes[4]
    ax4.plot(x, df["t2m"], color="#ff0000", linewidth=1.7, label="T 2m")
    ax4.plot(x, df["td2m"], color="#6b3f1d", linestyle="--", linewidth=1.5, label="Td 2m")
    vals = np.concatenate([df["t2m"].values, df["td2m"].values])
    vals = vals[np.isfinite(vals)]
    if len(vals):
        base = float(np.nanmin(vals))
        ax4.fill_between(x, df["td2m"], base - 2, color="#2693ff", alpha=0.85)
        ax4.fill_between(x, df["t2m"], df["td2m"], color="#25e225", alpha=0.65)
    ax4.set_ylabel("Temp\n°C")
    ax4.grid(True, linestyle="--", alpha=0.45)
    ax4.legend(loc="upper right", fontsize=8)

    # 6) Omega 700 hPa
    ax5 = axes[5]
    ax5.plot(x, df["omega700"], color="#004cff", linewidth=1.7)
    ax5.axhline(0, color="#777777", linestyle="--", linewidth=0.9)
    fijar_escala_omega(ax5, df["omega700"].values)
    ax5.set_ylabel("Omega 700\n(Pa/s)")
    ax5.set_title("Velocidad vertical 700 hPa", loc="left", fontsize=9)
    ax5.grid(True, linestyle="--", alpha=0.45)

    # 7) Precipitación por intervalo
    ax6 = axes[6]
    ax6.bar(x, df["tp_intervalo"], width=ancho_barra, color="#00c83a", alpha=0.9)
    ax6.set_ylabel("PP\nmm")
    fijar_escala_precipitacion(ax6, df["tp_intervalo"].values)
    ax6.grid(True, linestyle="--", alpha=0.45)
    ax6.xaxis.set_major_formatter(mdates.DateFormatter("%d%b\n%HZ"))

    for ax in axes[:-1]:
        plt.setp(ax.get_xticklabels(), visible=False)

    salida = carpeta_salidas / f"meteograma_{sanitize(nombre_punto)}.png"
    plt.tight_layout(rect=[0, 0, 0.92, 0.975])
    plt.savefig(salida, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"\n[MGRAM] Meteograma ECMWF generado: {salida.resolve()}", flush=True)

    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
