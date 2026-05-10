function filterEvents(type) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');

  document.querySelectorAll('.event-card').forEach(card => {
    if (type === 'all' || card.dataset.type === type) {
      card.classList.remove('hidden');
    } else {
      card.classList.add('hidden');
    }
  });
}

async function acknowledgeAlert(alertId) {
  await fetch(`/alerts/${alertId}/acknowledge`, { method: 'POST' });
  location.reload();
}
