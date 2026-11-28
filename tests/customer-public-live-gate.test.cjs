// Offline, no-post, first-time-visitor test for deployed HTML candidate.
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const locales=['ko','en','es','fr','ar','vi','id'];
const routes=['thanks','consortium/thanks','pricing','how','request','consortium'];
let checked=0,redirectPages=0;
for(const locale of locales){
  for(const route of routes){
    const path='public/'+locale+'/'+route+'/index.html';
    const html=fs.readFileSync(path,'utf8');
    const found=html.match(/<script>\(function\(\)\{try\{var q=location\.search,[\s\S]*?<\/script>/);
    if(!found){
      // Four non-English pricing and request pages deliberately redirect to
      // English request/pricing pages; those must NEVER appear as successful
      // translated support journeys.
      assert.ok(/http-equiv="refresh"/i.test(html),path+': neither gate nor declared redirect');
      assert.ok(html.includes('location.replace("/en/'),path+': unusual redirect target');
      redirectPages++; continue;
    }
    const script=found[0].slice('<script>'.length,-'</script>'.length);
    let wentTo=null;
    const location={pathname:'/'+locale+'/'+route+'/',search:'',hash:'',
       replace:(target)=>{wentTo=target;}};
    const document={documentElement:{lang:locale},addEventListener:()=>{}};
    const localStorage={getItem:()=>null};
    vm.runInNewContext(script,{location,document,localStorage},{timeout:750});
    assert.equal(wentTo,null,path+': anonymous customer redirected away');
    checked++;
  }
}
assert.ok(checked>=30,'expected public pages to be tested');
assert.equal(redirectPages,8,'expected exactly eight existing English fallbacks');
console.log('PASS: '+checked+' public customer pages accessible without login; '+redirectPages+' documented redirects.');
