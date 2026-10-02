#!/usr/bin/env python3
import argparse, json, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

def iso_now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def parse_iso(v): return datetime.fromisoformat(v.replace("Z","+00:00"))
def producto_de(rel): return rel.parts[0] if len(rel.parts)>1 else "Productos"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pedido-id",required=True); p.add_argument("--modelo",required=True)
    p.add_argument("--region",required=True); p.add_argument("--productos",required=True)
    p.add_argument("--salidas",default="salidas"); p.add_argument("--site",required=True)
    p.add_argument("--dias",type=int,default=7); a=p.parse_args()

    salidas=Path(a.salidas); site=Path(a.site); pedidos=site/"pedidos"; pedidos.mkdir(parents=True,exist_ok=True)
    ops=sorted([x for x in salidas.iterdir() if x.is_dir()],key=lambda x:x.stat().st_mtime,reverse=True)
    if not ops: raise SystemExit("No se encontro una carpeta de salida generada")
    origen=ops[0]; destino=pedidos/a.pedido_id
    if destino.exists(): shutil.rmtree(destino)
    productos_dest=destino/"productos"; shutil.copytree(origen,productos_dest)

    archivos=[]
    for f in sorted(productos_dest.rglob("*.png")):
        rel=f.relative_to(productos_dest)
        archivos.append({"nombre":f.name,"ruta":rel.as_posix(),"producto":producto_de(rel)})

    creado=iso_now()
    catalogo={"id":a.pedido_id,"creado":creado,"modelo":a.modelo,"region":a.region,"productos":a.productos,"archivos":archivos}
    destino.mkdir(parents=True,exist_ok=True)
    (destino/"catalogo.json").write_text(json.dumps(catalogo,ensure_ascii=False,indent=2),encoding="utf-8")
    (destino/"metadata.json").write_text(json.dumps({k:catalogo[k] for k in ("id","creado","modelo","region","productos")},ensure_ascii=False,indent=2),encoding="utf-8")

    limite=datetime.now(timezone.utc)-timedelta(days=a.dias)
    for carpeta in list(pedidos.iterdir()):
        if not carpeta.is_dir(): continue
        try:
            data=json.loads((carpeta/"metadata.json").read_text(encoding="utf-8"))
            if parse_iso(data["creado"])<limite: shutil.rmtree(carpeta)
        except Exception: pass

    historial=[]
    for carpeta in pedidos.iterdir():
        meta=carpeta/"metadata.json"
        if meta.exists():
            try: historial.append(json.loads(meta.read_text(encoding="utf-8")))
            except Exception: pass
    historial.sort(key=lambda x:x.get("creado",""),reverse=True)

    (site/"catalogo.json").write_text(json.dumps({"actualizado":iso_now(),"retencion_dias":a.dias,"pedidos":historial},ensure_ascii=False,indent=2),encoding="utf-8")
    (site/".nojekyll").write_text("",encoding="utf-8")
    links="\n".join(f'<li><a href="pedidos/{x["id"]}/catalogo.json">{x["id"]}</a> — {x.get("modelo","")} — {x.get("region","")}</li>' for x in historial)
    (site/"index.html").write_text(f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Productos meteorologicos</title></head><body><h1>Productos meteorologicos publicados</h1><p>Retencion: {a.dias} dias.</p><ul>{links}</ul></body></html>',encoding="utf-8")
    print(f"Publicado {a.pedido_id}: {len(archivos)} PNG; pedidos conservados: {len(historial)}")

if __name__=="__main__": main()
