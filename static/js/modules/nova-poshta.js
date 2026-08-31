function debounce(fn, delay = 280) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function clearFieldError(input) {
  const field = input?.closest('.field');
  if (!field) return;
  field.classList.remove('field--invalid');
  field.querySelectorAll('.field__error').forEach((el) => el.remove());
}

function renderList(list, items, onPick) {
  list.innerHTML = '';
  if (!items.length) {
    list.hidden = true;
    return;
  }
  items.forEach((item) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'autocomplete__item';
    button.textContent = item.area ? `${item.name} (${item.area})` : item.name;
    button.addEventListener('click', () => {
      onPick(item);
      list.hidden = true;
    });
    list.appendChild(button);
  });
  list.hidden = false;
}

export function initNovaPoshta() {
  const root = document.querySelector('[data-np]');
  if (!root) return;

  const cityInput = root.querySelector('[data-np-city]');
  const cityRef = root.querySelector('[data-np-city-ref]');
  const cityList = root.querySelector('[data-np-city-list]');
  const branchInput = root.querySelector('[data-np-branch]');
  const branchRef = root.querySelector('[data-np-branch-ref]');
  const branchList = root.querySelector('[data-np-branch-list]');

  const urls = { cities: root.dataset.npCitiesUrl, branches: root.dataset.npBranchesUrl };

  const fetchJson = async (url) => {
    try {
      const response = await fetch(url, { credentials: 'same-origin' });
      if (!response.ok) return [];
      const data = await response.json();
      return data.results || [];
    } catch (error) {
      return [];
    }
  };

  const searchCities = debounce(async () => {
    const query = cityInput.value.trim();
    if (query.length < 2) {
      cityList.hidden = true;
      return;
    }
    const items = await fetchJson(`${urls.cities}?q=${encodeURIComponent(query)}`);
    renderList(cityList, items, (item) => {
      cityInput.value = item.name;
      cityRef.value = item.ref;
      clearFieldError(cityInput);
      branchInput.value = '';
      branchRef.value = '';
      branchInput.disabled = false;
      loadBranches(item.ref);
    });
  });

  const loadBranches = async (ref) => {
    const items = await fetchJson(`${urls.branches}?city_ref=${encodeURIComponent(ref)}`);
    branchInput.dataset.loaded = JSON.stringify(items);
  };

  const filterBranches = () => {
    const stored = branchInput.dataset.loaded;
    if (!stored) return;
    const needle = branchInput.value.trim().toLowerCase();
    const items = JSON.parse(stored).filter((item) => item.name.toLowerCase().includes(needle));
    renderList(branchList, items.slice(0, 40), (item) => {
      branchInput.value = item.name;
      branchRef.value = item.ref;
      clearFieldError(branchInput);
    });
  };

  cityInput.addEventListener('input', () => {
    cityRef.value = '';
    clearFieldError(cityInput);
    searchCities();
  });
  branchInput.addEventListener('input', () => {
    branchRef.value = '';
    clearFieldError(branchInput);
    filterBranches();
  });
  branchInput.addEventListener('focus', filterBranches);

  if (cityRef.value) {
    loadBranches(cityRef.value);
  }

  document.addEventListener('click', (event) => {
    if (!root.contains(event.target)) {
      cityList.hidden = true;
      branchList.hidden = true;
    }
  });
}
