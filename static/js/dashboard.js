// Toggle More Stats
function toggleStats() {
    const moreStats = document.getElementById('more-stats');
    const seeMoreBtn = document.getElementById('seeMoreBtn');
    
    if (moreStats.style.display === 'none' || moreStats.style.display === '') {
        moreStats.style.display = 'block';
        seeMoreBtn.textContent = 'See Less';
    } else {
        moreStats.style.display = 'none';
        seeMoreBtn.textContent = 'See More';
    }
}

// Calendar state
let currentDate = new Date();
let selectedDate = null;
let events = {}; // Store events by date string like "2025-10-15"

function renderCalendar() {
    const monthYear = document.getElementById('calendarMonthYear');
    const grid = document.getElementById('calendarGrid');

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    monthYear.textContent = `${currentDate.toLocaleString('default', { month: 'long' })} ${year}`;

    grid.innerHTML = '';

    // Days of week headers
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    days.forEach(day => {
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day';
        dayEl.textContent = day;
        grid.appendChild(dayEl);
    });

    // Days in month
    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();

    // empty placeholders
    for (let i = 0; i < firstDay; i++) {
        const emptyEl = document.createElement('div');
        emptyEl.className = 'calendar-cell empty';
        grid.appendChild(emptyEl);
    }

    for (let date = 1; date <= lastDate; date++) {
        const dateEl = document.createElement('div');
        dateEl.className = 'calendar-cell';
        const dateStr = `${year}-${month + 1}-${date}`; // same format used in events map
        dateEl.dataset.date = dateStr;
        dateEl.textContent = date;
        if (events[dateStr]) {
            const evt = document.createElement('div');
            evt.className = 'calendar-event';
            evt.textContent = events[dateStr];
            dateEl.appendChild(evt);
        }
        dateEl.addEventListener('click', () => selectDate(dateEl));
        grid.appendChild(dateEl);
    }
}

function selectDate(el) {
    if (!el) return;
    if (selectedDate) {
        selectedDate.classList.remove('selected');
    }
    selectedDate = el;
    el.classList.add('selected');
}

// Initialize once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Chart.js Graph
    const graphCanvas = document.getElementById('purokBarGraph');
    if (graphCanvas) {
        const ctx = graphCanvas.getContext('2d');
        const labelsEl = document.getElementById('purokLabelsData');
        const dataEl = document.getElementById('purokPopulationData');
        try {
            const labels = labelsEl ? JSON.parse(labelsEl.textContent || '[]') : [];
            const data = dataEl ? JSON.parse(dataEl.textContent || '[]') : [];
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Population',
                        data: data,
                        backgroundColor: 'rgba(0, 123, 255, 0.5)',
                        borderColor: 'rgba(0, 123, 255, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Failed to parse purok chart data', e);
        }
    }

    // Wire calendar controls (safe now that DOM is loaded)
    const prevBtn = document.getElementById('prevMonthBtn');
    const nextBtn = document.getElementById('nextMonthBtn');
    const addEventBtn = document.getElementById('addEventBtn');

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            currentDate.setMonth(currentDate.getMonth() - 1);
            renderCalendar();
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            currentDate.setMonth(currentDate.getMonth() + 1);
            renderCalendar();
        });
    }
    if (addEventBtn) {
        addEventBtn.addEventListener('click', () => {
            const eventInput = document.getElementById('eventInput');
            const event = eventInput ? eventInput.value.trim() : '';
            if (event && selectedDate && selectedDate.dataset.date) {
                events[selectedDate.dataset.date] = event;
                if (eventInput) eventInput.value = '';
                renderCalendar();
            } else {
                // Optionally notify user to select a date first
                console.warn('No date selected or empty event.');
            }
        });
    }

    // Initialize calendar on page load
    const moreStats = document.getElementById('more-stats');
    if (moreStats) {
        moreStats.style.display = 'none'; // hidden by default
    }

    renderCalendar(); // Initialize calendar
});