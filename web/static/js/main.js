// DESAR Admin Panel JS

// Delete with confirmation
document.addEventListener('click', function(e) {
  const btn = e.target.closest('[data-delete-url]');
  if (!btn) return;
  const msg = btn.dataset.confirm || '¿Confirmar eliminación?';
  if (!confirm(msg)) return;
  fetch(btn.dataset.deleteUrl, {method:'DELETE'})
    .then(r => { if(r.ok) { btn.closest('tr')?.remove() || location.reload(); } else { alert('Error: ' + r.status); } })
    .catch(() => alert('Error de red'));
});

// Toggle (PUT) with confirmation
document.addEventListener('click', function(e) {
  const btn = e.target.closest('[data-toggle-url]');
  if (!btn) return;
  const msg = btn.dataset.confirm || '¿Confirmar cambio?';
  if (!confirm(msg)) return;
  fetch(btn.dataset.toggleUrl, {method:'PUT'})
    .then(r => { if(r.ok) location.reload(); else alert('Error: ' + r.status); })
    .catch(() => alert('Error de red'));
});

// Auto-set today's date on inputs named desde/hasta if empty
document.querySelectorAll('input[name="desde"], input[name="hasta"]').forEach(inp => {
  if (!inp.value) {
    const d = new Date();
    if (inp.name === 'desde') d.setDate(d.getDate() - 30);
    inp.value = d.toISOString().slice(0, 10);
  }
});
