/* ==== JAH deterministic product-cover engine — signature-cyber-mega-mall ====
   Zero storage, pure client-side SVG. (id, title, dept) -> PC-screen cover:
   the tool/app shown running on a PC monitor, per Manon's exact ask.
   ID hash -> palette (8 palettes); hash -> on-screen UI layout (4 layouts).
   Covers.svg({id,title,sub,dept,wide}) -> inline SVG string.
   Covers.thumb({id,title,sub,dept})    -> lazy placeholder <span>.
   Covers.lazy(scopeEl)                 -> IntersectionObserver fill for [data-cov]. */
(function(){
"use strict";
function xmur3(str){var h=1779033703^str.length;for(var i=0;i<str.length;i++){h=Math.imul(h^str.charCodeAt(i),3432918353);h=h<<13|h>>>19;}return function(){h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^=h>>>16)>>>0;};}
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function wrap(t,n){var w=String(t||"Untitled product").split(/\s+/),L=[],c="",i;for(i=0;i<w.length;i++){if((c+" "+w[i]).trim().length>n){if(c)L.push(c);c=w[i];}else c=(c+" "+w[i]).trim();}if(c)L.push(c);return L.slice(0,2);}
/* [bgTop,bgBot,screenBg,accent,accent2,ink] */
var PALS=[
 ["#141b2e","#080b14","#0e1830","#57d0e6","#9fc2ff","#eef4ff"],
 ["#1c1430","#0b0812","#180f2e","#c98aff","#f0d4ff","#f6eefb"],
 ["#14261a","#08110b","#0f2418","#7CFC00","#d6ff9e","#f0f7e6"],
 ["#2a1a14","#120b08","#2c1c10","#ff9f43","#ffd8a8","#faf3e3"],
 ["#241318","#100709","#2e1220","#ff7ab8","#ffc4dd","#fbeef3"],
 ["#12242a","#081014","#0e2230","#8ad8d8","#d2f4f4","#eef7f7"],
 ["#1f1a10","#0f0c06","#241c0e","#ffd166","#fff3c4","#fbf6e6"],
 ["#161d26","#090d12","#101c2c","#ff7a1a","#ffb300","#f2ede2"]
];
function palFor(id){return PALS[xmur3(String(id))()%PALS.length];}
function bars(x,y,w,n,hgt,c1,c2,rnd){
  var s="",i,bw=w/n;for(i=0;i<n;i++){var hh=10+rnd()%(hgt-10);s+='<rect x="'+(x+i*bw+2)+'" y="'+(y+hgt-hh)+'" width="'+(bw-4)+'" height="'+hh+'" rx="2" fill="'+(i%2?c2:c1)+'" opacity="0.85"/>';}return s;
}
function cardGrid(x,y,w,n,c1,c2,rnd){
  var s="",i,gw=w/3;for(i=0;i<n&&i<6;i++){var cx=x+(i%3)*gw,cy=y+Math.floor(i/3)*54;
    s+='<rect x="'+(cx+3)+'" y="'+cy+'" width="'+(gw-6)+'" height="48" rx="5" fill="'+c1+'" opacity="0.28"/>';
    s+='<rect x="'+(cx+8)+'" y="'+(cy+6)+'" width="'+(gw-26)+'" height="10" rx="2" fill="'+c2+'" opacity="0.8"/>';
    s+='<rect x="'+(cx+8)+'" y="'+(cy+21)+'" width="'+(gw-16)+'" height="5" rx="2" fill="'+c1+'" opacity="0.5"/>';
    s+='<rect x="'+(cx+8)+'" y="'+(cy+30)+'" width="'+(gw-30)+'" height="5" rx="2" fill="'+c1+'" opacity="0.35"/>';}return s;
}
function textLines(x,y,w,n,c1,rnd){
  var s="",i;for(i=0;i<n;i++){var lw=w*(0.55+rnd()*0.4);s+='<rect x="'+x+'" y="'+(y+i*13)+'" width="'+lw+'" height="6" rx="3" fill="'+c1+'" opacity="'+(0.35+rnd()*0.3)+'"/>';}return s;
}
function svg(o){
  o=o||{};var id=String(o.id||"?"),title=o.title||"Untitled product";
  var pal=palFor(id),h=xmur3(id+"::cov")(),rnd=xmur3(id+"::ui");
  var W=320,H=o.wide?300:300;
  var s='<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PC-screen cover art for '+esc(title)+'">';
  s+='<defs><linearGradient id="mbg'+(h%999983)+'" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="'+pal[0]+'"/><stop offset="1" stop-color="'+pal[1]+'"/></linearGradient>'
    +'<linearGradient id="scr'+(h%999983)+'" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="'+pal[2]+'"/><stop offset="1" stop-color="'+pal[1]+'"/></linearGradient></defs>';
  s+='<rect width="'+W+'" height="'+H+'" fill="url(#mbg'+(h%999983)+')"/>';
  var lines=wrap(title,22),ty=26;
  lines.forEach(function(ln,i){s+='<text x="'+(W/2)+'" y="'+(ty+i*22)+'" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-weight="bold" font-size="19" fill="'+pal[5]+'">'+esc(ln)+'</text>';});
  /* monitor */
  var mx=34,my=64,mw=W-68,mh=H-128;
  s+='<ellipse cx="'+(W/2)+'" cy="'+(my+mh+34)+'" rx="'+(mw*0.32)+'" ry="8" fill="#000" opacity="0.5"/>';
  s+='<rect x="'+(W/2-14)+'" y="'+(my+mh)+'" width="28" height="22" fill="#1a2233"/>';
  s+='<rect x="'+(W/2-58)+'" y="'+(my+mh+20)+'" width="116" height="10" rx="5" fill="#1a2233" stroke="'+pal[3]+'" stroke-width="1"/>';
  s+='<rect x="'+mx+'" y="'+my+'" width="'+mw+'" height="'+mh+'" rx="8" fill="#0a0e18" stroke="'+pal[3]+'" stroke-width="2"/>';
  var sx=mx+7,sy=my+7,sw=mw-14,sh=mh-14;
  s+='<rect x="'+sx+'" y="'+sy+'" width="'+sw+'" height="'+sh+'" rx="4" fill="url(#scr'+(h%999983)+')"/>';
  /* title bar with the product name */
  s+='<rect x="'+sx+'" y="'+sy+'" width="'+sw+'" height="22" rx="4" fill="'+pal[3]+'" opacity="0.9"/>';
  s+='<circle cx="'+(sx+12)+'" cy="'+(sy+11)+'" r="4" fill="#ff5f57"/><circle cx="'+(sx+26)+'" cy="'+(sy+11)+'" r="4" fill="#febc2e"/><circle cx="'+(sx+40)+'" cy="'+(sy+11)+'" r="4" fill="#28c840"/>';
  var nm=title.length>24?title.slice(0,24)+"…":title;
  s+='<text x="'+(sx+52)+'" y="'+(sy+15.5)+'" font-family="Arial,sans-serif" font-weight="bold" font-size="11" fill="#0a0e18">'+esc(nm)+'</text>';
  /* screen glow */
  s+='<rect x="'+sx+'" y="'+sy+'" width="'+sw+'" height="'+sh+'" rx="4" fill="'+pal[3]+'" opacity="0.06"/>';
  /* deterministic app UI layout */
  var bx=sx+10,by=sy+32,bw=sw-20,bh=sh-42,lay=h%4;
  s+='<rect x="'+bx+'" y="'+by+'" width="34" height="'+bh+'" rx="4" fill="'+pal[3]+'" opacity="0.22"/>';
  var k;for(k=0;k<4;k++){s+='<rect x="'+(bx+7)+'" y="'+(by+8+k*20)+'" width="20" height="12" rx="3" fill="'+pal[3]+'" opacity="'+(k===h%4?0.95:0.45)+'"/>';}
  var cx2=bx+42;
  if(lay===0){s+=bars(cx2,by+10,bw-52,8,bh-40,pal[3],pal[4],rnd);}
  else if(lay===1){s+=cardGrid(cx2,by+6,bw-52,6,pal[3],pal[4],rnd);}
  else if(lay===2){s+=textLines(cx2,by+12,bw-60,7,pal[4],rnd);s+='<rect x="'+cx2+'" y="'+(by+bh-26)+'" width="86" height="18" rx="9" fill="'+pal[3]+'"/><text x="'+(cx2+43)+'" y="'+(by+bh-13)+'" text-anchor="middle" font-family="Arial,sans-serif" font-weight="bold" font-size="10" fill="#0a0e18">RUN</text>';}
  else{s+='<circle cx="'+(cx2+(bw-52)/2)+'" cy="'+(by+bh/2)+'" r="'+(bh*0.3)+'" fill="none" stroke="'+pal[3]+'" stroke-width="5"/><circle cx="'+(cx2+(bw-52)/2)+'" cy="'+(by+bh/2)+'" r="'+(bh*0.16)+'" fill="'+pal[4]+'" opacity="0.85"/>';s+=textLines(cx2,by+bh-22,bw-60,1,pal[4],rnd);}
  /* ID stamp badge */
  var idt=id.length>24?id.slice(0,24)+"…":id,bw2=8+idt.length*8.2;
  s+='<rect x="10" y="'+(H-32)+'" width="'+bw2+'" height="23" rx="11.5" fill="#000" opacity="0.62"/>'
    +'<rect x="10" y="'+(H-32)+'" width="'+bw2+'" height="23" rx="11.5" fill="none" stroke="'+pal[3]+'" stroke-width="1.2"/>'
    +'<text x="'+(10+bw2/2)+'" y="'+(H-16)+'" text-anchor="middle" font-family="ui-monospace,Menlo,Consolas,monospace" font-size="12" fill="'+pal[4]+'">'+esc(idt)+'</text>';
  if(o.dept){var dd=String(o.dept).toUpperCase().slice(0,14);
    s+='<text x="'+(W-12)+'" y="'+(H-15)+'" text-anchor="end" font-family="Arial,sans-serif" font-size="11" letter-spacing="1" fill="'+pal[5]+'" opacity="0.75">'+esc(dd)+'</text>';}
  s+='</svg>';return s;
}
function thumb(o){
  return '<span class="covthumb" data-cov="1" data-cov-id="'+esc(o.id||"")+'" data-cov-title="'+esc(o.title||"")+'" data-cov-sub="'+esc(o.sub||"")+'" data-cov-dept="'+esc(o.dept||"")+'"><span class="covph" aria-hidden="true">▣</span></span>';
}
function fill(el){
  if(!el||el.getAttribute("data-cov-done"))return;
  el.setAttribute("data-cov-done","1");
  try{el.innerHTML=svg({id:el.getAttribute("data-cov-id"),title:el.getAttribute("data-cov-title"),sub:el.getAttribute("data-cov-sub"),dept:el.getAttribute("data-cov-dept")});}
  catch(e){el.innerHTML='<span class="covph">▣</span>';}
}
function lazy(scope){
  var root=scope||document;
  var els=root.querySelectorAll?root.querySelectorAll('[data-cov="1"]:not([data-cov-done])'):[];
  if(!els.length)return;
  if(typeof IntersectionObserver==="undefined"){for(var i=0;i<els.length;i++)fill(els[i]);return;}
  if(!lazy._io){lazy._io=new IntersectionObserver(function(es){for(var j=0;j<es.length;j++){if(es[j].isIntersecting){fill(es[j].target);lazy._io.unobserve(es[j].target);}}},{rootMargin:"240px"});}
  for(var i=0;i<els.length;i++)lazy._io.observe(els[i]);
}
window.Covers={svg:svg,thumb:thumb,lazy:lazy,fill:fill};
})();
