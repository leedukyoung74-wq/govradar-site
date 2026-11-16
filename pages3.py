import json
# GOV RADAR — conversion pages (2026-10-31 council round 3):
# who-it's-for segments with photos, business areas, tender deadline board, pricing/order page, country "next steps" box.
import re, datetime

# Free-licence photos from Unsplash (hot-linked; credited on the pages that use them)
PH = {
 "earth":  ("photo-1451187580459-43490279c0fa", "Q1p7bh3SHj8"),
 "port":   ("photo-1494412519320-aa613dfb7738", "9cCeS9Sg6nU"),
 "site":   ("photo-1541888946425-d81bb19240f5", "x-ghf9LjrVg"),
 "lab":    ("photo-1602052577122-f73b9710adba", "_9xRHrMOjeg"),
 "hand":   ("photo-1521791136064-7986c2920216", "n95VMLxqM2I"),
 "sign":   ("photo-1450101499163-c8848c66ca85", "OQMZwNd3ThU"),
 "solar":  ("photo-1509391366360-2e959784a276", "513dBrMJ_5w"),
 "health": ("photo-1517120026326-d87759a7b63b", "ZCO_5Y29s8k"),
 "city":   ("photo-1610956667016-15debe929a3f", "-aCxN_VcDO0"),
 "water":  ("photo-1533077162801-86490c593afb", "Ac97OqAWDvg"),
 "school": ("photo-1509062522246-3755977927d7", "zFSo6bnZJTw"),
 "piano":  ("photo-1589666629225-750e2f7875f5", "tiO7EhmdZyM"),
 "wind":   ("photo-1548337138-e87d889cc369", "pONBhDyOFoM"),
}
PH.update({
 "p_review": ("photo-1685609241440-f14d86cea774", "TwKr6yUHugA"),
 "p_expert": ("photo-1707944745860-4615eb585a41", "m-7R-AgsvbI"),
 "p_video":  ("photo-1616531770192-6eaea74c2456", "eTgMFFzroGc"),
 "p_study":  ("photo-1741699428220-65f37f3fbbcb", "klbApl9mxr0"),
 "p_shop":   ("photo-1753351052617-62818ffc9173", "dU3KJqyYlO0"),
 "p_free":   ("photo-1499914485622-a88fac536970", "hBuwVLcYTnA"),
 "p_hero":   ("photo-1515378791036-0648a3ef77b2", "Hcfwew744z4"),
})

def LTR(L, h):
    # new sections are written in ko/en only; keep English blocks left-to-right on the Arabic site
    return f'<div dir="ltr" lang="en">{h}</div>' if L == "ar" else h

def img(k, alt="", w=1200, h=None, cls="", eager=False):
    pid = PH[k][0]; base = f"https://images.unsplash.com/{pid}?auto=format&fit=crop&q=72"
    hh = f"&h={h}" if h else ""; hs = (lambda ww: f"&h={round(h*ww/w)}" if h else "")
    return (f'<img class="{cls}" src="{base}&w={w}{hh}" srcset="{base}&w=640{hs(640)} 640w, {base}&w={w}{hh} {w}w, {base}&w={w*2 if w<1000 else 1800}{hs(w*2 if w<1000 else 1800)} {w*2 if w<1000 else 1800}w" '
            f'sizes="(max-width:760px) 100vw, {min(w,1200)}px" alt="{alt}" {"" if eager else "loading=lazy"} decoding="async" referrerpolicy="no-referrer">')
def credit(keys, ko):
    links = ", ".join(f'<a href="https://unsplash.com/photos/{PH[k][1]}" target="_blank" rel="noopener">{i+1}</a>' for i, k in enumerate(keys))
    return f'<p class="pcredit">{"사진" if ko else "Photos"}: Unsplash ({"무료 라이선스" if ko else "free licence"}) {links}</p>'

# ---------------------------------------------------------------- sectors (keyword classification over real radar data)
SECT = [
 ("digital", "디지털·IT·전자정부", "Digital, IT & e-government", "city",
  r"software|digital|cloud|data|it |ict|cctv|cyber|sistema|informát|informat|network|e-gov|전자|디지털|소프트|데이터|정보|통신|ai\b|인공지능|플랫폼|platform|telecom|telefon|computer|서버|server"),
 ("energy", "에너지·전력·기후", "Energy, power & climate", "solar",
  r"energ|solar|wind|power|electric|grid|hydro|renewab|climate|전력|에너지|태양|풍력|발전|송전|기후|탄소|수소|hydrogen|battery|배터리"),
 ("health", "보건·의료", "Health & medical", "health",
  r"health|hospital|medic|clinic|pharma|vaccin|salud|santé|병원|의료|보건|백신|의약|진단"),
 ("water", "물·환경·위생", "Water, environment & sanitation", "water",
  r"water|sanitat|waste|sewer|agua|eau|환경|상수|하수|폐기물|정수|수자원|위생"),
 ("infra", "건설·교통·인프라", "Construction, transport & infrastructure", "site",
  r"road|bridge|rail|port|airport|construct|infra|highway|obra|construcción|건설|도로|교량|철도|항만|공항|인프라|주택|housing|metro|transport|교통"),
 ("edu", "교육·인재·연구", "Education, skills & research", "school",
  r"educat|school|training|universit|research|escuela|formación|교육|학교|훈련|대학|연구|인재|역량"),
 ("trade", "무역·물류·제조", "Trade, logistics & manufacturing", "port",
  r"trade|export|logist|manufactur|supply|customs|factory|무역|수출|물류|제조|공급|통관|공장|스마트공장"),
]
def classify(txt):
    t = (txt or "").lower()
    return [k for k, _, _, _, rx in SECT if re.search(rx, t)]

def sector_counts(DATA, G):
    c = {k: {"tenders": 0, "projects": 0, "countries": set()} for k, *_ in SECT}
    for iso, d in DATA.items():
        for t in d.get("tenders") or []:
            if isinstance(t, dict):
                for k in classify(t.get("title", "") + " " + t.get("buyer", "")): c[k]["tenders"] += 1; c[k]["countries"].add(iso)
        for p in d.get("projects") or []:
            p = p if isinstance(p, dict) else {"title": p}
            for k in classify(str(p.get("title", "")) + " " + str(p.get("detail", "")) + " " + str(p.get("ministry", ""))): c[k]["projects"] += 1; c[k]["countries"].add(iso)
    return c

def all_tenders(DATA, BY, today):
    out = []
    for iso, d in DATA.items():
        en = (d.get("en") or {}).get("tenders") or []
        for i, t in enumerate(d.get("tenders") or []):
            if not isinstance(t, dict): continue
            dl = str(t.get("deadline") or "")
            if not re.match(r"\d{4}-\d{2}-\d{2}$", dl) or dl < today: continue
            te = en[i] if i < len(en) and isinstance(en[i], dict) else {}
            out.append({"iso": iso, "t": t, "te": te, "dl": dl, "new": _is_new(t, today), "sec": classify(t.get("title", "") + " " + t.get("buyer", ""))})
    return sorted(out, key=lambda x: x["dl"])

def _is_new(t, today, days=7):
    a = str(t.get("added") or "")
    if not re.match(r"\d{4}-\d{2}-\d{2}$", a): return False
    import datetime as _dt
    return (_dt.date.fromisoformat(today) - _dt.date.fromisoformat(a)).days <= days

def past_tenders(DATA, today):
    out = []
    for iso, d in DATA.items():
        en = (d.get("en") or {}).get("tenders") or []
        for i, t in enumerate(d.get("tenders") or []):
            if not isinstance(t, dict): continue
            dl = str(t.get("deadline") or "")
            if not re.match(r"\d{4}-\d{2}-\d{2}$", dl) or dl >= today: continue
            te = en[i] if i < len(en) and isinstance(en[i], dict) else {}
            out.append({"iso": iso, "t": t, "te": te, "dl": dl, "sec": classify(t.get("title", "") + " " + t.get("buyer", "") + " " + str(te.get("title", "")))})
    return sorted(out, key=lambda x: x["dl"], reverse=True)

# feasibility-study preparation per field (what to have ready before the next round of the same kind of tender)
PREP = {
 "digital": (["발주처의 기존 시스템·데이터 현황(레거시, 연동 대상) 정리", "현지 개인정보·데이터 주권 규정과 클라우드 허용 여부 확인", "유지보수·현지 인력 교육까지 포함한 총소유비용(TCO) 산정", "유사 전자정부 납품 실적(한국 사례) 영문 레퍼런스 준비"],
             ["Map the buyer's existing systems and data (legacy, integrations)", "Check local data-protection and cloud rules", "Total cost of ownership including maintenance and local training", "English references for similar e-government deliveries"]),
 "energy": (["부지·일사량/풍황·계통 연계 용량 자료 확보", "전력구매계약(PPA) 구조와 요금·보조금 체계 확인", "ESS 포함 시 안전·인증 기준(현지/IEC) 정리", "개발은행 재원 조건(현지조달 비율, 환경사회 기준) 검토"],
            ["Site, resource and grid-connection data", "PPA structure, tariffs and subsidies", "Safety and certification rules for storage (local/IEC)", "Development-bank finance terms (local content, E&S standards)"]),
 "health": (["병상·장비 수요와 기존 장비 사용 현황 조사", "현지 의료기기 등록·인허가 절차와 기간 확인", "보건정보시스템(HIS)·표준(HL7/FHIR) 연동 범위", "운영·정비 인력 교육과 부품 공급 계획"],
            ["Demand for beds/equipment and what is in use", "Local medical-device registration and timelines", "Health information system scope and standards (HL7/FHIR)", "Training and spare-parts plan"]),
 "water": (["수량·수질 기초 데이터와 기존 시설 노후도 조사", "요금 체계와 운영비 회수(O&M) 구조 확인", "환경·사회 영향평가(ESIA) 요구 수준 확인", "운영 단계(DBO·위탁운영) 참여 가능성 검토"],
           ["Baseline flow/quality data and condition of existing assets", "Tariffs and how operating costs are recovered", "Required environmental and social impact assessment", "Whether design-build-operate or O&M contracts follow"]),
 "infra": (["교통량·수요 예측과 노선·부지 대안 비교", "용지 보상·이주(RAP) 리스크 확인", "현지 시공 파트너와 자재·장비 조달 경로", "공기·물가 변동 조항과 보증 요건 검토"],
           ["Traffic/demand forecasts and route or site options", "Land acquisition and resettlement risk", "Local construction partners and supply routes", "Schedule, price-adjustment and guarantee terms"]),
 "edu": (["대상 기관·인원과 현행 교육과정 진단", "교원 연수·콘텐츠 현지어화 범위", "기자재 유지관리와 인터넷 환경 확인", "성과지표(이수율·취업률) 설계"],
         ["Target institutions, learners and current curricula", "Teacher training and localisation scope", "Equipment upkeep and connectivity", "Outcome indicators (completion, employment)"]),
 "trade": (["물류 경로·통관 절차와 소요 시간 조사", "현지 유통·조달 파트너 후보 확보", "원산지·인증·관세 요건 정리", "공급 안정성(재고·납기) 계획"],
           ["Logistics routes, customs steps and lead times", "Local distribution or procurement partners", "Origin, certification and tariff requirements", "Supply reliability (stock, delivery times)"]),
}
PREP_DEF = (["발주처 과거 공고·낙찰 결과 수집", "현지 파트너와 컨소시엄 구성 검토", "예산 출처(정부·개발은행)와 재원 조건 확인", "다음 공고 예상 시기 추적"],
            ["Collect the buyer's past notices and awards", "Consider a consortium with a local partner", "Check the budget source and finance terms", "Track when the next round is expected"])

# ---- strings for the new/imminent/past tender features, all site languages
PT = {
 "new": {"ko": "신규", "en": "NEW", "es": "NUEVO", "fr": "NOUVEAU", "ar": "جديد", "vi": "MỚI", "id": "BARU"},
 "lg_new": {"ko": "신규 — 최근 7일 안에 올라온 공고", "en": "New — posted in the last 7 days", "es": "Nuevo: publicado en los últimos 7 días", "fr": "Nouveau : publié ces 7 derniers jours", "ar": "جديد: نُشر خلال آخر 7 أيام", "vi": "Mới: đăng trong 7 ngày qua", "id": "Baru: terbit dalam 7 hari terakhir"},
 "lg_hot": {"ko": "마감 임박 — D-15 이내", "en": "Closing soon — 15 days or less", "es": "Cierra pronto: 15 días o menos", "fr": "Clôture proche : 15 jours ou moins", "ar": "يغلق قريبًا: 15 يومًا أو أقل", "vi": "Sắp đóng: còn 15 ngày trở xuống", "id": "Segera tutup: 15 hari atau kurang"},
 "closed": {"ko": "마감", "en": "Closed", "es": "Cerrada", "fr": "Clôturé", "ar": "مغلقة", "vi": "Đã đóng", "id": "Ditutup"},
 "cnt": {"ko": "지난 입찰 {0}건 · {1}개국", "en": "{0} past tenders · {1} countries", "es": "{0} licitaciones pasadas · {1} países", "fr": "{0} appels d'offres passés · {1} pays", "ar": "{0} مناقصة سابقة · {1} دولة", "vi": "{0} gói thầu đã qua · {1} quốc gia", "id": "{0} tender lalu · {1} negara"},
 "multi": {"ko": "여러 나라 반복 수요", "en": "Recurring across countries", "es": "Se repite en varios países", "fr": "Récurrent dans plusieurs pays", "ar": "متكرر في عدة دول", "vi": "Lặp lại ở nhiều nước", "id": "Berulang di banyak negara"},
 "prep": {"ko": "다음 공고 대비 타당성 준비", "en": "Feasibility prep for the next round", "es": "Preparar la viabilidad para la próxima ronda", "fr": "Préparer la faisabilité pour le prochain appel", "ar": "إعداد دراسة الجدوى للجولة القادمة", "vi": "Chuẩn bị khả thi cho đợt tiếp theo", "id": "Persiapan kelayakan untuk putaran berikutnya"},
 "note": {"ko": "마감이 지난 공고입니다(📁). 같은 분야가 여러 나라에서 반복되면(🔁) 다음 공고가 나올 가능성이 높으니 타당성 자료를 미리 준비하세요.",
          "en": "These notices have closed (📁). When the same field recurs in several countries (🔁), another round is likely, so prepare the feasibility material early.",
          "es": "Estos avisos ya cerraron (📁). Si el mismo sector se repite en varios países (🔁), es probable otra ronda: prepare el estudio de viabilidad con antelación.",
          "fr": "Ces avis sont clos (📁). Quand un même secteur revient dans plusieurs pays (🔁), un nouvel appel est probable : préparez la faisabilité à l'avance.",
          "ar": "هذه الإعلانات أُغلقت (📁). عندما يتكرر القطاع نفسه في عدة دول (🔁) فالجولة التالية مرجحة، فجهّز مواد الجدوى مبكرًا.",
          "vi": "Các thông báo này đã đóng (📁). Khi cùng một lĩnh vực lặp lại ở nhiều nước (🔁), khả năng có đợt mới cao, hãy chuẩn bị tài liệu khả thi sớm.",
          "id": "Pengumuman ini sudah ditutup (📁). Jika bidang yang sama berulang di beberapa negara (🔁), putaran berikutnya kemungkinan besar ada, jadi siapkan bahan kelayakan lebih awal."},
 "h_mdb": {"ko": "⌛ 지난 입찰과 여러 나라 반복 수요", "en": "⌛ Past tenders and recurring needs", "es": "⌛ Licitaciones pasadas y necesidades recurrentes", "fr": "⌛ Appels d'offres passés et besoins récurrents", "ar": "⌛ المناقصات السابقة والاحتياجات المتكررة", "vi": "⌛ Gói thầu đã qua và nhu cầu lặp lại", "id": "⌛ Tender lalu dan kebutuhan berulang"},
 "h_home": {"ko": "⌛ 지난 입찰에서 보이는 반복 수요", "en": "⌛ Recurring needs in past tenders", "es": "⌛ Necesidades recurrentes en licitaciones pasadas", "fr": "⌛ Besoins récurrents dans les appels passés", "ar": "⌛ احتياجات متكررة في المناقصات السابقة", "vi": "⌛ Nhu cầu lặp lại trong các gói thầu đã qua", "id": "⌛ Kebutuhan berulang dari tender lalu"},
 "all": {"ko": "지난 입찰·타당성 준비 전체", "en": "All past tenders & feasibility prep", "es": "Todas las licitaciones pasadas y la preparación", "fr": "Tous les appels passés et la préparation", "ar": "كل المناقصات السابقة وإعداد الجدوى", "vi": "Tất cả gói thầu đã qua và chuẩn bị khả thi", "id": "Semua tender lalu & persiapan kelayakan"},
 "auto": {"ko": "자동 수집", "en": "auto-collected", "es": "recopilación automática", "fr": "collecte automatique", "ar": "جمع تلقائي", "vi": "tự động thu thập", "id": "dikumpulkan otomatis"},
 "autoc": {"ko": "⚙ 오늘 자동 수집된 공고 {n}건을 함께 표시합니다 (세계은행·EU 조달공보 TED·영국 정부조달, 매일 오전 6시 갱신 · 기준 {d}). 응찰 전 원문을 꼭 확인하세요.", "en": "⚙ Also showing {n} notices collected automatically (World Bank, EU TED and UK Find a Tender, refreshed daily at 06:00 KST · as of {d}). Check the original before bidding.", "es": "⚙ También se muestran {n} avisos recopilados automáticamente (Banco Mundial, TED de la UE y Find a Tender del Reino Unido, cada día a las 06:00 KST · al {d}). Verifique el original antes de ofertar.", "fr": "⚙ {n} avis collectés automatiquement sont aussi affichés (Banque mondiale, TED de l'UE et Find a Tender du Royaume-Uni, mis à jour chaque jour à 6 h KST · au {d}). Vérifiez l'original avant de soumissionner.", "ar": "⚙ تُعرض أيضًا {n} إعلانات جُمعت تلقائيًا (البنك الدولي، وTED الأوروبي، وFind a Tender البريطاني، تحديث يومي 06:00 بتوقيت كوريا · حتى {d}). راجع الأصل قبل التقدم.", "vi": "⚙ Hiển thị thêm {n} thông báo thu thập tự động (Ngân hàng Thế giới, TED của EU và Find a Tender của Anh, cập nhật 6:00 KST hằng ngày · ngày {d}). Hãy kiểm tra bản gốc trước khi dự thầu.", "id": "⚙ Juga ditampilkan {n} pengumuman yang dikumpulkan otomatis (Bank Dunia, TED Uni Eropa, dan Find a Tender Inggris, diperbarui tiap hari 06.00 KST · per {d}). Periksa dokumen asli sebelum menawar."},
 "other": {"ko": "기타", "en": "Other", "es": "Otros", "fr": "Autres", "ar": "أخرى", "vi": "Khác", "id": "Lainnya"},
}
def pt(k, L): return PT[k].get(L) or PT[k]["en"]

PREP_X = {
 "digital": {"es": ["Mapear sistemas y datos existentes del comprador", "Revisar normas locales de datos y nube", "Costo total de propiedad con mantenimiento y capacitación", "Referencias en inglés de proyectos de gobierno digital"],
             "fr": ["Cartographier les systèmes et données existants", "Vérifier les règles locales sur les données et le cloud", "Coût total de possession avec maintenance et formation", "Références en anglais de projets d'e-gouvernement"],
             "ar": ["حصر الأنظمة والبيانات الحالية لدى الجهة", "مراجعة قواعد حماية البيانات والحوسبة السحابية", "التكلفة الإجمالية للملكية مع الصيانة والتدريب", "مراجع بالإنجليزية لمشاريع حكومة إلكترونية مشابهة"],
             "vi": ["Rà soát hệ thống, dữ liệu hiện có của bên mời thầu", "Kiểm tra quy định dữ liệu và điện toán đám mây", "Tổng chi phí sở hữu gồm bảo trì và đào tạo", "Hồ sơ tham chiếu tiếng Anh về chính phủ điện tử"],
             "id": ["Petakan sistem dan data pembeli saat ini", "Periksa aturan data dan cloud setempat", "Total biaya kepemilikan termasuk pemeliharaan dan pelatihan", "Referensi berbahasa Inggris proyek e-government serupa"]},
 "energy": {"es": ["Datos de sitio, recurso y conexión a red", "Estructura del PPA, tarifas y subsidios", "Normas de seguridad y certificación del almacenamiento", "Condiciones del banco de desarrollo (contenido local, salvaguardas)"],
            "fr": ["Données de site, de ressource et de raccordement", "Structure du PPA, tarifs et subventions", "Règles de sécurité et de certification du stockage", "Conditions du bailleur (contenu local, normes E&S)"],
            "ar": ["بيانات الموقع والمورد والربط بالشبكة", "هيكل اتفاقية شراء الطاقة والتعرفة والدعم", "قواعد السلامة والاعتماد للتخزين", "شروط بنك التنمية (المحتوى المحلي والمعايير البيئية والاجتماعية)"],
            "vi": ["Dữ liệu địa điểm, tài nguyên và đấu nối lưới", "Cơ cấu PPA, giá điện và trợ giá", "Quy chuẩn an toàn, chứng nhận cho lưu trữ", "Điều kiện vốn ngân hàng phát triển (nội địa hóa, môi trường xã hội)"],
            "id": ["Data lokasi, sumber daya, dan sambungan jaringan", "Struktur PPA, tarif, dan subsidi", "Aturan keselamatan dan sertifikasi penyimpanan", "Syarat bank pembangunan (konten lokal, standar L&S)"]},
 "health": {"es": ["Demanda de camas y equipos y lo que está en uso", "Registro local de dispositivos médicos y plazos", "Alcance del sistema de información sanitaria (HL7/FHIR)", "Plan de capacitación y repuestos"],
            "fr": ["Besoins en lits et équipements, existant", "Enregistrement local des dispositifs médicaux et délais", "Périmètre du système d'information sanitaire (HL7/FHIR)", "Plan de formation et de pièces détachées"],
            "ar": ["الطلب على الأسرّة والأجهزة والموجود منها", "تسجيل الأجهزة الطبية محليًا ومدده", "نطاق نظام المعلومات الصحية (HL7/FHIR)", "خطة التدريب وقطع الغيار"],
            "vi": ["Nhu cầu giường bệnh, thiết bị và hiện trạng sử dụng", "Thủ tục, thời gian đăng ký thiết bị y tế", "Phạm vi hệ thống thông tin y tế (HL7/FHIR)", "Kế hoạch đào tạo và phụ tùng"],
            "id": ["Kebutuhan tempat tidur dan alat serta yang sudah dipakai", "Registrasi alat kesehatan setempat dan waktunya", "Cakupan sistem informasi kesehatan (HL7/FHIR)", "Rencana pelatihan dan suku cadang"]},
 "water": {"es": ["Datos base de caudal y calidad y estado de activos", "Tarifas y recuperación de costos de operación", "Evaluación de impacto ambiental y social requerida", "Si siguen contratos de diseño-construcción-operación"],
           "fr": ["Données de base débit/qualité et état des ouvrages", "Tarifs et recouvrement des coûts d'exploitation", "Étude d'impact environnemental et social requise", "Suite possible en conception-construction-exploitation"],
           "ar": ["بيانات أساسية للتدفق والجودة وحالة المنشآت", "التعرفة واسترداد تكاليف التشغيل", "متطلبات تقييم الأثر البيئي والاجتماعي", "إمكانية عقود التصميم والبناء والتشغيل لاحقًا"],
           "vi": ["Dữ liệu nền lưu lượng, chất lượng và hiện trạng công trình", "Giá nước và cơ chế thu hồi chi phí vận hành", "Yêu cầu đánh giá tác động môi trường xã hội", "Khả năng có hợp đồng thiết kế-xây dựng-vận hành"],
           "id": ["Data dasar debit, kualitas, dan kondisi aset", "Tarif dan pemulihan biaya operasi", "Kajian dampak lingkungan dan sosial yang diminta", "Kemungkinan kontrak rancang-bangun-operasi"]},
 "infra": {"es": ["Previsión de demanda y alternativas de trazado o sitio", "Riesgo de adquisición de tierras y reasentamiento", "Socios locales de construcción y suministro", "Plazos, reajuste de precios y garantías"],
           "fr": ["Prévisions de trafic et variantes de tracé ou de site", "Risque foncier et de réinstallation", "Partenaires locaux de construction et approvisionnement", "Délais, révision des prix et garanties"],
           "ar": ["توقعات الطلب وبدائل المسار أو الموقع", "مخاطر الاستملاك وإعادة التوطين", "شركاء البناء المحليون ومسارات التوريد", "الجدول الزمني وتعديل الأسعار والضمانات"],
           "vi": ["Dự báo nhu cầu, phương án tuyến hoặc địa điểm", "Rủi ro thu hồi đất và tái định cư", "Đối tác thi công địa phương và nguồn vật tư", "Tiến độ, điều chỉnh giá và bảo lãnh"],
           "id": ["Proyeksi permintaan dan alternatif trase atau lokasi", "Risiko pengadaan tanah dan pemukiman kembali", "Mitra konstruksi lokal dan jalur pasokan", "Jadwal, penyesuaian harga, dan jaminan"]},
 "edu": {"es": ["Instituciones, alumnos y planes de estudio actuales", "Formación docente y localización de contenidos", "Mantenimiento de equipos y conectividad", "Indicadores de resultados (finalización, empleo)"],
         "fr": ["Établissements, apprenants et programmes actuels", "Formation des enseignants et localisation", "Entretien des équipements et connectivité", "Indicateurs de résultats (réussite, emploi)"],
         "ar": ["المؤسسات والمتعلمون والمناهج الحالية", "تدريب المعلمين وتوطين المحتوى", "صيانة الأجهزة والاتصال بالإنترنت", "مؤشرات النتائج (الإكمال والتوظيف)"],
         "vi": ["Cơ sở, người học và chương trình hiện hành", "Đào tạo giáo viên và bản địa hóa nội dung", "Bảo trì thiết bị và kết nối mạng", "Chỉ số kết quả (hoàn thành, việc làm)"],
         "id": ["Lembaga, peserta didik, dan kurikulum saat ini", "Pelatihan guru dan lokalisasi konten", "Pemeliharaan peralatan dan konektivitas", "Indikator hasil (kelulusan, kerja)"]},
 "trade": {"es": ["Rutas logísticas, aduanas y plazos", "Socios locales de distribución o compras", "Origen, certificación y aranceles", "Fiabilidad del suministro (stock, entregas)"],
           "fr": ["Itinéraires logistiques, douanes et délais", "Partenaires locaux de distribution", "Origine, certification et droits de douane", "Fiabilité d'approvisionnement (stock, délais)"],
           "ar": ["مسارات الإمداد والجمارك والمدد", "شركاء التوزيع أو الشراء المحليون", "متطلبات المنشأ والاعتماد والرسوم", "موثوقية التوريد (المخزون ومواعيد التسليم)"],
           "vi": ["Tuyến logistics, thủ tục hải quan và thời gian", "Đối tác phân phối, mua sắm địa phương", "Yêu cầu xuất xứ, chứng nhận, thuế quan", "Độ ổn định nguồn cung (tồn kho, giao hàng)"],
           "id": ["Rute logistik, kepabeanan, dan waktu", "Mitra distribusi atau pengadaan lokal", "Syarat asal barang, sertifikasi, dan tarif", "Keandalan pasokan (stok, pengiriman)"]},
 "_def": {"es": ["Reunir avisos y adjudicaciones anteriores del comprador", "Valorar un consorcio con un socio local", "Verificar la fuente del presupuesto y sus condiciones", "Seguir cuándo se espera la próxima ronda"],
          "fr": ["Rassembler les avis et attributions passés de l'acheteur", "Envisager un consortium avec un partenaire local", "Vérifier l'origine du budget et ses conditions", "Suivre la date probable du prochain appel"],
          "ar": ["جمع الإعلانات والترسيات السابقة للجهة", "دراسة تحالف مع شريك محلي", "التحقق من مصدر الميزانية وشروط التمويل", "متابعة الموعد المتوقع للجولة القادمة"],
          "vi": ["Thu thập thông báo và kết quả trúng thầu trước đây", "Cân nhắc liên danh với đối tác địa phương", "Kiểm tra nguồn ngân sách và điều kiện vốn", "Theo dõi thời điểm dự kiến của đợt tới"],
          "id": ["Kumpulkan pengumuman dan pemenang tender sebelumnya", "Pertimbangkan konsorsium dengan mitra lokal", "Periksa sumber anggaran dan syarat pendanaan", "Pantau kapan putaran berikutnya diperkirakan"]},
}
def prep_list(k, L):
    if L in ("ko", "en"): return PREP.get(k, PREP_DEF)[0 if L == "ko" else 1]
    return (PREP_X.get(k) or PREP_X["_def"]).get(L) or PREP.get(k, PREP_DEF)[1]

SECT_L = {}
def past_groups(C):
    P = past_tenders(C["DATA"], C["TODAY"]); g = {}
    for x in P:
        for s in (x["sec"] or ["other"]): g.setdefault(s, []).append(x)
    order = sorted(g, key=lambda k: (-len({x["iso"] for x in g[k]}), -len(g[k])))
    return [(k, g[k]) for k in order]

def past_board(L, C, home=False):
    """Expired tenders grouped by field; fields seen in two or more countries come first, with a feasibility checklist."""
    ko = L == "ko"; e = C["e"]; G = past_groups(C)
    if not G: return ""
    names = {k: (nk, ne) for k, nk, ne, *_ in SECT}
    if home: G = [(k, xs) for k, xs in G if len({x["iso"] for x in xs}) >= 2][:4]
    cards = []
    for k, xs in G:
        cs = sorted({x["iso"] for x in xs}); multi = len(cs) >= 2
        flags = " ".join(C["flag"](i) for i in cs[:14]) + (f" +{len(cs)-14}" if len(cs) > 14 else "")
        ex = "".join('<li>📁 <span class="note">' + x["dl"] + "</span> " + C["flag"](x["iso"]) + " " + e(((x["te"].get("title") if not ko else None) or x["t"].get("title", ""))[:90]) + "</li>" for x in xs[:(3 if home else 6)])
        tag = (" · 🔁 " + pt("multi", L)) if multi else ""
        det = "" if home else ('<details><summary>📋 ' + pt("prep", L) + "</summary><ol>" + "".join("<li>" + e(p) + "</li>" for p in prep_list(k, L)) + "</ol></details>")
        nm_ = pt("other", L) if k == "other" else (names[k][0] if ko else (SECT_L.get(L, {}).get(k) or names[k][1]))
        cards.append(f'<div class="card past{" multi" if multi else ""}"><p class="note">⌛ {pt("cnt", L).format(len(xs), len(cs))}{tag}</p><h3>{e(nm_)}</h3><p class="flags">{flags}</p><ul class="pl">{ex}</ul>{det}</div>')
    return '<p class="note">' + pt("note", L) + '</p><div class="grid pastg">' + "".join(cards) + "</div>"

# ---------------------------------------------------------------- segments
SEG = [
 ("site", "해외 공공사업을 노리는 컨설팅·엔지니어링사", "Consulting and engineering firms bidding for overseas public contracts",
  ["분야별 입찰을 마감일 순으로 한곳에서", "그 나라 정부의 우선 과제와 예산", "함께 들어갈 컨소시엄 파트너", "AI 초안 + 사람 검수 제안서"],
  ["Tenders in your field, sorted by deadline", "Each government's priorities and budgets", "Consortium partners to bid with", "AI-drafted, human-reviewed proposals"],
  "국제기구 컨설팅 용역 · 타당성 조사 · 사업관리(PMC)", "Development-bank consulting · feasibility studies · project management consultancy"),
 ("port", "수출을 시작하는 중소 제조·소비재 기업", "SMEs starting to export",
  ["어느 나라 정부가 무엇을 사려 하는지", "그 나라에서 쓸 수 있는 한국 지원제도(수출바우처·KOTRA 등)", "제재·분쟁·환율 위험 미리 확인", "사람이 검수한 국가 진출 브리프"],
  ["What each government is trying to buy", "Korean support you can use there (export vouchers, KOTRA)", "Sanctions, conflict and currency risks checked in advance", "Human-reviewed market-entry briefs"],
  "정부 조달 납품 · 현지 유통 파트너 · 수출바우처 활용", "Government supply contracts · local distribution partners · export-voucher projects"),
 ("lab", "대학·연구기관", "Universities & research institutes",
  ["KOICA·EDCF·국제협력 과제 발굴", "협약 대학 박사진과 온라인 공동 검토", "학생 교육에 쓰는 실제 국가 데이터", "기관 코드로 교직원·학생 계정 일괄"],
  ["Find KOICA, EDCF and other international cooperation projects", "Online co-review with partner-university PhDs", "Real country data for teaching", "Staff and student accounts under one institution code"],
  "국제개발협력 과제 · 연구 용역 · 교육 프로그램 수출", "Development-cooperation projects · research contracts · education exports"),
 ("hand", "금융·공공기관·투자자", "Banks, public agencies & investors",
  ["국가별 정부 아젠다와 위험 브리핑", "분쟁·제재 상황을 출처와 함께", "프로젝트에 맞는 기업·대학 컨소시엄", "계약서·협력 의향서 양식"],
  ["Government agenda and risk briefings by country", "Conflict and sanctions status with sources", "Company and university consortia per project", "Contract and letter-of-intent templates"],
  "프로젝트 금융 · 보증·보험 · 공동 사업", "Project finance · guarantees & insurance · joint ventures"),
]
def segments_html(L, ko, compact=False):
    rows = []
    for i, (ph, tk, te, gk, ge, bk, be) in enumerate(SEG):
        gains = "".join(f"<li>{x}</li>" for x in (gk if ko else ge))
        rows.append(f'''<article class="seg{" flip" if i % 2 else ""}"><div class="segimg">{img(ph, tk if ko else te, 900, 640)}</div>
<div class="segtx"><h3>{tk if ko else te}</h3><ul>{gains}</ul><p class="segbiz"><span>{"여기서 이어지는 사업" if ko else "Business that follows"}</span>{bk if ko else be}</p></div></article>''')
    if compact: rows = rows[:4]
    return LTR(L, "".join(rows))

def sectors_html(L, ko, counts):
    out = []
    for k, nk, ne, ph, _ in SECT:
        c = counts[k]
        n = (f'입찰 {c["tenders"]}건 · 정부 사업 {c["projects"]}건 · {len(c["countries"])}개국' if ko else f'{c["tenders"]} tenders · {c["projects"]} government projects · {len(c["countries"])} countries')
        out.append(f'<a class="sect" href="/{L}/mdb/?s={k}#deadlines">{img(ph, nk if ko else ne, 640, 420)}<span><b>{nk if ko else ne}</b><small>{n}</small></span></a>')
    return "".join(out)

# ---------------------------------------------------------------- solutions page  (/L/solutions/)
def solutions_page(L, C):
    ko = L == "ko"; e = C["e"]; counts = sector_counts(C["DATA"], C["G"])
    body = f'''<section class="phero">{img("earth", "", 1800, 900, "bg", True)}<div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p>
<h1>{"정부가 사려는 것에서 사업이 시작됩니다" if ko else "Business starts with what governments want to buy"}</h1>
<p class="lede">{"193개국 정부의 과제·예산·입찰을 추적해, 한국 기업·대학·기관이 함께 들어갈 수 있는 사업으로 연결합니다. 요약은 무료로 보고, 전체 목록·분석과 연결은 사람이 검수해 드립니다." if ko else "We track the priorities, budgets and tenders of 193 governments and turn them into projects that Korean companies, universities and institutions can pursue together. Browse the data for free, and order human-reviewed analysis and introductions when you need them."}</p>
<p class="cta"><a class="btn pri" href="/{L}/pricing/">{"주문·요금 보기" if ko else "Orders & pricing"}</a> <a class="btn ghost" href="/{L}/mdb/#deadlines">{"마감 임박 입찰 보기" if ko else "See closing tenders"}</a></p></div></section>
<section class="band"><div class="in"><h2>{"이런 분들이 여기서 사업을 만듭니다" if ko else "Who does business here"}</h2>{segments_html(L, ko)}</div></section>
<section class="band alt"><div class="in"><h2>{"레이더에 잡힌 분야별 사업" if ko else "Business areas tracked by the radar"}</h2>
<p class="note">{"숫자는 지금 레이더 데이터에서 분야 단어로 자동 분류한 건수입니다. 한 건이 여러 분야에 들어갈 수 있습니다." if ko else "Counts are classified automatically by keyword from current radar data; one item may appear in several areas."}</p>
<div class="sects">{sectors_html(L, ko, counts)}</div></div></section>
<section class="band"><div class="in"><h2>{"함께 일하는 방법" if ko else "Ways to work with us"}</h2><div class="ways">
<a href="/{L}/individuals/"><b>{"개인 참여 안내" if ko else "For individuals"}</b><span>{"검증원·전문가·1인 사업자·학생이 할 수 있는 일" if ko else "What verifiers, experts, sole traders and students can do"}</span></a>
<a href="/{L}/consortium/"><b>{"컨소시엄 관심 등록" if ko else "Join the consortium"}</b><span>{"대학·기관·기업·전문가가 사업별로 팀을 이룹니다" if ko else "Universities, institutions, companies and experts team up per project"}</span></a>
<a href="/{L}/projects/"><b>{"프로젝트 랩" if ko else "Project Lab"}</b><span>{"정책 흐름에서 먼저 추론한 사업 아이디어" if ko else "Project ideas inferred early from policy trends"}</span></a>
<a href="/{L}/contracts/"><b>{"계약서·협력 의향서" if ko else "Contracts & LOI"}</b><span>{"표준 양식을 보고 요청할 수 있습니다" if ko else "Standard templates you can request"}</span></a>
<a href="/{L}/experts/"><b>{"검증원·전문가 참여" if ko else "Work as a verifier or expert"}</b><span>{"현지 언어와 전문성으로 결과물마다 보수" if ko else "Paid per deliverable for language and expertise"}</span></a>
<a href="/{L}/conflict/"><b>{"분쟁 상황판" if ko else "Conflict watch"}</b><span>{"진출 전 위험을 검증된 사실로 확인" if ko else "Check risks with verified facts before you go"}</span></a>
</div>{credit(["earth"] + [s[0] for s in SEG] + [x[3] for x in SECT], ko)}</div></section>'''
    return C["head"](L, ("진출 지원 — 누가 무엇을 얻나" if ko else "Market-entry support: who benefits and how") + " · GOV RADAR",
                     "정부 수요에서 시작하는 해외 사업: 컨설팅사·수출기업·대학·기관별 활용법" if ko else "Overseas business that starts from government demand: how consultancies, exporters, universities and institutions use GOV RADAR",
                     f"/{L}/solutions/", {l: f"/{l}/solutions/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)

# ---------------------------------------------------------------- pricing / order page  (/L/pricing/)
# ---------------------------------------------------------------- membership tiers (what each tier unlocks)
TIERS = [  # id, ko name, en name, ko price, en price
    ("free", "무료 가입 (M0)", "Free sign-up (M0)", "0원", "Free"),
    ("member", "분석 회원 (M1)", "Analysis member (M1)", "월 19,800원", "₩19,800/mo"),
    ("partner", "프로젝트 파트너십", "Project partnership", "첫 상담 무료 · 비용은 상담 후 결정", "First consultation free · fees agreed after it"),
    ("inst", "기관 라이선스", "Institutional licence", "연 300만 원부터", "from ₩3M/yr"),
]
TIER_ROWS = [  # ko, en, free, member, partner, inst
    ("193개국 지도·나라별 요약·상황판·재난 대비", "Map, country summaries, situation board and preparedness for 193 countries", "✓", "✓", "✓", "✓"),
    ("국가 리포트 상세 (아젠다·정부 사업·원조·한국 지원 전체 목록)", "Full country reports (agenda, programmes, aid, Korean support — every item)", "항목별 앞 2건", "전체", "전체", "전체"),
    ("열린 입찰 상세 (발주처·마감일·원문 링크)", "Open tender details (buyer, deadline, notice link)", "나라별 앞 2건", "전체", "전체", "전체"),
    ("전시회·무역사절단 일정", "Trade fairs and trade missions", "3건", "전체", "전체", "전체"),
    ("유망 사업의 이유·대상 바이어 (AI 분석 + 사람 검수)", "Why-now and target buyers (AI analysis, human-reviewed)", "주 1건", "전체", "전체", "전체"),
    ("관심 나라 주간 요약·마감 임박 알림 (이메일, 담당자 검수 후 발송)", "Weekly summary and closing-soon alerts (email, sent after staff review)", "—", "10개국", "무제한", "무제한"),
    ("호르무즈·중동 리스크 브리프 (중요한 변화가 있을 때)", "Hormuz & Middle East risk brief (when there is a significant change)", "—", "✓", "✓", "✓"),
    ("월 1회 해외 정부사업 설명회·파트너 매칭 모임", "Monthly briefing and partner-matching meet-up", "✓ (사전 신청)", "✓ 우선 좌석", "✓", "✓"),
    ("입찰 적합도 판정·프로젝트 랩 참여자 구성", "Tender fit verdicts and Project Lab participant line-ups", "—", "건당 10만 원", "포함", "분기 브리프"),
    ("파트너 연결·컨소시엄·현지 등록·제안서 동행", "Partner introductions, consortium, local registration and proposal support", "—", "—", "✓", "상담"),
    ("담당자 교육·견적서·세금계산서 일괄", "Staff training, quote and tax invoice pack", "—", "—", "—", "✓"),
]
NEED = {  # what was clicked -> the tier that unlocks it
    "biz": ("member", "유망 사업의 이유·대상 바이어 전체", "every why-now and target buyer"),
    "alerts": ("member", "관심 나라 주간 요약·마감 임박 알림 (이메일)", "a weekly summary and closing-soon alerts"),
    "risk": ("member", "중동 리스크 브리프 (중요한 변화 시)", "the Middle East risk brief when things change"),
    "fit": ("partner", "입찰 적합도 판정", "tender fit verdicts"),
    "lab": ("partner", "프로젝트 랩 참여자 구성·재원 후보", "Project Lab participants and funders"),
    "tenders": ("member", "관심 분야 입찰 알림", "tender alerts for your field"),
}
_NM = None
def paylink(L, need, iso=""):
    from urllib.parse import quote
    t = NEED.get(need, ("member",))[0]
    cn = (_NM(iso, L) if (_NM and iso) else iso)
    return f"/{L}/pricing/?t={t}&need={need}" + (f"&c={quote(cn)}" if iso else "") + "#tier"
def tier_price(L, t):
    for x in TIERS:
        if x[0] == t: return (x[1] + " " + x[3]) if L == "ko" else (x[2] + " " + x[4])
    return ""
def tier_cta(L, need, iso="", n=None):
    """Teaser footer linking straight to the tier that unlocks it."""
    ko = L == "ko"; t = NEED.get(need, ("member",))[0]
    more = (f"나머지 {n}건 보기 — " if ko else f"See the other {n} — ") if n else ""
    return (f'<a class="tierbar" href="{paylink(L, need, iso)}"><span>{more}<i class="lp">{"이 내용은" if ko else "Unlock with"}</i> <b>{tier_price(L, t)}</b></span>'
            f'<span class="go">{"바로 신청 →" if ko else "Start now →"}</span></a>')
def tier_table(L):
    ko = L == "ko"
    SUB = {"member": ("VAT 포함 · 연 198,000원", "VAT incl. · ₩198,000/yr"), "inst": ("VAT 별도 · 300만·600만·990만 원", "VAT excl. · ₩3M / 6M / 9.9M")}
    head = "".join(f'<th data-t="{i}">{nk if ko else ne}<small>{pk if ko else pe}</small>' + (f'<small class="vat">{SUB[i][0] if ko else SUB[i][1]}</small>' if i in SUB else "") + '</th>' for i, nk, ne, pk, pe in TIERS)
    EN = {"항목별 앞 2건": "First 2 per section", "나라별 앞 2건": "First 2 per country", "3건": "3", "주 1건": "1 a week", "전체": "All", "10개국": "10 countries", "무제한": "Unlimited", "✓ (사전 신청)": "✓ (register)", "✓ 우선 좌석": "✓ priority seat", "건당 10만 원": "₩100,000 each", "포함": "Included", "분기 브리프": "Quarterly brief", "상담": "On request"}
    rows = "".join(f'<tr><th>{r[0] if ko else r[1]}</th>' + "".join(f'<td data-t="{TIERS[j][0]}">{(v if ko else EN.get(v, v))}</td>' for j, v in enumerate(r[2:])) + "</tr>" for r in TIER_ROWS)
    lab = {"member": ("신청", "Choose"), "partner": ("무료 상담 신청", "Book a free consultation"), "inst": ("견적 요청", "Request a quote")}
    sign = "".join(f'<td data-t="{i}">' + ("" if i == "free" else f'<a class="btn sm{" pri" if i == "partner" else ""}" href="?t={i}#order" data-pick="{i}">{lab[i][0] if ko else lab[i][1]}</a>') + "</td>" for i, *_ in TIERS)
    return f'<div class="tscroll"><table class="tiers"><thead><tr><th></th>{head}</tr></thead><tbody>{rows}<tr><th></th>{sign}</tr></tbody></table></div>'

WMM_MS = "https://www.wmm-hoa.com/membership/"
def wmm_ladder(L):
    """GOV RADAR -> WMM membership: one shared ladder; upper grades join and pay on wmm-hoa.com."""
    ko = L == "ko"
    rows = ([("GOV RADAR 무료 가입 · M0", "요약 열람", "193개국 지도·요약·상황판을 보고, 사업·입찰·일정은 앞부분만 봅니다."),
             ("분석 회원 · 공통 입문 등급", "월 19,800원", "유망 사업의 이유·대상 바이어, 관심 나라 알림. WMM 멤버십의 공통 입문 단계입니다."),
             ("WMM 멤버십 M1–M3", "오프라인 사업자료", "고른 나라·사업으로 회사소개서·제안서·사업계획 같은 실제 사업자료를 함께 만듭니다."),
             ("WMM 멤버십 M4–M5", "메인 프로젝트 구축", "파트너·컨소시엄을 꾸려 실제 프로젝트를 구축하고 실행까지 함께 갑니다.")] if ko else
            [("GOV RADAR free sign-up · M0", "Summaries", "Map, summaries and situation board for 193 countries; the first items of programmes, tenders and events."),
             ("Analysis member · shared entry grade", "₩19,800/month", "Why-now, target buyers and alerts for your countries. The common entry step of WMM membership."),
             ("WMM membership M1–M3", "Offline business materials", "We build real materials with you for the chosen country and deal: company profile, proposal, business plan."),
             ("WMM membership M4–M5", "Main project build", "We form partners and a consortium and build and run the actual project with you.")])
    li = "".join(f'<tr><th>{a}</th><td><b>{b}</b></td><td style="text-align:left">{c}</td></tr>' for a, b, c in rows)
    h = "정보에서 실제 프로젝트까지 — WMM 멤버십 등급" if ko else "From information to a real project — WMM membership grades"
    n = ("GOV RADAR와 WMM 멤버십은 같은 등급 체계를 씁니다. 상위 등급(M1–M5)의 가입·결제는 WMM 홈페이지에서 합니다." if ko else
         "GOV RADAR and WMM membership share one grade system. Upper grades (M1–M5) are joined and paid for on the WMM website.")
    n += f'</p><p class="note" style="color:#c62828;font-weight:700;border-top:2px dashed #d32f2f;padding-top:10px">{REVIEW["ko" if ko else "en"]}' 
    b = "WMM 멤버십 가입·결제 (www.wmm-hoa.com) →" if ko else "Join and pay for WMM membership (www.wmm-hoa.com) →"
    return (f'<section class="band" id="wmm-membership"><div class="in"><h2>{h}</h2><p class="note">{n}</p>'
            f'<div class="tscroll"><table class="tiers">{li}</table></div>'
            f'<p class="cta"><a class="btn pri" href="{WMM_MS}{"?lang=ko" if ko else "?lang=en"}" target="_blank" rel="noopener">{b}</a> <a class="btn" href="/{L}/membership/">{"멤버십 등급·혜택 자세히 보기" if ko else "Membership grades & benefits in detail"}</a></p></div></section>')
def pricing_page(L, C, PLANS, PLAN_NOTE):
    ko = L == "ko"; e = C["e"]
    offers = [
     ("partner", "프로젝트 파트너십 (대표 상품)", "Project partnership (flagship)", "첫 상담 무료 (온라인 또는 서울 오프라인 30분) · 착수금·성공보수는 상담 후 결정", "First consultation free (30 min, online or in Seoul) · fees agreed after the consultation",
      "AI는 정보를 주지만 사람을 연결해 주지는 않습니다. 목표 나라·사업을 함께 정하고, GCSME 네트워크·현지 파트너·협약 대학을 통해 파트너를 찾아 공급자 등록·서류·컨소시엄·제안서까지 함께 갑니다. 비용은 사업 규모를 보고 첫 상담 뒤에 정하며, 성과가 났을 때 받는 성공보수 중심입니다. 정부·국제기구 사업은 반부패·수수료 공개 조항을 적용합니다.",
      "AI gives you information; it does not introduce you to people. We agree a target country and deal with you, find partners through the GCSME network, local partners and partner universities, and work with you through supplier registration, documents, consortium and proposal. Fees are set after the first consultation according to the deal, weighted toward a success fee. Anti-bribery and fee-disclosure clauses apply to public deals.", "hand"),
     ("meetup", "월 1회 해외 정부사업 설명회·파트너 매칭 모임", "Monthly briefing & partner-matching meet-up", "무료 · 사전 신청 (서울 오프라인 + 온라인 동시, 장소는 신청자에게 안내)", "Free · registration required (Seoul in person + online; venue sent to registrants)",
      "이달의 주요 정부 사업·입찰을 함께 보고, 같은 나라·분야를 노리는 기업·전문가와 직접 만나는 자리입니다. 프로젝트 파트너십 상담도 현장에서 받습니다.",
      "We walk through this month's key government programmes and tenders, and you meet companies and experts targeting the same countries and sectors. Partnership consultations are available on site.", "city"),
     ("member", "분석 회원", "Analysis membership", "월 19,800원 · 연 198,000원 (VAT 포함, 자동갱신 없음)", "₩19,800/month · ₩198,000/year (VAT incl., no auto-renewal)",
      "가입하면 요약은 무료로 보고, 분석 회원은 모든 나라의 전체 목록과 AI가 분석하고 사람이 검수한 '왜 지금인지·누가 살 사람인지'를 모든 나라에서 보고, 관심 나라 10곳의 주간 요약과 마감 임박 알림을 이메일로 받고(담당자 검수 후 발송), 중동 정세에 중요한 변화가 있으면 리스크 브리프를 받습니다. 설명회 우선 좌석도 드립니다.",
      "Summaries are free with sign-up. Analysis members see full lists plus the AI-analysed, human-reviewed why-now and target buyers for every country, get a weekly email summary with closing-soon alerts for 10 countries (sent after staff review), and a Middle East risk brief when there is a significant change. Priority seats at the meet-ups too.", "earth"),
     ("brief", "국가 진출 브리프", "Market-entry brief", "300,000원부터 (VAT 별도, 신청 당일 견적)", "From ₩300,000 (VAT excl., quote the same day)",
      "한 나라에 대해: 정부 우선 과제와 예산, 지금 열린 입찰, 쓸 수 있는 한국 지원제도, 위험·제재, 권장 진입 경로와 다음 행동. 고객 업종에 맞추고 모든 수치에 출처를 붙입니다. 납기는 견적 때 확정합니다(보통 5~10영업일).",
      "For one country, tailored to your sector: priorities and budgets, open tenders, Korean support you can use, risks and sanctions, a recommended entry route and next steps. Every figure is sourced. Turnaround is confirmed with the quote (usually 5–10 business days).", "site"),
     ("fit", "입찰 적합도 검토", "Tender fit review", "100,000원 (공고 1건, VAT 별도)", "₩100,000 per tender (VAT excl.)",
      "공고 1건에 대해: 참여 자격, 필요 서류, 현지 파트너 필요 여부, 일정, 참여 권장 여부를 원문 공고와 대조해 사람이 판단합니다. 영업일 3일.",
      "For one tender: eligibility, required documents, need for a local partner, timeline and a go/no-go recommendation, judged by a person against the original notice. Three business days.", "sign"),
     ("inst", "기관 라이선스 (연간)", "Institutional licence (annual)", "연 300만 · 600만 · 990만 원 (VAT 별도)", "₩3M · 6M · 9.9M a year (VAT excl.)",
      "지자체·테크노파크·공공기관·은행용입니다. 세 단계 모두 견적서 한 장으로 결재할 수 있는 금액이며, 견적서·사업자등록증·통장 사본·전자세금계산서를 바로 드립니다.<span class=\"itier\"><b>300만 원</b> 사용자 5명 · 분석 회원 기능 · 분기 브리프 1건</span><span class=\"itier\"><b>600만 원</b> 사용자 15명 · 분기 브리프 · 담당자 교육 1회 · 회원사 설명회 1회</span><span class=\"itier\"><b>990만 원</b> 사용자 무제한 · 월 브리프 · 맞춤 국가 10개 · 회원사 설명회 2회</span>",
      "For local governments, technoparks, public bodies and banks; every tier can be approved on a single quote.<span class=\"itier\"><b>₩3M</b> 5 users · analysis features · 1 brief a quarter</span><span class=\"itier\"><b>₩6M</b> 15 users · quarterly brief · 1 staff training · 1 member briefing</span><span class=\"itier\"><b>₩9.9M</b> unlimited users · monthly brief · 10 custom countries · 2 member briefings</span>", "hand"),
    ]
    orows = "".join(f'''<article class="offer">{img(ph, nk if ko else ne, 720, 480)}<div><h3>{nk if ko else ne}</h3><p class="price">{pk if ko else pe}</p><p>{dk if ko else de}</p>
<a class="btn pri" href="?p={pid}#order">{({"partner": "무료 상담 신청", "meetup": "설명회 신청"}.get(pid, "신청하기")) if ko else ({"partner": "Book a free consultation", "meetup": "Register"}.get(pid, "Request"))}</a>{(' <a class="btn" href="/'+L+'/sample/">'+("샘플 보기" if ko else "See a sample")+'</a>') if pid in ("brief","inst") else ""}{(' <a class="btn" href="/'+L+'/contracts/#connect">'+("계약 조건 보기" if ko else "Contract terms")+'</a>') if pid == "partner" else ""}</div></article>''' for pid, nk, ne, pk, pe, dk, de, ph in offers)
    plan_rows = "".join(f'<tr><th>{e(a)}</th><td><b>{e(b)}</b></td><td>{e(c)}</td></tr>' for a, b, c in PLANS[L])
    steps = (["신청서를 보내면 같은 날 견적서를 이메일로 보내 드립니다", "견적을 확인하고 회사 계좌로 입금합니다 (세금계산서·현금영수증 발행)", "입금 확인 후 영업일 2일 안에 작업을 시작합니다", "AI 초안을 사람이 검수해 이메일로 보내 드립니다"] if ko else
             ["Submit the form and we will email you a quote the same day", "Confirm the quote and pay by bank transfer (a tax invoice is issued)", "Work begins within two business days of payment", "A person reviews the AI draft, and we email you the result"])
    tier_opts = ""
    prod_opts = tier_opts + "".join(f'<option value="{pid}">{nk if ko else ne}</option>' for pid, nk, ne, *_ in offers) + f'<option value="uni">{"UNI 대학 (학과 연 49만 원 · 대학 전체 연 99만 원부터)" if ko else "UNI university (department ₩490k/yr · whole university from ₩990k/yr)"}</option><option value="member-year">{"분석 회원 연간 (198,000원)" if ko else "Analysis membership, annual (₩198,000)"}</option><option value="gcsme">{"GCSME 회원가 (20% 할인, 기업)" if ko else "GCSME member price (20% off, companies)"}</option><option value="other">{"기타 문의" if ko else "Other"}</option>'
    body = f'''<section class="phero short">{img("sign", "", 1800, 700, "bg", True)}<div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p>
<h1>{"필요한 만큼 주문하세요" if ko else "Order what you need"}</h1>
<p class="lede">{"무료 가입으로 193개국 요약을 보고, 전체 목록·분석·알림은 합리적인 월 19,800원에, 실제 사업은 직접 만나 프로젝트 파트너십으로 함께합니다. 카드 결제를 열기 전까지는 견적·계좌이체로 받고, 자동갱신은 하지 않습니다." if ko else "Sign up free for summaries of 193 countries. Full lists, analysis and alerts cost a fair ₩19,800/month, and real deals are done in person through a project partnership. Until card payment opens, we take orders by quote and bank transfer, with no auto-renewal."}</p></div></section>
<section class="band" id="tier"><div class="in"><div class="needban" id="needban" hidden></div><p class="cta" style="margin:0 0 18px"><a class="btn pri" href="/{L}/request/">{"회원 분석 의뢰 4가지 — 범위·한도·처리 기준 보고 보내기 →" if ko else "Member analysis requests — see scope, limit and handling before you send →"}</a></p><p class="note" style="margin:-8px 0 18px">{"분석 회원은 회원 의뢰(빠른 검토)를 매달 2건 포함합니다. 아래 표의 '입찰 적합도 판정(건당 10만 원)'은 서류 목록·컨소시엄 구성안까지 들어가는 상세판으로, 회원 포함 의뢰와 별개입니다." if ko else "Analysis members get two member requests (quick checks) a month. The per-tender fit assessment (KRW 100,000) below is a separate, detailed product with document list and consortium plan."}</p>
<h2>{"무료·분석 회원·파트너십 비교" if ko else "Free, analysis membership and partnership"}</h2><p class="note"><a href="/{L}/how/">{"신청 후 진행 순서·납기·고객 약속 보기 →" if ko else "How it works: steps, turnaround and our promises →"}</a></p><p class="note">{"무료로 가입하면 193개국 지도·요약·상황판·재난 대비를 보고, 각 나라의 사업·입찰·일정은 앞부분만 볼 수 있습니다. 전체 목록과 AI 분석·알림은 분석 회원(M1, 월 19,800원)부터, 사람이 하는 판단(적합도·브리프)과 직접 만나 함께하는 프로젝트 파트너십은 별도입니다." if ko else "Free sign-up shows the map, summaries, situation board and preparedness for 193 countries, plus the first items of each country's programmes, tenders and events. Full lists, AI analysis and alerts start at the analysis membership (M1, ₩19,800/month); human judgement (fit reviews, briefs) and in-person project partnerships are separate."}</p>{tier_table(L)}</div></section>
{wmm_ladder(L)}<section class="band"><div class="in"><h2>{"지금 주문할 수 있는 것" if ko else "Available now"}</h2><div class="offers">{orows}</div></div></section>
<section class="band alt"><div class="in"><h2>{"주문하면 이렇게 진행됩니다" if ko else "How an order works"}</h2><ol class="flow">{"".join(f"<li>{x}</li>" for x in steps)}</ol></div></section>
<section class="band alt" id="order"><div class="in narrow"><h2>{"신청서" if ko else "Request form"}</h2>
<form class="cform" name="order" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/thanks/"><input type="hidden" name="form-name" value="order"><p hidden><input name="hp"></p><input type="hidden" name="lang" value="{L}">
<div class="two"><label>{"신청 상품" if ko else "Product"}<select name="product" id="o-prod">{prod_opts}</select></label><label>{"관심 나라 (여러 곳 가능)" if ko else "Countries (several OK)"}<input name="countries" id="o-cty" required></label></div>
<div class="two"><label>{"회사·기관명" if ko else "Company / organisation"}<input name="org" required></label><label>{"담당자 이름" if ko else "Contact name"}<input name="name" required></label></div>
<div class="two"><label>{"업무용 이메일" if ko else "Work email"}<input name="email" type="email" required></label><label>{"분야 (예: IT, 에너지, 보건)" if ko else "Field (e.g. IT, energy, health)"}<input name="field"></label></div>
<label>{"원하는 내용 (공고 링크가 있으면 함께)" if ko else "What you need (include tender links if any)"}<textarea name="need" rows="4" maxlength="2000"></textarea></label>
<label class="chk"><input type="checkbox" name="tax_invoice" value="yes"> {"세금계산서가 필요합니다 (사업자등록증은 견적 회신 때 받습니다)" if ko else "I need a tax invoice"}</label>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> <span>{f'<a href="/{L}/legal/privacy/" target="_blank">개인정보 처리방침</a>에 동의합니다 (필수)' if ko else f'I agree to the <a href="/{L}/legal/privacy/" target="_blank">Privacy Policy</a> (required)'}</span></label>
<label class="chk"><input type="checkbox" name="marketing" value="yes"> {"새 공고·소식 이메일(광고)을 받겠습니다 (선택)" if ko else "Send me news and offers by email (optional)"}</label>
<button class="btn pri" type="submit">{"견적 요청 보내기" if ko else "Request a quote"}</button></form>
<p class="note">{"분석 회원은 VAT 포함, 기업·기관 상품은 VAT 별도 · 자동갱신 없음 · 결제일부터 7일 안에 유료 자료를 쓰지 않았다면 전액 환불 · 이용을 시작한 뒤 해지하면 남은 기간까지 이용 · 연간 선납은 이용한 달을 월 요금으로 계산해 뺀 금액 환불 · 맞춤 보고서는 작업 시작 전까지 전액 환불, 받은 뒤에는 청약철회 제한 · 학생·NGO(19세 이상) 50% 할인 · 결과물은 'AI 작성 + 사람 검수'로 표시합니다 · " if ko else "Analysis membership includes VAT; company and institutional products exclude VAT · no auto-renewal · full refund within 7 days of payment if no paid material was used · after use starts, cancel and keep access to the end of the period · annual prepay refunds the balance after charging the months used at the monthly price · custom reports are fully refundable until work starts, and cannot be withdrawn once delivered · 50% off for students and NGOs (19+) · deliverables are labelled 'AI-drafted, human-reviewed' · "}<a href="/{L}/legal/refund/">{"환불 정책" if ko else "Refund policy"}</a> · <a href="/{L}/legal/terms/">{"이용약관" if ko else "Terms"}</a> · 73036396@naver.com</p>
{credit(["sign"] + [o[-1] for o in offers], ko)}</div></section>
<script>(function(){{var NEED={json.dumps({k: [v[0], v[1] if ko else v[2]] for k, v in NEED.items()}, ensure_ascii=False)},TP={json.dumps({x[0]: (x[1]+" "+x[3]) if ko else (x[2]+" "+x[4]) for x in TIERS}, ensure_ascii=False)};var q=new URLSearchParams(location.search),p=q.get("p")||q.get("t"),c=q.get("c"),nd=q.get("need"),t=q.get("t");
if(t&&TP[t]){{document.querySelectorAll('.tiers [data-t="'+t+'"]').forEach(function(x){{x.classList.add("hit")}});var b=document.getElementById("needban");if(b){{var w=nd&&NEED[nd]?NEED[nd][1]:"";b.innerHTML="<span>"+(w?({json.dumps('보려는 내용: ' if ko else 'You want: ')}+"<b>"+w+"</b><br>"):"")+{json.dumps('가장 저렴한 등급' if ko else 'Lowest plan')}+"</span><span class=p>"+TP[t]+"</span><a class='btn pri' href='#order' data-pick='"+t+"'>"+{json.dumps('이 등급으로 신청' if ko else 'Request this plan')}+"</a>";b.hidden=false;}}}}
document.addEventListener("click",function(ev){{var a=ev.target.closest("[data-pick]");if(!a)return;ev.preventDefault();var s=document.getElementById("o-prod");if(s&&s.querySelector('option[value="'+a.dataset.pick+'"]'))s.value=a.dataset.pick;document.getElementById("order").scrollIntoView({{behavior:"smooth"}});}});if(p){{var s=document.getElementById("o-prod");if(s&&s.querySelector('option[value="'+p+'"]'))s.value=p;}}if(c){{var i=document.getElementById("o-cty");if(i)i.value=c;}}document.querySelectorAll('.offer a[href^="?p="]').forEach(function(a){{a.addEventListener("click",function(ev){{ev.preventDefault();var v=a.getAttribute("href").slice(3).split("#")[0];var s=document.getElementById("o-prod");if(s)s.value=v;document.getElementById("order").scrollIntoView({{behavior:"smooth"}});}});}});}})();</script>'''
    return C["head"](L, ("주문·요금" if ko else "Orders & pricing") + " · GOV RADAR",
                     "정보 무료 · 분석 회원 월 19,800원 · 국가 진출 브리프 · 적합도 검토 · 프로젝트 파트너십(첫 상담 무료)" if ko else "Free data · ₩19,800/month analysis · market-entry briefs · fit reviews · project partnership (first consultation free)",
                     f"/{L}/pricing/", {l: f"/{l}/pricing/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)

# ---------------------------------------------------------------- deadline board (top of /L/mdb/)
import os as _os
DLJS = open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "web", "dl.js"), encoding="utf8").read()
NB = lambda L: '<em class="nb">' + pt("new", L if isinstance(L, str) else ("ko" if L else "en")) + "</em>"
SV = {"ko": "내 관심 목록에 담기", "en": "Save to my watchlist", "es": "Guardar en mi lista", "fr": "Ajouter à ma liste", "ar": "احفظ في قائمتي", "vi": "Lưu vào danh sách của tôi", "id": "Simpan ke daftar saya"}
def deadline_board(L, C, limit=None, home=False):
    ko = L == "ko"; e = C["e"]; T = all_tenders(C["DATA"], C["BY"], C["TODAY"])
    if limit: T = T[:limit]
    free = set(range(12)); seen = {}
    for i, x in enumerate(T):
        for s in (x["sec"] or ["other"]):
            if seen.get(s, 0) < 2: free.add(i); seen[s] = seen.get(s, 0) + 1
    free = set(range(len(T)))
    def lockrow(x):
        tt = (x["te"].get("title") if not ko else None) or x["t"].get("title", "")
        return f'''<li class="lk" data-s="{" ".join(x["sec"]) or "other"}" data-dl="{x["dl"]}"><span class="dd" data-dl="{x["dl"]}">{"회원" if ko else "Members"}</span>
<a class="tt" href="{paylink(L, "tenders", x["iso"])}"><span class="cn">{C["flag"](x["iso"])} {e(C["nm"](x["iso"], L))}</span><b>{e(tt[:38])}…</b><small>{"발주처·마감일·원문 링크 — BUILD M1 월 49,000원부터" if ko else "Buyer, deadline and notice link — from BUILD M1 ₩49,000/mo"}</small></a>
<a class="src" href="{paylink(L, "tenders", x["iso"])}">{"🔒 보기" if ko else "🔒 Unlock"}</a></li>'''
    nlk = len(T) - len([i for i in range(len(T)) if i in free])
    rows = "".join(lockrow(x) if i not in free else f'''<li class="{"new" if x.get("new") else ""}" data-s="{" ".join(x["sec"]) or "other"}" data-dl="{x["dl"]}"><span class="dd" data-dl="{x["dl"]}" data-at="{e(str(x["t"].get("deadline_at") or ""))}">{x["dl"][5:].replace("-", "/")}{NB(L) if x.get("new") else ""}</span>
<span class="tt"><a href="{C["url"](L, x["iso"])}#tenders">{C["flag"](x["iso"])} {e(C["nm"](x["iso"], L))}</a><b>{e((x["te"].get("title") if not ko else None) or x["t"].get("title", ""))}</b><small>{e((x["te"].get("buyer") if not ko else None) or x["t"].get("buyer", "") or ("발주처: 원문에서 확인" if ko else "Buyer: see notice"))}</small></span>
{f'<a class="src" href="{e(x["t"]["url"])}" target="_blank" rel="noopener nofollow">{"원문" if ko else "Notice"} ↗</a>' if str(x["t"].get("url", "")).startswith("https://") else ""}<button class="sv" type="button" data-act="watch" data-iso="{x["iso"]}" data-title="{e((x["te"].get("title") if not ko else None) or x["t"].get("title", ""))}" data-deadline="{x["dl"]}" title="{SV.get(L, SV["en"])}" aria-label="{SV.get(L, SV["en"])}">☆</button></li>''' for i, x in enumerate(T))
    chips = "" if home else (f'<div class="filters dlf"><button class="chip on" data-s="all">{"전체" if ko else "All"}</button>' + "".join(f'<button class="chip" data-s="{k}">{nk if ko else ne}</button>' for k, nk, ne, *_ in SECT) + "</div>")
    js = "<script>" + DLJS + "</script>" + '''<script>(function(){var t=new Date();t.setHours(0,0,0,0);document.querySelectorAll(".dl .dd").forEach(function(s){var I=GRDL.info(s.dataset.at,s.dataset.dl),n=GRDL.days(I);if(!I.open){s.closest("li").remove();return}if(n==null)return;s.title=GRDL.label(I,document.documentElement.lang||"en");if(s.closest(".lk"))return;s.insertAdjacentHTML("beforeend","<i>D-"+(n||"day")+"</i>");if(n<=15){s.classList.add("soon");s.closest("li").classList.add("hot")}});
var cs=document.querySelectorAll(".dlf .chip");function f(k){cs.forEach(function(c){c.classList.toggle("on",c.dataset.s===k)});document.querySelectorAll(".dl li").forEach(function(li){li.hidden=!(k==="all"||li.dataset.s.split(" ").indexOf(k)>=0)})}
cs.forEach(function(c){c.addEventListener("click",function(){f(c.dataset.s)})});var q=new URLSearchParams(location.search).get("s");if(q&&cs.length)f(q);
var ul=document.querySelector(".dl[data-feed]");if(!ul)return;fetch("https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/tenders.json",{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){
var L=ul.dataset.l,have={},es=function(x){return String(x||"").replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};ul.querySelectorAll("a.src").forEach(function(a){have[a.href]=1});
var lis=[].slice.call(ul.children),add=0,wk=new Date(t);wk.setDate(wk.getDate()-7);
(j.items||[]).forEach(function(x){if(have[x.url])return;var I=GRDL.info(x.deadline_at,x.deadline),n=GRDL.days(I);if(!I.open||n==null)return;var nw=new Date(x.added+"T00:00:00")>=wk;
var li=document.createElement("li");li.className=(nw?"new ":"")+(n<=15?"hot":"");li.dataset.s=(x.sec||[]).join(" ")||"other";li.dataset.dl=x.deadline;li.dataset.pg=x.pg||"";li.dataset.pm=x.pm||"";li.dataset.est=x.est&&x.cur==="USD"?x.est:"";
li.innerHTML='<span class="dd'+(n<=15?" soon":"")+'">'+x.deadline.slice(5).replace("-","/")+(nw?'<em class="nb">'+ul.dataset.nw+'</em>':'')+"<i>D-"+(n||"day")+'</i></span><span class="tt"><a href="/'+L+'/'+x.slug+'/#tenders"><span class="fi fi-'+x.iso.toLowerCase()+'" aria-hidden="true"></span> '+es((x.n||{})[L]||(x.n||{}).en||x.iso)+'</a><b>'+es(x.title)+'</b><small>'+es(x.buyer)+' · '+es(GRDL.label(I,L))+' · ⚙ '+es((L=="ko"?{"World Bank":"세계은행","EU TED":"EU 조달공보(TED)","UK Find a Tender":"영국 정부조달","DAPA (Korea)":"방위사업청 해외입찰","UK Contracts Finder":"영국 Contracts Finder","CanadaBuys":"캐나다 CanadaBuys","Prozorro (Ukraine)":"우크라이나 Prozorro","SAM.gov (US)":"미국 SAM.gov"}[x.source]:x.source)||ul.dataset.au)+'</small></span><a class="src" href="'+es(x.url)+'" target="_blank" rel="noopener nofollow">'+ul.dataset.sr+' ↗</a>';
var at=lis.find(function(o){return o.dataset.dl&&o.dataset.dl>x.deadline});ul.insertBefore(li,at||null);add++});
var on=document.querySelector(".dlf .chip.on");if(on)f(on.dataset.s);var c=document.querySelector(".dfc");if(c&&add)c.textContent=c.dataset.t.replace("{n}",add).replace("{d}",String(j.updated||"").slice(0,10))}).catch(function(){})})();</script>'''
    leg = '<p class="dleg"><span class="lg-new">' + pt("lg_new", L) + '</span><span class="lg-hot">' + pt("lg_hot", L) + "</span></p>"
    feed = "" if home else f' data-feed="1" data-l="{L}" data-nw="{pt("new", L)}" data-sr="{"원문" if ko else "Notice"}" data-au="{pt("auto", L)}"'
    leg += "" if home else f'<p class="note dfc" data-t="{e(pt("autoc", L))}"></p>'
    return f'{chips}{leg}<ul class="dl"{feed}>{rows or "<li>—</li>"}</ul>' + ("" if home else lic_note(L)) + (tier_cta(L, "tenders", "", nlk) if nlk else "") + js + ("" if home else PREP_JS)


PREP_JS = r"""<script>(function(){var ul=document.querySelector(".dl[data-feed]");if(!ul)return;var L=ul.dataset.l,ko=L==="ko";
var W=ko?{btn:"준비할 것",type:{CW:"공사",GO:"물품",CS:"컨설팅",NC:"일반 용역"},tl:"유형",gs:"제목으로 판단",sch:"마감까지 역산 일정",docs:"보통 필요한 서류",jv:"파트너",fit:"적합도 검토 주문 (100,000원)",par:"현지 파트너 찾기",win:"수주 7단계 보기",
 s:[[21,"참여 여부 판단: 자격 요건과 회사 실적 대조"],[14,"자격 서류 확보 · 현지 파트너 확정"],[7,"제안서·입찰서 완성"],[3,"내부 검토 · 입찰보증서 발급"],[1,"제출 (시간대 확인)"]],
 short:"남은 기간이 짧습니다. 오늘 참여 여부를 정하고 서류부터 모으세요.",
 d:{CW:["입찰보증서","최근 5년 유사 공사 실적","최근 3년 재무제표","장비·핵심 인력 계획","현지 등록 또는 공동수급(JV) 협약서"],GO:["기술사양 적합표","제조사 공급 승인서(MAF)","가격·납기 견적","유사 납품 실적","제품 인증서"],CS:["관심표명서(EOI) 또는 제안서","회사 유사 실적","핵심 인력 이력서","방법론·업무 계획","현지 협력사 협약"],NC:["회사 실적","인력·장비 계획","가격 견적","보험·면허 증빙"]},
 jvy:"공사·대형 사업은 현지 등록업체와 공동수급(JV)을 검토하세요.",jvn:"현지 협력사가 있으면 평가·실행에 유리한 경우가 많습니다."}
:{btn:"What to prepare",type:{CW:"Works",GO:"Goods",CS:"Consulting",NC:"Non-consulting"},tl:"Type",gs:"judged from the title",sch:"Schedule counted back from the deadline",docs:"Documents usually required",jv:"Partner",fit:"Order a fit review (₩100,000)",par:"Find a local partner",win:"See the 7 steps",
 s:[[21,"Go/no-go: check eligibility against your record"],[14,"Collect eligibility documents · confirm local partner"],[7,"Finish the proposal or bid"],[3,"Internal review · issue the bid security"],[1,"Submit (check the time zone)"]],
 short:"Little time left. Decide today and start with the documents.",
 d:{CW:["Bid security","Similar works in the last 5 years","Financial statements, last 3 years","Equipment and key staff plan","Local registration or joint-venture agreement"],GO:["Technical compliance sheet","Manufacturer's authorisation (MAF)","Price and delivery quote","Similar supply record","Product certificates"],CS:["Expression of interest or proposal","Similar assignments","CVs of key experts","Methodology and work plan","Agreement with a local firm"],NC:["Company record","Staff and equipment plan","Price quote","Insurance and licences"]},
 jvy:"For works and large projects, consider a joint venture with a locally registered firm.",jvn:"A local partner often helps in evaluation and delivery."};
function guess(t){t=t.toLowerCase();if(/consult|용역|진단|수립|마스터플랜|연구|조사|technical assistance|\bta\b|study|assessment|design|audit|evaluation|advisor|expert|컨설팅|자문|설계|평가|감사|전문가/.test(t))return"CS";if(/construct|rehabilit|works|road|bridge|building|civil|공사|개보수|건설|개량|도로/.test(t))return"CW";if(/supply|equipment|procure|purchase|deliver|공급|장비|구매|설치/.test(t))return"GO";return""}
var t0=new Date();t0.setHours(0,0,0,0);
function box(li){var tt=(li.querySelector(".tt b")||{}).textContent||"",g=li.dataset.pg||"",gs=0;if(!W.type[g]){g=guess(tt)||"GO";gs=1}
var n=Math.round((new Date(li.dataset.dl+"T00:00:00")-t0)/864e5),est=+li.dataset.est||0,h='<div class="pp"><p><b>'+W.tl+"</b> "+W.type[g]+(li.dataset.pm?" · "+li.dataset.pm:"")+(gs?' <small>('+W.gs+")</small>":"")+"</p>";
h+="<p><b>"+W.sch+"</b></p><div class=\"pl\">";var any=0;W.s.forEach(function(s){if(s[0]<=n){var d=new Date(li.dataset.dl+"T00:00:00");d.setDate(d.getDate()-s[0]);h+="<div><span>D-"+s[0]+" · "+(d.getMonth()+1)+"/"+d.getDate()+"</span> "+s[1]+"</div>";any=1}});h+="</div>";if(!any||n<10)h+='<p class="pw">'+W.short+"</p>";
h+="<p><b>"+W.docs+"</b></p><div class=\"pd\">"+W.d[g].map(function(x){return"<span>"+x+"</span>"}).join("")+"</div><p><b>"+W.jv+"</b> "+(g==="CW"||est>5e6?W.jvy:W.jvn)+"</p>";
h+='<p class="pa"><a class="btn pri" href="/'+L+'/pricing/?p=fit#order">'+W.fit+'</a> <a class="btn" href="/'+L+'/consortium/">'+W.par+'</a> <a class="btn" href="/'+L+'/win/#steps">'+W.win+"</a></p></div>";return h}
function add(li){if(li.querySelector(".pb")||!li.dataset.dl||li.classList.contains("lk"))return;var b=document.createElement("button");b.type="button";b.className="pb";b.textContent=W.btn+" ▾";b.setAttribute("aria-expanded","false");
b.addEventListener("click",function(){var o=li.querySelector(".pp");if(o){o.remove();b.setAttribute("aria-expanded","false");return}li.insertAdjacentHTML("beforeend",box(li));b.setAttribute("aria-expanded","true")});li.appendChild(b)}
[].forEach.call(ul.children,add);new MutationObserver(function(ms){ms.forEach(function(m){[].forEach.call(m.addedNodes,function(x){if(x.nodeType===1&&x.tagName==="LI")add(x)})})}).observe(ul,{childList:true})})();</script>
<style>.dl .pb{grid-column:1/-1;justify-self:start;width:auto;font:inherit;font-size:12.5px;background:#fff;border:1px solid #c5cad3;padding:4px 12px;cursor:pointer;border-radius:14px;margin:2px 0 0}.dl .pp{grid-column:1/-1;background:#f6f7f9;border-left:3px solid #c9a45c;padding:12px 16px;margin:8px 0 4px;font-size:14px;line-height:1.6}
.dl .pp p{margin:0 0 6px}.dl .pp .pl{margin:0 0 10px}.dl .pp .pl div{padding:2px 0}.dl .pp .pl span{display:inline-block;min-width:104px;font-weight:700;color:#0b1f3a}.dl .pp .pd{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}.dl .pp .pd span{background:#fff;border:1px solid #dfe3e8;padding:3px 9px;font-size:13px}.dl .pp .pw{color:#b0263a;font-weight:700}.dl .pp .pa .btn{margin:4px 6px 0 0}</style>"""

# ---------------------------------------------------------------- country "what you can do now" box
def next_box(iso, L, C, d):
    ko = L == "ko"; e = C["e"]; G = C["G"]; out = []
    T = [x for x in all_tenders({iso: d}, C["BY"], C["TODAY"])]
    if T:
        x = T[0]; tt = (x["te"].get("title") if not ko else None) or x["t"].get("title", "")
        out.append((f'열린 입찰 {len(T)}건 — 가장 빠른 마감 {x["dl"]}' if ko else f'{len(T)} open tenders — next deadline {x["dl"]}', tt, "#tenders"))
    ks = G(d, "krsupport", L) or []
    if ks and isinstance(ks[0], dict):
        out.append(("쓸 수 있는 한국 지원" if ko else "Korean support you can use", f'{ks[0].get("title","")} · {ks[0].get("org","")}', "#krsupport"))
    bz = G(d, "biz", L) or []
    if bz:
        b = bz[0] if isinstance(bz[0], dict) else {"title": bz[0]}
        out.append(("유망 사업" if ko else "Promising business opportunity", b.get("title", ""), "#biz"))
    if len(out) < 3:
        pj = G(d, "projects", L) or []
        if pj:
            p = pj[0] if isinstance(pj[0], dict) else {"title": pj[0]}
            out.append(("정부가 돈을 쓰는 사업" if ko else "Where the government is spending", f'{p.get("title","")}{" · "+str(p.get("budget")) if p.get("budget") else ""}', "#projects"))
    if not out: return ""
    items = "".join(f'<li><a href="{h}"><small>{e(a)}</small><b>{e(b)}</b></a></li>' for a, b, h in out[:3])
    return LTR(L, f'''<section class="nextbox"><h2>{"한국 기업이 지금 할 수 있는 것" if ko else "What a Korean company can do now"}</h2><ul>{items}</ul>
<p class="cta"><button class="btn pri member" data-act="follow" data-iso="{iso}">{"이 나라 저장 (무료)" if ko else "Save this country (free)"}</button> <a class="btn" href="/{L}/pricing/?p=brief&c={e(C["nm"](iso, L))}#order">{"이 나라 진출 브리프 주문" if ko else "Order a market-entry brief"}</a></p></section>''')

# ---------------------------------------------------------------- HQ notices (/L/notices/) — posted only by WMM / GCSME KOREA
import json as _json, os as _os
def notices():
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "src", "notices.json")
    try: return sorted([x for x in _json.load(open(p, encoding="utf-8"))["items"] if x.get("public", True)], key=lambda x: x.get("date", ""), reverse=True)
    except Exception: return []
NST = {"open": ("모집·접수 중", "Open"), "progress": ("진행 중", "In progress"), "closed": ("마감", "Closed")}
NKD = {"order": ("주문 안내", "Orders"), "recruit": ("모집", "Recruiting"), "project": ("프로젝트", "Project"), "notice": ("공지", "Notice")}
def _nlink(L, x): 
    l = x.get("link", ""); return l if l.startswith("https://") else (f"/{L}/{l}" if l else "")
def notice_items(L, C, limit=None):
    ko = L == "ko"; e = C["e"]; out = []
    if not notices():
        return f'''<article class="ntc"><h3>{"지금 공개 모집 중인 본사 프로젝트는 없습니다" if ko else "No headquarters project is open right now"}</h3><p>{"새 본사 프로젝트가 생기면 이곳에 올리고, 관심 나라·분야가 맞는 회원에게 먼저 이메일로 알려 드립니다." if ko else "New headquarters projects are posted here, and members whose countries and sectors match hear about them first by email."}</p><p class="cta"><button class="btn pri" data-auth="signup">{"관심 나라 저장 (무료)" if ko else "Save your countries (free)"}</button></p></article>'''
    for x in notices()[:limit]:
        v = x.get("ko" if ko else "en") or x.get("en") or {}
        st = NST.get(x.get("status"), NST["open"]); kd = NKD.get(x.get("kind"), NKD["notice"]); lk = _nlink(L, x)
        out.append(f'''<article class="ntc" id="{e(x.get("id",""))}"><p class="nmeta"><span class="nst {e(x.get("status","open"))}">{st[0] if ko else st[1]}</span> {kd[0] if ko else kd[1]} · {e(x.get("date",""))} · {e(x.get("issuer","WMM"))}</p>
<h3>{f'<a href="{e(lk)}">{e(v.get("title",""))}</a>' if lk else e(v.get("title",""))}</h3><p>{e(v.get("body",""))}</p></article>''')
    return "".join(out)
def notices_page(L, C):
    ko = L == "ko"
    body = f'''<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{"본사 프로젝트 공지" if ko else "Headquarters project notices"}</h1>
<p class="lede" style="color:#d9d7d0;max-width:62ch">{"WMM(월드메이킹멤버스)과 GCSME KOREA와 GCSME 영국 본사가 직접 올리는 프로젝트·모집·주문 안내입니다." if ko else "Project, recruitment and order notices posted directly by WMM (World Making Members), GCSME KOREA and GCSME's UK headquarters."}</p></div></section>
<div class="in stock">{notice_items(L, C)}
<p class="note">{"이 공지란은 WMM·GCSME KOREA·GCSME 영국 본사만 올립니다. 공지를 내세워 돈을 요구하는 연락을 받으면 73036396@naver.com으로 먼저 확인하세요. WMM은 참여자에게 가입비·교육비를 받지 않습니다." if ko else "Only WMM, GCSME KOREA and GCSME's UK headquarters post here. If anyone asks you for money in connection with these notices, please check with 73036396@naver.com first. WMM never charges participants any fees."}</p></div>'''
    return C["head"](L, ("본사 프로젝트 공지" if ko else "Headquarters notices") + " · GOV RADAR",
                     "WMM · GCSME KOREA · GCSME 영국 본사가 직접 올리는 프로젝트·모집 공지" if ko else "Project and recruitment notices from WMM, GCSME KOREA and GCSME's UK headquarters",
                     f"/{L}/notices/", {l: f"/{l}/notices/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)


# ---------------------------------------------------------------- individuals (/L/individuals/)
IND = [
 ("p_review", "검증원·번역 감수", "Verifier & language reviewer", "만 19세 이상 · 재택·온라인",
  "19+ · remote", "AI가 정리한 각국 정부 정보를 원문과 대조해 맞는지 확인하고, 현지어 번역을 다듬습니다. 근무 시간은 정하지 않고 결과물마다 보수를 받습니다.",
  "Check AI-drafted government information against the originals and polish local-language translations. No fixed hours; you are paid per deliverable.",
  "정부 정보 검증 1건 10,000원부터 · 번역 감수 A4 1쪽 15,000원부터", "From ₩10,000 per verified item · from ₩15,000 per A4 page reviewed", "experts/", "지원하기", "Apply"),
 ("p_expert", "박사·기술사·기술자 전문가", "PhDs, engineers & technicians", "전문 분야가 있는 개인",
  "Individuals with specialist expertise", "국가 리포트의 기술 부분을 검토하고, 제안서 기술 파트를 쓰고, 기업에 화상으로 자문합니다. 협약 대학이 있는 나라는 그 대학 박사진과 함께 일합니다.",
  "Review the technical parts of country reports, write technical sections of proposals and advise companies by video. Where there is a partner university, you will work alongside its PhD faculty.",
  "국가 리포트 전문가 검토 150,000~300,000원 · 화상 자문 1시간 100,000원부터", "Country report review ₩150,000–300,000 · video consultation from ₩100,000 per hour", "experts/", "전문가로 등록", "Register as an expert"),
 ("p_video", "컨소시엄 개인 전문가", "Individual consortium member", "사업별 온라인 팀",
  "Online project teams", "정부·국제기구 사업마다 대학·기업·기관과 함께 팀을 꾸립니다. 개인도 전문 분야로 팀에 들어가 제안서와 사업 수행에 참여할 수 있습니다.",
  "A team is formed for each government or multilateral project, bringing together universities, companies and institutions. Individuals join for their expertise and take part in proposals and delivery.",
  "보수는 사업별 계약서로 정합니다", "Pay is set in each project contract", "consortium/", "관심 등록", "Register interest"),
 ("p_shop", "1인 기업·소상공인", "Sole traders & small businesses", "해외에 팔고 싶은 개인 사업자",
  "Business owners who want to sell abroad", "어느 나라 정부가 무엇을 사려 하는지, 그 나라에서 쓸 수 있는 한국 지원제도(수출바우처·KOTRA 등)가 무엇인지 무료로 찾고, 마감 알림을 받습니다. 필요하면 진출 브리프를 주문합니다.",
  "Find out, for free, what each government wants to buy and which Korean support schemes you can use there (export vouchers, KOTRA), and get deadline alerts. Order a market-entry brief when you need one.",
  "보기·알림 무료 · 브리프는 견적", "Browsing and alerts are free · briefs priced on quote", "mdb/", "입찰·마감 보기", "See tenders"),
 ("p_free", "프리랜서 컨설턴트·1인 창업자", "Freelance consultants & founders", "정부 사업을 고객에게 소개하는 일",
  "Bringing government work to your clients", "193개국 정부 과제·예산·입찰을 근거로 고객에게 사업 기회를 제안하고, 컨소시엄에 고객사를 연결합니다. 모든 수치에 출처가 붙어 있어 그대로 인용하기 좋습니다.",
  "Propose opportunities to your clients based on government priorities, budgets and tenders in 193 countries, and bring them into consortia. Every figure is sourced, so it is easy to cite.",
  "보기 무료 · 분석 회원 월 19,800원", "Browsing is free · analysis membership ₩19,800/mo", "pricing/", "주문·요금 보기", "Orders & pricing"),
 ("p_study", "대학생·청년·청소년", "Students & young people", "누구나 같은 무료",
  "Free for everyone", "실제 각국 정부 데이터로 국제개발·통상을 공부하고, 프로젝트 랩의 사업 아이디어로 제안서를 연습합니다. 만 14~18세는 열람·학습만 할 수 있고, 유료 작업은 만 19세부터입니다.",
  "Study international development and trade with real government data and practise writing proposals using Project Lab ideas. Those aged 14–18 can read and learn; paid work starts at 19.",
  "무료", "Free", "projects/", "프로젝트 랩 보기", "Open Project Lab"),
]
def individuals_page(L, C):
    ko = L == "ko"
    rows = "".join(f'''<article class="seg{" flip" if i % 2 else ""}"><div class="segimg">{img(ph, tk if ko else te, 900, 640)}</div>
<div class="segtx"><p class="note">{wk if ko else we}</p><h3>{tk if ko else te}</h3><p class="indp">{dk if ko else de}</p><p class="segbiz"><span>{"보수·비용" if ko else "Pay / cost"}</span>{pk if ko else pe}</p>
<p class="cta"><a class="btn pri" href="/{L}/{lk}">{bk if ko else be}</a></p></div></article>''' for i, (ph, tk, te, wk, we, dk, de, pk, pe, lk, bk, be) in enumerate(IND))
    rules = (["가입비·교육비·보증금은 받지 않습니다", "일감은 고객 주문이 있을 때만 열고, '가입하면 돈을 번다'고 약속하지 않습니다", "유료 작업은 만 19세 이상(거주국 성년 연령 이상)만 할 수 있습니다", "신분증 사진은 받지 않고, 첫 지급 전에만 본인 확인을 합니다", "국적과 관계없이 같은 일에는 같은 보수를 드립니다"] if ko else
             ["No sign-up, training or deposit fees, ever", "Work becomes available only when clients place orders; we never promise income for signing up", "Paid work is open only to people aged 19 or over (or the local age of majority, if higher)", "We never ask for ID photos; identity is verified only before the first payment", "Same work, same pay, regardless of nationality"])
    body = f'''<section class="phero">{img("p_hero", "", 1800, 900, "bg", True)}<div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a> / <a href="/{L}/solutions/">{"진출 지원" if ko else "Who it's for"}</a></p>
<h1>{"개인도 정부 사업으로 일하고 배울 수 있습니다" if ko else "Individuals can work and learn through government projects too"}</h1>
<p class="lede">{"검증원, 번역 감수, 박사·기술 전문가, 컨소시엄 팀원, 1인 사업자, 학생까지. 193개국 정부 데이터로 할 수 있는 개인의 일을 모았습니다. 모든 일은 온라인으로 합니다." if ko else "Verifiers, language reviewers, PhD and technical experts, consortium members, sole traders and students: the ways individuals can work with government data from 193 countries. Everything happens online."}</p>
<p class="cta"><a class="btn pri" href="/{L}/experts/#apply">{"검증원·전문가 지원" if ko else "Apply as a verifier or expert"}</a> <button class="btn ghost" data-auth="signup">{"무료로 가입하기" if ko else "Join free"}</button></p></div></section>
<section class="band segband"><div class="in"><h2>{"개인이 할 수 있는 여섯 가지" if ko else "Six ways for individuals to take part"}</h2>{rows}</div></section>
<section class="band alt"><div class="in"><h2>{"개인 참여자에게 약속하는 것" if ko else "Our commitments to individuals"}</h2><ul class="promise">{"".join(f"<li>{x}</li>" for x in rules)}</ul>
<p class="note">{"보수 기준은 예시이며 확정 전입니다. 세금은 한국 거주자 사업소득 3.3% 또는 기타소득 8.8% 원천징수, 해외 거주자는 거주국 기준으로 처리합니다." if ko else "Rates are indicative. Tax: Korean residents 3.3% (business income) or 8.8% (other income) withheld; for residents abroad, tax is handled under the rules of their country of residence."}</p>
{credit(["p_hero"] + [x[0] for x in IND], ko)}</div></section>'''
    return C["head"](L, ("개인 참여 안내" if ko else "For individuals") + " · GOV RADAR",
                     "검증원·번역 감수·박사·기술 전문가·컨소시엄·1인 사업자·학생: 개인이 GOV RADAR로 일하고 배우는 방법" if ko else "Verifiers, reviewers, experts, consortium members, sole traders and students: how individuals work and learn with GOV RADAR",
                     f"/{L}/individuals/", {l: f"/{l}/individuals/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)


# ---------------------------------------------------------------- free unlock (/L/unlock/): email the remaining WHY for up to 3 countries a month
# ---------------------------------------------------------------- how it works (service process & customer promises)
HOW_STEPS = [
 ("1", "둘러보기 (무료)", "Explore (free)", "193개국 정부 사업·입찰·위험을 가입 없이 봅니다. 관심 나라를 저장하면 무료 회원이 됩니다.", "Browse government programmes, tenders and risk for 193 countries without signing up. Save countries to become a free member."),
 ("2", "신청", "Request", "요금 페이지에서 등급이나 상품을 고르고 신청서를 보냅니다. 업종·관심 나라·필요한 것을 적어 주실수록 정확해집니다.", "Pick a plan or product on the pricing page and send the form. The more you tell us about your sector, countries and needs, the sharper the result."),
 ("3", "견적·확인 (영업일 1일)", "Quote (1 business day)", "영업일 1일 안에 견적서와 진행 일정을 이메일로 보냅니다. 기업은 전자세금계산서, 기관은 견적서·사업자등록증·통장 사본을 함께 드립니다.", "Within one business day we email a quote and schedule. Companies get an e-tax invoice; public bodies also get business registration and bank details."),
 ("4", "입금·시작 (영업일 1일)", "Payment & start (1 business day)", "입금을 확인하면 영업일 1일 안에 회원 권한을 열고 환영 메일을 보냅니다. 맞춤 작업은 착수 질문지 5문항을 함께 보냅니다.", "Within one business day of payment we activate your access and send a welcome email. Custom work starts with a 5-question kick-off form."),
 ("5", "받기", "Receive", "멤버십은 관심 나라 요약을 이메일로 받습니다(현재 담당자 검수 후 발송, 주 1회 목표). 브리프와 입찰 적합도 검토의 납기는 견적 때 확정합니다(보통 브리프 5~10영업일, 적합도 검토 3~5영업일).", "Members get an email summary for their countries (sent after staff review, aiming for once a week). Turnaround for briefs and tender fit reviews is confirmed with the quote (usually 5–10 business days for briefs, 3–5 for fit reviews)."),
 ("6", "수정·질문", "Revisions & questions", "맞춤 보고서는 받은 날부터 7일 안에 1회 무료로 고쳐 드립니다. 질문은 이메일로 영업일 1일 안에 답합니다.", "One free revision within 7 days of delivery for custom reports. Email questions are answered within one business day."),
 ("7", "점검", "Check-in", "시작 30일째에 만족도 3문항과 다음 단계(입찰·파트너·지원제도) 제안을 보냅니다. 기관 고객은 분기마다 온라인 점검 회의를 합니다.", "On day 30 we send a 3-question survey and next-step suggestions (tenders, partners, support schemes). Institutional clients get a quarterly online review."),
]
PROMISES = [
 ("사실은 2곳 이상 출처로 확인", "Facts checked against 2+ sources", "핵심 사실은 서로 독립된 출처 2곳 이상, 그중 1곳은 정부·국제기구·주요 언론일 때만 단정해 씁니다. 출처가 1곳이면 그렇다고 표시합니다.", "Key facts are stated plainly only with two independent sources, one of them official or a major outlet. Single-source items are labelled."),
 ("사람이 검수", "Human-reviewed", "모든 유료 결과물은 'AI 작성 + 사람 검수'로 표시하고, 보내기 전에 사람이 확인합니다.", "Every paid deliverable is labelled 'AI-drafted, human-reviewed' and checked by a person before it goes out."),
 ("틀리면 공개 정정", "Public corrections", "틀린 내용을 알려 주시면 영업일 2일 안에 확인해 고치고, 정정 기록을 남깁니다.", "Tell us about an error and we check and fix it within two business days, with a public correction record."),
 ("자동갱신 없음", "No auto-renewal", "선납 방식이며 자동으로 결제되지 않습니다. 만료 1개월 전에 이메일로 알려 드립니다.", "Prepaid, never charged automatically. We email you a month before expiry."),
 ("환불 규정 공개", "Clear refunds", "결제 후 7일 안에 유료 자료를 쓰지 않았다면 전액 환불합니다. 세부 기준은 환불 정책에 있습니다.", "Full refund within 7 days of payment if no paid material was used. Details are in the refund policy."),
 ("과장하지 않음", "No overselling", "수주·선정·매출을 보장하지 않습니다. 대신 근거와 출처를 보여 드리고 판단을 돕습니다.", "We never promise wins, selection or revenue. We show evidence and sources so you can decide."),
]
WHO_GETS = [
 ("무료 회원", "Free", ["193개국 정부 과제·사업·위험", "열린 입찰 전체 (발주처·마감일·원문)", "유망 사업 이번 주 공개 1건", "월 1회 설명회 (사전 신청)"], ["Priorities, projects and risk for 193 countries", "Every open tender with buyer, deadline and link", "One fully opened opportunity a week", "Monthly meet-up (registration)"]),
 ("분석 회원 · 월 19,800원", "Analysis member · ₩19,800/mo", ["모든 나라 유망 사업의 이유·대상 바이어", "관심 나라 10곳 주간 요약·마감 임박 알림 (이메일)", "중동 리스크 브리프(중요한 변화 시), 설명회 우선 좌석"], ["Why-now and target buyers for every country", "Weekly email: 10-country summary and closing-soon alerts", "Middle East brief on significant change, priority meet-up seats"]),
 ("프로젝트 파트너십 · 상담 후 결정", "Project partnership · after consultation", ["첫 상담 무료 (온라인 또는 서울 30분)", "파트너·컨소시엄 연결, 현지 등록·서류·제안서 동행", "성과 중심 보수 (성공보수)"], ["First 30-minute consultation free", "Partner and consortium introductions, registration, documents and proposal", "Fees weighted toward success"]),
 ("기관 라이선스 · 연 300만~990만 원", "Institutional · ₩3M–9.9M/yr", ["착수 회의와 담당자 교육", "정기 브리프, 회원사 대상 설명회", "견적서·세금계산서·사업자 서류 일괄"], ["Kick-off meeting and staff training", "Regular briefs and briefings for your member firms", "Quote, tax invoice and company documents in one pack"]),
]
FAQ = [
 ("결제는 어떻게 하나요?", "How do I pay?", "지금은 견적서를 받은 뒤 계좌이체로 결제합니다. 카드 결제는 준비 중입니다.", "For now, by bank transfer after you receive a quote. Card payment is coming."),
 ("관심 나라를 바꿀 수 있나요?", "Can I change my countries?", "언제든 이메일로 알려 주시면 다음 주 요약부터 바뀝니다.", "Yes, email us any time and the next weekly summary will reflect it."),
 ("여러 명이 같이 써도 되나요?", "Can several people use it?", "분석 회원은 1명 기준입니다. 여러 명이 쓰려면 기관 라이선스를 권합니다.", "An analysis membership is for one person. For teams, choose an institutional licence."),
 ("무료 가입으로는 어디까지 보나요?", "What does a free sign-up show?", "193개국 지도·나라별 요약·상황판·재난 대비는 모두 보고, 각 나라의 정부 사업·입찰·일정은 앞부분(항목별 2건, 일정 3건)만 봅니다. 전체 목록과 분석·알림은 분석 회원(M1, 월 19,800원)부터 열립니다.", "The map, country summaries, situation board and preparedness for 193 countries, plus the first items of each country's programmes, tenders and events (2 per section, 3 events). Full lists, analysis and alerts open from the analysis membership (M1, ₩19,800/month)."),
 ("정보가 틀리면요?", "What if something is wrong?", "73036396@naver.com 으로 알려 주세요. 영업일 2일 안에 확인해 고치고 정정 기록을 남깁니다.", "Email 73036396@naver.com. We check and correct within two business days and log the correction."),
 ("해외 입찰을 대신 내 주나요?", "Do you submit bids for us?", "입찰 참여 결정과 제출은 고객이 합니다. 우리는 정보·적합도 검토·제안서 초안·파트너 연결을 돕습니다.", "You decide and submit. We help with information, fit reviews, draft proposals and partner introductions."),
]
def how_page(L, C):
    ko = L == "ko"; e = C["e"]
    steps = "".join(f'<li class="hstep"><span class="n">{n}</span><div><b>{e(hk if ko else he)}</b><p>{e(dk if ko else de)}</p></div></li>' for n, hk, he, dk, de in HOW_STEPS)
    prom = "".join(f'<div class="card"><h3>✓ {e(a if ko else b)}</h3><p>{e(c if ko else d)}</p></div>' for a, b, c, d in PROMISES)
    gets = "".join(f'<div class="card"><h3>{e(a if ko else b)}</h3><ul>' + "".join(f"<li>{e(x)}</li>" for x in (c if ko else d)) + '</ul></div>' for a, b, c, d in WHO_GETS)
    faq = "".join(f'<details class="faq"><summary>{e(a if ko else b)}</summary><p>{e(c if ko else d)}</p></details>' for a, b, c, d in FAQ)
    fb = f"""<form class="cform" name="feedback" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/thanks/"><input type="hidden" name="form-name" value="feedback"><p hidden><input name="hp"></p><input type="hidden" name="lang" value="{L}">
<div class="two"><label>{"만족도 (1~5)" if ko else "Satisfaction (1–5)"}<select name="score" required><option value="">—</option>{"".join(f'<option>{i}</option>' for i in range(5,0,-1))}</select></label><label>{"이용 중인 상품" if ko else "Plan or product"}<input name="product"></label></div>
<label>{"가장 도움이 된 것" if ko else "What helped most"}<input name="best"></label>
<label>{"고쳐야 할 것 · 틀린 정보 신고" if ko else "What to improve · report an error"}<textarea name="improve" rows="3"></textarea></label>
<label>{"답변 받을 이메일 (선택)" if ko else "Email for a reply (optional)"}<input name="email" type="email"></label>
<button class="btn pri" type="submit">{"보내기" if ko else "Send"}</button><p class="note">{"이메일은 답변을 드릴 때만 쓰고, 답변 후 삭제합니다." if L=="ko" else "We use your email only to reply and delete it afterwards."}</p></form>"""
    body = f"""<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a> · <a href="/{L}/pricing/">{"요금" if ko else "Pricing"}</a></p>
<h1>{"서비스는 이렇게 진행됩니다" if ko else "How the service works"}</h1>
<p class="lede" style="color:#d9d7d0;max-width:64ch">{"신청부터 결과물을 받기까지 무엇을, 언제까지, 어떤 기준으로 드리는지 미리 약속합니다." if ko else "From request to delivery: what you get, by when, and to what standard — promised up front."}</p></div></section>
<div class="in stock">
<section class="sec"><h2>{"진행 순서" if ko else "Step by step"}</h2><ol class="hsteps">{steps}</ol></section>
<section class="sec"><h2>{"등급별로 받는 것" if ko else "What each plan delivers"}</h2><div class="hgrid">{gets}</div><p class="cta"><a class="btn pri" href="/{L}/pricing/#tier">{"요금·등급 비교" if ko else "Compare plans"}</a> <a class="btn" href="/{L}/sample/">{"샘플 브리프 보기" if ko else "See a sample brief"}</a></p></section>
<section class="sec"><h2>{"고객께 드리는 약속" if ko else "Our promises"}</h2><div class="hgrid">{prom}</div><p class="note"><a href="/{L}/verify/">{"검증 원칙" if ko else "Verification principles"}</a> · <a href="/{L}/legal/refund/">{"환불 정책" if ko else "Refund policy"}</a> · <a href="/{L}/legal/terms/">{"이용약관" if ko else "Terms"}</a></p></section>
<section class="sec"><h2>{"자주 묻는 질문" if ko else "FAQ"}</h2>{faq}</section>
<section class="sec" id="feedback"><h2>{"의견 보내기" if ko else "Send feedback"}</h2><p class="note">{"회원·고객이 아니어도 됩니다. 받은 의견은 매주 검토해 사이트에 반영합니다." if ko else "Anyone can send it. We review feedback weekly and act on it."}</p>{fb}</section>
</div>"""
    title = ("서비스 진행 방식" if ko else "How it works") + " · GOV RADAR"
    return C["head"](L, title, title, f"/{L}/how/", {l: f"/{l}/how/" for l in C["LANGS"]}) + body + C["foot"](L)

EDGE = [
 ("먼저 알려 줍니다", "We tell you first", "AI는 물어봐야 답합니다. 우리는 고객 업종에 맞는 공고·사업이 나오면 먼저 찾아 알려 드립니다.", "AI answers when asked. We watch for tenders and programmes in your field and tell you first."),
 ("사람을 연결합니다", "We connect people", "GCSME 193개국 네트워크, 현지 파트너, 협약 대학 박사진과 연결합니다. AI는 대신해 줄 수 없습니다.", "We introduce you to the GCSME network across 193 countries, local partners and partner-university experts — something AI cannot do."),
 ("책임지고 함께 갑니다", "We stay accountable", "공급자 등록·서류·컨소시엄·제안서까지 함께 하고, 보수는 성공보수 중심입니다.", "We work with you through registration, documents, consortium and proposal, and our fee is weighted toward success."),
 ("한국 기업 기준으로 묶습니다", "Built for Korean firms", "기회마다 쓸 수 있는 KOICA·EDCF·수출바우처와 한국 기업 수주 사례를 함께 보여 드립니다.", "Each opportunity comes with the Korean support schemes you can use and past Korean wins."),
 ("검증하고 기록합니다", "Verified and on record", "핵심 사실은 출처 2곳 이상으로 확인하고, 틀리면 공개 정정합니다. 우리가 미리 짚은 사업이 실제 발주됐는지 기록을 쌓고 있습니다(2026년 11월 시작).", "Key facts are checked against two sources and corrected in public. We keep a record of whether the projects we flagged were actually tendered (started November 2026)."),
]
def edge_html(L):
    ko = L == "ko"
    cards = "".join(f'<div class="card"><h3>{a if ko else b}</h3><p>{c if ko else d}</p></div>' for a, b, c, d in EDGE)
    return (f'<section class="band"><div class="in"><h2>{"AI에게 물어보는 것과 무엇이 다른가" if ko else "Why not just ask an AI?"}</h2>'
            f'<p class="note">{"정보는 누구나 AI로 얻을 수 있습니다. 우리는 그 다음 — 알림, 사람, 실행, 책임 — 을 합니다." if ko else "Anyone can get information from AI. We do what comes next: alerts, people, execution and accountability."}</p>'
            f'<div class="hgrid">{cards}</div><p class="cta"><a class="btn pri" href="/{L}/pricing/?p=partner#order">{"프로젝트 파트너십 무료 상담" if ko else "Free partnership consultation"}</a> <a class="btn" href="/{L}/how/">{"진행 방식" if ko else "How it works"}</a></p></div></section>')

def thanks2_page(L, C):
    ko = L == "ko"
    steps = [("영업일 1일 안에 견적서와 일정을 이메일로 보냅니다.", "Within one business day we email a quote and schedule."),
             ("메일이 안 보이면 스팸함을 확인하시거나 73036396@naver.com 으로 알려 주세요.", "If you can't find it, check spam or write to 73036396@naver.com."),
             ("입금이 확인되면 영업일 1일 안에 시작합니다. 맞춤 작업은 착수 질문 5개를 함께 보냅니다.", "Work starts within one business day of payment; custom work comes with a 5-question kick-off form."),
             ("무료 신청(이유 받기·의견)은 받은 순서대로 이메일로 답합니다.", "Free requests (unlock, feedback) are answered by email in order received.")]
    li = "".join(f"<li>{a if ko else b}</li>" for a, b in steps)
    body = f"""<section class="chero"><div class="in"><h1>{"신청을 받았습니다. 감사합니다" if ko else "Thank you — we've got your request"}</h1>
<p class="lede" style="color:#d9d7d0">{"다음 순서로 진행합니다." if ko else "Here is what happens next."}</p></div></section>
<div class="in stock narrow"><ol class="hsteps" style="padding-left:20px;list-style:decimal">{li}</ol>
<p class="cta"><a class="btn pri" href="/{L}/how/">{"진행 방식·고객 약속 보기" if ko else "How it works"}</a> <a class="btn" href="/{L}/sample/">{"샘플 브리프" if ko else "Sample brief"}</a> <a class="btn" href="/{L}/">{"홈으로" if ko else "Home"}</a></p></div>"""
    return C["head"](L, "GOV RADAR", "thanks", f"/{L}/thanks/", {l: f"/{l}/thanks/" for l in C["LANGS"]}, '<meta name="robots" content="noindex">') + body + C["foot"](L)

def sample_page(L, C, iso="ZA"):
    """Public sample of a market-entry brief, built from one country's verified data (everything unlocked)."""
    ko = L == "ko"; e = C["e"]; G = C["G"]; d = C["DATA"].get(iso, {})
    def g(k): return G(d, k, L) if L != "ko" else d.get(k)
    def li(xs, f): return "".join(f"<li>{f(x)}</li>" for x in (xs or []) if x)
    nm = C["nm"](iso, L)
    proj = li(g("projects"), lambda x: f'<b>{e(x.get("title"))}</b>' + (f' — {e(x.get("detail",""))}' if x.get("detail") else "") + (f' <span class="note">{e(x.get("ministry",""))} {e(x.get("budget",""))}</span>' if x.get("ministry") or x.get("budget") else ""))
    biz = li(g("biz"), lambda x: f'<b>{e(x.get("title"))}</b>' + (f'<br>{"이유" if ko else "Why now"}: {e(x.get("why",""))}' if x.get("why") else "") + (f'<br>{"대상 바이어" if ko else "Target buyers"}: {e(x.get("target",""))}' if x.get("target") else ""))
    td = li(g("tenders"), lambda x: f'<b>{e(x.get("title"))}</b> — {e(x.get("buyer",""))} · {"마감" if ko else "deadline"} {e(x.get("deadline",""))}' + (f' · <a href="{e(x["url"])}" target="_blank" rel="noopener nofollow">{"원문" if ko else "Notice"} ↗</a>' if str(x.get("url","")).startswith("https://") else ""))
    krs = li(g("krsupport"), lambda x: f'<b>{e(x.get("title"))}</b> — {e(x.get("detail",""))}')
    rk = d.get("risk_en" if not ko else "risk") or {}
    risk = li((rk.get("conflict") or []) + (rk.get("disaster") or []) + (rk.get("epidemic") or []), lambda x: e(x))
    src = li(d.get("sources"), lambda x: f'<a href="{e(x.get("url",""))}" target="_blank" rel="noopener nofollow">{e(C["stl"](x.get("title",""), x.get("url",""), L) if C.get("stl") else x.get("title",""))}</a>')
    nxt = (["이 나라 전자조달 포털에 공급자 등록 여부 확인", "위 입찰 중 1건을 골라 입찰 적합도 검토 받기", "한국 지원제도(위 목록) 중 해당하는 1개에 이번 분기 신청", "현지 파트너 후보 2~3곳 목록 만들기"] if ko else
           ["Check supplier registration on the national e-procurement portal", "Pick one tender above and get a fit review", "Apply this quarter to one Korean support programme listed above", "List 2–3 local partner candidates"])
    sec = lambda h, body: f'<section class="sec"><h2>{h}</h2>{body}</section>' if body else ""
    body = f"""<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a> · <a href="/{L}/pricing/">{"요금" if ko else "Pricing"}</a></p>
<h1>{"샘플: 국가 진출 브리프" if ko else "Sample: market-entry brief"} — {e(nm)}</h1>
<p class="lede" style="color:#d9d7d0;max-width:66ch">{"실제 주문하시면 이런 내용을 고객의 업종·제품에 맞춰 사람이 검수해 보내 드립니다. 이 샘플은 GOV RADAR에 공개된 자료와 회원 전용 자료(이유·대상 바이어)를 한 나라만 모두 열어 보여 드립니다. 'AI 작성 + 사람 검수' 자료입니다." if ko else "When you order, we tailor this to your sector and products and a person reviews it. This sample opens everything for one country, including member-only why-now and target buyers. AI-drafted, human-reviewed."}</p></div></section>
<div class="in stock narrow">
<p class="note">{"기준일" if ko else "As of"} {e(d.get("updated",""))} · {"출처는 맨 아래에 있습니다." if ko else "Sources are listed at the end."}</p>
{sec("1. " + ("요약" if ko else "Summary"), f"<p>{e(g('summary') or '')}</p><p><b>{'정부·지도자' if ko else 'Government'}</b>: {e(g('leader') or '')}</p>")}
{sec("2. " + ("정부 핵심 과제" if ko else "Government priorities"), "<ul>" + li(g("agenda"), lambda x: e(x)) + "</ul>")}
{sec("3. " + ("정부 사업과 예산" if ko else "Programmes and budgets"), "<ul>" + proj + "</ul>")}
{sec("4. " + ("유망 사업 — 이유와 대상 바이어 (회원 전용 내용)" if ko else "Opportunities — why now and target buyers (member content)"), "<ul>" + biz + "</ul>")}
{sec("5. " + ("지금 열린 입찰" if ko else "Open tenders"), "<ul>" + td + "</ul>")}
{sec("6. " + ("쓸 수 있는 한국 지원제도" if ko else "Korean support you can use"), "<ul>" + krs + "</ul>")}
{sec("7. " + ("위험" if ko else "Risks"), "<ul>" + risk + "</ul>")}
{sec("8. " + ("다음 행동" if ko else "Next steps"), "<ol>" + "".join(f"<li>{e(x)}</li>" for x in nxt) + "</ol>")}
{sec(("출처" if ko else "Sources"), "<ul>" + src + "</ul>")}
<div class="lockbox"><p><b>{"내 업종에 맞춘 브리프를 받으시겠어요?" if ko else "Want one tailored to your business?"}</b></p>
<p class="cta"><a class="btn pri" href="/{L}/pricing/?p=brief#order">{"국가 진출 브리프 신청 (300,000원부터)" if ko else "Order a brief (from ₩300,000)"}</a> <a class="btn" href="{paylink(L, "biz", iso)}">{"모든 나라 이유·바이어 — 분석 회원 월 19,800원" if ko else "All countries — analysis member ₩19,800/mo"}</a></p></div>
</div>"""
    title = ("샘플 국가 진출 브리프 — " if ko else "Sample market-entry brief — ") + nm
    return C["head"](L, title, title, f"/{L}/sample/", {l: f"/{l}/sample/" for l in C["LANGS"]}) + body + C["foot"](L)

def unlock_page(L, C):
    ko = L == "ko"
    body = f"""<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{"유망 사업의 이유·대상 바이어 받기 (무료)" if ko else "Get the why-now and target buyers (free)"}</h1>
<p class="lede" style="color:#d9d7d0;max-width:62ch">{"관심 나라를 적어 주시면 사람이 검수한 요약을 이메일로 보내 드립니다. 무료 회원은 매월 3개국까지, BUILD 회원은 제한 없이 받습니다." if ko else "Tell us the countries you follow and we email a human-reviewed summary. Free members get up to 3 countries a month; BUILD members get every country."}</p></div></section>
<div class="in stock narrow"><form class="cform" name="unlock" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/thanks/"><input type="hidden" name="form-name" value="unlock"><p hidden><input name="hp"></p><input type="hidden" name="lang" value="{L}">
<div class="two"><label>{"관심 나라 (최대 3개)" if ko else "Countries (up to 3)"}<input name="countries" id="u-cty" required></label><label>{"업무용 이메일" if ko else "Work email"}<input name="email" type="email" required></label></div>
<div class="two"><label>{"회사·기관명 (선택)" if ko else "Company / organisation (optional)"}<input name="org"></label><label>{"분야 (선택)" if ko else "Field (optional)"}<input name="field"></label></div>
<label class="chk"><input type="checkbox" name="adult14" value="yes" required> {"만 14세 이상입니다" if ko else "I am 14 or older"}</label>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> <span>{f'<a href="/{L}/legal/privacy/" target="_blank">개인정보 처리방침</a>에 동의합니다 (필수)' if ko else f'I agree to the <a href="/{L}/legal/privacy/" target="_blank">Privacy Policy</a> (required)'}</span></label>
<label class="chk"><input type="checkbox" name="marketing" value="yes"> {"새 공고·소식 이메일(광고)을 받겠습니다 (선택)" if ko else "Send me news and offers by email (optional)"}</label>
<button class="btn pri" type="submit">{"요약 받기" if ko else "Send me the summary"}</button></form>
<p class="note">{"영업일 기준 24시간 안에 보내 드립니다. 요약은 받는 분만 보시고 다른 곳에 올리지 말아 주세요(약관 제10조)." if ko else "Sent within one business day. Summaries are for the recipient only; please do not republish them (Terms, art. 10)."}</p></div>
<script>(function(){{var c=new URLSearchParams(location.search).get("c");if(c){{var i=document.getElementById("u-cty");if(i)i.value=c;}}}})();</script>"""
    return C["head"](L, ("유망 사업 이유 받기" if ko else "Get the why-now") + " · GOV RADAR", "무료 회원용 유망 사업 이유·대상 바이어 이메일 요약" if ko else "Free email summaries of why-now and target buyers",
                     f"/{L}/unlock/", {l: f"/{l}/unlock/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)

# ---------------------------------------------------------------- GCSME members (/L/gcsme/) — alternative A
def gcsme_page(L, C):
    ko = L == "ko"
    rows = [("Analysis membership", "US$15/mo", "월 19,800원 → 회원가 약 20% 할인", "All why-now & target buyers, weekly alerts for 10 countries"),
            ("Market-entry brief", "from US$220", "300,000원부터 → 회원가", "One country, human-reviewed, turnaround confirmed with the quote"),
            ("Project partnership", "free first call", "첫 상담 무료 · 비용은 상담 후 결정", "Introductions to Korean partners and consortia; fees agreed after the first call")]
    tr = "".join(f"<tr><th>{a}</th><td><b>{b}</b></td><td>{c if ko else d}</td></tr>" for a, b, c, d in rows)
    body = f"""<section class="phero short">{img("hand", "", 1800, 700, "bg", True)}<div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p>
<h1>{"GCSME 회원 전용 GOV RADAR" if ko else "GOV RADAR for GCSME members"}</h1>
<p class="lede">{"Global & Commonwealth SME Club 회원사는 회원가로 GOV RADAR를 이용하고, 한국·아시아 정부 사업과 한국 파트너를 찾을 수 있습니다. 판단 정보는 회원에게만 공개합니다." if ko else "Global & Commonwealth SME Club members use GOV RADAR at member prices to find government projects in Korea, Asia and beyond, and Korean partners. Our analysis is shared with members only."}</p></div></section>
<section class="band"><div class="in narrow"><h2>{"회원가" if ko else "Member prices"}</h2><table class="ptable">{tr}</table>
<p class="note">{"기업(B2B)에만 판매합니다. 회사명·사업자번호(또는 VAT 번호)를 받으며, 영문 인보이스와 해외 송금 또는 PayPal로 결제합니다. 미국 달러 가격은 예시이며 견적서로 확정합니다. 자동갱신 없음." if ko else "Sold to companies only (B2B). We ask for your company name and registration or VAT number; payment by English invoice and bank transfer or PayPal. USD prices are indicative and confirmed on the quote. No auto-renewal."}</p></div></section>
<section class="band alt" id="join"><div class="in narrow"><h2>{"회원 신청" if ko else "Member request"}</h2>
<form class="cform" name="gcsme-member" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/thanks/"><input type="hidden" name="form-name" value="gcsme-member"><p hidden><input name="hp"></p><input type="hidden" name="lang" value="{L}"><input type="hidden" name="ref" id="g-ref">
<div class="two"><label>{"회사명" if ko else "Company"}<input name="org" required></label><label>{"국가" if ko else "Country"}<input name="country" required></label></div>
<div class="two"><label>{"사업자·VAT 번호" if ko else "Company / VAT number"}<input name="vat" required></label><label>{"업무용 이메일" if ko else "Work email"}<input name="email" type="email" required></label></div>
<div class="two"><label>{"관심 상품" if ko else "Product"}<select name="product"><option>Analysis membership</option><option>Market-entry brief</option><option>Project partnership</option></select></label><label>{"관심 나라" if ko else "Countries of interest"}<input name="countries"></label></div>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> <span>{f'<a href="/{L}/legal/privacy/" target="_blank">개인정보 처리방침</a>에 동의합니다 (필수)' if ko else f'I agree to the <a href="/{L}/legal/privacy/" target="_blank">Privacy Policy</a> (required)'}</span></label>
<button class="btn pri" type="submit">{"견적 받기" if ko else "Request a quote"}</button></form>
{credit(["hand"], ko)}</div></section>
<script>(function(){{var r=new URLSearchParams(location.search).get("ref");if(r){{var i=document.getElementById("g-ref");if(i)i.value=r;try{{localStorage.setItem("wmm.ref",r)}}catch(e){{}}}}}})();</script>"""
    return C["head"](L, ("GCSME 회원" if ko else "GCSME members") + " · GOV RADAR", "GCSME 회원 전용 GOV RADAR 회원가" if ko else "GOV RADAR member prices for GCSME members",
                     f"/{L}/gcsme/", {l: f"/{l}/gcsme/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)

# ---------------------------------------------------------------- partner programme (/L/partners/) — alternative B
def partners_page(L, C):
    ko = L == "ko"
    ways = ([("기관 재판매", "테크노파크·상공회의소·협회가 회원사에게 GOV RADAR 기관 라이선스를 제공합니다.", "기관 라이선스 가격 기준, 재판매 할인은 계약으로 정함"),
             ("소개 파트너", "컨설팅사·회계법인·대학 산학협력단이 고객을 소개하고, 소개 코드로 성사된 첫 계약에 소개 수수료를 받습니다.", "첫 결제액의 10% (계약으로 확정)"),
             ("공동 설명회", "대사관·무역관·지자체와 국가별 진출 설명회를 온라인으로 함께 엽니다.", "비용 없음, 참가 기업 대상 상품 안내")]
            if ko else
            [("Institutional resale", "Technoparks, chambers and associations provide GOV RADAR institutional licences to their members.", "Institutional licence prices; resale discount set by contract"),
             ("Referral partner", "Consultancies, accounting firms and university offices refer clients and earn a fee on the first contract closed with their referral code.", "10% of the first payment (set by contract)"),
             ("Joint briefings", "Run online country briefings with embassies, trade offices and local governments.", "No cost; products offered to attending companies")])
    cards = "".join(f'<div class="way"><b>{a}</b><p>{b}</p><p class="note">{c}</p></div>' for a, b, c in ways)
    body = f"""<section class="phero short">{img("site", "", 1800, 700, "bg", True)}<div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p>
<h1>{"GOV RADAR 파트너 프로그램" if ko else "GOV RADAR partner programme"}</h1>
<p class="lede">{"기관과 전문가가 각자의 회원·고객에게 GOV RADAR를 전하고 함께 수익을 나눕니다." if ko else "Institutions and professionals bring GOV RADAR to their members and clients, and share the revenue."}</p></div></section>
<section class="band"><div class="in"><div class="ways3">{cards}</div>
<p class="note">{"소개 수수료와 재판매 조건은 서면 계약으로 정합니다. 파트너는 GOV RADAR에 대해 계약서·사이트에 없는 약속(수주 보장 등)을 할 수 없으며, 정부·국제기구 사업에는 반부패·수수료 공개 조항을 적용합니다." if ko else "Referral fees and resale terms are set in a written contract. Partners may not promise anything not in the contract or on the site (such as guaranteed wins); anti-bribery and fee-disclosure clauses apply to government and multilateral work."}</p></div></section>
<section class="band alt"><div class="in narrow"><h2>{"파트너 신청" if ko else "Apply as a partner"}</h2>
<form class="cform" name="partner-apply" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/thanks/"><input type="hidden" name="form-name" value="partner-apply"><p hidden><input name="hp"></p><input type="hidden" name="lang" value="{L}">
<div class="two"><label>{"기관·회사명" if ko else "Organisation"}<input name="org" required></label><label>{"담당자" if ko else "Contact"}<input name="name" required></label></div>
<div class="two"><label>{"업무용 이메일" if ko else "Work email"}<input name="email" type="email" required></label><label>{"파트너 유형" if ko else "Partner type"}<select name="type"><option>{ways[0][0]}</option><option>{ways[1][0]}</option><option>{ways[2][0]}</option></select></label></div>
<label>{"회원·고객 규모와 분야" if ko else "Members / clients and sectors"}<textarea name="detail" rows="3"></textarea></label>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> <span>{f'<a href="/{L}/legal/privacy/" target="_blank">개인정보 처리방침</a>에 동의합니다 (필수)' if ko else f'I agree to the <a href="/{L}/legal/privacy/" target="_blank">Privacy Policy</a> (required)'}</span></label>
<button class="btn pri" type="submit">{"신청 보내기" if ko else "Send application"}</button></form>{credit(["site"], ko)}</div></section>"""
    return C["head"](L, ("파트너 프로그램" if ko else "Partner programme") + " · GOV RADAR", "GOV RADAR 재판매·소개·공동 설명회 파트너" if ko else "GOV RADAR resale, referral and joint-briefing partners",
                     f"/{L}/partners/", {l: f"/{l}/partners/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)


# ---------------------------------------------------------------- analysis-member access (/L/member/)
def member_page(L, C):
    ko = L == "ko"
    body = f'''<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{"분석 회원 열람" if ko else "Analysis member access"}</h1>
<p class="lede" style="color:#d9d7d0;max-width:62ch">{"입금 확인 후 이메일로 받은 개인 열람 링크를 누르거나, 열람 코드를 아래에 넣으세요. 이 브라우저에서 모든 나라의 '왜 지금인지·누가 살 사람인지'가 열립니다." if ko else "Open the personal link we emailed after payment, or enter your access code below. Every country's why-now and target buyers then open in this browser."}</p></div></section>
<section class="band"><div class="in" style="max-width:640px">
<div id="mstate" class="note" role="status"></div>
<form id="mform" class="mform" onsubmit="return false"><label>{"열람 코드" if ko else "Access code"}<input id="mcode" autocomplete="off" placeholder="XXXX-XXXX-XXXX-XXXX" style="text-transform:uppercase"></label>
<p class="cta"><button class="btn pri" id="mgo" type="button">{"열기" if ko else "Unlock"}</button> <button class="btn" id="mout" type="button">{"이 브라우저에서 해제" if ko else "Sign out on this browser"}</button></p></form>
<p class="note">{"코드는 본인만 쓰세요. 여러 사람이 함께 쓰려면 기관 라이선스를 이용해 주세요. 코드를 잃어버렸으면 73036396@naver.com으로 연락 주세요." if ko else "Keep the code to yourself. For several users, choose an institutional licence. Lost your code? Write to 73036396@naver.com."}</p>
<p class="cta"><a class="btn" href="/{L}/pricing/?p=member#order">{"분석 회원 신청 (월 19,800원)" if ko else "Become an analysis member (₩19,800/mo)"}</a></p>
</div></section>'''
    return C["head"](L, ("분석 회원 열람" if ko else "Analysis member access") + " · GOV RADAR",
                     "분석 회원 개인 열람 코드로 잠긴 분석을 엽니다" if ko else "Open member-only analysis with your personal access code",
                     f"/{L}/member/", {l: f"/{l}/member/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)


# ---------------------------------------------------------------- what is open to whom (home + pricing)
ACCESS = [
 ("open", "누구나 · 가입 없이", "Anyone · no sign-up", "무료", "Free",
  ["193개국 개요·국정 과제·정부 사업", "모든 입찰 목록(발주처·마감·원문 링크)", "전쟁·분쟁·자연재해·감염병 상황판", "유망 사업 제목 + 나라마다 매주 1건 분석 공개"],
  ["Overview, priorities and programmes for 193 countries", "Every open tender (buyer, deadline, notice link)", "War, conflict, disaster and outbreak board", "Opportunity titles + one fully opened analysis per country each week"],
  "#map", "나라 찾기", "Find a country", ""),
 ("free", "무료 가입 · 이메일만", "Free sign-up · email only", "무료", "Free",
  ["나라별 '정부에 파는 법'(조달 등록·현지 파트너 요건)", "한국 기업 수주 실적 전체", "입찰 참가 조건 상세(매출·실적·인증·컨소시엄)", "관심 나라 저장·내 입찰 담기"],
  ["How to sell to each government (registration, local-partner rules)", "All past Korean wins", "Detailed tender eligibility (revenue, track record, certificates, consortium)", "Save countries and keep your own tender list"],
  "", "무료 가입", "Sign up free", "signup"),
 ("member", "분석 회원", "Analysis member", "월 19,800원", "₩19,800/mo",
  ["모든 나라의 '왜 지금·누가 살 사람·근거' 전체", "주간 맞춤 이메일: 관심 10개국 요약·마감 임박 알림", "중동 리스크 브리프 (중요한 변화 시)", "회원에게 맞는 본사 프로젝트 개인 안내·설명회 우선 좌석"],
  ["Why-now, target buyers and basis for every country", "Weekly email: 10-country summary and closing-soon alerts", "Middle East risk brief (on significant change)", "Personal invitations to matching HQ projects, priority meet-up seats"],
  "pricing/?p=member#order", "분석 회원 신청", "Become a member", ""),
 ("order", "주문형 · 사람이 함께", "On request · with a person", "상담 후", "After a call",
  ["국가 진출 브리프 30만 원부터", "입찰 적합도 검토 10만 원", "프로젝트 파트너십: 첫 상담 무료, 착수금·성공보수는 상담 후 결정"],
  ["Market-entry brief from ₩300,000", "Tender fit review ₩100,000", "Project partnership: first call free, fees agreed after it"],
  "pricing/?p=partner#order", "무료 상담 신청", "Book a free call", ""),
]
def access_html(L):
    ko = L == "ko"
    cols = []
    for key, hk, he, pk, pe, ik, ie, link, bk, be, auth in ACCESS:
        btn = (f'<button class="btn{" pri" if key == "free" else ""}" data-auth="signup">{bk if ko else be}</button>' if auth
               else f'<a class="btn{" pri" if key == "member" else ""}" href="/{L}/{link}">{bk if ko else be}</a>')
        cols.append(f'<div class="acc acc-{key}"><p class="acc-h">{hk if ko else he}</p><p class="acc-p">{pk if ko else pe}</p><ul>'
                    + "".join(f"<li>{x}</li>" for x in (ik if ko else ie)) + f'</ul><p class="cta">{btn}</p></div>')
    h = "무엇을 어디까지 볼 수 있나" if ko else "What you can see, and when"
    p = "가입하면 요약과 실무 자료 일부가, 회원이면 분석이 열리고, 실제 사업은 사람이 함께 갑니다." if ko else "Sign up for summaries and some working details, become a member for full lists and analysis, and do real deals with a person alongside you."
    return f'<section class="band" id="access"><div class="in"><h2>{h}</h2><p class="note">{p}</p><div class="accs">{"".join(cols)}</div></div></section>'

REVIEW = {
 "ko": "M2부터 심사 등급 — 심사를 거쳐 가입하며, M3부터는 심사가 진행되는 동안 투자자와의 협의도 함께 시작할 수 있습니다.",
 "en": "From M2, membership is by review — you join after a review, and from M3 investor discussions can start while the review is under way.",
 "es": "Desde M2, la membresía requiere evaluación: se accede tras una revisión y, desde M3, las conversaciones con inversores pueden empezar mientras la revisión está en curso.",
 "fr": "À partir de M2, l’adhésion se fait sur examen : vous rejoignez après un examen et, dès M3, les échanges avec des investisseurs peuvent commencer pendant l’examen.",
 "ar": "ابتداءً من M2 تكون العضوية بعد مراجعة: تنضم بعد المراجعة، وابتداءً من M3 يمكن بدء النقاش مع المستثمرين أثناء المراجعة.",
 "vi": "Từ M2, tư cách thành viên cần xét duyệt: bạn tham gia sau khi được xét duyệt, và từ M3 có thể bắt đầu trao đổi với nhà đầu tư ngay trong thời gian xét duyệt.",
 "id": "Mulai M2, keanggotaan melalui peninjauan: Anda bergabung setelah ditinjau, dan mulai M3 pembicaraan dengan investor dapat dimulai selama peninjauan berlangsung.",
}
def review_row(L, cols):
    return (f'<tr class="rvw"><td colspan="{cols}" style="border-top:2px dashed #d32f2f;border-bottom:0;padding:12px 15px;color:#c62828;font-weight:700;text-align:start">'
            f'{REVIEW[L]}</td></tr>')
MS_TX = {
 "es": dict(t="Membresía WMM", h="Membresía WMM — de la primera mirada a la ejecución", lede="Acompañamos a las empresas en su salida al exterior, desde el diagnóstico hasta la ejecución.", tbl="Niveles y precios",
   head=("Nivel", "Para", "Beneficios clave", "Precio"),
   rows=[("M0 OPEN", "Empresas que dan un primer vistazo", "Mapa, resúmenes y panel de situación · primeros elementos de programas, licitaciones y eventos", "Gratis"),
         ("M1 MEMBER", "Empresas que siguen los datos", "Todas las listas completas + 2 solicitudes de análisis al mes", "₩19.800/mes"),
         ("M2 PRO", "Empresas que preparan su entrada", "Alertas por país, apoyo con documentos en inglés", "₩149.000/mes"),
         ("M3 BUSINESS", "Empresas ya validadas", "Preparación de contrapartes, consulta prioritaria, conversaciones con inversores (desde la revisión)", "₩390.000/mes"),
         ("M4 PROJECT", "Entrada en un país concreto", "Validación de mercado de 6 semanas, agenda local, conversaciones con inversores", "desde ₩1,9 M"),
         ("M5 STRATEGIC", "Contratos públicos o grandes", "Desde la preparación de la oferta hasta el contrato, conversaciones con inversores", "3–5 % del contrato")],
   note="IVA no incluido · Propuesta v2.0, se confirmará. No garantizamos inversión, contratos ni ventas.", btn="Unirse y pagar en www.wmm-hoa.com →", c="Contacto"),
 "fr": dict(t="Adhésion WMM", h="Adhésion WMM — du premier regard à l’exécution", lede="Nous accompagnons les entreprises à l’international, du diagnostic à l’exécution.", tbl="Niveaux et tarifs",
   head=("Niveau", "Pour", "Avantages clés", "Tarif"),
   rows=[("M0 OPEN", "Entreprises qui découvrent", "Carte, synthèses et tableau de situation · premiers éléments des programmes, appels d’offres et événements", "Gratuit"),
         ("M1 MEMBER", "Entreprises qui suivent les données", "Toutes les listes complètes + 2 demandes d’analyse par mois", "19 800 ₩/mois"),
         ("M2 PRO", "Entreprises qui préparent leur entrée", "Alertes pays, aide aux documents en anglais", "149 000 ₩/mois"),
         ("M3 BUSINESS", "Entreprises validées", "Préparation des contreparties, consultation prioritaire, échanges avec des investisseurs (dès l’examen)", "390 000 ₩/mois"),
         ("M4 PROJECT", "Entrée dans un pays précis", "Validation de marché en 6 semaines, agenda local, échanges avec des investisseurs", "à partir de 1,9 M₩"),
         ("M5 STRATEGIC", "Marchés publics ou grands contrats", "De la préparation de l’offre au contrat, échanges avec des investisseurs", "3–5 % du contrat")],
   note="TVA non comprise · Proposition v2.0, à confirmer. Nous ne garantissons ni investissement, ni contrat, ni chiffre d’affaires.", btn="Adhérer et payer sur www.wmm-hoa.com →", c="Contact"),
 "ar": dict(t="عضوية WMM", h="عضوية WMM — من النظرة الأولى إلى التنفيذ", lede="نرافق الشركات في توسعها الخارجي من التشخيص حتى التنفيذ.", tbl="المستويات والأسعار",
   head=("المستوى", "لمن", "المزايا الأساسية", "السعر"),
   rows=[("M0 OPEN", "شركات تلقي نظرة أولى", "الخريطة والملخصات ولوحة الأوضاع · أول البنود من البرامج والمناقصات والفعاليات", "مجاني"),
         ("M1 MEMBER", "شركات تتابع البيانات", "جميع القوائم كاملة + طلبا تحليل شهريًا", "19,800 وون/شهريًا"),
         ("M2 PRO", "شركات تستعد للدخول", "تنبيهات الدول، دعم المستندات بالإنجليزية", "149,000 وون/شهريًا"),
         ("M3 BUSINESS", "شركات اجتازت التحقق", "التحضير للشركاء، استشارة ذات أولوية، نقاش مع المستثمرين (منذ بدء المراجعة)", "390,000 وون/شهريًا"),
         ("M4 PROJECT", "دخول دولة محددة", "تحقق من السوق خلال 6 أسابيع، جدولة محلية، نقاش مع المستثمرين", "من 1.9 مليون وون"),
         ("M5 STRATEGIC", "عقود عامة أو كبيرة", "من إعداد العطاء حتى العقد، نقاش مع المستثمرين", "3–5% من قيمة العقد")],
   note="غير شامل ضريبة القيمة المضافة · مقترح v2.0 وسيتم تأكيده. لا نضمن الاستثمار أو العقود أو المبيعات.", btn="الانضمام والدفع عبر www.wmm-hoa.com ←", c="التواصل"),
 "vi": dict(t="Thành viên WMM", h="Thành viên WMM — từ tìm hiểu đến triển khai", lede="Chúng tôi đồng hành cùng doanh nghiệp ra nước ngoài, từ chẩn đoán đến triển khai.", tbl="Hạng và mức phí",
   head=("Hạng", "Dành cho", "Quyền lợi chính", "Mức phí"),
   rows=[("M0 OPEN", "Doanh nghiệp mới tìm hiểu", "Bản đồ, tóm tắt và bảng tình hình · vài mục đầu của dự án, đấu thầu và sự kiện", "Miễn phí"),
         ("M1 MEMBER", "Doanh nghiệp theo dõi dữ liệu", "Toàn bộ danh sách + 2 yêu cầu phân tích mỗi tháng", "₩19.800/tháng"),
         ("M2 PRO", "Doanh nghiệp chuẩn bị gia nhập", "Cảnh báo theo quốc gia, hỗ trợ tài liệu tiếng Anh", "₩149.000/tháng"),
         ("M3 BUSINESS", "Doanh nghiệp đã được xác minh", "Chuẩn bị đối tác, tư vấn ưu tiên, trao đổi với nhà đầu tư (từ khi xét duyệt)", "₩390.000/tháng"),
         ("M4 PROJECT", "Gia nhập một quốc gia cụ thể", "Kiểm chứng thị trường 6 tuần, sắp xếp lịch tại chỗ, trao đổi với nhà đầu tư", "từ ₩1,9 triệu"),
         ("M5 STRATEGIC", "Hợp đồng công hoặc quy mô lớn", "Từ chuẩn bị hồ sơ thầu đến ký hợp đồng, trao đổi với nhà đầu tư", "3–5% giá trị hợp đồng")],
   note="Chưa gồm VAT · Đề xuất v2.0, sẽ được xác nhận. Chúng tôi không bảo đảm đầu tư, hợp đồng hay doanh thu.", btn="Tham gia và thanh toán tại www.wmm-hoa.com →", c="Liên hệ"),
 "id": dict(t="Keanggotaan WMM", h="Keanggotaan WMM — dari melihat pertama hingga eksekusi", lede="Kami mendampingi perusahaan ke luar negeri, dari diagnosis hingga eksekusi.", tbl="Tingkat dan harga",
   head=("Tingkat", "Untuk", "Manfaat utama", "Harga"),
   rows=[("M0 OPEN", "Perusahaan yang baru melihat", "Peta, ringkasan dan papan situasi · beberapa item pertama program, tender dan acara", "Gratis"),
         ("M1 MEMBER", "Perusahaan yang mengikuti data", "Semua daftar lengkap + 2 permintaan analisis per bulan", "₩19.800/bulan"),
         ("M2 PRO", "Perusahaan yang bersiap masuk", "Peringatan negara, dukungan dokumen bahasa Inggris", "₩149.000/bulan"),
         ("M3 BUSINESS", "Perusahaan yang sudah tervalidasi", "Persiapan mitra, konsultasi prioritas, pembicaraan dengan investor (sejak peninjauan)", "₩390.000/bulan"),
         ("M4 PROJECT", "Masuk ke negara tertentu", "Validasi pasar 6 minggu, penjadwalan lokal, pembicaraan dengan investor", "mulai ₩1,9 juta"),
         ("M5 STRATEGIC", "Kontrak publik atau besar", "Dari persiapan tender hingga kontrak, pembicaraan dengan investor", "3–5% nilai kontrak")],
   note="Belum termasuk PPN · Usulan v2.0, akan dikonfirmasi. Kami tidak menjamin investasi, kontrak, atau penjualan.", btn="Bergabung dan bayar di www.wmm-hoa.com →", c="Kontak"),
}

# ---------------------------------------------------------------- WMM membership introduction (from the owner's deck v2.0, 2026-11-15)
CONCEPT = {"es": "Imagen conceptual", "fr": "Image conceptuelle", "ar": "صورة توضيحية", "vi": "Hình ảnh minh họa", "id": "Gambar konsep"}
MS_LUX = ("<style>"
 ".mlux{background:#0b0f19;color:#f3efe6;padding:72px 0 64px}.mlux .in{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:48px;align-items:center}"
 ".mlux .crumb,.mlux .crumb a{color:#b9b3a6}.mlux h1{font-size:clamp(32px,4.6vw,56px);line-height:1.15;margin:14px 0 18px;color:#fff}.mlux .lede{color:#d8d2c4;font-size:18px;max-width:34em}"
 ".mlux figure{margin:0}.mlux img{width:100%;height:auto;border-radius:10px;display:block}.mlux figcaption{font-size:12px;color:#8d877a;margin-top:6px;text-align:right}"
 ".btn.gold{background:#c9a45c;color:#0b0f19;border-color:#c9a45c;font-weight:700}.btn.ghost{background:transparent;color:#f3efe6;border-color:#6f6a5e}"
 ".mlux-ladder{background:#121826;color:#f3efe6;padding:64px 0}.mlux-ladder h2{color:#fff;margin:0 0 26px}"
 ".lad{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.lad .g{background:#1a2133;border-radius:8px;padding:22px;min-width:0}"
 ".lad .g b{color:#c9a45c;font-size:15px}.lad .g h3{color:#fff;margin:6px 0 8px;font-size:20px}.lad .g p{color:#cfc9bb;margin:0 0 14px;font-size:15px}.lad .g strong{color:#fff;font-size:18px}"
 ".lad .g.top{background:#1d1a12;outline:1px solid #c9a45c}.lad .mrv{grid-column:1/-1;border-top:2px dashed #e53935;color:#ff8a80;font-weight:700;padding-top:10px;font-size:15px}"
 ".mlux-rows{padding:24px 0}.mrow{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:48px;align-items:center;max-width:1200px;margin:0 auto;padding:56px 20px}"
 ".mrow img{width:100%;height:auto;aspect-ratio:3/2;object-fit:cover;border-radius:8px}.mrow b{color:#9a7a34;font-size:15px}.mrow h2{font-size:clamp(24px,3vw,36px);margin:6px 0 12px}.mrow p{font-size:17px;line-height:1.6}"
 ".mrow.rev img{order:2}.mfull{margin-top:18px}.mfull summary{cursor:pointer;font-weight:700;padding:10px 0}"
 "@media(max-width:860px){.mlux .in,.mrow{grid-template-columns:1fr;gap:24px}.mrow.rev img{order:0}.lad{grid-template-columns:1fr}.mlux{padding:40px 0}.mrow{padding:32px 16px}}"
 "</style>")
MROWS = {
 "ko": [("earth", "193개국 정부가 지금 무엇을 사려 하는지", "EXPLORE · M0–M1", "나라별 정부 과제·예산·입찰을 한곳에서 보고, 사람이 검수한 분석으로 우리 회사에 맞는 나라를 고릅니다."),
        ("sign", "상대를 만날 수 있는 회사로 준비합니다", "BUILD · M2–M3", "M2부터 심사를 거쳐 가입하고, 영문 회사소개서·제안서·사업계획을 함께 만듭니다. M3부터는 투자자 협의까지 준비합니다."),
        ("hand", "현지 파트너와 실제 프로젝트를 움직입니다", "EXECUTE · M4–M5", "6주 시장 검증, 현지 일정 조율, 컨소시엄 구성과 공공 입찰 준비부터 계약까지 동행합니다."),
        ("piano", "멤버십은 아이들의 피아노 수업으로도 이어집니다", "WMM 선행사업", "멤버십 수익의 일부는 자폐 아동 피아노·힐링 지원 프로그램에 쓰이고, 사용 내역은 기준서에 따라 공개합니다.")],
 "en": [("earth", "What 193 governments want to buy now", "EXPLORE · M0–M1", "See each country's priorities, budgets and tenders in one place, and choose the countries that fit you with human-reviewed analysis."),
        ("sign", "Get ready to meet counterparts", "BUILD · M2–M3", "From M2 you join after a review, and we build your English company profile, proposals and business plan with you; from M3 we prepare investor discussions too."),
        ("hand", "Move a real project with local partners", "EXECUTE · M4–M5", "Six-week market validation, local scheduling, consortium building, and support from bid preparation to contract."),
        ("piano", "Membership also funds piano lessons for children", "WMM giving programme", "Part of membership revenue supports a piano and healing programme for autistic children; spending is reported under a published standard.")],
}

def membership_page(L, C):
    ko = L == "ko"; T = lambda k, en: k if ko else en
    if L in MS_TX:
        X = MS_TX[L]
        rows = "".join(f"<tr><th>{a}</th><td>{b}</td><td>{c}</td><td><b>{d}</b></td></tr>" for a, b, c, d in X["rows"])
        _r = rows.split("</tr>"); rows = "</tr>".join(_r[:2]) + "</tr>" + review_row(L, 4) + "</tr>".join(_r[2:])
        hd = "<tr>" + "".join(f"<th>{h}</th>" for h in X["head"]) + "</tr>"
        body = (f'<style>.tiers td,.tiers th{{text-align:start}}</style>{MS_LUX}<section class="mlux"><div class="in"><div><h1>{X["h"]}</h1><p class="lede">{X["lede"]}</p>'
                f'<p class="cta"><a class="btn gold" href="https://www.wmm-hoa.com/membership/" target="_blank" rel="noopener">{X["btn"]}</a></p></div>'
                f'<figure><img src="/assets/wmm-card.webp" alt="WMM" width="1408" height="768"><figcaption>{CONCEPT.get(L, "Concept image")}</figcaption></figure></div></section>'
                f'<section class="band" id="tiers"><div class="in"><h2>{X["tbl"]}</h2><div class="tscroll"><table class="tiers">{hd}{rows}</table></div><p class="note">{X["note"]}</p>'
                f'<p class="note">{X["c"]} · 73036396@naver.com · WORLD MAKING MEMBERS (WMM)</p></div></section>')
        return C["head"](L, X["t"] + " · GOV RADAR", X["lede"], f"/{L}/membership/", {l: f"/{l}/membership/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)
    css = ('<style>.mtr{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:22px}'
           '.mtr>div,.mpr>div,.mfc>div{background:var(--card,#fff);padding:22px;border-radius:6px}'
           '.mtr b{display:block;font-size:13px;letter-spacing:.5px;opacity:.7}.mtr h3{margin:6px 0 8px}'
           '.mpr{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:20px}.mpr h3{margin:0 0 6px;font-size:18px}'
           '.mfc{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:20px}.mfc strong{display:block;font-size:40px;line-height:1.1}'
           '.mstep{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-top:20px}.mstep>div{border-top:3px solid currentColor;padding-top:10px}'
           '.mac{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:20px}.mac h3{font-size:17px;margin:0 0 8px}'
           '.mdoor{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:20px}.mdoor>a{display:block;padding:24px;border-radius:6px;background:var(--card,#fff);color:inherit;text-decoration:none}'
           '.tiers td,.tiers th{text-align:left}.mac>div,.mtr>div,.mpr>div,.mfc>div,.mstep>div{min-width:0}.mac .tiers{min-width:0}'
           '@media(max-width:760px){.mtr,.mpr,.mfc,.mac,.mdoor{grid-template-columns:1fr}.mstep{grid-template-columns:1fr 1fr}}</style>' + MS_LUX)
    tracks = [("EXPLORE · " + T("탐색", "Explore"), "M0 — M1", T("세계 정부 아젠다와 입찰을 보고, 우리 회사에 맞는 나라를 고릅니다.", "Read government agendas and tenders and choose the countries that fit your company.")),
              ("BUILD · " + T("준비", "Build"), "M2 — M3", T("서류와 검증을 갖추고, 상대를 만날 수 있는 회사로 준비합니다.", "Get your documents and validation ready so you can meet counterparts.")),
              ("EXECUTE · " + T("실행", "Execute"), "M4 — M5", T("특정 국가 프로젝트와 공공 수주를 실제로 추진합니다.", "Carry out a country project or a public contract bid for real."))]
    tiers = ([("M0 OPEN · 오픈", "처음 둘러보는 기업", "193개국 지도·요약·상황판, 사업·입찰·일정은 앞부분만", "무료"),
              ("M1 MEMBER · 분석 회원", "정보를 꾸준히 보는 기업", "모든 나라 전체 목록 + 분석 의뢰 월 2건", "월 19,800원"),
              ("M2 PRO · 프로", "진출을 준비하는 기업", "관심 국가 알림·영문 서류 지원", "월 149,000원"),
              ("M3 BUSINESS · 비즈니스", "검증을 마친 기업", "상대 연결 준비·우선 상담·투자자 협의(심사 중부터)", "월 390,000원"),
              ("M4 PROJECT · 진출 패키지", "특정 국가 진출 실행", "6주 시장 검증·현지 일정 조율·투자자 협의", "190만 원부터"),
              ("M5 STRATEGIC · 수주 대행", "공공·대형 수주 추진", "입찰 준비부터 계약까지 동행·투자자 협의", "수주액 3~5%"),
              ("FC FOUNDING CIRCLE", "초기 10곳 한정 초청", "CONNECT 50% 할인·운영 자문 참여", "별도 협의")] if ko else
             [("M0 OPEN", "Companies taking a first look", "Map, summaries and situation board; first items of programmes, tenders and events", "Free"),
              ("M1 MEMBER · Analysis", "Companies following the data", "Every list in full + 2 analysis requests a month", "₩19,800/month"),
              ("M2 PRO", "Companies preparing to enter", "Country alerts, English document support", "₩149,000/month"),
              ("M3 BUSINESS", "Companies that have validated", "Counterpart preparation, priority consultation, investor discussions (from review)", "₩390,000/month"),
              ("M4 PROJECT · Entry package", "Entering a specific country", "6-week market validation, local scheduling, investor discussions", "from ₩1.9M"),
              ("M5 STRATEGIC · Bid support", "Public or large contracts", "With you from bid preparation to contract, investor discussions", "3–5% of contract value"),
              ("FC FOUNDING CIRCLE", "First 10 companies, by invitation", "50% off CONNECT, input on operations", "By agreement")])
    trows = "".join(f"<tr><th>{a}</th><td>{b}</td><td>{c}</td><td><b>{d}</b></td></tr>" for a, b, c, d in tiers)
    _r = trows.split("</tr>"); trows = "</tr>".join(_r[:2]) + "</tr>" + review_row(L, 4) + "</tr>".join(_r[2:])
    thead = T("<tr><th>등급</th><th>이런 기업에게</th><th>핵심 혜택</th><th>요금</th></tr>", "<tr><th>Grade</th><th>For</th><th>Key benefits</th><th>Price</th></tr>")
    adds = ([("M1", "정보", "레이더 전체 열람과 회원 분석 의뢰"), ("M2", "준비", "관심 국가 알림, 영문 서류 지원"), ("M3", "연결 준비", "상대 후보 정리와 우선 상담"),
             ("M4", "실행", "6주 시장 검증과 현지 일정"), ("M5", "수주", "입찰 준비부터 계약까지 동행")] if ko else
            [("M1", "Information", "Full radar and member analysis requests"), ("M2", "Preparation", "Country alerts, English documents"), ("M3", "Connection-ready", "Counterpart shortlist, priority consultation"),
             ("M4", "Execution", "6-week market validation and local scheduling"), ("M5", "Contracts", "From bid preparation to contract")])
    steps = "".join(f"<div><b>{a}</b><h3 style='font-size:16px;margin:4px 0'>{b}</h3><p class='note'>{c}</p></div>" for a, b, c in adds)
    alc = [("CONNECT · " + T("연결", "Connect"), [(T("후보 숏리스트", "Candidate shortlist"), T("150만 원", "₩1.5M")), (T("소개·첫 미팅", "Introduction & first meeting"), T("300만 원", "₩3M")), (T("90일 스프린트", "90-day sprint"), T("1,200만 원부터", "from ₩12M")), (T("성공보수", "Success fee"), "3~5%")]),
           ("TRANSLATE · " + T("번역", "Translate"), [(T("전문 번역", "Professional translation"), T("쪽당 3.5만 원", "₩35,000/page")), (T("원어민 검수", "Native review"), T("39만 원", "₩390,000")), (T("번역 패키지", "Translation package"), T("129만 원", "₩1.29M"))]),
           ("CHECK · " + T("판정", "Check"), [(T("입찰 적합도 판정", "Tender fit assessment"), T("건당 10만 원", "₩100,000 each"))])]
    alch = "".join(f"<div><h3>{h}</h3><div class='tscroll'><table class='tiers'>" + "".join(f"<tr><th>{a}</th><td><b>{b}</b></td></tr>" for a, b in rows) + "</table></div></div>" for h, rows in alc)
    journey = ([("무료 가입", "M0로 레이더와 브리핑을 둘러봅니다."), ("관심 등록", "관심 국가와 업종을 고릅니다."), ("구독 선택", "M1~M3 중 고르고 첫 달은 무료입니다."),
                ("회사 확인", "사업자 정보와 자료를 확인합니다."), ("프로젝트 상담", "M4 범위와 견적을 정합니다."), ("실행", "검증·연결·수주를 함께 진행합니다.")] if ko else
               [("Free sign-up", "Browse the radar and briefings as M0."), ("Register interests", "Choose countries and sectors."), ("Choose a plan", "Pick M1–M3; the first month is free."),
                ("Company check", "We confirm your business details and materials."), ("Project consultation", "Agree M4 scope and quote."), ("Execution", "Validation, connection and bids, together.")])
    jr = "".join(f"<li><b>{a}</b> — {b}</li>" for a, b in journey)
    fc = [("50%", T("CONNECT 할인", "off CONNECT"), T("파운딩 고객 10곳 한정", "First 10 founding clients only")),
          (T("1개월", "1 month"), T("구독 무료", "free subscription"), T("BUILD 구독 첫 달", "First month of a BUILD plan")),
          (T("2개월", "2 months"), T("연간 결제 혜택", "annual-plan bonus"), T("연간 결제 시 무료 기간", "Free months when paying annually"))]
    fch = "".join(f"<div><strong>{a}</strong><b>{b}</b><p class='note'>{c}</p></div>" for a, b, c in fc)
    pr = ([("성과를 보장하지 않습니다", "수주, 계약, 매출은 기업과 상대의 결정입니다. 우리는 준비와 과정을 돕습니다."),
           ("공공기관 접근권을 팔지 않습니다", "정부·발주기관과의 특별한 관계를 상품으로 내세우지 않습니다."),
           ("양쪽이 동의한 소개만 합니다", "소개는 두 회사가 모두 동의한 뒤에만 진행합니다."),
           ("모든 결제는 세금계산서로", "정해진 요금표와 견적서대로 받고 세금계산서를 발행합니다.")] if ko else
          [("We do not guarantee results", "Contracts and sales are decided by you and your counterpart. We help with preparation and process."),
           ("We do not sell access", "We never market special relationships with governments or buyers as a product."),
           ("Introductions only with consent", "We introduce two companies only after both agree."),
           ("Every payment is invoiced", "We charge by the published price list and quote, and issue a tax invoice.")])
    prh = "".join(f"<div><h3>{a}</h3><p>{b}</p></div>" for a, b in pr)
    hs = "?lang=ko" if ko else "?lang=en"
    body = f'''{css}<section class="mlux"><div class="in"><div><p class="crumb"><a href="/{L}/">GOV RADAR</a> › <a href="/{L}/pricing/">{T("주문·요금", "Pricing")}</a></p>
<h1>{T("하나의 멤버십으로, 정보에서 수주까지", "One membership, from information to contract")}</h1>
<p class="lede">{T("WMM 멤버십은 193개국 정부 정보를 보는 데서 시작해, 영문 서류·시장 검증·파트너 연결·공공 수주까지 한 팀으로 함께 갑니다.", "WMM membership starts with government intelligence on 193 countries and carries on, as one team, through English documents, market validation, partner introductions and public contracts.")}</p>
<p class="cta"><a class="btn gold" href="https://www.wmm-hoa.com/membership/{hs}" target="_blank" rel="noopener">{T("멤버십 가입하기", "Join the membership")}</a> <a class="btn ghost" href="#ladder">{T("등급 살펴보기", "See the grades")}</a></p></div>
<figure><img src="/assets/wmm-card.webp" alt="{T("WMM 멤버십 카드", "WMM membership card")}" width="1408" height="768" fetchpriority="high"><figcaption>{T("콘셉트 이미지", "Concept image")}</figcaption></figure></div></section>
<section class="mlux-ladder" id="ladder"><div class="in"><h2>{T("등급마다 열리는 문이 다릅니다", "Each grade opens a different door")}</h2>
<div class="lad">{"".join(f'<div class="g{" top" if k >= 2 else ""}"><b>{a}</b><h3>{b}</h3><p>{c}</p><strong>{d}</strong></div>' + (f'<div class="mrv">{REVIEW["ko" if ko else "en"]}</div>' if k == 1 else "") for k, (a, b, c, d) in enumerate(tiers[:6]))}</div></div></section>
<section class="mlux-rows">{"".join(f'<div class="mrow{" rev" if n % 2 else ""}">{img(ph, "", 1200, 800)}<div><b>{t2}</b><h2>{t1}</h2><p>{t3}</p></div></div>' for n, (ph, t1, t2, t3) in enumerate(MROWS[L if ko else "en"]))}</section>
<section class="band"><div class="in"><h2>{T("해외 진출은 대개 세 곳에서 멈춥니다", "Going abroad usually stalls in three places")}</h2>
<div class="mpr" style="grid-template-columns:repeat(3,minmax(0,1fr))"><div><h3>{T("정보가 흩어져 있다", "Information is scattered")}</h3><p>{T("정부 정책, 입찰, 제재, 재난 소식이 나라마다 다른 곳에 있습니다.", "Policies, tenders, sanctions and disaster news sit in different places for each country.")}</p></div>
<div><h3>{T("순서를 알기 어렵다", "The order is unclear")}</h3><p>{T("무엇부터 준비하고 얼마를 써야 할지 판단할 기준이 부족합니다.", "There is little to go on for what to prepare first and how much to spend.")}</p></div>
<div><h3>{T("연결이 닿지 않는다", "Connections are hard to reach")}</h3><p>{T("믿을 만한 현지 상대를 만나기까지 시간과 비용이 큽니다.", "Meeting a trustworthy local counterpart takes time and money.")}</p></div></div></div></section>
<section class="band" id="tiers"><div class="in"><h2>{T("멤버십 등급 v2.0", "Membership grades v2.0")}</h2>
<details class="mfull"><summary>{T("등급별 전체 비교표 열기", "Open the full grade table")}</summary><div class="tscroll"><table class="tiers">{thead}{trows}</table></div></details>
<p class="note">{T("M1은 GOV RADAR 분석 회원(월 19,800원)과 같은 등급입니다. 부가세 별도, 세금계산서 발행. 등급과 요금은 v2.0 안이며 확정되면 다시 안내합니다. 투자 유치·계약·매출을 보장하지 않습니다.", "M1 is the same grade as the GOV RADAR analysis membership (₩19,800/month). VAT excluded; tax invoices issued. Grades and prices are the v2.0 proposal and will be confirmed. We do not guarantee investment, contracts or sales.")}</p>
<h3 style="margin-top:34px">{T("한 단계 오를 때마다 더해지는 것", "What each level adds")}</h3><div class="mstep">{steps}</div></div></section>
<section class="band alt"><div class="in"><h2>{T("멤버십으로 쓰는 두 개의 창구", "Two doors, one membership")}</h2><div class="mdoor">
<a href="/{L}/"><b>radar.wmm-hoa.com · GOV RADAR</b><p>{T("세계 정부 아젠다, 공공 입찰, 제재 동향, 재난 대비 정보를 나라별로 모아 보여 줍니다. 분석 의뢰와 입찰 적합도 판정도 여기서 신청합니다.", "Government agendas, public tenders, sanctions and disaster preparedness by country. Analysis requests and tender fit assessments are ordered here.")}</p></a>
<a href="https://www.wmm-hoa.com/{hs}" target="_blank" rel="noopener"><b>www.wmm-hoa.com · WMM</b><p>{T("글로벌 진출 진단, 영문 서류, 6주 시장 검증, 교육·웨비나, 국가 브리핑을 안내합니다. 멤버십 가입·결제와 프로젝트 상담은 이곳에서 합니다.", "Entry diagnosis, English documents, 6-week market validation, training, webinars and country briefings. Membership sign-up, payment and project consultations happen here.")}</p></a></div>
<p class="note">{T("두 사이트를 하나의 회원 계정으로 쓰도록 연결하는 작업을 준비하고 있습니다.", "We are preparing to link both sites to a single member account.")}</p></div></section>
<section class="band"><div class="in"><h2>{T("필요할 때만 더하는 별도 상품", "Add-ons when you need them")}</h2><div class="mac">{alch}</div>
<p class="note">{T("회원 분석 의뢰는 참고용 정리이고, 판정은 특정 입찰 참여 여부를 검토하는 별도 상품입니다. 부가세 별도. 상세 범위와 일정은 견적서에 적어 드립니다.", "Member analysis requests are reference summaries; the fit assessment is a separate product reviewing whether to bid on a specific tender. VAT excluded. Scope and timing are set out in the quote.")}</p></div></section>
<section class="band alt"><div class="in"><h2>{T("가입부터 실행까지의 흐름", "From sign-up to execution")}</h2><ol class="flow">{jr}</ol></div></section>
<section class="band"><div class="in"><h2>{T("FOUNDING CIRCLE — 시작하는 기업을 위한 혜택", "Founding Circle — for early companies")}</h2><div class="mfc">{fch}</div>
<p class="note">{T("CONNECT 50% 할인은 파운딩 고객 10곳에만 적용되며, 선정 기준과 기간은 신청 후 안내합니다.", "The 50% CONNECT discount applies to 10 founding clients only; criteria and period are shared after you apply.")}</p></div></section>
<section class="band alt"><div class="in"><h2>{T("우리가 약속하지 않는 것", "What we do not promise")}</h2><div class="mpr">{prh}</div></div></section>
<section class="band alt"><div class="in"><h2>{T("무료 가입으로 시작해 보세요", "Start with a free sign-up")}</h2>
<p class="cta"><a class="btn pri" href="https://www.wmm-hoa.com/membership/{hs}" target="_blank" rel="noopener">{T("WMM 멤버십 가입·결제 →", "Join WMM membership →")}</a> <a class="btn" href="/{L}/pricing/">{T("GOV RADAR 요금 보기", "GOV RADAR pricing")}</a></p>
<p class="note">{T("문의", "Contact")} 73036396@naver.com · {T("월드메이킹멤버스(WMM)", "WORLD MAKING MEMBERS (WMM)")}</p>{credit([r[0] for r in MROWS["en"]], ko)}</div></section>'''
    return C["head"](L, T("WMM 멤버십", "WMM Membership") + " · GOV RADAR",
                     T("WMM 멤버십 M0–M5: 정보 탐색부터 서류 준비, 시장 검증, 공공 수주까지. 가입·결제는 wmm-hoa.com.", "WMM membership M0–M5: from information to documents, market validation and public contracts. Join at wmm-hoa.com."),
                     f"/{L}/membership/", {l: f"/{l}/membership/" for l in C["LANGS"]}) + LTR(L, body) + C["foot"](L)

# ---------------------------------------------------------------- WMM emergency kits (owner's product images, 2026-11-15)
KIT_TX = {
"es": dict(h="Kits de emergencia WMM — GO72 · HOME3 · CAR24", p="Una mochila para salir, una caja para casa y una bolsa para el coche: tres kits para tres situaciones.", alt="Contenido de GO72, HOME3 y CAR24",
  k=[("Mochila de supervivencia personal · 1 persona, 2–3 días","Mochila impermeable de 28 L, linterna frontal LED, batería externa de 10.000 mAh, radio portátil, manta térmica, poncho, silbato, funda impermeable para documentos, kit de higiene y mascarillas, kit de apósitos y vendas, tentempiés, tarjeta de contacto y guía, embalaje e inspección (13 artículos)"),
     ("Kit de emergencia para el hogar · 2 personas, 3 días","24 L de agua (2 L × 12), 18 comidas no perecederas, radio a pilas, 2 luces LED, 2 baterías externas, kit de higiene de emergencia, 2 mantas, caja de almacenamiento y guía (8 artículos)"),
     ("Kit de emergencia para el coche · 24 horas","Funda resistente al calor, chaleco reflectante, linterna, kit de primeros auxilios e higiene, manta y lámina térmica, tarjeta de contacto y silbato (6 artículos)")],
  g=["HOME3 · 24 L de agua · 18 comidas · radio a pilas","GO72 · mochila de 28 L · linterna frontal · batería externa","Radio portátil · manta térmica · poncho","Silbato · funda para documentos · kit de higiene","Kit de apósitos · tentempiés · tarjeta de contacto · embalaje inspeccionado","HOME3 · 2 luces LED · 2 baterías externas · kit de higiene","HOME3 · 2 mantas · caja de almacenamiento y guía","CAR24 · funda resistente al calor · chaleco reflectante · linterna","CAR24 · botiquín · manta · tarjeta de contacto y silbato"],
  n="Las imágenes son conceptuales. El contenido es orientativo antes del lanzamiento y puede cambiar. Pedidos para grupos: 73036396@naver.com"),
"fr": dict(h="Kits d’urgence WMM — GO72 · HOME3 · CAR24", p="Un sac à emporter, une boîte pour la maison et un sac pour la voiture : trois kits pour trois situations.", alt="Contenu de GO72, HOME3 et CAR24",
  k=[("Sac de survie individuel · 1 personne, 2–3 jours","Sac à dos étanche 28 L, lampe frontale LED, batterie externe 10 000 mAh, radio portable, couverture de survie, poncho, sifflet, pochette étanche pour documents, kit hygiène et masques, kit pansements, en-cas, carte de contact et guide, emballage et contrôle (13 articles)"),
     ("Kit d’urgence pour la maison · 2 personnes, 3 jours","24 L d’eau (2 L × 12), 18 repas longue conservation, radio à piles, 2 lampes LED, 2 batteries externes, kit hygiène d’urgence, 2 couvertures, boîte de rangement et guide (8 articles)"),
     ("Kit d’urgence pour la voiture · 24 heures","Pochette résistante à la chaleur, gilet réfléchissant, lampe torche, trousse de secours et d’hygiène, couverture et feuille de survie, carte de contact et sifflet (6 articles)")],
  g=["HOME3 · 24 L d’eau · 18 repas · radio à piles","GO72 · sac à dos 28 L · lampe frontale · batterie externe","Radio portable · couverture de survie · poncho","Sifflet · pochette à documents · kit hygiène","Kit pansements · en-cas · carte de contact · emballage contrôlé","HOME3 · 2 lampes LED · 2 batteries externes · kit hygiène","HOME3 · 2 couvertures · boîte de rangement et guide","CAR24 · pochette résistante à la chaleur · gilet réfléchissant · lampe torche","CAR24 · trousse de secours · couverture · carte de contact et sifflet"],
  n="Images conceptuelles. Le contenu est indicatif avant le lancement et peut changer. Commandes groupées : 73036396@naver.com"),
"ar": dict(h="حقائب الطوارئ من WMM — GO72 · HOME3 · CAR24", p="حقيبة ظهر للخروج، وصندوق للمنزل، وحقيبة للسيارة: ثلاث حقائب لثلاثة مواقف.", alt="محتويات GO72 وHOME3 وCAR24",
  k=[("حقيبة نجاة شخصية · شخص واحد، 2–3 أيام","حقيبة ظهر مقاومة للماء 28 لترًا، مصباح رأس LED، بطارية متنقلة 10,000 مللي أمبير، راديو محمول، بطانية حرارية، معطف مطر، صفارة، حافظة وثائق مقاومة للماء، عدة نظافة وكمامات، عدة ضمادات، وجبات خفيفة، بطاقة اتصال ودليل، تغليف وفحص (13 قطعة)"),
     ("حقيبة طوارئ منزلية · شخصان، 3 أيام","24 لترًا من الماء (2 لتر × 12)، 18 وجبة لا تحتاج تبريدًا، راديو بالبطاريات، مصباحا LED، بطاريتان متنقلتان، عدة نظافة للطوارئ، بطانيتان، صندوق تخزين ودليل (8 قطع)"),
     ("حقيبة طوارئ للسيارة · 24 ساعة","حافظة مقاومة للحرارة، سترة عاكسة، مصباح يدوي، عدة إسعافات ونظافة، بطانية وغطاء حراري، بطاقة اتصال وصفارة (6 قطع)")],
  g=["HOME3 · ماء 24 لترًا · 18 وجبة · راديو بالبطاريات","GO72 · حقيبة ظهر 28 لترًا · مصباح رأس · بطارية متنقلة","راديو محمول · بطانية حرارية · معطف مطر","صفارة · حافظة وثائق · عدة نظافة","عدة ضمادات · وجبات خفيفة · بطاقة اتصال · تغليف مفحوص","HOME3 · مصباحا LED · بطاريتان متنقلتان · عدة نظافة","HOME3 · بطانيتان · صندوق تخزين ودليل","CAR24 · حافظة مقاومة للحرارة · سترة عاكسة · مصباح يدوي","CAR24 · عدة إسعافات · بطانية · بطاقة اتصال وصفارة"],
  n="الصور تصورية. المحتويات إرشادية قبل الإطلاق وقد تتغير. الطلبات الجماعية: 73036396@naver.com"),
"vi": dict(h="Bộ dụng cụ khẩn cấp WMM — GO72 · HOME3 · CAR24", p="Ba lô mang theo, hộp để ở nhà và túi để trên xe: ba bộ cho ba tình huống.", alt="Thành phần của GO72, HOME3 và CAR24",
  k=[("Ba lô sinh tồn cá nhân · 1 người, 2–3 ngày","Ba lô chống nước 28 L, đèn pin đội đầu LED, sạc dự phòng 10.000 mAh, radio cầm tay, chăn giữ nhiệt, áo mưa, còi, túi đựng giấy tờ chống nước, bộ vệ sinh và khẩu trang, bộ băng gạc, đồ ăn nhẹ, thẻ liên lạc và hướng dẫn, đóng gói và kiểm tra (13 món)"),
     ("Bộ khẩn cấp gia đình · 2 người, 3 ngày","24 L nước (2 L × 12), 18 bữa ăn bảo quản thường, radio dùng pin, 2 đèn LED, 2 sạc dự phòng, bộ vệ sinh khẩn cấp, 2 chăn, hộp đựng và hướng dẫn (8 món)"),
     ("Bộ khẩn cấp cho ô tô · 24 giờ","Túi chịu nhiệt, áo phản quang, đèn pin, bộ sơ cứu và vệ sinh, chăn và tấm giữ nhiệt, thẻ liên lạc và còi (6 món)")],
  g=["HOME3 · 24 L nước · 18 bữa ăn · radio dùng pin","GO72 · ba lô 28 L · đèn đội đầu · sạc dự phòng","Radio cầm tay · chăn giữ nhiệt · áo mưa","Còi · túi giấy tờ · bộ vệ sinh","Bộ băng gạc · đồ ăn nhẹ · thẻ liên lạc · đóng gói đã kiểm tra","HOME3 · 2 đèn LED · 2 sạc dự phòng · bộ vệ sinh","HOME3 · 2 chăn · hộp đựng và hướng dẫn","CAR24 · túi chịu nhiệt · áo phản quang · đèn pin","CAR24 · bộ sơ cứu · chăn · thẻ liên lạc và còi"],
  n="Hình ảnh mang tính minh họa. Thành phần là thông tin trước khi ra mắt và có thể thay đổi. Đặt hàng số lượng lớn: 73036396@naver.com"),
"id": dict(h="Kit darurat WMM — GO72 · HOME3 · CAR24", p="Tas punggung untuk dibawa pergi, kotak untuk rumah, dan tas untuk mobil: tiga kit untuk tiga situasi.", alt="Isi GO72, HOME3, dan CAR24",
  k=[("Tas bertahan hidup pribadi · 1 orang, 2–3 hari","Tas punggung tahan air 28 L, senter kepala LED, power bank 10.000 mAh, radio portabel, selimut termal, jas hujan ponco, peluit, kantong dokumen tahan air, paket kebersihan dan masker, paket perban, camilan, kartu kontak dan panduan, pengemasan dan pemeriksaan (13 item)"),
     ("Kit darurat rumah · 2 orang, 3 hari","Air 24 L (2 L × 12), 18 porsi makanan tahan simpan, radio baterai, 2 lampu LED, 2 power bank, paket kebersihan darurat, 2 selimut, kotak penyimpanan dan panduan (8 item)"),
     ("Kit darurat mobil · 24 jam","Kantong tahan panas, rompi reflektif, senter, paket P3K dan kebersihan, selimut dan lembar termal, kartu kontak dan peluit (6 item)")],
  g=["HOME3 · air 24 L · 18 porsi makanan · radio baterai","GO72 · tas 28 L · senter kepala · power bank","Radio portabel · selimut termal · ponco","Peluit · kantong dokumen · paket kebersihan","Paket perban · camilan · kartu kontak · kemasan terperiksa","HOME3 · 2 lampu LED · 2 power bank · paket kebersihan","HOME3 · 2 selimut · kotak penyimpanan dan panduan","CAR24 · kantong tahan panas · rompi reflektif · senter","CAR24 · paket P3K · selimut · kartu kontak dan peluit"],
  n="Gambar bersifat konsep. Isi merupakan panduan sebelum peluncuran dan dapat berubah. Pemesanan dalam jumlah besar: 73036396@naver.com"),
}

def wmm_kits(L):
    ko = L == "ko"; T = lambda a, b: a if ko else b
    kits = [("GO72", T("개인 생존배낭 · 1인 2~3일", "Personal survival pack · 1 person, 2–3 days"),
             T("28L 방수형 백팩, LED 헤드랜턴, 보조배터리 10,000mAh, 휴대형 라디오, 보온 은박포, 우의, 호루라기, 방수 서류 파우치, 위생·마스크 팩, 기본 드레싱/밴드 팩, 간식·식량 소량, 연락카드·가이드, 패키징·검수 (13종)",
               "28L waterproof backpack, LED headlamp, 10,000mAh power bank, portable radio, thermal blanket, poncho, whistle, waterproof document pouch, hygiene & mask pack, dressing & bandage pack, snacks, contact card & guide, packing & inspection (13 items)")),
            ("HOME3", T("가정용 대비 키트 · 2인 3일", "Home emergency kit · 2 people, 3 days"),
             T("생수 24L(2L×12), 상온 식량 18끼, 건전지 라디오, LED 조명 2종, 보조배터리 2종, 응급 위생팩, 방한담요 2개, 수납함·설명서 (8종)",
               "24L water (2L × 12), 18 shelf-stable meals, battery radio, 2 LED lights, 2 power banks, emergency hygiene pack, 2 warm blankets, storage box & guide (8 items)")),
            ("CAR24", T("차량용 비상 키트 · 24시간", "Car emergency kit · 24 hours"),
             T("내열 보관 파우치, 반사 조끼, 손전등, 구급·위생 소형팩, 담요·보온포, 연락카드·호루라기 (6종)",
               "Heat-resistant storage pouch, reflective vest, flashlight, first-aid & hygiene kit, blanket & thermal sheet, contact card & whistle (6 items)"))]
    X = KIT_TX.get(L)
    if X: kits = [(kits[i][0], X['k'][i][0], X['k'][i][1]) for i in range(3)]
    kc = "".join(f'<div class="wk-k"><b>{a}</b><span>{b}</span><p>{c}</p></div>' for a, b, c in kits)
    gal = [("kit-home3", T("HOME3 · 생수 24L · 상온 식량 18끼 · 건전지 라디오", "HOME3 · 24L water · 18 meals · battery radio")),
           ("kit-go72-a", T("GO72 · 28L 방수 백팩 · LED 헤드랜턴 · 보조배터리", "GO72 · 28L backpack · headlamp · power bank")),
           ("kit-go72-b", T("휴대형 라디오 · 보온 은박포 · 우의", "Portable radio · thermal blanket · poncho")),
           ("kit-go72-c", T("호루라기 · 방수 서류 파우치 · 위생·마스크 팩", "Whistle · document pouch · hygiene pack")),
           ("kit-go72-d", T("드레싱/밴드 팩 · 간식·식량 · 연락카드·가이드 · 검수 포장", "Dressing pack · snacks · contact card · inspected packing")),
           ("kit-home3-b", T("HOME3 · LED 조명 2종 · 보조배터리 2종 · 응급 위생팩", "HOME3 · 2 LED lights · 2 power banks · hygiene pack")),
           ("kit-home3-c", T("HOME3 · 방한담요 2개 · 수납함·설명서", "HOME3 · 2 blankets · storage box & guide")),
           ("kit-car24-a", T("CAR24 · 내열 파우치 · 반사 조끼 · 손전등", "CAR24 · heat-resistant pouch · reflective vest · flashlight")),
           ("kit-car24-b", T("CAR24 · 구급·위생팩 · 담요·보온포 · 연락카드·호루라기", "CAR24 · first-aid pack · blanket · contact card & whistle"))]
    if X: gal = [(gal[i][0], X['g'][i]) for i in range(9)]
    gh = "".join(f'<figure><img src="/assets/{f}.webp" alt="{c}" width="1200" height="675" loading="lazy" decoding="async"><figcaption>{c}</figcaption></figure>' for f, c in gal)
    css = ('<style>.wk-main{width:100%;height:auto;display:block;border-radius:6px;margin:18px 0 6px}'
           '.wk-ks{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:22px 0}'
           '.wk-k{background:#fff;color:#111;padding:20px;border-radius:6px;min-width:0}.wk-k b{display:block;font-size:26px;line-height:1.1}.wk-k span{display:block;font-weight:700;margin:6px 0 8px}.wk-k p{margin:0;font-size:14.5px;line-height:1.6}'
           '.wk-g{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:18px}.wk-g figure{margin:0;min-width:0}.wk-g img{width:100%;height:auto;display:block;border-radius:6px}.wk-g figcaption{font-size:13px;margin-top:6px;opacity:.8}'
           '.wk-n{font-size:13px;opacity:.75}'
           '@media(max-width:900px){.wk-ks,.wk-g{grid-template-columns:1fr 1fr}}@media(max-width:560px){.wk-ks,.wk-g{grid-template-columns:1fr}}</style>')
    if X: T = lambda a, b, _m={"WMM 비상 키트 — GO72 · HOME3 · CAR24": X["h"], "들고 나가는 배낭, 집에 두는 상자, 차에 싣는 가방. 상황에 맞춰 세 가지로 준비했습니다.": X["p"], "GO72·HOME3·CAR24 구성품": X["alt"], "사진은 콘셉트 이미지입니다. 구성은 출시 전 안내용이며 바뀔 수 있습니다. 단체 주문 문의: 73036396@naver.com": X["n"]}: _m.get(a, b)
    return (css + f'<h2>{T("WMM 비상 키트 — GO72 · HOME3 · CAR24", "WMM emergency kits — GO72 · HOME3 · CAR24")}</h2>'
            f'<p>{T("들고 나가는 배낭, 집에 두는 상자, 차에 싣는 가방. 상황에 맞춰 세 가지로 준비했습니다.", "A pack to grab, a box for home and a bag for the car — three kits for three situations.")}</p>'
            f'<img class="wk-main" src="/assets/kit-overview.webp" alt="{T("GO72·HOME3·CAR24 구성품", "GO72, HOME3 and CAR24 contents")}" width="1600" height="900" loading="lazy" decoding="async">'
            f'<div class="wk-ks">{kc}</div><div class="wk-g">{gh}</div>'
            f'<p class="wk-n">{T("사진은 콘셉트 이미지입니다. 구성은 출시 전 안내용이며 바뀔 수 있습니다. 단체 주문 문의: 73036396@naver.com", "Images are concept images. Contents are pre-launch guidance and may change. Bulk enquiries: 73036396@naver.com")}</p>')

# ---------------------------------------------------------------- country tender intel (feeds/cty/{ISO}.json)
CI = {
 "ko": ["이 나라 입찰·수주 데이터", "매일 갱신합니다. 열린 입찰은 세계은행·EU 조달공보(TED)·영국 정부조달에서, 공고 전 사업과 낙찰 결과는 세계은행에서 가져옵니다.", "열린 입찰", "공고 전 사업", "최근 낙찰", "현지 기업 낙찰", "곧 입찰이 나올 사업 (세계은행 승인 대기)", "최근 낙찰 — 누가, 얼마에", "마감", "이 나라 데이터가 아직 없습니다. 입찰 보드에서 주변국 공고를 보세요.", "수주 센터에서 전체 보기", "이 나라 공고 적합도 검토 (10만 원)", "출처: 세계은행 API · EU TED · 영국 Find a Tender · 갱신", "사업 규모는 세계은행 사업 총액이며 입찰 1건 금액이 아닙니다.", "한국 기업", "진행 중인 세계은행 사업", "진행 중 사업 (약정액 큰 순)", "종료 예정"],
 "en": ["Tenders and awards in this country", "Updated daily. Open tenders come from the World Bank, EU TED and UK Find a Tender; pre-tender projects and awards from the World Bank.", "Open tenders", "Pre-tender projects", "Recent awards", "won by local firms", "Projects that will tender soon (awaiting World Bank approval)", "Recent awards — who won, for how much", "Closes", "No data for this country yet. See nearby countries on the tender board.", "See everything in the win centre", "Fit review for a notice here (₩100,000)", "Sources: World Bank API · EU TED · UK Find a Tender · updated", "Project size is the World Bank project total, not a single tender.", "Korean firms", "Active World Bank projects", "Active projects (largest first)", "ends"],
 "es": ["Licitaciones y adjudicaciones en este país", "Actualizado a diario. Las licitaciones abiertas vienen del Banco Mundial, TED de la UE y Find a Tender del Reino Unido; los proyectos previos y adjudicaciones, del Banco Mundial.", "Licitaciones abiertas", "Proyectos previos", "Adjudicaciones recientes", "ganadas por empresas locales", "Proyectos que licitarán pronto (pendientes de aprobación del Banco Mundial)", "Adjudicaciones recientes — quién ganó y por cuánto", "Cierre", "Aún no hay datos de este país. Vea países vecinos en el tablero.", "Ver todo en el centro para ganar licitaciones", "Revisión de idoneidad de un anuncio aquí (₩100.000)", "Fuentes: API del Banco Mundial · TED de la UE · Find a Tender (Reino Unido) · actualizado", "El tamaño es el total del proyecto del Banco Mundial, no una sola licitación.", "Empresas coreanas", "Proyectos activos del Banco Mundial", "Proyectos activos (mayores primero)", "finaliza"],
 "fr": ["Appels d'offres et attributions dans ce pays", "Mis à jour chaque jour. Les appels d'offres ouverts viennent de la Banque mondiale, du TED de l'UE et de Find a Tender (Royaume-Uni) ; projets en amont et attributions, de la Banque mondiale.", "Appels d'offres ouverts", "Projets en amont", "Attributions récentes", "remportées par des entreprises locales", "Projets bientôt en appel d'offres (en attente d'approbation de la Banque mondiale)", "Attributions récentes — qui a gagné, pour combien", "Clôture", "Pas encore de données pour ce pays. Voir les pays voisins sur le tableau.", "Tout voir dans le centre des appels d'offres", "Examen d'adéquation d'un avis ici (100 000 ₩)", "Sources : API de la Banque mondiale · TED (UE) · Find a Tender (Royaume-Uni) · mis à jour", "Le montant est le total du projet de la Banque mondiale, pas un seul appel d'offres.", "Entreprises coréennes", "Projets actifs de la Banque mondiale", "Projets actifs (les plus grands d'abord)", "fin prévue"],
 "ar": ["المناقصات والترسيات في هذا البلد", "تُحدَّث يوميًا. المناقصات المفتوحة من البنك الدولي وTED الأوروبي وFind a Tender البريطاني، والمشاريع قبل الطرح والترسيات من البنك الدولي.", "مناقصات مفتوحة", "مشاريع قبل الطرح", "ترسيات حديثة", "فازت بها شركات محلية", "مشاريع ستُطرح قريبًا (بانتظار موافقة البنك الدولي)", "ترسيات حديثة — من فاز وبكم", "الإغلاق", "لا توجد بيانات لهذا البلد بعد. اطّلع على الدول المجاورة في لوحة المناقصات.", "اعرض الكل في مركز الفوز بالمناقصات", "مراجعة ملاءمة لإعلان هنا (100,000 وون)", "المصادر: واجهة البنك الدولي · TED الأوروبي · Find a Tender البريطاني · آخر تحديث", "الحجم هو إجمالي مشروع البنك الدولي وليس مناقصة واحدة.", "شركات كورية", "مشروعات البنك الدولي الجارية", "المشروعات الجارية (الأكبر أولًا)", "الانتهاء المتوقع"],
 "vi": ["Gói thầu và trao thầu tại quốc gia này", "Cập nhật hằng ngày. Gói thầu đang mở lấy từ Ngân hàng Thế giới, TED của EU và Find a Tender của Anh; dự án trước đấu thầu và trao thầu lấy từ Ngân hàng Thế giới.", "Gói thầu đang mở", "Dự án trước đấu thầu", "Trao thầu gần đây", "do doanh nghiệp địa phương thắng", "Dự án sắp mời thầu (chờ Ngân hàng Thế giới phê duyệt)", "Trao thầu gần đây — ai thắng, giá bao nhiêu", "Hạn", "Chưa có dữ liệu cho quốc gia này. Xem các nước lân cận trên bảng thầu.", "Xem tất cả tại trung tâm thắng thầu", "Xem xét mức phù hợp cho một thông báo ở đây (₩100.000)", "Nguồn: API Ngân hàng Thế giới · TED của EU · Find a Tender của Anh · cập nhật", "Quy mô là tổng vốn dự án của Ngân hàng Thế giới, không phải một gói thầu.", "Doanh nghiệp Hàn Quốc", "Dự án Ngân hàng Thế giới đang triển khai", "Dự án đang triển khai (lớn nhất trước)", "kết thúc"],
 "id": ["Tender dan pemenang di negara ini", "Diperbarui setiap hari. Tender terbuka berasal dari Bank Dunia, TED Uni Eropa, dan Find a Tender Inggris; proyek pra-tender dan pemenang dari Bank Dunia.", "Tender terbuka", "Proyek pra-tender", "Pemenang terbaru", "dimenangkan perusahaan lokal", "Proyek yang segera ditenderkan (menunggu persetujuan Bank Dunia)", "Pemenang terbaru — siapa dan berapa nilainya", "Tutup", "Belum ada data untuk negara ini. Lihat negara tetangga di papan tender.", "Lihat semua di pusat memenangkan tender", "Tinjauan kesesuaian untuk pengumuman di sini (₩100.000)", "Sumber: API Bank Dunia · TED Uni Eropa · Find a Tender Inggris · diperbarui", "Nilai adalah total proyek Bank Dunia, bukan satu tender.", "Perusahaan Korea", "Proyek Bank Dunia yang berjalan", "Proyek berjalan (terbesar dulu)", "berakhir"],
}
def cty_intel(iso, L):
    s = CI.get(L) or CI["en"]; S = _json.dumps(s, ensure_ascii=False)
    return f'''<section class="ci" id="tender-intel" data-iso="{iso}"><h2>{s[0]}</h2><p class="note">{s[1]}</p>
<div class="cist"><div><b id="ci-t">–</b><span>{s[2]}</span></div><div><b id="ci-p">–</b><span>{s[3]}</span><small id="ci-pu"></small></div><div><b id="ci-a">–</b><span>{s[4]}</span><small id="ci-al"></small></div><div><b id="ci-v">–</b><span>{s[15]}</span><small id="ci-vu"></small></div></div>
<div class="cicols"><div><h3>{s[6]}</h3><ol id="ci-pl" class="cil"></ol><p class="fine">{s[13]}</p></div><div><h3>{s[16]}</h3><ol id="ci-vl" class="cil"></ol></div><div><h3>{s[7]}</h3><ol id="ci-al2" class="cil"></ol></div></div>
<p class="cta"><a class="btn pri" href="/{L}/win/">{s[10]}</a> <a class="btn" href="/{L}/pricing/?p=fit#order">{s[11]}</a></p><p class="fine" id="ci-src"></p>{lic_note(L)}</section>
<style>.ci{{margin:48px 0}}.cist{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0}}.cist div{{background:var(--bg2,#f3f5f8);padding:16px;border-radius:10px}}.cist b{{display:block;font-size:30px;line-height:1.1}}.cist span{{display:block;font-size:14px}}.cist small{{display:block;font-size:13px;opacity:.75;margin-top:4px}}.cicols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:28px}}.cil{{padding:0;margin:0;list-style:none}}.cil li{{padding:10px 0;border-bottom:1px solid rgba(127,127,127,.18);font-size:15px;line-height:1.45}}.cil li a{{color:inherit}}.cil li small{{display:block;opacity:.72;font-size:13px}}@media(max-width:760px){{.cist{{grid-template-columns:1fr 1fr;gap:8px}}.cist div{{padding:12px 10px}}.cist b{{font-size:22px}}.cist span{{font-size:12px}}.cicols{{grid-template-columns:1fr}}}}</style>
<script>(function(){{var S={S},sec=document.getElementById("tender-intel");if(!sec)return;
function E(x){{return String(x==null?"":x).replace(/[&<>"]/g,function(c){{return{{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
function U(v){{v=+v||0;return v>=1e9?"US$"+(v/1e9).toFixed(1)+"bn":v>=1e6?"US$"+(v/1e6).toFixed(1)+"M":v>0?"US$"+Math.round(v/1e3)+"k":""}}
function $(i){{return document.getElementById(i)}}
fetch("https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/cty/{iso}.json",{{cache:"no-store"}}).then(function(r){{if(!r.ok)throw 0;return r.json()}}).then(function(d){{
$("ci-t").textContent=d.t.n;$("ci-p").textContent=d.p.n;$("ci-a").textContent=d.a.n;
if(d.p.usd)$("ci-pu").textContent=U(d.p.usd);var v=d.v||{{n:0,usd:0,items:[]}};$("ci-v").textContent=v.n;if(v.usd)$("ci-vu").textContent=U(v.usd);
$("ci-vl").innerHTML=v.items.length?v.items.map(function(x){{return'<li dir="auto"><a href="'+E(x.url)+'" target="_blank" rel="noopener">'+E(x.title)+'</a><small>'+U(x.usd)+(x.close&&x.close>=new Date().toISOString().slice(0,10)?" · "+S[17]+" "+E(x.close):"")+(x.sec&&x.sec.length?" · "+E(x.sec.join(", ")):"")+'</small></li>'}}).join(""):'<li>—</li>';
if(d.a.n)$("ci-al").textContent=d.a.local+" "+S[5]+(d.a.kr?" · "+S[14]+" "+d.a.kr:"");
$("ci-pl").innerHTML=d.p.items.length?d.p.items.map(function(x){{return'<li dir="auto"><a href="'+E(x.url)+'" target="_blank" rel="noopener">'+E(x.title)+'</a><small>'+U(x.usd)+(x.sec&&x.sec.length?" · "+E(x.sec.join(", ")):"")+'</small></li>'}}).join(""):'<li>—</li>';
$("ci-al2").innerHTML=d.a.items.length?d.a.items.map(function(x){{return'<li dir="auto"><a href="'+E(x.url)+'" target="_blank" rel="noopener">'+E(x.title)+'</a><small>'+E(x.date)+" · "+E(x.winner)+" ("+E(x.wctry)+")"+(x.usd?" · ≈ "+U(x.usd):"")+'</small></li>'}}).join(""):'<li>—</li>';
$("ci-src").textContent=S[12]+" "+String(d.updated).slice(0,10);
}}).catch(function(){{sec.querySelector(".cist").remove();sec.querySelector(".cicols").remove();sec.querySelector(".note").textContent=S[9];}});}})();</script>'''


# Country "at a glance" economy strip — reads data/feeds/econ.json (World Bank + exchange rates, collected daily, no AI)
EC = {
 "ko": ["한눈에 보는 경제·환율", "인구", "국내총생산(GDP)", "1인당 GDP", "경제성장률", "물가상승률", "통화·환율", "경제 지표는 세계은행이 발표한 가장 최근 연도 값이고, 환율은 매일 갱신합니다.", "출처: 세계은행 Open Data(CC BY 4.0) · 환율 Exchange Rate API · 갱신", "년", "이 나라 경제 지표를 지금 불러오지 못했습니다."],
 "en": ["Economy and exchange rate at a glance", "Population", "GDP", "GDP per capita", "Real GDP growth", "Inflation (CPI)", "Currency", "Indicators are the latest year published by the World Bank; exchange rates are refreshed daily.", "Sources: World Bank Open Data (CC BY 4.0) · Rates by Exchange Rate API · updated", "", "Economic indicators for this country could not be loaded right now."],
 "es": ["Economía y tipo de cambio de un vistazo", "Población", "PIB", "PIB per cápita", "Crecimiento del PIB real", "Inflación (IPC)", "Moneda", "Los indicadores son del último año publicado por el Banco Mundial; los tipos de cambio se actualizan a diario.", "Fuentes: Banco Mundial Open Data (CC BY 4.0) · tipos de Exchange Rate API · actualizado", "", "No se pudieron cargar ahora los indicadores de este país."],
 "fr": ["Économie et taux de change en un coup d'œil", "Population", "PIB", "PIB par habitant", "Croissance du PIB réel", "Inflation (IPC)", "Monnaie", "Les indicateurs sont ceux de la dernière année publiée par la Banque mondiale ; les taux de change sont mis à jour chaque jour.", "Sources : Banque mondiale Open Data (CC BY 4.0) · taux Exchange Rate API · mis à jour", "", "Les indicateurs de ce pays n'ont pas pu être chargés pour le moment."],
 "ar": ["الاقتصاد وسعر الصرف في لمحة", "السكان", "الناتج المحلي الإجمالي", "نصيب الفرد من الناتج", "نمو الناتج الحقيقي", "التضخم (مؤشر الأسعار)", "العملة", "المؤشرات لأحدث سنة نشرها البنك الدولي، وأسعار الصرف تُحدَّث يوميًا.", "المصادر: بيانات البنك الدولي المفتوحة (CC BY 4.0) · أسعار Exchange Rate API · آخر تحديث", "", "تعذّر تحميل المؤشرات الاقتصادية لهذا البلد الآن."],
 "vi": ["Kinh tế và tỷ giá trong nháy mắt", "Dân số", "GDP", "GDP bình quân đầu người", "Tăng trưởng GDP thực", "Lạm phát (CPI)", "Tiền tệ", "Chỉ số là năm gần nhất do Ngân hàng Thế giới công bố; tỷ giá được cập nhật hằng ngày.", "Nguồn: Ngân hàng Thế giới Open Data (CC BY 4.0) · tỷ giá Exchange Rate API · cập nhật", "", "Hiện chưa tải được chỉ số kinh tế của nước này."],
 "id": ["Ekonomi dan kurs sekilas", "Penduduk", "PDB", "PDB per kapita", "Pertumbuhan PDB riil", "Inflasi (IHK)", "Mata uang", "Indikator adalah tahun terbaru yang diterbitkan Bank Dunia; kurs diperbarui setiap hari.", "Sumber: Bank Dunia Open Data (CC BY 4.0) · kurs Exchange Rate API · diperbarui", "", "Indikator ekonomi negara ini belum dapat dimuat sekarang."],
}
def cty_econ(iso, L):
    s = EC.get(L) or EC["en"]; S = _json.dumps(s, ensure_ascii=False)
    cells = "".join(f'<div><b id="ec-{k}">–</b><span>{s[i]}</span><small id="ec-{k}y"></small></div>' for i, k in ((1, "pop"), (2, "gdp"), (3, "pc"), (4, "gr"), (5, "cpi"), (6, "fx")))
    return f'''<section class="ec" id="econ" data-iso="{iso}"><h2>{s[0]}</h2><p class="note">{s[7]}</p><div class="ecg">{cells}</div><p class="fine" id="ec-src"></p></section>
<style>.ec{{margin:40px 0}}.ecg{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}}.ecg div{{background:var(--bg2,#f3f5f8);padding:16px;border-radius:10px}}.ecg b{{display:block;font-size:26px;line-height:1.15;word-break:keep-all}}.ecg span{{display:block;font-size:14px;margin-top:2px}}.ecg small{{display:block;font-size:13px;opacity:.75;margin-top:4px}}@media(max-width:760px){{.ecg{{grid-template-columns:1fr 1fr;gap:8px}}.ecg div{{padding:12px 10px}}.ecg b{{font-size:20px}}.ecg span{{font-size:12px}}}}</style>
<script>(function(){{var S={S},L="{L}",I="{iso}",sec=document.getElementById("econ");if(!sec)return;
function $(i){{return document.getElementById(i)}}
var loc=L==="ar"?"ar-u-nu-latn":L;
function C(v,cur){{if(L==="ko"&&cur)return v>=1e12?(v/1e12).toFixed(1)+"조 달러":v>=1e8?Math.round(v/1e8).toLocaleString("ko")+"억 달러":Math.round(v).toLocaleString("ko")+"달러";if(L==="ko"&&v>=1e4)return v>=1e8?(v/1e8).toFixed(1)+"억 명":Math.round(v/1e4).toLocaleString("ko")+"만 명";try{{return new Intl.NumberFormat(loc,cur?{{style:"currency",currency:"USD",notation:"compact",maximumFractionDigits:1}}:{{notation:"compact",maximumFractionDigits:1}}).format(v)}}catch(e){{return String(Math.round(v))}}}}
function N(v,d){{try{{return new Intl.NumberFormat(loc,{{maximumFractionDigits:d}}).format(v)}}catch(e){{return String(v)}}}}
function Y(a){{return a&&a[1]?a[1]+S[9]:""}}
fetch("https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/econ.json",{{cache:"no-store"}}).then(function(r){{if(!r.ok)throw 0;return r.json()}}).then(function(j){{
var d=(j.c||{{}})[I];if(!d||!(d.gdp||d.pop||d.usd))throw 0;
if(d.pop){{$("ec-pop").textContent=C(d.pop[0]);$("ec-popy").textContent=Y(d.pop)}}
if(d.gdp){{$("ec-gdp").textContent=C(d.gdp[0],1);$("ec-gdpy").textContent=Y(d.gdp)}}
if(d.pc){{$("ec-pc").textContent=C(d.pc[0],1);$("ec-pcy").textContent=Y(d.pc)}}
if(d.gr){{$("ec-gr").textContent=(d.gr[0]>0?"+":"")+N(d.gr[0],1)+"%";$("ec-gry").textContent=Y(d.gr)}}
if(d.cpi){{$("ec-cpi").textContent=N(d.cpi[0],1)+"%";$("ec-cpiy").textContent=Y(d.cpi)}}
if(d.cur){{$("ec-fx").textContent=d.cur;var t=[];if(d.cur!=="USD"&&d.usd)t.push("1 USD = "+N(d.usd,d.usd<10?3:1)+" "+d.cur);if(d.cur!=="KRW"&&d.krw)t.push("1 "+d.cur+" = "+N(d.krw,d.krw<10?3:1)+" KRW");$("ec-fxy").textContent=t.join(" · ")}}
var fx=(j.src||{{}}).fx||{{}};$("ec-src").textContent=S[8]+" "+String(fx.at||j.updated).slice(0,10)+(fx.ok===false?" (!)":"");
}}).catch(function(){{sec.querySelector(".ecg").remove();sec.querySelector(".note").textContent=S[10];}});}})();</script>'''


# Country sanctions card — reads data/feeds/sanctions.json (UN, US OFAC, EU, UK lists, collected daily, no AI)
SX = {
 "ko": ["제재 명단 현황", "4개 공식 제재 명단에서 이 나라 국적이나 주소로 등재된 개인·단체 수입니다. 나라 전체가 제재 대상이라는 뜻은 아닙니다. 거래 상대가 명단에 있는지는 원문 명단에서 직접 확인하세요.", "UN 안보리", "미국 재무부(OFAC)", "EU", "영국", "건", "4개 공식 명단에 이 나라와 연결된 등재가 없습니다.", "출처: UN 안보리 통합 제재 명단 · 미국 OFAC SDN 명단 · EU 금융제재 파일 · 영국 제재 명단(OGL v3.0) · 갱신", "제재 명단을 지금 불러오지 못했습니다.", "원문 명단 검색"],
 "en": ["Sanctions lists", "People and organisations on four official sanctions lists whose nationality or address is in this country. This does not mean the country itself is sanctioned. Always check a counterparty against the original list.", "UN Security Council", "US Treasury (OFAC)", "EU", "UK", "", "No entries tied to this country on the four official lists.", "Sources: UN Security Council Consolidated List · US OFAC SDN List · EU Financial Sanctions Files · UK Sanctions List (OGL v3.0) · updated", "The sanctions lists could not be loaded right now.", "Search the original list"],
 "es": ["Listas de sanciones", "Personas y entidades de cuatro listas oficiales de sanciones con nacionalidad o dirección en este país. No significa que el país esté sancionado. Verifique siempre a una contraparte en la lista original.", "Consejo de Seguridad de la ONU", "Tesoro de EE. UU. (OFAC)", "UE", "Reino Unido", "", "No hay registros vinculados a este país en las cuatro listas oficiales.", "Fuentes: Lista consolidada del Consejo de Seguridad de la ONU · Lista SDN de OFAC · Archivos de sanciones financieras de la UE · Lista de sanciones del Reino Unido (OGL v3.0) · actualizado", "No se pudieron cargar ahora las listas de sanciones.", "Buscar en la lista original"],
 "fr": ["Listes de sanctions", "Personnes et entités figurant sur quatre listes officielles de sanctions dont la nationalité ou l'adresse est dans ce pays. Cela ne signifie pas que le pays lui-même est sanctionné. Vérifiez toujours une contrepartie dans la liste d'origine.", "Conseil de sécurité de l'ONU", "Trésor américain (OFAC)", "UE", "Royaume-Uni", "", "Aucune inscription liée à ce pays sur les quatre listes officielles.", "Sources : Liste récapitulative du Conseil de sécurité de l'ONU · Liste SDN de l'OFAC · Fichiers des sanctions financières de l'UE · UK Sanctions List (OGL v3.0) · mis à jour", "Les listes de sanctions n'ont pas pu être chargées pour le moment.", "Chercher dans la liste d'origine"],
 "ar": ["قوائم العقوبات", "أفراد وكيانات مدرجون في أربع قوائم عقوبات رسمية وجنسيتهم أو عنوانهم في هذا البلد. لا يعني ذلك أن البلد نفسه خاضع للعقوبات. تحقّق دائمًا من الطرف المقابل في القائمة الأصلية.", "مجلس الأمن الدولي", "وزارة الخزانة الأمريكية (OFAC)", "الاتحاد الأوروبي", "المملكة المتحدة", "", "لا توجد إدراجات مرتبطة بهذا البلد في القوائم الرسمية الأربع.", "المصادر: القائمة الموحدة لمجلس الأمن · قائمة SDN لمكتب OFAC · ملفات العقوبات المالية للاتحاد الأوروبي · قائمة العقوبات البريطانية (OGL v3.0) · آخر تحديث", "تعذّر تحميل قوائم العقوبات الآن.", "ابحث في القائمة الأصلية"],
 "vi": ["Danh sách trừng phạt", "Cá nhân và tổ chức trong bốn danh sách trừng phạt chính thức có quốc tịch hoặc địa chỉ tại nước này. Điều này không có nghĩa là bản thân quốc gia bị trừng phạt. Luôn kiểm tra đối tác trong danh sách gốc.", "Hội đồng Bảo an LHQ", "Bộ Tài chính Mỹ (OFAC)", "EU", "Anh", "", "Không có mục nào liên quan đến nước này trong bốn danh sách chính thức.", "Nguồn: Danh sách hợp nhất của HĐBA LHQ · Danh sách SDN của OFAC · Tệp trừng phạt tài chính EU · Danh sách trừng phạt của Anh (OGL v3.0) · cập nhật", "Hiện chưa tải được danh sách trừng phạt.", "Tra cứu danh sách gốc"],
 "id": ["Daftar sanksi", "Orang dan organisasi di empat daftar sanksi resmi yang berkewarganegaraan atau beralamat di negara ini. Ini tidak berarti negara itu sendiri dikenai sanksi. Selalu periksa mitra di daftar aslinya.", "Dewan Keamanan PBB", "Departemen Keuangan AS (OFAC)", "UE", "Inggris", "", "Tidak ada entri yang terkait dengan negara ini di empat daftar resmi.", "Sumber: Daftar Konsolidasi Dewan Keamanan PBB · Daftar SDN OFAC · Berkas Sanksi Keuangan UE · Daftar Sanksi Inggris (OGL v3.0) · diperbarui", "Daftar sanksi belum dapat dimuat sekarang.", "Cari di daftar asli"],
}
SX_URL = {"un": "https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list", "us": "https://sanctionssearch.ofac.treas.gov/",
          "eu": "https://www.sanctionsmap.eu/", "uk": "https://www.gov.uk/government/publications/the-uk-sanctions-list"}
def cty_sanctions(iso, L):
    s = SX.get(L) or SX["en"]; S = _json.dumps(s, ensure_ascii=False)
    cells = "".join(f'<div data-k="{k}"><b>–</b><span>{s[i]}</span><small></small><a href="{SX_URL[k]}" target="_blank" rel="noopener">{s[10]} ↗</a></div>' for i, k in ((2, "un"), (3, "us"), (4, "eu"), (5, "uk")))
    return f'''<section class="ec sx" id="sanctions" data-iso="{iso}"><h2>{s[0]}</h2><p class="note">{s[1]}</p><div class="ecg sxg">{cells}</div><p class="fine sx-src"></p></section>
<style>.sxg{{grid-template-columns:repeat(4,1fr)}}.sxg a{{display:inline-block;font-size:13px;margin-top:8px}}.sxg div.z b{{opacity:.45}}@media(max-width:760px){{.sxg{{grid-template-columns:1fr 1fr}}}}</style>
<script>(function(){{var S={S},I="{iso}",L="{L}",sec=document.getElementById("sanctions");if(!sec)return;var loc=L==="ar"?"ar-u-nu-latn":L;
fetch("https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/sanctions.json",{{cache:"no-store"}}).then(function(r){{if(!r.ok)throw 0;return r.json()}}).then(function(j){{
var d=(j.c||{{}})[I]||{{}},any=0;sec.querySelectorAll(".sxg>div").forEach(function(el){{var v=d[el.dataset.k];var n=v?v[0]:0;any+=n;
el.querySelector("b").textContent=new Intl.NumberFormat(loc).format(n)+S[6];el.querySelector("small").textContent=v&&v[1]?v[1].join(" · "):"";if(!n)el.classList.add("z")}});
if(!any)sec.querySelector(".note").textContent=S[7];var u=(j.src||{{}}),t=[];for(var k in u)if(u[k].ok===false)t.push(k.toUpperCase()+" (!)");
sec.querySelector(".sx-src").textContent=S[8]+" "+String(j.updated).slice(0,10)+(t.length?" · "+t.join(" "):"");
}}).catch(function(){{sec.querySelector(".sxg").remove();sec.querySelector(".note").textContent=S[9]}});}})();</script>'''


# Home "today's changes" — reads data/feeds/today.json (built daily from the feeds, no AI)
TD = {
 "ko": ["오늘의 변화", "매일 아침 AI 없이 새로 모은 결과입니다. 공고는 원문 기준이며, 숫자는 모두 실제 건수입니다.", "오늘 새로 잡힌 공고", "2일 안에 마감", "지금 열린 입찰", "48시간 내 공식 경보", "새로 잡힌 공고", "마감 임박", "공식 기관 경보", "데이터 출처 상태", "정상", "일부", "실패", "갱신", "오늘의 변화를 지금 불러오지 못했습니다.", "개국", "마감", "입찰·수주 센터에서 전체 보기", "결과 없음"],
 "en": ["Today's changes", "Collected fresh every morning without AI. Notices follow the original source and every number is a real count.", "New notices today", "Closing within 2 days", "Open tenders now", "Official alerts, last 48 h", "New notices", "Closing soon", "Official alerts", "Data source status", "OK", "Partial", "Failed", "updated", "Today's changes could not be loaded right now.", "countries", "closes", "See everything in the tender centre", "none"],
 "es": ["Cambios de hoy", "Recopilado cada mañana sin IA. Los avisos siguen la fuente original y cada número es un recuento real.", "Avisos nuevos hoy", "Cierran en 2 días", "Licitaciones abiertas", "Alertas oficiales, 48 h", "Avisos nuevos", "Cierre próximo", "Alertas oficiales", "Estado de las fuentes", "OK", "Parcial", "Falló", "actualizado", "No se pudieron cargar ahora los cambios de hoy.", "países", "cierre", "Ver todo en el centro de licitaciones", "ninguno"],
 "fr": ["Les changements du jour", "Collecté chaque matin sans IA. Les avis suivent la source d'origine et chaque nombre est un décompte réel.", "Nouveaux avis aujourd'hui", "Clôture sous 2 jours", "Appels d'offres ouverts", "Alertes officielles, 48 h", "Nouveaux avis", "Clôture proche", "Alertes officielles", "État des sources", "OK", "Partiel", "Échec", "mis à jour", "Les changements du jour n'ont pas pu être chargés.", "pays", "clôture", "Tout voir dans le centre des marchés", "aucun"],
 "ar": ["تغييرات اليوم", "تُجمع كل صباح دون ذكاء اصطناعي. الإعلانات وفق المصدر الأصلي وكل رقم عدد فعلي.", "إعلانات جديدة اليوم", "تُغلق خلال يومين", "مناقصات مفتوحة الآن", "تنبيهات رسمية خلال 48 ساعة", "إعلانات جديدة", "إغلاق قريب", "تنبيهات رسمية", "حالة مصادر البيانات", "سليم", "جزئي", "فشل", "آخر تحديث", "تعذّر تحميل تغييرات اليوم الآن.", "بلدًا", "الإغلاق", "عرض الكل في مركز المناقصات", "لا شيء"],
 "vi": ["Thay đổi hôm nay", "Thu thập mới mỗi sáng, không dùng AI. Thông báo theo nguồn gốc và mọi con số là số đếm thực.", "Thông báo mới hôm nay", "Đóng trong 2 ngày", "Gói thầu đang mở", "Cảnh báo chính thức 48 giờ", "Thông báo mới", "Sắp đóng", "Cảnh báo chính thức", "Trạng thái nguồn dữ liệu", "Tốt", "Một phần", "Lỗi", "cập nhật", "Hiện chưa tải được thay đổi hôm nay.", "quốc gia", "đóng", "Xem tất cả ở trung tâm đấu thầu", "không có"],
 "id": ["Perubahan hari ini", "Dikumpulkan setiap pagi tanpa AI. Pengumuman mengikuti sumber asli dan setiap angka adalah hitungan nyata.", "Pengumuman baru hari ini", "Tutup dalam 2 hari", "Tender terbuka", "Peringatan resmi 48 jam", "Pengumuman baru", "Segera tutup", "Peringatan resmi", "Status sumber data", "OK", "Sebagian", "Gagal", "diperbarui", "Perubahan hari ini belum dapat dimuat.", "negara", "tutup", "Lihat semua di pusat tender", "tidak ada"],
}
def today_band(L):
    s = TD.get(L) or TD["en"]; S = _json.dumps(s, ensure_ascii=False)
    hz = f'/hazards/{"" if L == "ko" else "?l=en"}'
    return f'''<section class="band td" id="today"><div class="in"><h2>{s[0]}</h2><p class="note">{s[1]}</p>
<div class="tdk"><a href="/{L}/win/"><b id="td-new">–</b><span>{s[2]}</span></a><a href="/{L}/win/"><b id="td-urg">–</b><span>{s[3]}</span></a><a href="/{L}/win/"><b id="td-open">–</b><span>{s[4]}</span><small id="td-c"></small></a><a href="{hz}"><b id="td-al">–</b><span>{s[5]}</span></a></div>
<div class="tdc"><div><h3>{s[6]}</h3><ol class="cil" id="td-nl"></ol></div><div><h3>{s[7]}</h3><ol class="cil" id="td-ul"></ol></div><div><h3>{s[8]}</h3><ol class="cil" id="td-al2"></ol></div></div>
<h3 class="tds-h">{s[9]}</h3><ul class="tds" id="td-src"></ul>{lic_note(L)}<p class="cta"><a class="btn pri" href="/{L}/win/">{s[17]} →</a></p><p class="fine" id="td-up"></p></div></section>
<style>.tdk{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 28px}}.tdk a{{display:block;background:var(--bg2,#f3f5f8);padding:18px;border-radius:12px;color:inherit;text-decoration:none;transition:transform .2s}}.tdk a:hover{{transform:translateY(-2px)}}.tdk b{{display:block;font-size:36px;line-height:1.1}}.tdk span{{display:block;font-size:14px;margin-top:4px}}.tdk small{{display:block;font-size:13px;opacity:.7}}
.tdc{{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}}.tdc .cil{{padding:0;margin:0;list-style:none}}.tdc .cil li{{padding:10px 0;border-bottom:1px solid rgba(127,127,127,.18);font-size:15px;line-height:1.45}}.tdc .cil li a{{color:inherit}}.tdc .cil li small{{display:block;opacity:.72;font-size:13px}}
.tds-h{{margin-top:32px}}.tds{{list-style:none;padding:0;margin:10px 0 0;display:flex;flex-wrap:wrap;gap:8px}}.tds li{{font-size:13px;padding:6px 12px;border-radius:999px;background:var(--bg2,#f3f5f8)}}.tds li i{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:#16a34a}}.tds li.p i{{background:#f59e0b}}.tds li.f i{{background:#dc2626}}
@media(max-width:760px){{.tdk{{grid-template-columns:1fr 1fr;gap:8px}}.tdk a{{padding:14px 12px}}.tdk b{{font-size:26px}}.tdc{{grid-template-columns:1fr;gap:8px}}}}</style>
<script>{DLJS}</script><script>(function(){{var S={S},L="{L}",sec=document.getElementById("today");if(!sec)return;var loc=L==="ar"?"ar-u-nu-latn":L;
function E(x){{return String(x==null?"":x).replace(/[&<>"]/g,function(c){{return{{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
function $(i){{return document.getElementById(i)}}function F(n){{return new Intl.NumberFormat(loc).format(n||0)}}
function li(x){{var I=GRDL.info(x.dla,x.dl);if(!I.open)return"";var c=(x.n&&(x.n[L]||x.n.en))||x.iso||"";return'<li dir="auto"><a href="'+E(x.url)+'" target="_blank" rel="noopener">'+E(x.t)+'</a><small>'+E(c)+" · "+E(x.src)+(I.date?" · "+E(GRDL.label(I,L)):"")+'</small></li>'}}
fetch("https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/today.json",{{cache:"no-store"}}).then(function(r){{if(!r.ok)throw 0;return r.json()}}).then(function(d){{
var n=d.n||{{}};$("td-new").textContent=F(n.new);$("td-urg").textContent=F(n.urgent);$("td-open").textContent=F(n.open);$("td-c").textContent=F(n.countries)+" "+S[15];$("td-al").textContent=F(n.alerts);
var no='<li>'+S[18]+'</li>';$("td-nl").innerHTML=(d.new||[]).map(li).join("")||no;$("td-ul").innerHTML=(d.urgent||[]).map(li).join("")||no;
$("td-al2").innerHTML=(d.alerts||[]).map(function(a){{return'<li dir="auto"><a href="'+E(a.url)+'" target="_blank" rel="noopener">'+E(a.t)+'</a><small>'+E(a.src)+" · "+E(a.date)+'</small></li>'}}).join("")||no;
$("td-src").innerHTML=(d.src||[]).map(function(x){{var st=x.state,c=st==="SUCCESS"||st==="EMPTY_SUCCESS"?"":st==="PARTIAL"?"p":"f",w=c===""?S[10]:c==="p"?S[11]:S[12];return'<li class="'+c+'"><i></i>'+E(x.name)+" · "+w+(x.kept?" · "+F(x.kept):"")+'</li>'}}).join("");
$("td-up").textContent=S[13]+" "+String(d.updated).replace("T"," ").replace("Z"," UTC");
}}).catch(function(){{sec.querySelector(".tdk").remove();sec.querySelector(".tdc").remove();sec.querySelector(".note").textContent=S[14]}});}})();</script>'''


# Source credits and reuse terms shown under every tender list (registry: tools/sources/registry.json reuse_*)
LIC = {
 "ko": ("출처·이용조건", "세계은행 조달·사업·낙찰 데이터 (CC BY 4.0)", "EU 조달공보 TED (자유 재사용, EU 결정 2011/833)", "영국 Find a Tender·Contracts Finder (Open Government Licence v3.0)", "우크라이나 Prozorro 공식 공개 데이터 (원문 링크 제공 · 이용조건 확인 중)", "한국어 제목·분석은 GOV RADAR가 만든 것이며 각 기관의 보증이나 제휴가 아닙니다. 응찰 전 원문 공고를 확인하세요."),
 "en": ("Sources and terms", "World Bank procurement, project and award data (CC BY 4.0)", "EU TED (free reuse, Decision 2011/833/EU)", "UK Find a Tender and Contracts Finder (Open Government Licence v3.0)", "Prozorro, Ukraine's official open data (link to the original; terms under review)", "Translations and analysis are GOV RADAR's own and are not endorsed by these bodies. Check the original notice before bidding."),
 "es": ("Fuentes y condiciones", "Datos de adquisiciones, proyectos y adjudicaciones del Banco Mundial (CC BY 4.0)", "TED de la UE (reutilización libre, Decisión 2011/833/UE)", "Find a Tender y Contracts Finder del Reino Unido (Open Government Licence v3.0)", "Prozorro, datos abiertos oficiales de Ucrania (enlace al original; condiciones en revisión)", "Las traducciones y análisis son de GOV RADAR y no están avalados por estos organismos. Consulte el aviso original antes de licitar."),
 "fr": ("Sources et conditions", "Données de marchés, projets et attributions de la Banque mondiale (CC BY 4.0)", "TED de l'UE (réutilisation libre, décision 2011/833/UE)", "Find a Tender et Contracts Finder du Royaume-Uni (Open Government Licence v3.0)", "Prozorro, données ouvertes officielles de l'Ukraine (lien vers l'original ; conditions en cours de vérification)", "Les traductions et analyses sont celles de GOV RADAR et ne sont pas approuvées par ces organismes. Vérifiez l'avis d'origine avant de soumissionner."),
 "ar": ("المصادر وشروط الاستخدام", "بيانات المشتريات والمشروعات والترسيات من البنك الدولي (CC BY 4.0)", "منصة TED الأوروبية (إعادة استخدام حرة، القرار 2011/833)", "منصتا Find a Tender وContracts Finder البريطانيتان (Open Government Licence v3.0)", "Prozorro، البيانات المفتوحة الرسمية لأوكرانيا (رابط إلى الأصل؛ الشروط قيد المراجعة)", "الترجمات والتحليلات من إعداد GOV RADAR وليست معتمدة من هذه الجهات. راجع الإعلان الأصلي قبل التقديم."),
 "vi": ("Nguồn và điều khoản", "Dữ liệu mua sắm, dự án và trao thầu của Ngân hàng Thế giới (CC BY 4.0)", "TED của EU (tái sử dụng tự do, Quyết định 2011/833/EU)", "Find a Tender và Contracts Finder của Anh (Open Government Licence v3.0)", "Prozorro, dữ liệu mở chính thức của Ukraina (liên kết bản gốc; điều khoản đang xem xét)", "Bản dịch và phân tích là của GOV RADAR, không được các cơ quan này bảo đảm. Hãy xem thông báo gốc trước khi dự thầu."),
 "id": ("Sumber dan ketentuan", "Data pengadaan, proyek, dan pemenang Bank Dunia (CC BY 4.0)", "TED Uni Eropa (bebas digunakan ulang, Keputusan 2011/833/UE)", "Find a Tender dan Contracts Finder Inggris (Open Government Licence v3.0)", "Prozorro, data terbuka resmi Ukraina (tautan ke aslinya; ketentuan sedang ditinjau)", "Terjemahan dan analisis dibuat oleh GOV RADAR dan tidak didukung oleh lembaga-lembaga ini. Periksa pengumuman asli sebelum mengajukan penawaran."),
}
LIC_URL = ["https://datacatalog.worldbank.org/search/dataset/0037776/procurement-notice", "https://ted.europa.eu/en/legal-notice",
           "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/", "https://prozorro.gov.ua/about"]
def lic_note(L):
    s = LIC.get(L) or LIC["en"]
    items = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{t}</a>' for t, u in zip(s[1:5], LIC_URL))
    return f'<p class="fine lic"><b>{s[0]}:</b> {items}. {s[5]}</p>'
