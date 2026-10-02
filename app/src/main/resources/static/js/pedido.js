const pedidoId=document.body.dataset.pedidoId,pagesBase=document.body.dataset.pagesBase.replace(/\/$/,"");
let grupos={},grupoActual="",indice=0,timer=null;
const estado=document.getElementById("estado"),mensaje=document.getElementById("mensaje"),dot=document.getElementById("statusDot"),visor=document.getElementById("visorCard"),errorCard=document.getElementById("errorCard");

async function consultar(){
  try{
    const r=await fetch("/api/pedidos/"+encodeURIComponent(pedidoId));
    if(r.status===404){
      const prod=await fetch("/api/pedidos/"+encodeURIComponent(pedidoId)+"/productos");
      if(prod.ok){estado.textContent="FINALIZADO";dot.className="status-dot ok";await cargarProductos();return}
      throw new Error("Pedido no encontrado");
    }
    const p=await r.json(); estado.textContent=p.estado; mensaje.textContent=p.mensaje||"";
    dot.className="status-dot "+(p.estado==="FINALIZADO"?"ok":p.estado==="ERROR"?"error":"running");
    if(p.estado==="FINALIZADO"){await cargarProductos();return}
    if(p.estado==="ERROR"){errorCard.classList.remove("hidden");document.getElementById("errorDetalle").textContent=p.mensaje||"Error de generacion";return}
    setTimeout(consultar,4000);
  }catch(e){mensaje.textContent=e.message;setTimeout(consultar,5000)}
}

async function cargarProductos(){
  const r=await fetch("/api/pedidos/"+encodeURIComponent(pedidoId)+"/productos");
  if(!r.ok){mensaje.textContent="Generacion finalizada. Esperando publicacion de productos...";setTimeout(cargarProductos,3000);return}
  const data=await r.json();
  document.getElementById("resumenPedido").textContent=`${data.modelo||""} · ${data.region||""} · ${data.productos||""}`;
  grupos={}; (data.archivos||[]).forEach(a=>{const g=a.producto||"Productos";(grupos[g]||=[]).push(a)});
  const select=document.getElementById("productoSelect");
  select.innerHTML=Object.keys(grupos).map(g=>`<option>${g}</option>`).join("");
  grupoActual=select.value; indice=0;
  select.addEventListener("change",()=>{grupoActual=select.value;indice=0;mostrar()});
  document.getElementById("prevBtn").onclick=()=>mover(-1);
  document.getElementById("nextBtn").onclick=()=>mover(1);
  document.getElementById("playBtn").onclick=loop;
  visor.classList.remove("hidden"); mostrar();
}
function mover(d){const a=grupos[grupoActual]||[];if(!a.length)return;indice=(indice+d+a.length)%a.length;mostrar()}
function mostrar(){const a=grupos[grupoActual]||[];if(!a.length)return;const x=a[indice];document.getElementById("productoImg").src=pagesBase+"/pedidos/"+encodeURIComponent(pedidoId)+"/productos/"+x.ruta.split("/").map(encodeURIComponent).join("/");document.getElementById("archivoActual").textContent=x.nombre}
function loop(){const b=document.getElementById("playBtn");if(timer){clearInterval(timer);timer=null;b.textContent="▶ Loop";return}timer=setInterval(()=>mover(1),900);b.textContent="■ Detener"}
consultar();
