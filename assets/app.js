const state = {
  events: [],
  filtered: [],
};

const locationFilter = document.getElementById("locationFilter");
const startDateInput = document.getElementById("startDate");
const endDateInput = document.getElementById("endDate");
const openOnlyInput = document.getElementById("openOnly");
const resetButton = document.getElementById("resetFilters");
const eventsContainer = document.getElementById("events");
const summaryText = document.getElementById("summaryText");
const template = document.getElementById("eventCardTemplate");

const formatDate = (value) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-Hant", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
};

const updateSummary = () => {
  const total = state.events.length;
  const visible = state.filtered.length;
  const openCount = state.filtered.filter((event) => event.registrationOpen).length;
  summaryText.textContent = `共有 ${total} 場賽事，符合條件 ${visible} 場，其中可報名 ${openCount} 場。`;
};

const renderEvents = () => {
  eventsContainer.innerHTML = "";
  if (state.filtered.length === 0) {
    eventsContainer.innerHTML =
      '<p class="summary__note">目前沒有符合條件的賽事，請調整篩選條件。</p>';
    updateSummary();
    return;
  }

  const fragment = document.createDocumentFragment();
  state.filtered.forEach((event) => {
    const card = template.content.cloneNode(true);
    const title = card.querySelector(".card__title");
    const status = card.querySelector(".card__status");
    const meta = card.querySelector(".card__meta");
    const location = card.querySelector(".card__location");
    const deadline = card.querySelector(".card__deadline");
    const link = card.querySelector("a");
    const source = card.querySelector(".card__source");

    title.textContent = event.name;
    status.textContent = event.registrationOpen ? "可報名" : "已截止";
    status.classList.add(
      event.registrationOpen ? "card__status--open" : "card__status--closed"
    );
    meta.textContent = `比賽日期：${formatDate(event.raceDate)}`;
    location.textContent = `地點：${event.location}`;
    deadline.textContent = `報名截止：${formatDate(event.registrationDeadline)}`;
    link.href = event.website;
    source.textContent = `來源：${event.source}`;

    fragment.appendChild(card);
  });

  eventsContainer.appendChild(fragment);
  updateSummary();
};

const applyFilters = () => {
  const locationValue = locationFilter.value;
  const startDate = startDateInput.value ? new Date(startDateInput.value) : null;
  const endDate = endDateInput.value ? new Date(endDateInput.value) : null;
  const openOnly = openOnlyInput.checked;

  state.filtered = state.events.filter((event) => {
    if (locationValue !== "all" && event.location !== locationValue) {
      return false;
    }

    const raceDate = new Date(event.raceDate);
    if (startDate && raceDate < startDate) {
      return false;
    }

    if (endDate) {
      const end = new Date(endDate);
      end.setHours(23, 59, 59, 999);
      if (raceDate > end) {
        return false;
      }
    }

    if (openOnly && !event.registrationOpen) {
      return false;
    }

    return true;
  });

  renderEvents();
};

const populateLocations = () => {
  const locations = Array.from(new Set(state.events.map((event) => event.location)));
  locations.sort();
  locations.forEach((location) => {
    const option = document.createElement("option");
    option.value = location;
    option.textContent = location;
    locationFilter.appendChild(option);
  });
};

const resetFilters = () => {
  locationFilter.value = "all";
  startDateInput.value = "";
  endDateInput.value = "";
  openOnlyInput.checked = false;
  applyFilters();
};

const loadEvents = async () => {
  try {
    const response = await fetch("data/events.json");
    const data = await response.json();
    state.events = data.events;
    state.filtered = [...state.events];
    populateLocations();
    applyFilters();
  } catch (error) {
    summaryText.textContent = "無法載入賽事資料，請稍後再試。";
  }
};

locationFilter.addEventListener("change", applyFilters);
startDateInput.addEventListener("change", applyFilters);
endDateInput.addEventListener("change", applyFilters);
openOnlyInput.addEventListener("change", applyFilters);
resetButton.addEventListener("click", resetFilters);

loadEvents();
