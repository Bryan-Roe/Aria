// Aria shared navigation bar — injected into all docs sub-pages.
// Usage: <script src="../aria-nav.js"></script> (adjusts paths based on depth)
(function () {
  'use strict';

  // Detect depth: how many levels deep from docs/ root
  var path = location.pathname;
  var docsIdx = path.indexOf('/docs/');
  var prefix = '../';
  if (docsIdx !== -1) {
    var sub = path.substring(docsIdx + 6); // after /docs/
    var depth = (sub.match(/\//g) || []).length;
    if (sub.endsWith('/')) depth--;
    prefix = depth > 0 ? '../'.repeat(depth) : './';
  }
  // Fallback for local file or simple relative
  if (!prefix) prefix = '../';

  // Determine current section for active highlight
  var current = '';
  if (/\/aria\//.test(path)) current = 'aria';
  else if (/\/chat\//.test(path)) current = 'chat';
  else if (/\/dashboard\//.test(path)) current = 'dashboard';
  else if (/\/quantum\//.test(path)) current = 'quantum';
  else if (/\/store\//.test(path)) current = 'store';
  else if (/\/monetization\//.test(path)) current = 'monetization';
  else if (/documentation/.test(path)) current = 'docs';

  var links = [
    { label: 'Home', href: prefix, id: 'home' },
    { label: 'Docs', href: prefix + 'documentation.html', id: 'docs' },
    { label: 'Aria', href: prefix + 'aria/', id: 'aria' },
    { label: 'Chat', href: prefix + 'chat/', id: 'chat' },
    { label: 'Dashboard', href: prefix + 'dashboard/', id: 'dashboard' },
    { label: 'Quantum', href: prefix + 'quantum/', id: 'quantum' },
    { label: 'Store', href: prefix + 'store/', id: 'store' },
    { label: 'GitHub', href: 'https://github.com/Bryan-Roe/Aria', id: 'github', external: true },
  ];

  var navHTML = '<nav id="aria-nav" style="' +
    'position:sticky;top:0;z-index:10000;' +
    'backdrop-filter:blur(20px) saturate(1.8);' +
    '-webkit-backdrop-filter:blur(20px) saturate(1.8);' +
    'background:rgba(15,11,30,.8);' +
    'border-bottom:1px solid rgba(255,255,255,.06);' +
    'font-family:Segoe UI,system-ui,-apple-system,sans-serif;' +
    '">' +
    '<div style="display:flex;align-items:center;justify-content:space-between;max-width:1280px;margin:0 auto;padding:12px 20px;">' +
    '<a href="' + prefix + '" style="display:flex;align-items:center;gap:8px;text-decoration:none;color:#fff;font-weight:700;font-size:1.1em;">' +
    '\uD83D\uDC64 Aria</a>' +
    '<button id="aria-nav-toggle" onclick="document.getElementById(\'aria-nav-links\').classList.toggle(\'open\')" style="' +
    'display:none;background:none;border:1px solid rgba(255,255,255,.15);color:#fff;' +
    'padding:6px 10px;border-radius:6px;cursor:pointer;font-size:1em;">☰</button>' +
    '<div id="aria-nav-links" style="display:flex;gap:4px;flex-wrap:wrap;">';

  for (var i = 0; i < links.length; i++) {
    var l = links[i];
    var isActive = l.id === current;
    var activeStyle = isActive
      ? 'color:#fff;background:rgba(255,255,255,.1);'
      : 'color:rgba(255,255,255,.65);';
    navHTML += '<a href="' + l.href + '"' +
      (l.external ? ' target="_blank" rel="noopener"' : '') +
      ' style="' + activeStyle +
      'text-decoration:none;font-size:.85em;font-weight:500;' +
      'padding:5px 12px;border-radius:7px;transition:color .2s,background .2s;' +
      '">' + l.label + (l.external ? ' ↗' : '') + '</a>';
  }

  navHTML += '</div></div></nav>';

  // Inject responsive CSS
  var style = document.createElement('style');
  style.textContent =
    '@media(max-width:768px){' +
    '#aria-nav-toggle{display:block!important}' +
    '#aria-nav-links{display:none!important;position:absolute;top:100%;left:0;right:0;' +
    'background:rgba(15,11,30,.95);padding:12px 20px;flex-direction:column;gap:4px;' +
    'border-bottom:1px solid rgba(255,255,255,.06)}' +
    '#aria-nav-links.open{display:flex!important}' +
    '}';
  document.head.appendChild(style);

  // Insert at top of body
  var temp = document.createElement('div');
  temp.innerHTML = navHTML;
  var navEl = temp.firstChild;
  document.body.insertBefore(navEl, document.body.firstChild);

  // Remove old back-links that are now redundant
  var oldLinks = document.querySelectorAll('a.back-link, a[href="../"]');
  for (var j = 0; j < oldLinks.length; j++) {
    var el = oldLinks[j];
    var text = (el.textContent || '').trim();
    if (text === '← Back to Aria Home' || text === '\u2190 Back to Aria Home') {
      el.style.display = 'none';
    }
  }
})();
