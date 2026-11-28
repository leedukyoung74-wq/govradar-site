"""Member analysis requests (doc 2026-11-14 §2–3): four fixed-scope requests.
Flow: pick a request → see output, limit and handling rule before sending → fill only what is needed →
request number issued, double submit blocked → lands in the Netlify "order" form (same inbox and Gmail-draft alert).
Copy is localized for seven site languages; API field identifiers remain stable."""
from html import escape as e

K = {
 "ko": dict(
  t="회원 분석 의뢰", lede="결과물의 범위가 정해진 네 가지 의뢰부터 받습니다. 보내기 전에 받게 될 결과물, 한도 차감, 처리 기준을 먼저 보여 드립니다.",
  who="대상: 분석 회원(월 20,000원). 매달 2건까지 포함됩니다. 회원이 아니거나 2건을 넘으면 건당 견적을 먼저 이메일로 보내 드리고, 동의하신 뒤에 시작합니다.",
  pick="1. 의뢰 고르기", fill="2. 필요한 정보만 입력", send="3. 확인하고 보내기",
  out="받는 결과물", need="필요한 정보", rule="처리 기준",
  limit="한도: 분석 회원은 매달 2건까지이며, 쓰지 않은 건수는 다음 달로 넘어가지 않습니다. 처리 기간은 의뢰 내용과 자료 범위에 따라 다르며, 접수 확인 메일에서 예상 기간을 먼저 알려 드립니다(AI가 정리하고 사람이 확인하는 빠른 검토, 보통 영업일 3일). 추가 질문이나 범위 변경은 별도 의뢰로 접수합니다. 결과물은 공개 자료에 근거한 참고용 검토이며 법률·투자·입찰 결과를 보장하지 않습니다. 요금표의 '입찰 적합도 판정(상담 후 견적)'은 서류 목록·컨소시엄 구성안까지 들어가는 상세판이고, 여기의 회원 의뢰는 참가 가능 여부와 부족한 조건을 정리하는 빠른 검토입니다.",
  rule_all="접수 확인은 영업일 기준 1~2일 안에 이메일로 보냅니다. 결과물에는 결론·근거·확인하지 못한 점·다음 할 일을 함께 적습니다. 분석을 진행할 수 없는 의뢰는 사유를 알려 드립니다.",
  email="이메일", name="이름 또는 담당자", org="회사·단체명 (선택)", country="관심 국가", code="회원 코드 (있으면)",
  agree="개인정보 수집·이용(의뢰 처리 목적, 처리 후 1년 보관)에 동의합니다", btn="의뢰 보내기", sending="보내는 중…",
  done="접수되었습니다. 요청번호", dup="같은 내용을 방금 보내셨습니다. 요청번호", mine="이 브라우저에서 보낸 의뢰", mine_n="아직 보낸 의뢰가 없습니다.",
  st="접수됨 — 확인 메일을 기다려 주세요", req="필수 항목을 채워 주세요.", left="이번 달 남은 의뢰 {n}건", over="이번 달 포함 건수(2건)를 넘어 견적을 먼저 보내 드립니다", quote="회원이 아니어서 견적을 먼저 이메일로 보내 드립니다", sent="접수 완료", delivery_failed="전달을 확인하지 못했습니다. 다시 보내 주세요. 요청번호", retry="다시 보내기",
  S={"received": "서버 기록됨 · 관리자 확인 전", "gateway_reported": "중계 성공 보고 · 관리자 확인 전", "gateway_failed_reported": "중계 실패 보고 · 재확인 필요", "relayed": "과거 중계 보고 · 관리자 수신 미확인", "relay_failed": "과거 중계 실패 보고 · 재확인 필요", "in_progress": "처리 중", "done": "완료 · 이메일 확인", "failed": "처리 불가 · 한도 반환", "cancelled": "취소 · 한도 반환"},
  types=[
   ("tender", "이 입찰에 우리 회사가 참여할 수 있는지 검토", "참가 자격·필요 서류·부족한 조건을 정리한 참가 조건표와 참여 권고(예·조건부·아니오)", "공고 링크 또는 제목, 업종, 연 매출, 공공·해외 실적, 보유 인증",
    [("tender", "공고 링크 또는 제목", "text", True), ("industry", "업종·주력 제품", "text", True), ("revenue", "연 매출 (억 원)", "number", False), ("record", "공공·해외 실적 (간단히)", "textarea", False), ("certs", "보유 인증", "text", False)]),
   ("country", "관심 국가의 사업 기회 정리", "그 나라 정부 과제·예산 사업·진행 중 입찰·ODA 중 우리 업종과 맞는 기회 5~10건과 접근 순서", "국가, 업종·제품, 원하는 진출 방식",
    [("industry", "업종·주력 제품", "text", True), ("mode", "원하는 방식 (수출·현지 파트너·입찰·투자 등)", "text", False), ("goal", "알고 싶은 것", "textarea", False)]),
   ("family", "우리 가족 재난 준비계획 작성", "우리 지역 위험에 맞춘 30일 준비계획: 비축 목록·수량, 연락·대피 계획, 점검 일정", "지역(시·군 단위), 가족 수, 영유아·고령자·반려동물 여부",
    [("area", "사는 지역 (시·군 단위까지만)", "text", True), ("people", "가족 수", "number", True), ("care", "영유아·고령자·반려동물 (해당하는 것만)", "text", False), ("note", "특별히 챙길 점 (선택, 건강 정보는 꼭 필요한 만큼만)", "textarea", False)]),
   ("partner", "내가 찾는 파트너와 지원 경로 정리", "찾는 상대의 유형·후보를 찾는 경로, 정부·기관 지원 사업, 첫 연락 방법", "찾는 상대, 내 제품·기술, 지역",
    [("seek", "찾는 상대 (바이어·제조사·현지 대리인 등)", "text", True), ("offer", "우리 제품·기술", "text", True), ("note", "조건·일정 (선택)", "textarea", False)]),
  ]),
 "en": dict(
  t="Member analysis requests", lede="We start with four requests whose output is fixed in advance. Before you send, you see what you will receive, how it counts against your limit, and how it is handled.",
  who="For analysis members (KRW 20,000 a month): two requests a month are included. Non-members and extra requests get a quote by email first, and we start only after you agree.",
  pick="1. Choose a request", fill="2. Give only what is needed", send="3. Check and send",
  out="You receive", need="We need", rule="Handling",
  limit="Limit: two requests a month for analysis members; unused requests do not carry over. Turnaround depends on the request and the material, and our confirmation email gives the expected time first (an AI-prepared quick review checked by a person, usually 3 business days). Follow-up questions or a wider scope count as a new request. Results are a reference review based on public information and do not guarantee legal, investment or tender outcomes. The per-tender fit assessment (quoted after consultation) on the pricing page is the detailed version with document list and consortium plan; member requests are a quick check of eligibility and gaps.",
  rule_all="We confirm receipt by email within one to two business days. Every result states the conclusion, the evidence, what could not be confirmed and the next step. If we cannot carry out a request, we tell you why.",
  email="Email", name="Name or contact person", org="Company or organisation (optional)", country="Country of interest", code="Member code (if any)",
  agree="I agree to the collection and use of my details to handle this request (kept for one year)", btn="Send request", sending="Sending…",
  done="Received. Request number", dup="You just sent the same request. Request number", mine="Requests sent from this browser", mine_n="No requests yet.",
  st="Received — watch for our confirmation email", req="Please fill in the required fields.", left="{n} requests left this month", over="Over this month's two included requests — we will send a quote first", quote="Not a member — we will email a quote first", sent="Received", delivery_failed="Delivery not confirmed. Please retry. Request number", retry="Retry sending",
  S={"received": "Server recorded · staff receipt unverified", "gateway_reported": "Gateway success reported · staff receipt unverified", "gateway_failed_reported": "Gateway failure reported · recheck needed", "relayed": "Legacy gateway report · staff receipt unverified", "relay_failed": "Legacy failure report · recheck needed", "in_progress": "In progress", "done": "Done · check your email", "failed": "Could not be done · allowance returned", "cancelled": "Cancelled · allowance returned"},
  types=[
   ("tender", "Can our company bid on this tender?", "An entry-conditions table (eligibility, documents, gaps) and a recommendation: yes, conditional or no", "Notice link or title, industry, annual revenue, public or overseas record, certifications",
    [("tender", "Notice link or title", "text", True), ("industry", "Industry and main product", "text", True), ("revenue", "Annual revenue (USD)", "text", False), ("record", "Public or overseas record (brief)", "textarea", False), ("certs", "Certifications", "text", False)]),
   ("country", "Business opportunities in a country", "5–10 matching opportunities from government priorities, funded projects, open tenders and ODA, with an order of approach", "Country, industry or product, preferred way in",
    [("industry", "Industry and main product", "text", True), ("mode", "Preferred way in (export, local partner, tender, investment…)", "text", False), ("goal", "What you want to know", "textarea", False)]),
   ("family", "A preparedness plan for my family", "A 30-day plan for your area's risks: supplies and quantities, contact and evacuation plan, check-up schedule", "Area (city or district only), household size, infants, elderly or pets",
    [("area", "Where you live (city or district only)", "text", True), ("people", "Household size", "number", True), ("care", "Infants, elderly, pets (only what applies)", "text", False), ("note", "Anything special (optional; health details only as needed)", "textarea", False)]),
   ("partner", "Partners and support routes for what I need", "Types of partner and where to find candidates, public support programmes, how to make first contact", "Who you seek, your product or technology, region",
    [("seek", "Who you seek (buyer, manufacturer, local agent…)", "text", True), ("offer", "Your product or technology", "text", True), ("note", "Conditions or timing (optional)", "textarea", False)]),
  ]),
}


# Five additional full request-page languages. Keep the underlying field IDs,
# request type IDs, quota, consent and Cloudflare/Netlify client logic unchanged.
# Editors may review the translated text without touching any storage schema.
_LOCALIZED_REQUESTS = {
 "es": dict(
  t="Solicitudes de análisis para miembros",
  lede="Elija uno de cuatro análisis definidos. Antes de enviarlo verá el resultado, el límite y las condiciones de tramitación.",
  who="Los miembros de análisis (20.000 KRW al mes) incluyen dos solicitudes al mes. Para no miembros o solicitudes adicionales enviaremos primero un presupuesto y no comenzaremos sin su aceptación.",
  pick="1. Elija el análisis",fill="2. Facilite solo los datos necesarios",send="3. Revise y envíe",
  out="Resultado",need="Datos necesarios",rule="Tramitación",
  limit="Dos solicitudes al mes por miembro; las no utilizadas no se acumulan. La confirmación indicará el plazo estimado (revisión rápida preparada por IA y verificada por una persona, normalmente 3 días hábiles). Ampliaciones y preguntas adicionales cuentan como otra solicitud. Este servicio orientativo basado en fuentes públicas no garantiza resultados legales, de inversión o licitación. La evaluación detallada de una licitación (presupuesto tras consulta) se contrata por separado.",
  rule_all="Confirmaremos la recepción por correo en 1–2 días hábiles. El informe explica las conclusiones, las fuentes, las incertidumbres y los próximos pasos. Si no podemos realizar el análisis, explicaremos el motivo.",
  email="Correo electrónico",name="Nombre o persona de contacto",org="Empresa u organización (opcional)",country="País de interés",code="Código de miembro (si existe)",
  agree="Acepto la recopilación y el uso de mis datos para tramitar esta solicitud (conservación durante un año).",btn="Enviar solicitud",sending="Enviando…",
  done="Solicitud recibida. Número",dup="Esta solicitud acaba de enviarse. Número",mine="Solicitudes enviadas desde este navegador",mine_n="Todavía no hay solicitudes.",
  st="Recibida — espere el correo de confirmación",req="Complete los campos obligatorios.",left="Solicitudes restantes este mes: {n}",over="Supera las dos solicitudes incluidas: enviaremos primero un presupuesto",quote="No tiene membresía: enviaremos primero un presupuesto",sent="Recibido",delivery_failed="No se ha confirmado la entrega. Vuelva a intentarlo. Número",retry="Reintentar",
  gateway="La pasarela recibió la solicitud; recepción por el personal no verificada. Número",
  S={"received":"Registrada en el servidor · pendiente de revisión","gateway_reported":"Pasarela confirmada · recepción por el personal no verificada","gateway_failed_reported":"Error de pasarela · revisar","relayed":"Registro anterior · recepción no verificada","relay_failed":"Error de envío anterior · revisar","in_progress":"En trámite","done":"Finalizada · revise su correo","failed":"No se puede tramitar · cuota restituida","cancelled":"Cancelada · cuota restituida"},
  type_text=[
   ("¿Puede nuestra empresa participar en esta licitación?","Tabla de requisitos, documentos y carencias, con recomendación: sí, condicionado o no","Enlace o título del anuncio, actividad, facturación anual, experiencia pública o exterior y certificaciones",["Enlace o título de la licitación","Sector y producto principal","Ingresos anuales (USD)","Experiencia en contratación pública o internacional","Certificaciones"]),
   ("Oportunidades de negocio en un país","Entre cinco y diez oportunidades relevantes (prioridades públicas, proyectos financiados, licitaciones y AOD) y orden de actuación","País, sector o producto y modalidad de acceso",["Sector y producto principal","Modalidad (exportación, socio local, licitación, inversión…)","Qué desea averiguar"]),
   ("Plan familiar de preparación ante emergencias","Plan de 30 días: suministros y cantidades, contactos, evacuación y revisiones","Zona (solo ciudad/distrito), número de convivientes, menores, mayores o animales",["Zona donde vive (solo ciudad o distrito)","Número de convivientes","Menores, mayores o animales (si procede)","Necesidades especiales (solo lo imprescindible)"]),
   ("Socios y vías de apoyo para su proyecto","Tipo de socio, cómo encontrar candidatos, programas públicos de apoyo y primer contacto","Tipo de socio, producto o tecnología y región",["Socio deseado (comprador, fabricante, representante…)","Producto o tecnología","Condiciones o calendario (opcional)"]),
  ]),
 "fr": dict(
  t="Demandes d’analyse des membres",
  lede="Choisissez parmi quatre analyses au périmètre défini. Avant l’envoi, consultez le livrable, le quota et les conditions de traitement.",
  who="Les membres Analyse (20 000 KRW par mois) disposent de deux demandes mensuelles. Pour les non-membres ou les demandes supplémentaires, un devis est envoyé et aucun travail ne débute sans acceptation.",
  pick="1. Choisir une analyse",fill="2. Fournir uniquement les informations utiles",send="3. Vérifier et envoyer",
  out="Livrable",need="Informations nécessaires",rule="Traitement",
  limit="Deux demandes par mois, non reportables. L’accusé de réception précisera le délai (revue rapide préparée par l’IA et vérifiée par une personne, généralement 3 jours ouvrés). Les questions supplémentaires ou l’élargissement du périmètre constituent une nouvelle demande. Cette analyse indicative fondée sur des données publiques ne garantit aucun résultat juridique, financier ou d’appel d’offres. L’évaluation détaillée d’un appel d’offres (sur devis après échange) est vendue séparément.",
  rule_all="Nous confirmons la réception par e-mail sous 1 à 2 jours ouvrés. Le livrable indique la conclusion, les sources, les incertitudes et les prochaines actions. Toute impossibilité est expliquée.",
  email="E-mail",name="Nom ou responsable",org="Entreprise ou organisation (facultatif)",country="Pays ciblé",code="Code membre (si disponible)",
  agree="J’accepte la collecte et l’utilisation de mes données pour traiter la demande (conservation pendant un an).",btn="Envoyer la demande",sending="Envoi en cours…",
  done="Demande reçue. Référence",dup="Cette demande vient d’être envoyée. Référence",mine="Demandes envoyées depuis ce navigateur",mine_n="Aucune demande pour le moment.",
  st="Reçue — attendez l’e-mail de confirmation",req="Renseignez les champs obligatoires.",left="Demandes restantes ce mois-ci : {n}",over="Deux demandes incluses dépassées : un devis sera envoyé",quote="Sans adhésion : un devis sera envoyé",sent="Reçue",delivery_failed="Livraison non confirmée. Réessayez. Référence",retry="Réessayer",
  gateway="La passerelle a accepté la demande ; réception par l’équipe non vérifiée. Référence",
  S={"received":"Enregistrée sur le serveur · à vérifier","gateway_reported":"Passerelle signalée · réception non vérifiée","gateway_failed_reported":"Échec de passerelle · contrôle requis","relayed":"Transfert antérieur · réception non vérifiée","relay_failed":"Échec de transfert · contrôle requis","in_progress":"En cours","done":"Terminée · consultez vos e-mails","failed":"Impossible · quota rétabli","cancelled":"Annulée · quota rétabli"},
  type_text=[
   ("Notre entreprise peut-elle répondre à cet appel d’offres ?","Tableau des conditions, pièces et manques, avec recommandation : oui, sous condition ou non","Lien ou titre de l’avis, activité, chiffre d’affaires annuel, références publiques ou étrangères, certifications",["Lien ou titre de l’avis","Secteur et produit principal","Chiffre d’affaires annuel (USD)","Références publiques ou internationales","Certifications"]),
   ("Opportunités commerciales dans un pays","Cinq à dix opportunités pertinentes (priorités publiques, projets financés, appels d’offres, APD) et un plan d’approche","Pays, secteur ou produit, mode d’entrée envisagé",["Secteur et produit principal","Mode d’entrée (export, partenaire, appel d’offres, investissement…)","Ce que vous souhaitez savoir"]),
   ("Plan familial de préparation aux catastrophes","Plan de 30 jours : réserves et quantités, contacts, évacuation et contrôles","Zone (ville ou district seulement), taille du foyer, enfants, personnes âgées, animaux",["Lieu de vie (ville ou district seulement)","Nombre de personnes au foyer","Enfants, personnes âgées, animaux (si pertinent)","Besoin particulier (données sensibles au strict minimum)"]),
   ("Partenaires et dispositifs de soutien","Types de partenaires, recherche de candidats, aides publiques et méthode de premier contact","Partenaires recherchés, produit ou technologie et région",["Partenaire recherché (acheteur, fabricant, agent local…)","Votre produit ou technologie","Conditions ou calendrier (facultatif)"]),
  ]),
 "ar": dict(
  t="طلبات التحليل للأعضاء",
  lede="اختر واحداً من أربعة طلبات ذات مخرجات محددة. ستعرف المخرجات والحد الشهري وآلية المعالجة قبل الإرسال.",
  who="تشمل عضوية التحليل (20,000 وون كوري شهرياً) طلبين شهرياً. يُرسل عرض سعر مسبقاً لغير الأعضاء والطلبات الإضافية، ولا نبدأ العمل إلا بعد الموافقة.",
  pick="١. اختر نوع الطلب",fill="٢. أدخل المعلومات الضرورية فقط",send="٣. راجع وأرسل",
  out="ما ستحصل عليه",need="المعلومات المطلوبة",rule="آلية المعالجة",
  limit="طلبان شهرياً للعضو، ولا تُرحَّل الطلبات غير المستخدمة. يوضح تأكيد الاستلام المدة المتوقعة (مراجعة سريعة يعدّها الذكاء الاصطناعي ويتحقق منها شخص، عادةً ٣ أيام عمل). تُحتسب الأسئلة الإضافية وتوسيع النطاق طلباً جديداً. هذه مراجعة استرشادية تعتمد على المصادر العامة ولا تضمن نتائج قانونية أو استثمارية أو نتائج المناقصات. تقييم المناقصة المفصل (بعرض سعر بعد الاستشارة) خدمة منفصلة.",
  rule_all="نرسل تأكيد الاستلام خلال يوم أو يومي عمل بالبريد الإلكتروني. يوضح التقرير النتيجة والأدلة وما تعذّر التحقق منه والخطوة التالية. سنشرح السبب إذا تعذّر تنفيذ الطلب.",
  email="البريد الإلكتروني",name="الاسم أو مسؤول التواصل",org="الشركة أو المؤسسة (اختياري)",country="الدولة المعنية",code="رمز العضوية (إن وجد)",
  agree="أوافق على جمع بياناتي واستخدامها لمعالجة الطلب (الاحتفاظ لمدة سنة واحدة).",btn="إرسال الطلب",sending="جارٍ الإرسال…",
  done="تم الاستلام. رقم الطلب",dup="أُرسل الطلب نفسه للتو. رقمه",mine="الطلبات المرسلة من هذا المتصفح",mine_n="لا توجد طلبات بعد.",
  st="تم الاستلام — انتظر رسالة التأكيد",req="يرجى تعبئة الحقول المطلوبة.",left="الطلبات المتبقية هذا الشهر: {n}",over="تجاوزت الطلبين المشمولين — سنرسل عرض سعر أولاً",quote="لست عضواً — سنرسل عرض سعر أولاً",sent="تم الاستلام",delivery_failed="تعذّر تأكيد التسليم. حاول مجدداً. رقم الطلب",retry="إعادة المحاولة",
  gateway="استقبلت بوابة الإرسال الطلب؛ لم يُتحقق من وصوله إلى الموظفين. رقم الطلب",
  S={"received":"سُجّل في الخادم · بانتظار المراجعة","gateway_reported":"تم الإبلاغ عن نجاح البوابة · الاستلام غير مؤكد","gateway_failed_reported":"خطأ بوابة · يلزم التحقق","relayed":"إرسال سابق · غير مؤكد","relay_failed":"خطأ إرسال سابق · يلزم التحقق","in_progress":"قيد المعالجة","done":"مكتمل · راجع بريدك","failed":"تعذّر التنفيذ · تمت إعادة الحصة","cancelled":"ملغى · تمت إعادة الحصة"},
  type_text=[
   ("هل يمكن لشركتنا المشاركة في هذه المناقصة؟","جدول الأهلية والمستندات والنواقص وتوصية بالمشاركة أو المشاركة المشروطة أو عدمها","رابط أو عنوان الإعلان والقطاع والإيراد السنوي والخبرة والشهادات",["رابط أو عنوان المناقصة","القطاع والمنتج الرئيسي","الإيراد السنوي (دولار أمريكي)","الخبرة في المناقصات العامة أو الدولية","الشهادات"]),
   ("فرص الأعمال في دولة معينة","٥–١٠ فرص مناسبة من الأولويات والمشاريع الحكومية والمناقصات والمساعدات، وترتيب خطوات الدخول","الدولة والقطاع أو المنتج وطريقة الدخول",["القطاع والمنتج الرئيسي","طريقة الدخول (تصدير، شريك محلي، مناقصة، استثمار…)","ما تريد معرفته"]),
   ("خطة استعداد الأسرة للطوارئ","خطة لمدة ٣٠ يوماً: المخزون والكميات والاتصال والإخلاء والفحص الدوري","المنطقة (المدينة أو الحي فقط) وعدد الأفراد والأطفال وكبار السن والحيوانات",["مكان السكن (مدينة أو حي فقط)","عدد أفراد الأسرة","أطفال أو كبار سن أو حيوانات (عند الحاجة)","احتياجات خاصة (بالحد الأدنى اللازم)"]),
   ("الشركاء ومسارات الدعم المناسبة","أنواع الشركاء وطرق إيجادهم وبرامج الدعم الحكومي وكيفية بدء التواصل","نوع الشريك والمنتج أو التقنية والمنطقة",["الشريك المطلوب (مشترٍ أو مصنع أو وكيل محلي…)","المنتج أو التقنية","الشروط أو المواعيد (اختياري)"]),
  ]),
 "vi": dict(
  t="Yêu cầu phân tích dành cho thành viên",
  lede="Chọn một trong bốn loại yêu cầu có đầu ra xác định. Xem trước kết quả, hạn mức và quy trình xử lý trước khi gửi.",
  who="Thành viên Phân tích (20.000 KRW/tháng) được bao gồm hai yêu cầu mỗi tháng. Người chưa là thành viên hoặc yêu cầu vượt hạn mức sẽ nhận báo giá trước; chỉ bắt đầu khi bạn đồng ý.",
  pick="1. Chọn yêu cầu",fill="2. Chỉ điền thông tin cần thiết",send="3. Kiểm tra và gửi",
  out="Kết quả nhận được",need="Thông tin cần cung cấp",rule="Quy trình xử lý",
  limit="Hai yêu cầu mỗi tháng, không chuyển phần chưa dùng sang tháng sau. Email xác nhận sẽ nêu thời gian dự kiến (bản rà soát nhanh do AI soạn và có người kiểm tra, thường 3 ngày làm việc). Câu hỏi bổ sung hoặc mở rộng phạm vi tính thành yêu cầu mới. Kết quả chỉ mang tính tham khảo dựa trên nguồn công khai, không bảo đảm kết quả pháp lý, đầu tư hay trúng thầu. Đánh giá hồ sơ thầu chuyên sâu (báo giá sau khi tư vấn) là dịch vụ riêng.",
  rule_all="Chúng tôi xác nhận tiếp nhận qua email trong 1–2 ngày làm việc. Báo cáo nêu kết luận, căn cứ, nội dung chưa xác minh và bước tiếp theo. Nếu không thể xử lý, chúng tôi sẽ giải thích lý do.",
  email="Email",name="Họ tên hoặc người phụ trách",org="Công ty hoặc tổ chức (không bắt buộc)",country="Quốc gia quan tâm",code="Mã thành viên (nếu có)",
  agree="Tôi đồng ý cho thu thập và sử dụng thông tin để xử lý yêu cầu (lưu giữ trong một năm).",btn="Gửi yêu cầu",sending="Đang gửi…",
  done="Đã tiếp nhận. Mã yêu cầu",dup="Bạn vừa gửi yêu cầu trùng. Mã yêu cầu",mine="Yêu cầu đã gửi từ trình duyệt này",mine_n="Chưa có yêu cầu.",
  st="Đã tiếp nhận — vui lòng chờ email xác nhận",req="Vui lòng điền các mục bắt buộc.",left="Số yêu cầu còn lại tháng này: {n}",over="Vượt hai yêu cầu đã bao gồm — chúng tôi sẽ báo giá trước",quote="Chưa là thành viên — chúng tôi sẽ báo giá trước",sent="Đã nhận",delivery_failed="Chưa xác nhận gửi thành công. Hãy thử lại. Mã yêu cầu",retry="Thử gửi lại",
  gateway="Cổng tiếp nhận đã nhận yêu cầu; chưa xác minh nhân viên đã nhận. Mã yêu cầu",
  S={"received":"Đã ghi trên máy chủ · chờ kiểm tra","gateway_reported":"Cổng báo thành công · chưa xác minh nhân viên nhận","gateway_failed_reported":"Cổng báo lỗi · cần kiểm tra","relayed":"Chuyển tiếp cũ · chưa xác minh nhận","relay_failed":"Chuyển tiếp lỗi · cần kiểm tra","in_progress":"Đang xử lý","done":"Hoàn thành · kiểm tra email","failed":"Không thể xử lý · hoàn hạn mức","cancelled":"Đã hủy · hoàn hạn mức"},
  type_text=[
   ("Công ty chúng tôi có đủ điều kiện dự thầu không?","Bảng điều kiện tham gia, tài liệu cần có và thiếu sót; kết luận có, có điều kiện hoặc không","Đường dẫn hoặc tên thông báo, ngành, doanh thu, kinh nghiệm trong/ngoài nước và chứng nhận",["Liên kết hoặc tên gói thầu","Ngành và sản phẩm chính","Doanh thu hằng năm (USD)","Kinh nghiệm đấu thầu công hoặc quốc tế","Chứng nhận"]),
   ("Cơ hội kinh doanh tại một quốc gia","5–10 cơ hội phù hợp từ ưu tiên chính phủ, dự án có vốn, đấu thầu và ODA cùng thứ tự tiếp cận","Quốc gia, ngành hoặc sản phẩm và hình thức thâm nhập",["Ngành và sản phẩm chính","Cách tiếp cận (xuất khẩu, đối tác, thầu, đầu tư…)","Điều bạn muốn tìm hiểu"]),
   ("Kế hoạch chuẩn bị thiên tai cho gia đình","Kế hoạch 30 ngày về vật tư và số lượng, liên hệ, sơ tán và kiểm tra định kỳ","Khu vực (chỉ thành phố/quận), số người, trẻ nhỏ, người cao tuổi, thú nuôi",["Nơi ở (chỉ thành phố/quận)","Số người trong gia đình","Trẻ em, người già, thú nuôi (nếu có)","Điều cần lưu ý (chỉ thông tin cần thiết)"]),
   ("Đối tác và kênh hỗ trợ cho dự án","Loại đối tác, cách tìm ứng viên, chương trình hỗ trợ công và cách liên hệ ban đầu","Đối tác cần tìm, sản phẩm/công nghệ và khu vực",["Đối tác cần tìm (người mua, nhà sản xuất, đại lý…)","Sản phẩm hoặc công nghệ","Điều kiện hoặc thời gian (không bắt buộc)"]),
  ]),
 "id": dict(
  t="Permintaan analisis untuk anggota",
  lede="Pilih satu dari empat permintaan dengan hasil yang sudah ditentukan. Tinjau hasil, kuota, dan proses sebelum mengirim.",
  who="Anggota Analisis (KRW 20.000 per bulan) memperoleh dua permintaan per bulan. Nonanggota atau permintaan tambahan akan menerima penawaran harga terlebih dahulu, dan pekerjaan baru dimulai setelah persetujuan.",
  pick="1. Pilih analisis",fill="2. Isi hanya informasi yang diperlukan",send="3. Periksa dan kirim",
  out="Hasil yang diterima",need="Informasi yang dibutuhkan",rule="Proses",
  limit="Dua permintaan per bulan; sisa kuota tidak dibawa ke bulan berikutnya. Email konfirmasi memuat estimasi waktu (tinjauan cepat yang disusun AI dan diperiksa manusia, biasanya 3 hari kerja). Pertanyaan tambahan atau perluasan lingkup merupakan permintaan baru. Tinjauan berdasarkan sumber publik ini tidak menjamin hasil hukum, investasi, atau tender. Penilaian tender terperinci (penawaran setelah konsultasi) merupakan layanan terpisah.",
  rule_all="Kami mengirim konfirmasi penerimaan dalam 1–2 hari kerja melalui email. Setiap laporan memuat kesimpulan, sumber, hal yang belum diverifikasi dan langkah selanjutnya. Jika permintaan tidak dapat ditangani, alasannya akan dijelaskan.",
  email="Email",name="Nama atau penanggung jawab",org="Perusahaan atau organisasi (opsional)",country="Negara tujuan",code="Kode anggota (jika ada)",
  agree="Saya setuju data dikumpulkan dan digunakan untuk memproses permintaan ini (disimpan selama satu tahun).",btn="Kirim permintaan",sending="Mengirim…",
  done="Permintaan diterima. Nomor",dup="Permintaan yang sama baru saja dikirim. Nomor",mine="Permintaan dari peramban ini",mine_n="Belum ada permintaan.",
  st="Diterima — tunggu email konfirmasi",req="Lengkapi bidang wajib.",left="Sisa permintaan bulan ini: {n}",over="Melebihi dua permintaan termasuk paket — kami akan mengirim penawaran harga terlebih dahulu",quote="Bukan anggota — penawaran harga akan dikirim terlebih dahulu",sent="Diterima",delivery_failed="Pengiriman belum dapat dikonfirmasi. Silakan ulangi. Nomor",retry="Kirim ulang",
  gateway="Gateway menerima permintaan, tetapi penerimaan oleh staf belum terverifikasi. Nomor",
  S={"received":"Dicatat di server · menunggu pemeriksaan","gateway_reported":"Gateway melaporkan berhasil · penerimaan staf belum terverifikasi","gateway_failed_reported":"Gateway gagal · perlu pemeriksaan","relayed":"Diteruskan sebelumnya · penerimaan belum diverifikasi","relay_failed":"Penerusan sebelumnya gagal · perlu pemeriksaan","in_progress":"Diproses","done":"Selesai · periksa email","failed":"Tidak dapat diproses · kuota dikembalikan","cancelled":"Dibatalkan · kuota dikembalikan"},
  type_text=[
   ("Bisakah perusahaan kami mengikuti tender ini?","Tabel kelayakan, dokumen, kesenjangan dan rekomendasi: bisa, bersyarat atau tidak","Tautan atau judul tender, bidang usaha, pendapatan tahunan, pengalaman publik atau luar negeri, sertifikasi",["Tautan atau judul tender","Sektor dan produk utama","Pendapatan tahunan (USD)","Pengalaman tender publik atau internasional","Sertifikasi"]),
   ("Peluang bisnis di suatu negara","5–10 peluang yang cocok dari prioritas pemerintah, proyek didanai, tender dan ODA serta urutan pendekatannya","Negara, sektor atau produk dan cara memasuki pasar",["Sektor dan produk utama","Cara masuk (ekspor, mitra lokal, tender, investasi…)","Hal yang ingin diketahui"]),
   ("Rencana kesiapsiagaan bencana keluarga","Rencana 30 hari: persediaan, jumlah, kontak, evakuasi dan pemeriksaan berkala","Area (hanya kota/kecamatan), jumlah anggota keluarga, anak, lansia atau hewan",["Lokasi tinggal (hanya kota/kecamatan)","Jumlah anggota keluarga","Anak, lansia, hewan peliharaan (jika ada)","Kebutuhan khusus (seperlunya saja)"]),
   ("Mitra dan jalur dukungan yang diperlukan","Jenis mitra, cara mencari kandidat, program dukungan pemerintah dan cara kontak pertama","Mitra yang dicari, produk/teknologi dan wilayah",["Mitra yang dicari (pembeli, produsen, agen lokal…)","Produk atau teknologi Anda","Syarat atau jadwal (opsional)"]),
  ]),
}
for _lang, _copy in _LOCALIZED_REQUESTS.items():
    _names = []
    for _base, _translated in zip(K["en"]["types"], _copy["type_text"]):
        _id, _, _, _, _fields = _base
        _title, _deliverable, _requirements, _labels = _translated
        assert len(_fields) == len(_labels), (_lang, _id)
        _names.append((_id, _title, _deliverable, _requirements,
                       [(f[0], label, f[2], f[3]) for f, label in zip(_fields, _labels)]))
    K[_lang] = dict(K["en"], **{k:v for k,v in _copy.items() if k!="type_text"})
    K[_lang]["types"] = _names



def request_page(L, head, foot, LANGS):
    k = K.get(L) or K["en"]
    ko = L == "ko"
    cards = "".join(f'''<label class="rq-c"><input type="radio" name="rqt" value="{tid}"{" checked" if i == 0 else ""}><b>{e(tt)}</b>
<span><i>{e(k["out"])}</i> {e(out)}</span><span><i>{e(k["need"])}</i> {e(nd)}</span></label>''' for i, (tid, tt, out, nd, _) in enumerate(k["types"]))
    fields = "".join(f'<div class="rq-f" data-t="{tid}"' + ("" if i == 0 else " hidden") + ">" + "".join(
        (f'<label>{e(lb)}{" *" if rq else ""}<textarea data-k="{fk}" rows="3"{" data-req" if rq else ""}></textarea></label>' if ty == "textarea"
         else f'<label>{e(lb)}{" *" if rq else ""}<input data-k="{fk}" type="{ty}"{" data-req" if rq else ""}></label>')
        for fk, lb, ty, rq in fl) + "</div>" for i, (tid, _, _, _, fl) in enumerate(k["types"]))
    names = {tid: tt for tid, tt, *_ in k["types"]}
    import json
    body = f'''<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{e(k["t"])}</h1><p class="lede">{e(k["lede"])}</p><p style="font-size:14px;color:#d8d8d4;margin:10px 0 0">{e(k["who"])}</p></div></section>
<section class="band"><div class="in rq">
<h2>{e(k["pick"])}</h2><div class="rq-g">{cards}</div>
<div class="rq-rule"><p><b>{e(k["rule"])}</b> · {e(k["rule_all"])}</p><p>{e(k["limit"])}</p></div>
<h2>{e(k["fill"])}</h2>
<form class="cform rq-form" name="order" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/thanks/">
<input type="hidden" name="form-name" value="order"><input type="hidden" name="lang" value="{L}"><input type="hidden" name="product"><input type="hidden" name="need"><input type="hidden" name="field">
<p hidden><label>hp<input name="hp"></label></p>
{fields}
<div class="two"><label>{e(k["email"])} *<input name="email" type="email" required></label><label>{e(k["name"])} *<input name="name" required></label></div>
<div class="two"><label>{e(k["org"])}<input name="org"></label><label>{e(k["country"])}<input name="countries"></label></div>

<h2>{e(k["send"])}</h2>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> {e(k["agree"])}</label>
<p><button class="btn pri" type="submit">{e(k["btn"])}</button> <span class="rq-msg note" role="status"></span></p>
</form>
<h3>{e(k["mine"])}</h3><ul class="rq-mine"></ul>
</div></section>
<script>(function(){{var K={json.dumps({"names": names, "done": k["done"], "dup": k["dup"], "st": k["st"], "none": k["mine_n"], "req": k["req"], "sending": k["sending"], "left": k.get("left", "이번 달 남은 의뢰 {n}건"), "over": k.get("over", "이번 달 포함 건수를 넘어 견적을 먼저 보내 드립니다"), "quote": k.get("quote", "견적을 먼저 이메일로 보내 드립니다"), "sent": k.get("sent", "접수 완료"), "gateway": k.get("gateway", ("전송 서버가 요청을 받았습니다. 관리자 확인 전입니다. 요청번호" if L == "ko" else "Gateway accepted the request; staff receipt not verified. Request number")), "delivery_failed": k.get("delivery_failed", "Delivery not confirmed. Please retry. Request number"), "retry": k.get("retry", "Retry sending"), "S": k.get("S", {})}, ensure_ascii=False)};
var f=document.querySelector(".rq-form"),msg=f.querySelector(".rq-msg"),btn=f.querySelector("button[type=submit]");
function cur(){{return (document.querySelector("input[name=rqt]:checked")||{{}}).value}}
document.querySelectorAll("input[name=rqt]").forEach(function(r){{r.addEventListener("change",function(){{f.querySelectorAll(".rq-f").forEach(function(d){{d.hidden=d.dataset.t!==cur()}})}})}});
function load(){{try{{return JSON.parse(localStorage.getItem("gv_rq")||"[]")}}catch(e){{return []}}}}
function save(a){{try{{localStorage.setItem("gv_rq",JSON.stringify(a.slice(0,30)))}}catch(e){{}}}}
function paint(){{var a=load(),u=document.querySelector(".rq-mine");u.innerHTML=a.length?a.map(function(x){{return "<li><b>"+x.id+"</b> · "+(K.names[x.t]||x.t)+" <small class=note>"+x.at+" · "+(x.relay_failed?K.delivery_failed:(x.gateway_only?K.gateway:K.st))+"</small></li>"}}).join(""):"<li class=note>"+K.none+"</li>"}}
function hash(s){{var h=0;for(var i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))|0;return String(h)}}
f.addEventListener("submit",function(ev){{var t=cur(),box=f.querySelector('.rq-f[data-t="'+t+'"]'),lines=[],ok=true;
box.querySelectorAll("[data-k]").forEach(function(i){{var v=(i.value||"").trim();if(i.hasAttribute("data-req")&&!v)ok=false;if(v)lines.push(i.parentNode.firstChild.textContent.replace(" *","")+": "+v)}});
// Membership is determined by verified sign-in, never a secret code in an inquiry.
if(!ok||!f.querySelector('input[name="privacy_agree"]').checked){{ev.preventDefault();msg.textContent=K.req;return}}
var h=hash(t+lines.join("|")+f.email.value),a=load(),prev=a.filter(function(x){{return x.h===h&&Date.now()-x.ts<6e5}})[0];
if(prev&&!prev.relay_failed){{ev.preventDefault();msg.textContent=K.dup+" "+prev.id;return}}
var d=new Date(),id="RQ-"+String(d.getFullYear()).slice(2)+("0"+(d.getMonth()+1)).slice(-2)+("0"+d.getDate()).slice(-2)+"-"+Math.random().toString(36).slice(2,6).toUpperCase();
f.product.value="request:"+t+" "+id;f.field.value=t;f.need.value="["+id+"] "+(K.names[t]||t)+"\\n"+lines.join("\\n");
a.unshift({{id:id,t:t,h:h,ts:Date.now(),at:d.toISOString().slice(0,10)}});save(a);btn.disabled=true;btn.textContent=K.sending;msg.textContent=K.sending+" "+id;
/* server record (Cloudflare D1): if /api/req answers, it issues the number, counts the monthly allowance and blocks duplicates;
   the Netlify form is then posted by fetch and its result reported back. 503 (not configured) -> the browser-only flow above. */
ev.preventDefault();var sendBody=lines.join("\\n");
function relayWithoutD1(){{return fetch(f.getAttribute("action"),{{method:"POST",headers:{{"content-type":"application/x-www-form-urlencoded"}},body:new URLSearchParams(new FormData(f)).toString(),redirect:"manual"}}).then(function(r){{
if(r.type!=="opaqueredirect"&&r.status!==303)throw Error("relay-not-accepted");
a[0].relay_failed=false;a[0].gateway_only=true;save(a);msg.textContent=K.gateway+" "+id;btn.textContent=K.sent;paint();
}}).catch(function(){{a[0].relay_failed=true;save(a);msg.textContent=K.delivery_failed+" "+id;btn.disabled=false;btn.textContent=K.retry;paint()}})}}
if(SRV){{
fetch("/api/req",{{method:"POST",headers:hdr({{"content-type":"application/json"}}),body:JSON.stringify({{type:t,body:sendBody,email:f.email.value,lang:L,privacy_consent:f.querySelector('input[name="privacy_agree"]').checked}})}}).then(function(r){{if(r.status===503){{SRV=false;throw Error("D1_UNAVAILABLE")}}if(!r.ok)throw Error("REQUEST_API_ERROR");return r.json()}}).then(function(j){{
if(!j.req_no)throw 0;id=j.req_no;a[0].id=id;save(a);f.product.value="request:"+t+" "+id;f.need.value="["+id+"] "+(K.names[t]||t)+"\\n"+sendBody;
var info=j.duplicate?K.dup+" "+id:K.done+" "+id+(j.member?(j.counted?" · "+K.left.replace("{{n}}",j.left):" · "+K.over):" · "+K.quote);msg.textContent=K.sending+" "+id;
function relayFailed(){{a[0].relay_failed=true;save(a);msg.textContent=K.delivery_failed+" "+id;btn.disabled=false;btn.textContent=K.retry;paint()}}
return fetch(f.getAttribute("action"),{{method:"POST",headers:{{"content-type":"application/x-www-form-urlencoded"}},body:new URLSearchParams(new FormData(f)).toString(),redirect:"manual"}}).then(function(r2){{
var ok=r2.type==="opaqueredirect"||r2.status===303;
var mark=tok()?fetch("/api/req",{{method:"PATCH",headers:hdr({{"content-type":"application/json"}}),body:JSON.stringify({{req_no:id,ok:ok}})}}).catch(function(){{}}):Promise.resolve();
return mark.then(function(){{if(ok){{a[0].relay_failed=false;save(a);msg.textContent=info;btn.textContent=K.sent;paint()}}else relayFailed()}})
}}).catch(relayFailed);
}}).catch(function(){{if(!SRV){{relayWithoutD1()}}else{{a[0].relay_failed=true;save(a);msg.textContent=K.delivery_failed+" "+id;btn.disabled=false;btn.textContent=K.retry;paint()}}}})}}else relayWithoutD1();
}});
var L=document.documentElement.lang||"ko",SRV=true;
function tok(){{try{{var x=JSON.parse(localStorage.getItem("wmm.auth.v1")||"null");return x&&x.access_token}}catch(e){{return null}}}}
function hdr(h){{var k=tok();if(k)h.authorization="Bearer "+k;return h}}
paint();
if(tok())fetch("/api/req",{{headers:hdr({{}})}}).then(function(r){{if(!r.ok)throw 0;return r.json()}}).then(function(j){{var u=document.querySelector(".rq-mine");
u.innerHTML=(j.member?"<li class=note>"+K.left.replace("{{n}}",j.left)+"</li>":"")+((j.items||[]).map(function(x){{return "<li><b>"+x.req_no+"</b> · "+(K.names[x.type]||x.type)+" <small class=note>"+String(x.created_at).slice(0,10)+" · "+(K.S[x.status]||x.status)+"</small></li>"}}).join("")||"<li class=note>"+K.none+"</li>")}}).catch(function(){{}})
}})();</script>'''
    t_ = k["t"]
    return head(L, t_ + " · GOV RADAR", k["lede"][:150], f"/{L}/request/", {l: f"/{l}/request/" for l in LANGS}) + body + foot(L)
