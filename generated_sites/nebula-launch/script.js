document.getElementById('ctaBtn')?.addEventListener('click',()=>alert('Welcome to Nebula Launch 🚀'));
document.getElementById('contactForm')?.addEventListener('submit',(e)=>{
  e.preventDefault();
  const status=document.getElementById('formStatus');
  if(status) status.textContent='Thanks! We will notify you soon.';
});
