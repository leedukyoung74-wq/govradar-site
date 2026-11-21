const emailOrProvider = /(?:^|&)(?:access_token|error_description|confirmation_token|recovery_token|invite_token)=/;
const fragment = location.hash.slice(1);
if (emailOrProvider.test(fragment)) {
  let language = document.documentElement.lang;
  try { language = sessionStorage.getItem('govradar.oauth.language') || language; } catch { /* continue with page language */ }
  if (!/^(ko|en|es|fr|ar|vi|id)$/.test(language)) language = 'ko';
  location.replace(`/access/${language}/${location.hash}`);
} else {
  location.replace(document.getElementById('intro').href);
}
