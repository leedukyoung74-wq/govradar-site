// Offline semantic test for GOV RADAR inline anonymous-nav gate.
// No network, customer form submission, paid API or website publication.
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const source=fs.readFileSync('build.py','utf8');
const match=source.match(/_GATE\s*=\s*r"""([\s\S]*?)"""/);
assert.ok(match,'shared gate source found');
const script=match[1].replace(/^<script>/,'').replace(/<\/script>$/,'');
function check(path,lang,search='',hash=''){
  let redirect=null,opened=false;
  const location={pathname:path,search,hash,replace:(v)=>{redirect=v;}};
  const document={documentElement:{lang},addEventListener:()=>{opened=true;}};
  const localStorage={getItem:()=>null};
  vm.runInNewContext(script,{location,document,localStorage}, {timeout:750});
  return {redirect,opened};
}
const publicRoutes=['/ko/thanks/','/ko/consortium/thanks/','/en/pricing/','/ko/pricing/',
  '/es/how/','/fr/request/','/ar/consortium/','/vi/legal/refund/',
  '/id/membership/','/ko/help/','/en/help/','/ko/solutions/','/en/contracts/',
  '/ko/ready/','/ko/about/','/ko/verify/'];
for(const path of publicRoutes){
  const lang=path.split('/')[1];
  assert.equal(check(path,lang).redirect,null,'must show anonymous customer page: '+path);
}
assert.equal(check('/ko/vietnam/','ko').redirect,'/map/');
assert.equal(check('/en/united-states/','en').redirect,'/map/en/');
assert.equal(check('/ko/account/','ko','?auth=login').redirect,null);
assert.equal(check('/ko/pricing/','ko','?stay=1').redirect,null);
assert.equal(check('/ko/pricing/','ko','', '#access_token=TEST-NO-SECRET').redirect,null);
console.log('PASS: anonymous help/quote/confirmation pages stay accessible; protected country routing unchanged');
