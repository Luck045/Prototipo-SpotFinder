document.addEventListener('DOMContentLoaded', () => {
  const filterForm = document.getElementById('filterForm');
  const resultsDiv = document.getElementById('resultsList');
  const timeSlider = document.getElementById('slider-time-range');
  const timeMinDisplay = document.getElementById('timeMinDisplay');
  const timeMaxDisplay = document.getElementById('timeMaxDisplay');

  if (timeSlider) {
    const TIME_MIN = parseInt(timeSlider.getAttribute('data-time-min')) || 1900;
    const TIME_MAX = parseInt(timeSlider.getAttribute('data-time-max')) || 2023;
    const TIME_START_MIN = parseInt(timeSlider.getAttribute('data-time-start-min')) || TIME_MIN;
    const TIME_START_MAX = parseInt(timeSlider.getAttribute('data-time-start-max')) || TIME_MAX;

    noUiSlider.create(timeSlider, {
      start: [TIME_START_MIN, TIME_START_MAX],
      connect: true,
      range: { min: TIME_MIN, max: TIME_MAX },
      step: 1,
      tooltips: [true, true],
      format: { to: v => Math.round(v), from: v => Math.round(v) }
    });

    timeSlider.noUiSlider.on('update', values => {
      const [min, max] = values.map(v => Math.round(v));
      timeMinDisplay.textContent = min;
      timeMaxDisplay.textContent = max;
      document.getElementById('time_min').value = min;
      document.getElementById('time_max').value = max;
    });
  }

  async function searchByFilters() {
    const styles = Array.from(filterForm.querySelectorAll('input[name="style"]:checked')).map(el => el.value);
    const genders = Array.from(filterForm.querySelectorAll('input[name="singer_gender"]:checked')).map(el => el.value);
    const instruments = Array.from(filterForm.querySelectorAll('input[name="instruments"]:checked')).map(el => el.value);

    const params = new URLSearchParams();
    styles.forEach(s => params.append('style', s));
    genders.forEach(g => params.append('singer_gender', g));
    instruments.forEach(i => params.append('instruments', i));
    params.append('time_min', document.getElementById('time_min').value);
    params.append('time_max', document.getElementById('time_max').value);

    console.log(`Enviando parâmetros: ${params.toString()}`);
    resultsDiv.innerHTML = '<p>Carregando...</p>';

    try {
      const response = await fetch(`/filter_results?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });

      if (!response.ok) throw new Error('Erro ao buscar filtros');

      const html = await response.text();
      resultsDiv.innerHTML = html;
    } catch (error) {
      resultsDiv.innerHTML = '<p>Erro ao buscar resultados com filtros.</p>';
      console.error(error);
    }
  }

  if (filterForm) {
    filterForm.addEventListener('submit', e => {
      e.preventDefault();
      searchByFilters();
    });
  }
});
