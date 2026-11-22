#!/usr/bin/env python3
"""GOV RADAR 메인(/<lang>/) 정리 — 2026-11-22 대표 지시: '내용을 쉽게 알 수 있고, 고객이 원하는 솔루션을 바로 취합, 디자인 깔끔하게'.

빌드된 cf/public/<lang>/index.html 를 고친다(내용은 지우지 않음).
1) 흰 바탕 깔끔한 화면 (assets/home-clean.css)
2) 첫 화면 바로 아래 '필요한 솔루션 고르기' — 6가지 중 고르고 나라·연락처를 적어 한 번에 요청(기존 신청서 order)
3) 순서: 첫 화면 → 솔루션 고르기 → 오늘의 변화 → 마감 입찰 → 제안할 수 있는 사업 → 지도 → 세계 상황 → 요금
   나머지(수주 센터, 결과물 예시, 21가지 재해 화면, 사이버, 재난 대비, AI와 차이, 고객 유형, 전시회, 세 주체)는 '더 보기' 안으로
Usage: python3 tools/home_clean.py cf/public
"""
import html, os, re, sys

PUB = sys.argv[1] if len(sys.argv) > 1 else "cf/public"
LANGS = ["ko", "en", "es", "fr", "ar", "vi", "id"]
MAIN = ["hero", "tick", "@solutions", "today", "deadlines", "board", "map", "world-now", "access"]

TX = {
 "ko": dict(t="필요한 솔루션을 고르세요", l="여러 개를 함께 골라 한 번에 요청하면, 1영업일 안에 무엇을·어떻게·얼마에 할 수 있는지 회신합니다. 상담은 무료입니다.",
   s=[("나라 진출 검토", "어느 나라에서 무엇을 팔 수 있는지 한 장으로"), ("입찰 적합도·참가 준비", "공고 조건 확인, 제출 서류 목록"),
      ("제안서·영문 서류", "영문 회사소개서·제안서·현지어 자료"), ("현지 파트너·컨소시엄", "함께 들어갈 현지 기업·기관 찾기"),
      ("국제기구·ODA 사업 상담", "세계은행·ADB·EDCF·KOICA 사업 참여"), ("분석 회원", "전체 입찰·분석 열람 · 월 20,000원(VAT 별도)")],
   c="관심 나라 (여러 곳 가능)", ch="예: 베트남, 사우디, 케냐", o="회사·기관명", n="담당자 이름", e="업무용 이메일", nd="더 알리고 싶은 내용 (선택)",
   pv="개인정보 처리방침에 동의합니다 (필수)", sn="솔루션 고르기", mo="더 보기", go="고른 솔루션으로 상담 요청", mp="지도에서 나라를 고르고 입찰을 담으려면 →", more="더 보기 — 수주 센터 · 결과물 예시 · 재해·사이버 · 고객 유형 · 전시회 · 세 주체", pick="하나 이상 골라 주세요."),
 "en": dict(t="Pick the solutions you need", l="Choose one or more and send them in one request. We reply within one business day with what we can do, how and at what cost. The consultation is free.",
   s=[("Market-entry review", "What you can sell where, on one page"), ("Tender fit & bid prep", "Eligibility check and document list"),
      ("Proposals & English documents", "Company profile, proposals, local-language material"), ("Local partners & consortia", "Find companies and bodies to bid with"),
      ("MDB & ODA project advice", "World Bank, ADB, EDCF, KOICA projects"), ("Analysis membership", "All tenders and analysis · ₩20,000/month (VAT excl.)")],
   c="Countries of interest", ch="e.g. Vietnam, Saudi Arabia, Kenya", o="Company or organisation", n="Your name", e="Work email", nd="Anything else (optional)",
   pv="I agree to the privacy policy (required)", sn="Pick solutions", mo="More", go="Request these solutions", mp="Pick countries on the map and add tenders →", more="More — bid centre · sample outputs · hazards & cyber · who uses it · trade events · three organisations", pick="Please choose at least one."),
 "es": dict(t="Elija las soluciones que necesita", l="Elija una o varias y envíelas en una sola solicitud. Respondemos en un día hábil con qué, cómo y a qué coste. La consulta es gratuita.",
   s=[("Estudio de entrada al mercado", "Qué vender y dónde, en una página"), ("Idoneidad y preparación de licitación", "Requisitos y lista de documentos"),
      ("Propuestas y documentos en inglés", "Perfil de empresa, propuestas, material local"), ("Socios locales y consorcios", "Empresas y entidades para licitar juntos"),
      ("Asesoría BMD y AOD", "Proyectos del Banco Mundial, BAsD, EDCF, KOICA"), ("Membresía de análisis", "Todas las licitaciones · ₩20.000/mes (sin IVA)")],
   c="Países de interés", ch="p. ej. Vietnam, Arabia Saudí, Kenia", o="Empresa u organización", n="Su nombre", e="Correo de trabajo", nd="Algo más (opcional)",
   pv="Acepto la política de privacidad (obligatorio)", sn="Elegir soluciones", mo="Más", go="Solicitar estas soluciones", mp="Elija países en el mapa y añada licitaciones →", more="Más — centro de licitación · ejemplos · riesgos y ciber · usuarios · ferias · tres organizaciones", pick="Elija al menos una."),
 "fr": dict(t="Choisissez les solutions utiles", l="Choisissez-en une ou plusieurs et envoyez une seule demande. Réponse sous un jour ouvré : quoi, comment, à quel coût. La consultation est gratuite.",
   s=[("Étude d'entrée sur le marché", "Quoi vendre et où, sur une page"), ("Éligibilité et préparation d'offre", "Conditions et liste des pièces"),
      ("Propositions et documents en anglais", "Présentation, propositions, supports locaux"), ("Partenaires locaux et consortiums", "Trouver avec qui soumissionner"),
      ("Conseil BMD et APD", "Projets Banque mondiale, BAsD, EDCF, KOICA"), ("Adhésion analyse", "Tous les appels d'offres · 20 000 ₩/mois (HT)")],
   c="Pays visés", ch="ex. Viêt Nam, Arabie saoudite, Kenya", o="Entreprise ou organisme", n="Votre nom", e="E-mail professionnel", nd="Autre chose (facultatif)",
   pv="J'accepte la politique de confidentialité (obligatoire)", sn="Choisir des solutions", mo="Plus", go="Demander ces solutions", mp="Choisir des pays sur la carte et ajouter des appels →", more="Plus — centre d'offres · exemples · risques et cyber · utilisateurs · salons · trois organisations", pick="Choisissez-en au moins une."),
 "ar": dict(t="اختر الحلول التي تحتاجها", l="اختر حلًا أو أكثر وأرسلها في طلب واحد. نرد خلال يوم عمل بما يمكن فعله وكيف وبأي تكلفة. الاستشارة مجانية.",
   s=[("دراسة دخول السوق", "ماذا تبيع وأين، في صفحة واحدة"), ("ملاءمة المناقصة والتحضير", "الشروط وقائمة المستندات"),
      ("العروض والوثائق بالإنجليزية", "تعريف الشركة والعروض والمواد المحلية"), ("شركاء محليون واتحادات", "جهات للتقدم معًا"),
      ("استشارة مشاريع البنوك التنموية والمساعدات", "البنك الدولي، بنك التنمية الآسيوي، EDCF، KOICA"), ("عضوية التحليل", "كل المناقصات · 20,000 وون شهريًا (دون الضريبة)")],
   c="الدول المهتم بها", ch="مثل فيتنام، السعودية، كينيا", o="الشركة أو الجهة", n="الاسم", e="البريد الإلكتروني للعمل", nd="شيء آخر (اختياري)",
   pv="أوافق على سياسة الخصوصية (إلزامي)", sn="اختيار الحلول", mo="المزيد", go="اطلب هذه الحلول", mp="اختر الدول على الخريطة وأضف المناقصات ←", more="المزيد — مركز المناقصات · نماذج · المخاطر والأمن السيبراني · المستخدمون · المعارض · ثلاث جهات", pick="اختر حلًا واحدًا على الأقل."),
 "vi": dict(t="Chọn giải pháp bạn cần", l="Chọn một hoặc nhiều và gửi trong một yêu cầu. Chúng tôi trả lời trong một ngày làm việc: làm gì, làm thế nào và chi phí. Tư vấn miễn phí.",
   s=[("Đánh giá thâm nhập thị trường", "Bán gì, ở đâu, trong một trang"), ("Đánh giá gói thầu & chuẩn bị", "Điều kiện và danh mục hồ sơ"),
      ("Đề xuất & tài liệu tiếng Anh", "Hồ sơ công ty, đề xuất, tài liệu bản địa"), ("Đối tác & liên danh địa phương", "Tìm đơn vị cùng dự thầu"),
      ("Tư vấn dự án MDB & ODA", "Ngân hàng Thế giới, ADB, EDCF, KOICA"), ("Hội viên phân tích", "Toàn bộ gói thầu · ₩20.000/tháng (chưa VAT)")],
   c="Quốc gia quan tâm", ch="VD: Việt Nam, Ả Rập Xê Út, Kenya", o="Công ty hoặc tổ chức", n="Họ tên", e="Email công việc", nd="Thông tin thêm (không bắt buộc)",
   pv="Tôi đồng ý với chính sách bảo mật (bắt buộc)", sn="Chọn giải pháp", mo="Thêm", go="Yêu cầu các giải pháp này", mp="Chọn quốc gia trên bản đồ và thêm gói thầu →", more="Thêm — trung tâm dự thầu · mẫu kết quả · rủi ro & an ninh mạng · người dùng · hội chợ · ba tổ chức", pick="Hãy chọn ít nhất một."),
 "id": dict(t="Pilih solusi yang Anda perlukan", l="Pilih satu atau lebih lalu kirim dalam satu permintaan. Kami membalas dalam satu hari kerja: apa, bagaimana, dan berapa biayanya. Konsultasi gratis.",
   s=[("Kajian masuk pasar", "Apa yang bisa dijual dan di mana, dalam satu halaman"), ("Kesesuaian tender & persiapan", "Syarat dan daftar dokumen"),
      ("Proposal & dokumen bahasa Inggris", "Profil perusahaan, proposal, materi lokal"), ("Mitra lokal & konsorsium", "Cari mitra untuk ikut tender"),
      ("Konsultasi proyek MDB & ODA", "Bank Dunia, ADB, EDCF, KOICA"), ("Keanggotaan analisis", "Semua tender · ₩20.000/bulan (belum PPN)")],
   c="Negara yang diminati", ch="mis. Vietnam, Arab Saudi, Kenya", o="Perusahaan atau lembaga", n="Nama Anda", e="Email kerja", nd="Hal lain (opsional)",
   pv="Saya setuju dengan kebijakan privasi (wajib)", sn="Pilih solusi", mo="Lainnya", go="Minta solusi ini", mp="Pilih negara di peta dan tambahkan tender →", more="Lainnya — pusat tender · contoh hasil · risiko & siber · pengguna · pameran · tiga organisasi", pick="Pilih minimal satu."),
}


def section_key(tag):
    m = re.search(r'id="([^"]+)"', tag)
    if m:
        return m.group(1)
    c = re.search(r'class="([^"]+)"', tag)
    cl = c.group(1).split() if c else []
    for k in ("hero", "tick", "sbnd", "rd-band", "segband", "gx-orgs"):
        if k in cl:
            return k
    return "band-misc"


def solutions(lang):
    x = TX[lang]
    e = html.escape
    cards = "".join(
        f'<label class="sol"><input type="checkbox" name="sol" value="{e(TX["en"]["s"][i][0])}"><span><b>{e(a)}</b><small>{e(b)}</small></span></label>'
        for i, (a, b) in enumerate(x["s"]))
    return f'''<section class="band hc-sol" id="solutions"><div class="in">
<h2>{e(x["t"])}</h2><p class="hc-lead">{e(x["l"])}</p>
<form class="hc-form" method="POST" action="/nfform?next=/{lang}/thanks/" id="hcform"><input type="hidden" name="form-name" value="order"><p hidden><input name="hp"></p><input type="hidden" name="lang" value="{lang}"><input type="hidden" name="product" value="partner">
<div class="sols">{cards}</div>
<div class="hc-row"><label>{e(x["c"])}<input name="countries" required placeholder="{e(x["ch"])}"></label><label>{e(x["o"])}<input name="org" required></label></div>
<div class="hc-row"><label>{e(x["n"])}<input name="name" required></label><label>{e(x["e"])}<input name="email" type="email" required></label></div>
<label>{e(x["nd"])}<textarea name="need" rows="3" maxlength="2000" id="hcneed"></textarea></label>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> <a href="/{lang}/legal/privacy/?stay=1" target="_blank">{e(x["pv"])}</a></label>
<div class="hc-act"><button class="hc-go" type="submit">{e(x["go"])}</button><a class="hc-map" href="/map/{'' if lang == 'ko' else lang + '/'}">{e(x["mp"])}</a></div>
<p class="hc-err" id="hcerr" hidden>{e(x["pick"])}</p>
</form>
<script>(function(){{var f=document.getElementById("hcform");f.addEventListener("submit",function(ev){{var s=[].slice.call(f.querySelectorAll('input[name=sol]:checked')).map(function(i){{return i.value}});if(!s.length){{ev.preventDefault();document.getElementById("hcerr").hidden=false;return}}var t=document.getElementById("hcneed");t.value="[Solutions] "+s.join(" / ")+(t.value?"\\n\\n"+t.value:"");f.querySelectorAll('input[name=sol]').forEach(function(i){{i.disabled=true}})}})}})();</script>
</div></section>'''


def _cssv():
    import hashlib
    for c in (os.path.join(PUB, "assets", "home-clean.css"), os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cf", "extra", "assets", "home-clean.css")):
        if os.path.exists(c):
            return hashlib.md5(open(c, "rb").read()).hexdigest()[:8]
    return "1"


def main():
    global CSSV
    CSSV = _cssv()
    n = 0
    for lang in LANGS:
        p = os.path.join(PUB, lang, "index.html")
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        if 'id="solutions"' in s:
            continue
        a = s.find("<section")
        last = s.rfind("</section>")
        if a < 0 or last < 0:
            continue
        b = last + len("</section>")
        body = s[a:b]
        parts, pos = [], 0
        for m in re.finditer(r"<section\b[^>]*>.*?</section>", body, flags=re.S):
            gap = body[pos:m.start()]  # styles/scripts written just before a section belong to it
            parts.append((section_key(re.match(r"<section\b[^>]*>", m.group(0)).group(0)), gap + m.group(0)))
            pos = m.end()
        if not parts or sum(len(x[1]) for x in parts) < len(body.strip()) * 0.98:
            print(f"home_clean: {lang} unexpected structure, skipped")
            continue
        got = {k: v for k, v in parts}
        order, used = [], set()
        for k in MAIN:
            if k == "@solutions":
                order.append(solutions(lang))
            elif k in got:
                order.append(got[k]); used.add(k)
        rest = [v for k, v in parts if k not in used]
        if rest:
            order.append(f'<details class="hc-more"><summary><span>{html.escape(TX[lang]["more"])}</span></summary>{"".join(rest)}</details>')
        s = s[:a] + "\n".join(order) + s[b:]
        # subnav: keep links to sections still on the page, add 'pick solutions' first and 'more' last
        m = re.search(r'(<nav class="subnav toc"[^>]*><div class="in">)(.*?)(</div></nav>)', s, flags=re.S)
        if m:
            d0 = s.find('<details class="hc-more"')
            keep = []
            for a_ in re.findall(r'<a href="#([^"]+)">(.*?)</a>', m.group(2)):
                pos = s.find(f'id="{a_[0]}"')
                if pos >= 0 and (d0 < 0 or pos < d0):
                    keep.append(f'<a href="#{a_[0]}">{a_[1]}</a>')
            links = f'<a href="#solutions">{html.escape(TX[lang]["sn"])}</a>' + "".join(keep) + (f'<a href="#more">{html.escape(TX[lang]["mo"])}</a>' if d0 >= 0 else "")
            s = s[:m.start()] + m.group(1) + links + m.group(3) + s[m.end():]
        s = s.replace('<details class="hc-more">', '<details class="hc-more" id="more">', 1)
        s = s.replace("</body>", '<script>(function(){function o(){var h=location.hash.slice(1);if(!h)return;var e=document.getElementById(h);if(!e)return;var d=e.closest("details");if(d&&!d.open){d.open=true;setTimeout(function(){e.scrollIntoView()},50)}}addEventListener("hashchange",o);o()})()</script></body>', 1)
        s = s.replace("</head>", f'<link rel="stylesheet" href="/assets/home-clean.css?v={CSSV}"></head>', 1)
        open(p, "w", encoding="utf-8").write(s)
        n += 1
    print(f"home_clean: {n} home pages")


if __name__ == "__main__":
    main()
