# Extra UI strings (2026-10-31): sign-in, short top menu, new pages.
LANGS7 = ["ko", "en", "es", "fr", "ar", "vi", "id"]

AT = {
 "ko": dict(login="로그인", signup="회원가입", reset="비밀번호 재설정", newpw="새 비밀번호 설정", account="내 정보", send_reset="재설정 메일 받기", save_pw="비밀번호 저장",
   have_acct="이미 계정이 있어요 · 로그인", no_acct="처음이세요? 무료 가입", forgot="비밀번호를 잊었어요", back="로그인으로 돌아가기", google="Google로 계속하기",
   name="이름 또는 기관명", email="이메일", pw="비밀번호 (8자 이상)", age="연령대", age_opts=[["adult","만 19세 이상"],["teen","만 14세 이상 19세 미만 (청소년)"],["u14","만 14세 미만"]],
   terms='<a href="/ko/legal/terms/" target="_blank">이용약관</a>과 <a href="/ko/legal/privacy/" target="_blank">개인정보 처리방침</a>에 동의합니다 (필수)',
   need_terms="이용약관과 개인정보 처리방침에 동의해 주세요.", u14="만 14세 미만은 보호자 동의가 필요합니다. 보호자가 73036396@naver.com으로 신청해 주세요.",
   pw_short="비밀번호는 8자 이상이어야 합니다.", check_mail="가입 확인 메일을 보냈습니다. 메일의 링크를 누르면 바로 로그인됩니다.", welcome="환영합니다. 로그인되었습니다.",
   confirmed="이메일 확인이 끝났습니다. 로그인되었습니다.", reset_sent="재설정 메일을 보냈습니다. 메일의 링크를 눌러 새 비밀번호를 정하세요.", pw_saved="새 비밀번호를 저장했습니다.",
   bad_login="이메일 또는 비밀번호가 맞지 않습니다.", not_confirmed="이메일 확인이 아직 안 됐습니다. 받은 메일의 링크를 눌러 주세요.", exists="이미 가입된 이메일입니다. 로그인해 주세요.",
   not_enabled="로그인 서비스 점검 중입니다. 잠시 후 다시 시도해 주세요. 문의: 73036396@naver.com", ask_soon="AI 질문은 곧 열립니다.",
   tiers=dict(free="무료 회원 (EXPLORE)", member="분석 회원", partner="프로젝트 파트너십", inst="기관 라이선스", youth="청소년 (무료 학습)", edu="학생·청년 (EDU)", m1="BUILD M1", uni="대학·기관 라이선스", m2="BUILD M2", m3="BUILD M3", m4="EXECUTE M4", m5="EXECUTE M5", admin="운영자")),
 "en": dict(login="Sign in", signup="Create account", reset="Reset password", newpw="Set a new password", account="My account", send_reset="Email me a reset link", save_pw="Save password",
   have_acct="Have an account? Sign in", no_acct="New here? Join free", forgot="Forgot password", back="Back to sign in", google="Continue with Google",
   name="Name or organisation", email="Email", pw="Password (8+ characters)", age="Age group", age_opts=[["adult","19 or older"],["teen","14 to under 19"],["u14","Under 14"]],
   terms='I agree to the <a href="/en/legal/terms/" target="_blank">Terms</a> and <a href="/en/legal/privacy/" target="_blank">Privacy Policy</a> (required)',
   need_terms="Please accept the Terms and Privacy Policy.", u14="Under-14s need a parent's consent. Ask a parent to write to 73036396@naver.com.",
   pw_short="Password must be at least 8 characters.", check_mail="We sent a confirmation email. Click the link to finish and sign in.", welcome="Welcome — you're signed in.",
   confirmed="Email confirmed. You're signed in.", reset_sent="Reset email sent. Use the link to set a new password.", pw_saved="New password saved.",
   bad_login="Email or password is incorrect.", not_confirmed="Please confirm your email first (check your inbox).", exists="That email is already registered. Please sign in.",
   not_enabled="Sign-in is under maintenance. Please try again shortly. Contact: 73036396@naver.com", ask_soon="AI questions open soon.",
   tiers=dict(free="Free (EXPLORE)", member="Analysis member", partner="Project partnership", inst="Institutional licence", youth="Youth (free learning)", edu="Student / young adult (EDU)", m1="BUILD M1", uni="University / institution licence", m2="BUILD M2", m3="BUILD M3", m4="EXECUTE M4", m5="EXECUTE M5", admin="Operator")),
}
def _tr(base, **kw):
    d = dict(AT["en"]); d.update(kw); return d
AT["es"] = _tr("en", login="Acceder", signup="Crear cuenta", reset="Restablecer contraseña", newpw="Nueva contraseña", account="Mi cuenta", send_reset="Enviar enlace", save_pw="Guardar",
   have_acct="¿Ya tienes cuenta? Accede", no_acct="¿Nuevo? Únete gratis", forgot="Olvidé mi contraseña", back="Volver", google="Continuar con Google", name="Nombre u organización", email="Correo", pw="Contraseña (8+ caracteres)", age="Edad",
   age_opts=[["adult","19 años o más"],["teen","14 to under 19"],["u14","Menos de 14"]], terms='Acepto los <a href="/es/legal/terms/" target="_blank">Términos</a> y la <a href="/es/legal/privacy/" target="_blank">Privacidad</a> (obligatorio)',
   need_terms="Acepta los Términos y la Privacidad.", pw_short="Mínimo 8 caracteres.", check_mail="Te enviamos un correo de confirmación.", welcome="Bienvenido. Sesión iniciada.", bad_login="Correo o contraseña incorrectos.", not_enabled="Acceso en mantenimiento. Contacto: 73036396@naver.com")
AT["fr"] = _tr("en", login="Connexion", signup="Créer un compte", reset="Réinitialiser", newpw="Nouveau mot de passe", account="Mon compte", send_reset="Recevoir le lien", save_pw="Enregistrer",
   have_acct="Déjà inscrit ? Connexion", no_acct="Nouveau ? Inscription gratuite", forgot="Mot de passe oublié", back="Retour", google="Continuer avec Google", name="Nom ou organisation", email="E-mail", pw="Mot de passe (8 caractères min.)", age="Âge",
   age_opts=[["adult","19 ans et plus"],["teen","14–18 ans"],["u14","Moins de 14 ans"]], terms='J\'accepte les <a href="/fr/legal/terms/" target="_blank">Conditions</a> et la <a href="/fr/legal/privacy/" target="_blank">Confidentialité</a> (obligatoire)',
   need_terms="Veuillez accepter les Conditions.", pw_short="8 caractères minimum.", check_mail="E-mail de confirmation envoyé.", welcome="Bienvenue, vous êtes connecté.", bad_login="E-mail ou mot de passe incorrect.", not_enabled="Connexion en maintenance. Contact : 73036396@naver.com")
AT["ar"] = _tr("en", login="تسجيل الدخول", signup="إنشاء حساب", reset="إعادة تعيين كلمة المرور", newpw="كلمة مرور جديدة", account="حسابي", send_reset="أرسل الرابط", save_pw="حفظ",
   have_acct="لديك حساب؟ سجّل الدخول", no_acct="جديد؟ انضم مجانًا", forgot="نسيت كلمة المرور", back="رجوع", google="المتابعة عبر Google", name="الاسم أو الجهة", email="البريد الإلكتروني", pw="كلمة المرور (8 أحرف على الأقل)", age="الفئة العمرية",
   age_opts=[["adult","19 سنة فأكثر"],["teen","14 to under 19"],["u14","أقل من 14"]], terms='أوافق على <a href="/ar/legal/terms/" target="_blank">الشروط</a> و<a href="/ar/legal/privacy/" target="_blank">سياسة الخصوصية</a> (إلزامي)',
   need_terms="يرجى الموافقة على الشروط.", pw_short="8 أحرف على الأقل.", check_mail="أرسلنا رسالة تأكيد إلى بريدك.", welcome="مرحبًا، تم تسجيل دخولك.", bad_login="البريد أو كلمة المرور غير صحيحة.", not_enabled="الدخول قيد الصيانة. للتواصل: 73036396@naver.com")
AT["vi"] = _tr("en", login="Đăng nhập", signup="Tạo tài khoản", reset="Đặt lại mật khẩu", newpw="Mật khẩu mới", account="Tài khoản", send_reset="Gửi liên kết", save_pw="Lưu",
   have_acct="Đã có tài khoản? Đăng nhập", no_acct="Người mới? Tham gia miễn phí", forgot="Quên mật khẩu", back="Quay lại", google="Tiếp tục với Google", name="Tên hoặc tổ chức", email="Email", pw="Mật khẩu (từ 8 ký tự)", age="Độ tuổi",
   age_opts=[["adult","Từ 19 tuổi"],["teen","14 to under 19"],["u14","Dưới 14"]], terms='Tôi đồng ý với <a href="/vi/legal/terms/" target="_blank">Điều khoản</a> và <a href="/vi/legal/privacy/" target="_blank">Quyền riêng tư</a> (bắt buộc)',
   need_terms="Vui lòng đồng ý Điều khoản.", pw_short="Tối thiểu 8 ký tự.", check_mail="Đã gửi email xác nhận.", welcome="Chào mừng, bạn đã đăng nhập.", bad_login="Email hoặc mật khẩu không đúng.", not_enabled="Đăng nhập đang bảo trì. Liên hệ: 73036396@naver.com")
AT["id"] = _tr("en", login="Masuk", signup="Buat akun", reset="Atur ulang sandi", newpw="Sandi baru", account="Akun saya", send_reset="Kirim tautan", save_pw="Simpan",
   have_acct="Sudah punya akun? Masuk", no_acct="Baru? Gabung gratis", forgot="Lupa sandi", back="Kembali", google="Lanjut dengan Google", name="Nama atau organisasi", email="Email", pw="Sandi (min. 8 karakter)", age="Usia",
   age_opts=[["adult","19 tahun ke atas"],["teen","14 to under 19"],["u14","Di bawah 14"]], terms='Saya setuju dengan <a href="/id/legal/terms/" target="_blank">Ketentuan</a> dan <a href="/id/legal/privacy/" target="_blank">Privasi</a> (wajib)',
   need_terms="Harap setujui Ketentuan.", pw_short="Minimal 8 karakter.", check_mail="Email konfirmasi telah dikirim.", welcome="Selamat datang, Anda sudah masuk.", bad_login="Email atau sandi salah.", not_enabled="Login sedang dipelihara. Kontak: 73036396@naver.com")

# short top menu: (anchor/path, label)
NAV = {
 "ko": [('#map', '나라 찾기'), ('mdb/', '입찰·사업'), ('conflict/', '세계 상황'), ('ready/', '재난 대비'), ('solutions/', '진출 지원'), ('pricing/', '요금·회원')],
 "en": [('#map', 'Countries'), ('mdb/', 'Tenders'), ('conflict/', 'World watch'), ('ready/', 'Preparedness'), ('solutions/', 'Go global'), ('pricing/', 'Pricing')],
 "es": [('#map', 'Países'), ('mdb/', 'Licitaciones'), ('conflict/', 'Situación mundial'), ('ready/', 'Preparación'), ('solutions/', 'Expansión'), ('pricing/', 'Precios')],
 "fr": [('#map', 'Pays'), ('mdb/', "Appels d'offres"), ('conflict/', 'Veille mondiale'), ('ready/', 'Préparation'), ('solutions/', "S'implanter"), ('pricing/', 'Tarifs')],
 "ar": [('#map', 'الدول'), ('mdb/', 'المناقصات'), ('conflict/', 'الوضع العالمي'), ('ready/', 'الاستعداد'), ('solutions/', 'التوسع'), ('pricing/', 'الأسعار')],
 "vi": [('#map', 'Quốc gia'), ('mdb/', 'Đấu thầu'), ('conflict/', 'Tình hình thế giới'), ('ready/', 'Phòng bị'), ('solutions/', 'Mở rộng'), ('pricing/', 'Bảng giá')],
 "id": [('#map', 'Negara'), ('mdb/', 'Tender'), ('conflict/', 'Situasi dunia'), ('ready/', 'Kesiapsiagaan'), ('solutions/', 'Ekspansi'), ('pricing/', 'Harga')],
}
MENU = {"ko":"메뉴","en":"Menu","es":"Menú","fr":"Menu","ar":"القائمة","vi":"Menu","id":"Menu"}
PREP_T = {  # prep-bar chip names for languages without full content
 "es": {"base":"Kit básico 72 h","war":"Guerra","famine":"Hambruna","pandemic":"Pandemia","econ":"Crisis económica","blackout":"Apagón","nature":"Desastres naturales"},
 "fr": {"base":"Kit de base 72 h","war":"Guerre","famine":"Famine","pandemic":"Pandémie","econ":"Crise économique","blackout":"Panne générale","nature":"Catastrophes naturelles"},
 "ar": {"base":"حقيبة 72 ساعة","war":"الحرب","famine":"المجاعة","pandemic":"الأوبئة","econ":"الأزمة الاقتصادية","blackout":"انقطاع الكهرباء","nature":"الكوارث الطبيعية"},
 "vi": {"base":"Bộ dụng cụ 72 giờ","war":"Chiến tranh","famine":"Nạn đói","pandemic":"Đại dịch","econ":"Khủng hoảng kinh tế","blackout":"Mất điện","nature":"Thiên tai"},
 "id": {"base":"Kit dasar 72 jam","war":"Perang","famine":"Kelaparan","pandemic":"Pandemi","econ":"Krisis ekonomi","blackout":"Pemadaman","nature":"Bencana alam"},
}
LANG_SHORT = {"ko":"KO","en":"EN","es":"ES","fr":"FR","ar":"AR","vi":"VI","id":"ID"}

# WMM Membership — public price list incl. low-cost youth / student / university tiers (proposal 2026-10-31)

# WMM Membership public price list (council decision 2026-10-31: no student tier; everyone 14+ free; top tier by quote until track record)
PLANS = {
 "ko": [("FREE 누구나","무료","만 14세 이상 누구나: 193개국 지도·요약·분쟁 상황판·프로젝트 랩 열람. 학생·청년·청소년 모두 무료 (만 19세 미만은 열람·학습 전용)"),
        ("분석 회원","월 19,800원","유망 사업 이유·대상 바이어 전체, 관심 나라 10곳 월요일 알림"),
        ("국가 진출 브리프","30만 원부터","한 나라, 고객 업종 맞춤, 사람 검수"),
        ("프로젝트 파트너십","첫 상담 무료","파트너 연결·컨소시엄·현지 등록 동행, 비용은 상담 후 결정"),
        ("UNI 대학·기관","연 990,000원부터","교직원·학생 계정 일괄(기관 코드), 컨소시엄 정식 참여, 강의 자료"),
        ("EXECUTE","개별 견적","리포트 납품·제안서·온라인 원격 검토·CONNECT 연결 (사람이 검수해 납품)")],
 "en": [("FREE","Free","Anyone 14+: map, summaries, conflict watch, Project Lab. Students and youth included (under-19s: reading and learning only)"),
        ("Analysis member","₩19,800/mo","All why-now and target buyers, Monday alerts for 10 countries"),
        ("Market-entry brief","from ₩300,000","One country, tailored to your sector, human-reviewed"),
        ("Project partnership","free first consultation","Partner introductions, consortium and local registration; fees agreed after the consultation"),
        ("UNI","from ₩990,000/yr","Institution code for staff & student seats, consortium membership"),
        ("EXECUTE","By quote","Human-reviewed reports, proposals, online remote review, CONNECT introductions")],
}
for _l in ("es","fr","ar","vi","id"): PLANS[_l] = PLANS["en"]
PLAN_NOTE = {"ko":"VAT 별도 · 학생 할인 등급은 없고 무료가 누구에게나 같습니다 · 언제든 해지 가능 (환불 정책 참고)","en":"VAT excluded · no student tier: FREE is the same for everyone · cancel any time (see refund policy)"}
