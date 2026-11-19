#!/usr/bin/env python3
"""Stage a NEVER-DEPLOYED selective WMM resilience overlay over a live snapshot.

This script reads the existing Cloudflare live/public tree and a canonical
src->dist->cf/public generated tree. It writes a third *preview only* folder.
It never invokes git, Cloudflare, payments, email, or a remote API.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

LANGS=("ko","en","es","fr","ar","vi","id")
ALLOW=[
    *(f"{lang}/{page}/index.html" for lang in LANGS for page in ("prepare","resilience")),
    "assets/wmm-resilience.js",
    "assets/wmm-resilience.css",
    "data/wmm-food-country-profiles.json",
    "data/wmm-food-primary-guidance-reviewed.json",
]
import re

PREPARE_PATCHES=json.loads(r'''{"ko":{"water":"비상 식수는 1인 하루 약 3.8L를 출발 기준으로 계산합니다. 성인 2명·14일 기준 106.4L 이상이며, 기후·건강·영유아·반려동물 등에 따라 추가량이 필요합니다.","oldProduct":"1인 하루 3L 기준","newProduct":"1인 하루 약 3.8L 비축 출발 기준","oldStove":"버너는 반드시 실외 또는 충분히 환기된 곳에서만 사용","newStove":"캠핑용 버너는 실외에서만 사용하세요. 실내·차고·텐트에서는 환기하더라도 사용하지 마세요.","oldOutage":"휴대용 버너와 연료 (실내 사용 시 환기)","newOutage":"휴대용 버너와 연료 (실외 전용)"},"en":{"water":"Emergency water starts with about 3.8 L (1 US gallon) per person per day. For 2 adults over 14 days, plan at least 106.4 L; add more for heat, health needs, infants and pets.","oldProduct":"3 L per person per day","newProduct":"about 3.8 L per person per day","oldStove":"Use stoves outdoors or with strong ventilation only","newStove":"Use camping fuel stoves outdoors only; never indoors, in garages or tents, even with ventilation.","oldOutage":"Camping stove and fuel (ventilate indoors)","newOutage":"Camping stove and fuel (outdoor use only)"},"es":{"water":"Para emergencias, calcule unos 3,8 L (1 galón estadounidense) de agua por persona y día. Para 2 adultos durante 14 días: al menos 106,4 L, con más reserva según clima y necesidades.","oldProduct":"3 L por persona y día","newProduct":"aproximadamente 3,8 L por persona y día","oldStove":"Use las estufas solo al aire libre o con buena ventilación","newStove":"Use los hornillos de camping solo al aire libre, nunca en casa, garaje ni tienda, aunque haya ventilación.","oldOutage":"Hornillo de camping y combustible (ventile en interiores)","newOutage":"Hornillo de camping y combustible (solo al aire libre)"},"fr":{"water":"Pour les urgences, prévoyez environ 3,8 L (1 gallon américain) d’eau par personne et par jour. Pour 2 adultes pendant 14 jours : au moins 106,4 L, davantage selon le climat et les besoins.","oldProduct":"3 L par personne et par jour","newProduct":"environ 3,8 L par personne et par jour","oldStove":"N'utilisez les réchauds qu'à l'extérieur ou avec une forte ventilation","newStove":"Utilisez les réchauds de camping seulement à l'extérieur, jamais dans une habitation, un garage ou une tente, même ventilés.","oldOutage":"Réchaud de camping et combustible (aérer en intérieur)","newOutage":"Réchaud de camping et combustible (utilisation extérieure uniquement)"},"ar":{"water":"للطوارئ، خصص نحو 3.8 لتر (غالون أمريكي واحد) من الماء للشخص يوميًا. يحتاج شخصان بالغان لمدة 14 يومًا إلى 106.4 لتر على الأقل، مع زيادة الكمية حسب الحرارة والاحتياجات الخاصة.","oldProduct":"3 لترات للشخص يوميًا","newProduct":"نحو 3.8 لتر للشخص يوميًا","oldStove":"استخدم المواقد في الهواء الطلق أو مع تهوية جيدة فقط","newStove":"استخدم مواقد التخييم في الهواء الطلق فقط، وليس داخل المنازل أو المرائب أو الخيام حتى مع التهوية.","oldOutage":"موقد تخييم ووقود (مع التهوية داخل المباني)","newOutage":"موقد تخييم ووقود (للاستخدام في الهواء الطلق فقط)"},"vi":{"water":"Trong tình huống khẩn cấp, dùng mức khởi điểm khoảng 3,8 L nước/người/ngày. Hai người lớn trong 14 ngày cần ít nhất 106,4 L; chuẩn bị thêm theo khí hậu và nhu cầu.","oldProduct":"3 L mỗi người mỗi ngày","newProduct":"khoảng 3,8 L mỗi người mỗi ngày","oldStove":"Chỉ sử dụng bếp ngoài trời hoặc nơi thông gió tốt","newStove":"Chỉ dùng bếp dã ngoại ngoài trời; không dùng trong nhà, ga-ra hoặc lều kể cả khi có thông gió.","oldOutage":"Bếp cắm trại và nhiên liệu (thông gió khi dùng trong nhà)","newOutage":"Bếp cắm trại và nhiên liệu (chỉ dùng ngoài trời)"},"id":{"water":"Untuk keadaan darurat, gunakan patokan awal sekitar 3,8 L air per orang per hari. Dua orang dewasa selama 14 hari memerlukan sedikitnya 106,4 L; tambah sesuai cuaca dan kebutuhan.","oldProduct":"3 L per orang per hari","newProduct":"sekitar 3,8 L per orang per hari","oldStove":"Gunakan kompor hanya di luar ruangan atau dengan ventilasi yang baik","newStove":"Gunakan kompor kemah hanya di luar ruangan; jangan gunakan di dalam rumah, garasi atau tenda meski ada ventilasi.","oldOutage":"Kompor kemah dan bahan bakar (pastikan ventilasi jika di dalam ruangan)","newOutage":"Kompor kemah dan bahan bakar (hanya untuk penggunaan luar ruangan)"}}''')

def patch_live_prepare(text, lang):
    """Patch only 4 exact safety locations in the existing live HTML; keep everything else byte-for-byte."""
    if lang not in PREPARE_PATCHES: raise RuntimeError("Unsupported preparedness locale: "+lang)
    spec=PREPARE_PATCHES[lang]
    if text.count("84L")!=1:
        raise RuntimeError("Unexpected quantity marker in live prepare: "+lang)
    text=text.replace("84L","106.4L",1)
    water_re=r'(<h2 id="s5">[^<]*</h2><ul><li>)([^<]*)(</li>)'
    match=re.search(water_re,text)
    if not match: raise RuntimeError("Cannot locate official water safety note: "+lang)
    if not ("3L" in match.group(2) or "3 L" in match.group(2) or "3 لترات" in match.group(2)):
        raise RuntimeError("Old water note was unexpectedly changed: "+lang)
    text=text[:match.start(2)]+spec["water"]+text[match.end(2):]
    for key in ("Product","Stove","Outage"):
        old=spec["old"+key]
        new=spec["new"+key]
        if text.count(old)!=1: raise RuntimeError("Refusing ambiguous/missing "+key+" old text: "+lang)
        text=text.replace(old,new,1)
    if "84L" in text or "<b>106.4L" not in text:
        raise RuntimeError("Water quantity not reconciled: "+lang)
    return text

PROTECTED=(
    "_routes.json","_headers","_redirects",
    "assets/auth.js","assets/site.js",
    "ko/index.html","en/index.html",
    "data/countries.json","data/regions.json",
)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def stage(generated:Path, current:Path, output:Path):
    generated=generated.resolve()
    current=current.resolve()
    output=output.resolve()
    if not current.is_dir() or not generated.is_dir():
        raise RuntimeError("Missing live/public snapshot or generated Cloudflare site")
    if output==current or output==generated or current in output.parents or generated in output.parents:
        raise RuntimeError("Refusing to modify source or existing live trees")
    if output.exists(): raise RuntimeError("Output must be new; refusing to overwrite prior evidence")
    old_files={str(p.relative_to(current)):sha(p) for p in current.rglob("*") if p.is_file()}
    for rel in PROTECTED:
        if rel not in old_files: raise RuntimeError("Missing protected live file: "+rel)
    if len(ALLOW)!=18: raise RuntimeError("Unexpected overlay allowlist length")
    for rel in ALLOW:
        p=generated/rel
        if not p.is_file(): raise RuntimeError("Missing required generated file: "+rel)
        if rel.endswith("/prepare/index.html"):
            page=p.read_text(encoding="utf-8")
            if "106.4L" not in page or "84L" in page:
                raise RuntimeError("Unsafe legacy water baseline in "+rel)
        if rel.endswith("/resilience/index.html"):
            page=p.read_text(encoding="utf-8")
            if "noindex, nofollow" not in page or "wmm-resilience" not in page:
                raise RuntimeError("Missing review/launch guards "+rel)
    guides=json.loads((generated/"data/wmm-food-primary-guidance-reviewed.json").read_text("utf-8"))
    food=json.loads((generated/"data/wmm-food-country-profiles.json").read_text("utf-8"))
    if {x["iso"] for x in guides["countries"]}!={"KR","JP","US"}:
        raise RuntimeError("Official general guidance records changed unexpectedly")
    if len(food)!=193 or any(x["local_official_guidance_verified"] or x["retail_availability_verified"] or x["shelf_life_verified"] for x in food):
        raise RuntimeError("Country-product evidence claims are not approved")
    shutil.copytree(current,output)
    changes=[]
    for rel in ALLOW:
        dest=output/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        previous=sha(dest) if dest.exists() else None
        if rel.endswith("/prepare/index.html"):
            language=rel.split("/")[0]
            preserved=patch_live_prepare((current/rel).read_text(encoding="utf-8"),language)
            dest.write_text(preserved,encoding="utf-8")
        else:
            shutil.copy2(generated/rel,dest)
        changes.append({"path":rel,"previous_sha256":previous,"staged_sha256":sha(dest)})
    for rel,digest in old_files.items():
        if rel not in ALLOW and sha(output/rel)!=digest:
            raise RuntimeError("Protected live file modified unexpectedly: "+rel)
    for rel in PROTECTED:
        if sha(output/rel)!=old_files[rel]:
            raise RuntimeError("Protected auth/core/route file changed: "+rel)
    staged_files={str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
    if not set(old_files).issubset(staged_files):
        raise RuntimeError("Current live files were deleted during review staging")
    result={
        "type":"WMM_SELECTIVE_LIVE_OVERLAY_REVIEW",
        "deployable":False,
        "publication_performed":False,
        "live_files_retained":len(old_files),
        "changed_or_added_files":len(changes),
        "protected_live_paths":list(PROTECTED),
        "not_included_review_routes":["quality/","review/"],
        "verified_country_products":0,
        "file_changes":changes,
    }
    report=output.parent/"live-overlay-review-manifest.json"
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--generated",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    summary=stage(args.generated,args.live,args.out)
    print("PASS: staged review only",summary["changed_or_added_files"],"allowlisted files; originals untouched")
