import test from "node:test";
import assert from "node:assert/strict";
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from "node:fs";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {auditForms} from "../scripts/wmm_form_routes_audit.mjs";

const languages=["ko","en","es","fr","ar","vi","id"];
function fixture(run){
  const root=mkdtempSync(join(tmpdir(),"wmm-form-routes-"));
  function put(lang,subpath,html){
    const parent=join(root,lang,...subpath.split("/").filter(Boolean));
    mkdirSync(parent,{recursive:true});
    writeFileSync(join(parent,"index.html"),html);
  }
  try {
    for(const lang of languages){
      put(lang,"","<!doctype html><title>ok</title>");
      put(lang,"thanks","<!doctype html><title>Thanks</title>");
      put(lang,"consortium/thanks","<!doctype html><title>Thanks</title>");
      put(lang,"request",'<form name="order" method="POST" data-netlify="true" action="/nfform?next=/' +lang+'/thanks/"><input type="hidden" name="form-name" value="order"><input name="email"></form>');
    }
    return run({root,put});
  }finally{rmSync(root,{recursive:true,force:true});}
}

test("all seven localized forms have real same-language confirmation pages",()=>{
  fixture(({root})=>{
    const audit=auditForms(root);
    assert.equal(audit.forms,7);
    assert.deepEqual(audit.problems,[]);
    assert.deepEqual(audit.names,["order"]);
    assert.equal(audit.productionSubmissionVerified,false);
  });
});

test("misdirected cross-language response URL is rejected",()=>{
  fixture(({root,put})=>{
    put("ko","request",'<form name="order" method="POST" data-netlify="true" action="/nfform?next=/en/thanks/"><input name="form-name" value="order"></form>');
    assert.ok(auditForms(root).problems.some(x=>x.issue==="UNSAFE_OR_INCORRECT_NEXT"));
  });
});

test("missing hidden form-name fields prevent false positives",()=>{
  fixture(({root,put})=>{
    put("ko","request",'<form name="order" method="POST" data-netlify="true" action="/nfform?next=/ko/thanks/"></form>');
    assert.ok(auditForms(root).problems.some(x=>x.issue==="FORM_NAME_HIDDEN_MISMATCH"));
  });
});

test("non-POST forms are flagged",()=>{
  fixture(({root,put})=>{
    put("ko","request",'<form name="order" method="GET" data-netlify="true" action="/nfform?next=/ko/thanks/"><input name="form-name" value="order"></form>');
    assert.ok(auditForms(root).problems.some(x=>x.issue==="FORM_NOT_POST"));
  });
});

test("legacy consortium confirmation is kept",()=>{
  fixture(({root,put})=>{
    put("ko","request",'<form name="order" method="POST" data-netlify="true" action="/nfform?next=/ko/consortium/thanks/"><input name="form-name" value="order"></form>');
    assert.equal(auditForms(root).problems.length,0);
    put("ko","request",'<form name="order" method="POST" data-netlify="true" action="/nfform?next=/ko/other/thanks/"><input name="form-name" value="order"></form>');
    assert.ok(auditForms(root).problems.some(x=>x.issue==="UNSAFE_OR_INCORRECT_NEXT"));
  });
});

test("missing localized homepages are detected",()=>{
  const root=mkdtempSync(join(tmpdir(),"wmm-form-missing-"));
  try{
    const a=auditForms(root);
    assert.equal(a.forms,0);
    assert.equal(a.problems.filter(x=>x.issue==="LANGUAGE_HOME_MISSING").length,7);
    assert.ok(a.problems.some(x=>x.issue==="NO_FORMS_DISCOVERED"));
  }finally{rmSync(root,{recursive:true,force:true});}
});
