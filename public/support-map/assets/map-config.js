/* Runtime capability only; VWorld credential stays in server Secrets. */
window.WMM_FREE_MAP_CONFIG=Object.freeze({provider:'vworld',tileEndpoint:'/api/wmm/tiles',enabled:window.WMM_RUNTIME_MAP_CONFIG?.enabled===true,startOnLoad:window.WMM_RUNTIME_MAP_CONFIG?.enabled===true,initialZoom:7,attribution:'© 국토교통부 · 브이월드'});
window.WMM_MAPS_CONFIG=Object.freeze({approved:false,apiKey:'',startOnLoad:false});
