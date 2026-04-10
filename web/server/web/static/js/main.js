// DESAR Admin - main.js
// Utilidades generales del panel

// ── Confirmación de eliminación ───────────────────────────────
document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-confirm]');
  if (!el) return;
  if (!confirm(el.dataset.confirm || '¿Confirmar acción?')) {
    e.preventDefault();
    e.stopPropagation();
  }
});

// ── DELETE via fetch ──────────────────────────────────────────
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('[data-delete-url]');
  if (!btn) return;
  e.preventDefault();
  if (!confirm(btn.dataset.confirm || '¿Eliminar este registro?')) return;
  try {
    const r = await fetch(btn.dataset.deleteUrl, { method: 'DELETE' });
    if (r.ok) {
      const row = btn.closest('tr, .card, [data-row]');
      if (row) row.remove();
    } else {
      alert('Error al eliminar');
    }
  } catch(e) {
    alert('Error de red');
  }
});

// ── Toggle switch via fetch ───────────────────────────────────
document.addEventListener('change', async (e) => {
  const sw = e.target.closest('[data-toggle-url]');
  if (!sw) return;
  await fetch(sw.dataset.toggleUrl, { method: 'PUT' });
});

// ── Auto-cerrar alertas ───────────────────────────────────────
document.querySelectorAll('.alert').forEach(a => {
  setTimeout(() => a.style.opacity = '0', 4000);
  setTimeout(() => a.remove(), 4500);
});

// ── Formatear timestamps ──────────────────────────────────────
document.querySelectorAll('[data-ts]').forEach(el => {
  const d = new Date(el.dataset.ts);
  el.textContent = d.toLocaleString('es-MX');
});

// ── Solicitar permiso de notificaciones ──────────────────────
if ('Notification' in window && Notification.permission === 'default') {
  // No pedir inmediatamente, esperar interacción del usuario
  document.addEventListener('click', function once() {
    Notification.requestPermission();
    document.removeEventListener('click', once);
  }, { once: true });
}
