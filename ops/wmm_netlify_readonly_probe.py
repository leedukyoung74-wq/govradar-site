#!/usr/bin/env python3
"""Netlify Forms + Identity GET-only site readiness probe.

Not a form-submission test. Do not infer inbox persistence, email notifications
or user authentication success from transport or static markup alone.
No headers/cookies containing credentials and no POST/PUT/PATCH requests.
"""
import json
import re
import urllib.error
import urllib.request

ORIGIN = "https://wmm-govradar.netlify.app"
URLS = {
    "site": "/",
    "identity_settings": "/.netlify/identity/settings",
    "anonymous_identity": "/.netlify/identity/user",
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_code(path, opener):
    if path not in URLS.values():
        raise ValueError("path not allowlisted")
    req = urllib.request.Request(ORIGIN+path, method="GET",
              headers={"User-Agent":"WMM-Netlify-GET-only-form-audit/1.0"})
    try:
        with opener.open(req,timeout=15) as r:
            return r.status, r.read(280001)
    except urllib.error.HTTPError as ex:
        # HTTP errors are status evidence, not authorization proof.
        return ex.code, b""
    except Exception:
        # Do not emit potentially sensitive raw network exception text.
        return "NETWORK_ERROR", b""


def analyze(responses):
    data = {}
    for label, (status, raw) in responses.items():
        if len(raw)>280000:
            data[label] = {"http_status":status,"state":"TOO_LARGE"}
            continue
        if label == "site":
            html = raw.decode("utf-8","replace") if status==200 else ""
            # Netlify may strip data-netlify from served HTML after registering
            # a form at build time. Neither presence nor absence proves inbox.
            has_static = bool(re.search(r"<form\b[^>]*\bname\s*=",html,re.I))
            has_form_name = 'name="form-name"' in html or "name='form-name'" in html
            has_data_netlify = 'data-netlify="true"' in html or "data-netlify='true'" in html
            data[label]={"http_status":status,"html_form_markup":has_static,
                         "form_name_hidden_inputs_present":has_form_name,
                         "netlify_data_attribute_present":has_data_netlify}
        elif label == "identity_settings":
            try:
                j=json.loads(raw) if status==200 else {}
                if not isinstance(j,dict):
                    raise ValueError("not object")
                # Public settings structure changes across Netlify versions.
                x=j.get("external",{})
                available=isinstance(x,dict) and x.get("google") is True
                data[label]={"http_status":status,
                             "json_settings_readable":status==200,
                             "external_google_explicit_true":available}
            except (ValueError,TypeError):
                data[label]={"http_status":status,"json_settings_readable":False}
        else:
            data[label]={"http_status":status,
                         "anonymous_identity_guard":status in (401,403)}
    site_status=data["site"].get("http_status")
    data["assessment"] = {
        "netlify_site_public_get_ok":site_status==200,
        "live_form_submission_verified":False,
        "netlify_registered_form_verified":False,
        "inbox_item_verified":False,
        "notification_email_verified":False,
        "member_google_login_verified":False,
        "paid_member_entitlement_verified":False,
        "warning":"Read-only checks cannot prove Netlify submission persistence or emails."
    }
    return data


def run(opener=None):
    opener=opener or urllib.request.build_opener(NoRedirect)
    responses={k:fetch_code(path,opener) for k,path in URLS.items()}
    return analyze(responses)


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
