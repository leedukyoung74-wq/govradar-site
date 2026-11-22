/* WMM v1.3 - 국토교통부 VWorld 영상지도. Google/외부 유료 지도 호출 없음.
   공개 서비스용 브이월드 WMTS API(무료, 출처표시). 키/도메인 등록이 있어야 네트워크 요청 발생.
   지도가 로드되지 않더라도 기존 SVG 지도 및 공고 목록은 항상 이용 가능.
 */
(()=>{'use strict';
const MERC_MAX = 85.05112878;
const tileSize = 256;
function clamp(n, a, b){return Math.max(a,Math.min(b,n));}
function world(lat,lng,z){
  const scale=tileSize*Math.pow(2,z);
  const x=(lng+180)/360*scale;
  const rad=clamp(lat,-MERC_MAX,MERC_MAX)*Math.PI/180;
  const y=(1-Math.log(Math.tan(rad)+1/Math.cos(rad))/Math.PI)/2*scale;
  return [x,y];
}
function unworld(x,y,z){
  const scale=tileSize*Math.pow(2,z);
  const lng=x/scale*360-180;
  const n=Math.PI-2*Math.PI*y/scale;
  const lat=180/Math.PI*Math.atan(Math.sinh(n));
  return [lat,lng];
}
const validation=/^[A-Za-z0-9_-]{6,200}$/;
class Satellite{
  constructor(host,opt){
    if(opt.endpoint!=='/api/wmm/tiles')throw new Error('지도 서버 설정을 확인하세요');
    this.showCounts=opt.showCounts!==false;this.endpoint=opt.endpoint;this.pending=new AbortController();this.objectUrls=[]; this.host=host;this.regions=opt.regions||[];
    this.onSelect=opt.onSelect||(()=>{});
    this.zoom=clamp(opt.zoom||7,6,17);
    this.center=[36.65,127.65];this.active=true;
    this.counts=[];this.tileFailures=0;
    this.host.replaceChildren();
    const stage=document.createElement('div');stage.className='wr-vworld-stage';stage.tabIndex=0;
    stage.setAttribute('role','application');stage.setAttribute('aria-label','브이월드 대한민국 항공 영상지도. 마우스 휠 또는 확대 축소 버튼으로 이동');
    this.stage=stage;
    const tiles=document.createElement('div');tiles.className='wr-vworld-tiles';this.tiles=tiles;
    const pins=document.createElement('div');pins.className='wr-vworld-pins';this.pins=pins;
    const attribution=document.createElement('div');attribution.className='wr-vworld-attrib';
    attribution.textContent='영상지도 제공: 국토교통부 · 브이월드 | 출처 표시';
    stage.append(tiles,pins,attribution);this.host.append(stage);
    this.onWheel=(ev)=>{ev.preventDefault();this.changeZoom(ev.deltaY<0?1:-1)};
    stage.addEventListener('wheel',this.onWheel,{passive:false});
    this.onKey=(ev)=>{if(ev.key==='+'||ev.key==='='){ev.preventDefault();this.changeZoom(1)}if(ev.key==='-'){ev.preventDefault();this.changeZoom(-1)}};
    stage.addEventListener('keydown',this.onKey);
    stage.addEventListener('keydown',ev=>{const deltas={ArrowUp:[-64,0],ArrowDown:[64,0],ArrowLeft:[0,-64],ArrowRight:[0,64]};if(!deltas[ev.key])return;ev.preventDefault();const [dy,dx]=deltas[ev.key];const [cx,cy]=world(...this.center,this.zoom);const [lat,lng]=unworld(cx+dx,cy+dy,this.zoom);this.center=[clamp(lat,32,40),clamp(lng,123,132.5)];this.render();});
    this.pointer=null;
    stage.addEventListener('pointerdown',ev=>{if(ev.target.closest('button'))return;this.pointer={x:ev.clientX,y:ev.clientY,center:[...this.center],id:ev.pointerId};stage.setPointerCapture?.(ev.pointerId)});
    stage.addEventListener('pointermove',ev=>{if(!this.pointer||ev.pointerId!==this.pointer.id)return;
      const dx=ev.clientX-this.pointer.x,dy=ev.clientY-this.pointer.y;
      this.tiles.style.transform=`translate(${dx}px,${dy}px)`;
      this.pins.style.transform=`translate(${dx}px,${dy}px)`;});
    this.pointerUp=ev=>{if(!this.pointer||ev.pointerId!==this.pointer.id)return;
      const dx=ev.clientX-this.pointer.x,dy=ev.clientY-this.pointer.y;
      const [cx,cy]=world(this.pointer.center[0],this.pointer.center[1],this.zoom);
      const [lat,lng]=unworld(cx-dx,cy-dy,this.zoom);
      this.pointer=null;this.center=[clamp(lat,32,40),clamp(lng,123,132.5)];
      this.tiles.style.transform='';this.pins.style.transform='';this.render();};
    stage.addEventListener('pointerup',this.pointerUp);stage.addEventListener('pointercancel',this.pointerUp);
    this.resize=()=>{if(this.active)this.render()};
    if(typeof ResizeObserver!=='undefined'){this.observer=new ResizeObserver(this.resize);this.observer.observe(stage)}
    this.onLock=()=>this.destroy();window.addEventListener('wmm:auth-locked',this.onLock);
    this.render();
  }
  updateMarkers(arr){this.counts=Array.isArray(arr)?arr:[];this.drawPins();}
  changeZoom(delta){this.zoom=clamp(this.zoom+delta,6,17);this.render();}
  focus(name){const info=this.regions.find(x=>x[0]===name);if(!info)return;this.center=[info[1],info[2]];this.zoom=9;this.render();}
  reset(){this.center=[36.65,127.65];this.zoom=7;this.render();}
  render(){if(!this.active)return;this.pending.abort();this.pending=new AbortController();this.objectUrls.forEach(u=>URL.revokeObjectURL(u));this.objectUrls=[];const signal=this.pending.signal;const w=this.stage.clientWidth||580,h=this.stage.clientHeight||600;
    const [cx,cy]=world(this.center[0],this.center[1],this.zoom);
    const originX=cx-w/2,originY=cy-h/2;
    const x0=Math.floor(originX/tileSize),y0=Math.floor(originY/tileSize),
      x1=Math.ceil((originX+w)/tileSize),y1=Math.ceil((originY+h)/tileSize);
    const max=Math.pow(2,this.zoom);
    const fragment=document.createDocumentFragment();
    for(let x=x0;x<x1;x++)for(let y=y0;y<y1;y++){
      if(x<0||y<0||x>=max||y>=max)continue;
      const im=document.createElement('img');
      im.alt='';im.loading='lazy';im.decoding='async';im.className='wr-vworld-tile';
      im.style.left=Math.round(x*tileSize-originX)+'px';im.style.top=Math.round(y*tileSize-originY)+'px';
      // VWorld WMTS 행/열 순서가 z/y/x임에 유의
      const url=this.endpoint+'?z='+this.zoom+'&y='+y+'&x='+x;
      (async()=>{try{
        const token=await window.WMM_AUTH_GET_TOKEN?.();
        if(!token||signal.aborted)return;
        const response=await fetch(url,{signal,headers:{Authorization:'Bearer '+token}});
        if(response.status===401){window.dispatchEvent(new Event('wmm:auth-expired'));return;}
        if(!response.ok)throw Error('tile');
        if(!/^image\/(jpeg|png)(?:;|$)/i.test(response.headers.get('content-type')||''))throw Error('non_image_tile');
        const blob=await response.blob();if(blob.size>1200000)throw Error('tile_size');if(signal.aborted)return;
        const objectUrl=URL.createObjectURL(blob);this.objectUrls.push(objectUrl);im.src=objectUrl;
      }catch(e){if(e.name!=='AbortError'&&!signal.aborted)im.dispatchEvent(new Event('error'));}})();
      im.addEventListener('error',()=>{if(this.active&&++this.tileFailures===3)this.host.dispatchEvent(new CustomEvent('wmm:tile-error'));});
      fragment.append(im);
    }
    this.tiles.replaceChildren(fragment);this.drawPins();
  }
  drawPins(){if(!this.active)return;
    const [cx,cy]=world(this.center[0],this.center[1],this.zoom);
    const w=this.stage.clientWidth||580,h=this.stage.clientHeight||600;
    const f=document.createDocumentFragment();
    const placed=[];for(const info of this.counts){
      const [x,y]=world(info.lat,info.lng,this.zoom);
      const left=x-cx+w/2,top=y-cy+h/2;
      if(left < -50||top < -50||left > w+50||top > h+50)continue;
      const pin=document.createElement('button');pin.type='button';
      pin.className='wr-geo-pin'+(info.selected?' wr-geo-pin-selected':'');
      let px=left,py=top,found=false;for(let ring=0;ring<15&&!found;ring++){const steps=ring?16:1;for(let i=0;i<steps;i++){const angle=i*Math.PI*2/steps,X=clamp(left+Math.cos(angle)*ring*12,23,w-23),Y=clamp(top+Math.sin(angle)*ring*12,23,h-23);if(placed.every(([a,b])=>Math.hypot(a-X,b-Y)>=47)){px=X;py=Y;found=true;break}}}if(!found)continue;placed.push([px,py]);
      pin.style.left=Math.round(px-22)+'px';pin.style.top=Math.round(py-22)+'px';
      pin.setAttribute('aria-label',this.showCounts?`${info.name} 지원사업 ${info.count}건`:`${info.name} · 지역 선택`);
      const name=document.createElement('span');name.textContent=info.name;
      const num=document.createElement('b');num.textContent=String(info.count);
      pin.append(name);if(this.showCounts)pin.append(num);pin.addEventListener('click',()=>this.onSelect(info.name));f.append(pin);
    }
    this.pins.replaceChildren(f);
  }
  destroy(){window.removeEventListener('wmm:auth-locked',this.onLock);this.active=false;this.pending.abort();this.objectUrls.forEach(u=>URL.revokeObjectURL(u));this.observer?.disconnect();this.stage.removeEventListener('wheel',this.onWheel);this.stage.removeEventListener('keydown',this.onKey);this.stage.removeEventListener('pointerup',this.pointerUp);this.stage.removeEventListener('pointercancel',this.pointerUp);this.host.replaceChildren();}
}
window.WMMFreeSatellite=Object.freeze({create:(host,opt)=>new Satellite(host,opt),world,unworld});
})();
