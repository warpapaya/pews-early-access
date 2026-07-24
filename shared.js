// Nav scroll effect
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 10);
});

// Mobile menu
const toggle = document.getElementById('mobileToggle');
const links = document.getElementById('navLinks');
toggle.addEventListener('click', () => {
  toggle.classList.toggle('active');
  links.classList.toggle('open');
});
links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
  toggle.classList.remove('active');
  links.classList.remove('open');
}));

// Fade-in on scroll
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); }});
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));

// Mailchimp subscribe — hidden iframe submit (no popup, no redirect)
function submitForm(e, prefix) {
  e.preventDefault();
  var form = e.target;
  var msgEl = document.getElementById(prefix + 'Msg');
  var email = form.querySelector('input[name="EMAIL"]').value;
  var fname = form.querySelector('input[name="FNAME"]');
  if (!email) return false;

  msgEl.textContent = 'Signing you up...';
  msgEl.className = (prefix === 'hero' ? 'hero-form-msg' : 'cta-form-msg');

  // Create hidden iframe as form target
  var iframeName = 'mc_iframe_' + Date.now();
  var iframe = document.createElement('iframe');
  iframe.name = iframeName;
  iframe.style.display = 'none';
  document.body.appendChild(iframe);

  // Create and submit a real form into the hidden iframe
  var mcForm = document.createElement('form');
  mcForm.method = 'POST';
  mcForm.action = 'https://warpapaya.us4.list-manage.com/subscribe/post';
  mcForm.target = iframeName;
  mcForm.style.display = 'none';

  var fields = {
    'u': '7f239d430d3572b980795a2ab',
    'id': 'e665c7e29c',
    'EMAIL': email,
    'group[bdb8993f60][47f5ba21c0]': '1'
  };
  if (fname && fname.value) fields['FNAME'] = fname.value;
  var church = form.querySelector('input[name="CHURCH"]');
  if (church && church.value) fields['CHURCH'] = church.value;
  var size = form.querySelector('select[name="SIZE"]');
  if (size && size.value) fields['SIZE'] = size.value;

  for (var k in fields) {
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = k;
    input.value = fields[k];
    mcForm.appendChild(input);
  }

  document.body.appendChild(mcForm);
  mcForm.submit();

  // Show success after brief delay (can't read iframe response cross-origin)
  setTimeout(function() {
    msgEl.textContent = '🎉 You\'re on the list! Check your email to confirm.';
    msgEl.className = (prefix === 'hero' ? 'hero-form-msg' : 'cta-form-msg') + ' success';
    form.reset();
    // Clean up
    mcForm.remove();
    setTimeout(function() { iframe.remove(); }, 5000);
  }, 1500);

  return false;
}

// FAQ accordion
document.querySelectorAll('.faq-question').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.parentElement;
    const answer = item.querySelector('.faq-answer');
    const isOpen = item.classList.contains('open');
    
    // Close all
    document.querySelectorAll('.faq-item.open').forEach(openItem => {
      openItem.classList.remove('open');
      openItem.querySelector('.faq-answer').style.maxHeight = '0';
    });
    
    if (!isOpen) {
      item.classList.add('open');
      answer.style.maxHeight = answer.scrollHeight + 'px';
    }
  });
});
