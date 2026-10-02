const form=document.getElementById("pedidoForm"),modo=document.getElementById("modoCorrida"),mensaje=document.getElementById("mensaje");
const v=id=>document.getElementById(id).value;
const n=id=>v(id)===""?null:Number(v(id));

modo.addEventListener("change",()=>document.querySelectorAll(".manual").forEach(el=>el.classList.toggle("hidden",modo.value!=="MANUAL")));

form.addEventListener("submit",async e=>{
  e.preventDefault(); mensaje.classList.add("hidden");
  const productos=[...document.querySelectorAll('input[name="producto"]:checked')].map(x=>x.value);
  const payload={modelo:v("modelo"),productos,nombreRegion:v("nombreRegion"),norte:n("norte"),sur:n("sur"),oeste:n("oeste"),este:n("este"),nombrePunto:v("nombrePunto"),latPunto:n("latPunto"),lonPunto:n("lonPunto"),fInicio:n("fInicio"),fFin:n("fFin"),salto:n("salto"),modoCorrida:v("modoCorrida"),fecha:v("fecha"),ciclo:v("ciclo")};
  try{
    const r=await fetch("/api/pedidos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const data=await r.json(); if(!r.ok)throw new Error(data.error||"No se pudo crear el pedido");
    location.href="/pedido/"+encodeURIComponent(data.id);
  }catch(err){mensaje.textContent=err.message;mensaje.classList.remove("hidden")}
});

async function cargarHistorial(){
  const box=document.getElementById("historial");
  try{
    const r=await fetch("/api/pedidos/historial"); if(!r.ok)throw new Error();
    const data=await r.json(),pedidos=data.pedidos||[];
    if(!pedidos.length){box.textContent="Todavia no hay pedidos publicados.";return}
    box.innerHTML=pedidos.map(p=>`<div class="history-item"><div><strong>${p.id}</strong><br><small>${p.modelo||""} · ${p.region||""} · ${p.creado||""}</small></div><a href="/pedido/${encodeURIComponent(p.id)}">Ver productos</a></div>`).join("");
  }catch{box.textContent="El historial estara disponible despues del primer pedido publicado."}
}
cargarHistorial();
