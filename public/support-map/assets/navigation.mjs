// Restrict post-login navigation to local WMM destinations; never accept external URLs.
export function safeReturnPath(raw, origin) {
 if(!raw || /[\\\x00-\x20]/.test(raw) || !raw.startsWith('/') || raw.startsWith('//'))return null;
 try { const u=new URL(raw,origin);if(u.origin!==origin || !['/','/start/','/membership/','/support-map/'].includes(u.pathname))return null;
 u.searchParams.delete('returnTo');u.searchParams.delete('embed');return u.pathname+u.search+u.hash;
 }catch{return null;}
}
