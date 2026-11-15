import re
SKIP = {'AR','Español','Français','Tiếng Việt','Bahasa Indonesia','English','GOV RADAR','WORLD MAKING MEMBERS','Unsplash','한국어','العربية','EN','ES','FR','VI','ID','KO'}
def want(t):
    t = t.strip()
    if not re.search(r'[A-Za-z]{2,}', t) or re.search(r'[؀-ۿ가-힣]', t): return False
    if re.match(r'^(https?:|/|#|\.|data:|\(|translate)', t) or re.search(r'[{}]|prefers-reduced|button|\bevs\b', t): return False
    if t in SKIP: return False
    if re.fullmatch(r'[\w.@-]+\.(gov|com|org|be|ie|se|it|ua|nl|uk|fr|in|sg|au|ca|kr|jp|de)(\.[a-z]{2})?(/[\w./-]*)?', t): return False
    if re.fullmatch(r'[A-Z0-9 .·:/+-]{1,8}', t) and not re.search('[a-z]', t): return False
    return True
