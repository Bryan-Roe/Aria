document.querySelectorAll('aside a').forEach(a=>a.addEventListener('click',()=>{
  document.querySelectorAll('aside a').forEach(x=>x.style.fontWeight='400');
  a.style.fontWeight='700';
}));
