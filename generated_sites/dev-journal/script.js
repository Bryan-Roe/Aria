const seed=[
  {title:'Shipping safer CI workflows',date:'2026-04-11',excerpt:'How we hardened workflow reliability and observability.'},
  {title:'Aria gesture abilities update',date:'2026-04-10',excerpt:'Added clap, nod, bow, shrug, thumbs_up command support.'},
  {title:'Testing focused bugfixes',date:'2026-04-09',excerpt:'Run smaller suites first, then widen confidence checks.'}
];
const posts=document.getElementById('posts');
function render(list){
  posts.innerHTML=list.map(p=>`<article class="post"><h2>${p.title}</h2><p class="meta">${p.date}</p><p>${p.excerpt}</p></article>`).join('');
}
render(seed);
document.getElementById('search')?.addEventListener('input',e=>{
  const q=e.target.value.toLowerCase();
  render(seed.filter(p=>p.title.toLowerCase().includes(q)||p.excerpt.toLowerCase().includes(q)));
});
