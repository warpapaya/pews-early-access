const dialog = document.querySelector('#action-dialog');
document.querySelector('[data-open-dialog]')?.addEventListener('click', () => dialog.showModal());
document.querySelector('[data-close-dialog]')?.addEventListener('click', () => dialog.close());
dialog?.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });

const search = document.querySelector('#person-search');
const results = document.querySelector('#people-results');
let timer;
search?.addEventListener('input', () => {
  clearTimeout(timer);
  results.replaceChildren();
  if (search.value.trim().length < 2) return;
  timer = setTimeout(async () => {
    try {
      const body = new URLSearchParams({ q: search.value.trim() });
      const response = await fetch('/api/people/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });
      if (!response.ok) throw new Error('unavailable');
      const payload = await response.json();
      for (const person of payload.data) {
        const button = document.createElement('button');
        button.type = 'button';
        button.role = 'option';
        button.textContent = person.label;
        button.addEventListener('click', () => {
          document.querySelector('#external-id').value = person.external_id;
          search.value = person.label;
          results.replaceChildren();
        });
        results.append(button);
      }
    } catch (_) {
      const note = document.createElement('p');
      note.textContent = 'Planning Center search is unavailable.';
      results.append(note);
    }
  }, 250);
});
