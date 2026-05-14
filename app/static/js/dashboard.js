document.addEventListener("DOMContentLoaded", () => {

    // Получение CSRF токена
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : null;

    // Инициализация GridStack (Drag & Drop, Resize)
    const container = document.querySelector('.grid-stack');
    let grid;
    if (container && typeof GridStack !== 'undefined') {
        const isLocked = container.getAttribute('data-locked') === 'true';
        grid = GridStack.init({
            cellHeight: 100,
            margin: 10,
            disableOneColumnMode: false,
            float: true,
            staticGrid: isLocked,
            handle: '.drag-handle' // Перетаскивать можно только за шапку
        });

        // Событие изменения позиций и размеров
        grid.on('change', function (event, items) {
            if (!items) return;
            const newLayout = [];
            grid.engine.nodes.forEach(node => {
                const el = node.el;
                const widgetCard = el.querySelector('.widget-card');
                if (!widgetCard) return;
                const widgetType = widgetCard.getAttribute('data-widget');
                newLayout.push({
                    widget_type: widgetType,
                    x: node.x,
                    y: node.y,
                    w: node.w,
                    h: node.h
                });
            });

            // Отправляем новый порядок на бэкенд
            if (csrfToken && newLayout.length > 0) {
                fetch('/api/v1/widgets/save-grid', {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ items: newLayout })
                }).catch(err => console.error('Ошибка сохранения сетки:', err));
            }
        });
    }

    const lockBtn = document.getElementById('lockGridBtn');
    if (lockBtn && grid) {
        lockBtn.addEventListener('click', () => {
            const isCurrentlyLocked = container.getAttribute('data-locked') === 'true';
            const willBeLocked = !isCurrentlyLocked;

            fetch('/api/v1/user/lock-grid', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ is_grid_locked: willBeLocked })
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        container.setAttribute('data-locked', data.is_grid_locked);
                        grid.setStatic(data.is_grid_locked);

                        if (data.is_grid_locked) {
                            lockBtn.className = 'btn btn-warning btn-sm shadow-sm me-2';
                            lockBtn.innerHTML = '<i class="fas fa-lock"></i> <span>Сетка зафиксирована</span>';
                        } else {
                            lockBtn.className = 'btn btn-light btn-sm shadow-sm me-2';
                            lockBtn.innerHTML = '<i class="fas fa-unlock"></i> <span>Зафиксировать сетку</span>';
                        }
                    }
                });
        });
    }

    // 1. Логика загрузки виджетов на главном экране (Fetch API)
    const widgetCards = document.querySelectorAll('.widget-card');

    widgetCards.forEach(card => {
        const type = card.getAttribute('data-widget');
        const contentDiv = card.querySelector('.widget-content');

        // Маппинг URL'ов
        let url = '';
        if (type === 'currency') url = '/api/v1/widgets/currency';
        if (type === 'it_news') url = '/api/v1/widgets/it-news';
        if (type === 'politics') url = '/api/v1/widgets/politics';
        if (type === 'ai_models') url = '/api/v1/widgets/ai-models';
        if (type === 'ai_summary') url = '/api/v1/widgets/ai-summary';
        if (type === 'weather') url = '/api/v1/widgets/weather';

        if (url) {
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    renderWidget(type, data, contentDiv);
                })
                .catch(error => {
                    const errorMsg = error.message ? error.message : String(error);
                    const el = contentDiv.querySelector('.loading-indicator');
                    if (el) {
                        el.innerHTML = `<div class="text-danger small">Ошибка загрузки: ${errorMsg}</div>`;
                    }
                });
        } else if (type === 'analog_clock') {
            initAnalogClock();
        } else if (type === 'calendar') {
            initCalendar();
        } else if (type === 'bookmarks') {
            initBookmarks(contentDiv);
        }
    });

    // Хранилище для инстансов Chart.js чтобы уничтожать старые при обновлении
    window.widgetCharts = window.widgetCharts || {};

    function renderWidget(type, data, container) {
        if (data.error) {
            const el = container.querySelector('.loading-indicator');
            if (el) el.innerHTML = `<div class="text-danger small">Ошибка: ${data.error}</div>`;
            return;
        }

        let html = '';

        if (type === 'ai_summary') {
            const parsedSummary = typeof marked !== 'undefined' ? marked.parse(data.summary) : data.summary;
            html = `
                <div class="text-muted small p-1 ai-summary-content" style="line-height: 1.4;">${parsedSummary}</div>
                <div class="text-end mt-2"><a href="https://artificialanalysis.ai/models" target="_blank" class="small text-decoration-none">Источник ИИ: Artificial Analysis</a></div>
            `;
        }
        else if (type === 'currency') {
            html = `
                <div class="d-flex justify-content-around mt-2">
                    <div class="text-center">
                        <span class="text-muted d-block small">USD</span>
                        <span class="currency-value">${data.USD.current} ₽</span>
                        <small class="${data.USD.current >= data.USD.previous ? 'text-danger' : 'text-success'}">
                            ${data.USD.current >= data.USD.previous ? '▲' : '▼'} ${Math.abs(data.USD.current - data.USD.previous).toFixed(2)}
                        </small>
                    </div>
                    <div class="text-center">
                        <span class="text-muted d-block small">EUR</span>
                        <span class="currency-value">${data.EUR.current} ₽</span>
                        <small class="${data.EUR.current >= data.EUR.previous ? 'text-danger' : 'text-success'}">
                            ${data.EUR.current >= data.EUR.previous ? '▲' : '▼'} ${Math.abs(data.EUR.current - data.EUR.previous).toFixed(2)}
                        </small>
                    </div>
                    <div class="text-center">
                        <span class="text-muted d-block small">CNY</span>
                        <span class="currency-value">${data.CNY.current} ₽</span>
                        <small class="${data.CNY.current >= data.CNY.previous ? 'text-danger' : 'text-success'}">
                            ${data.CNY.current >= data.CNY.previous ? '▲' : '▼'} ${Math.abs(data.CNY.current - data.CNY.previous).toFixed(2)}
                        </small>
                    </div>
                </div>
                <div class="mt-3 px-2" style="height: 100px; width: 100%;">
                    <canvas id="currencyChart"></canvas>
                </div>
                <div class="text-end text-muted mt-2" style="font-size: 0.7rem;">Обновлено: ${new Date(data.date).toLocaleDateString()}</div>
            `;
        }
        else if (type === 'crypto') {
            html = `
                <div class="d-flex flex-wrap justify-content-around mt-2">
                    <div class="text-center m-1">
                        <span class="text-muted d-block small">BTC</span>
                        <span class="currency-value fw-bold fs-5">$${data.BTC.price}</span>
                        <span class="small d-block ${data.BTC.change >= 0 ? 'text-success' : 'text-danger'}">${data.BTC.change}%</span>
                    </div>
                    <div class="text-center m-1">
                        <span class="text-muted d-block small">ETH</span>
                        <span class="currency-value fw-bold fs-5">$${data.ETH.price}</span>
                        <span class="small d-block ${data.ETH.change >= 0 ? 'text-success' : 'text-danger'}">${data.ETH.change}%</span>
                    </div>
                    <div class="text-center m-1">
                        <span class="text-muted d-block small">TON</span>
                        <span class="currency-value fw-bold fs-5">$${data.TON.price}</span>
                        <span class="small d-block ${data.TON.change >= 0 ? 'text-success' : 'text-danger'}">${data.TON.change}%</span>
                    </div>
                </div>
                <div class="mt-3 px-2" style="height: 120px; width: 100%;">
                    <canvas id="cryptoChart"></canvas>
                </div>
            `;
        }
        else if (type === 'it_news' || type === 'politics' || type === 'ai_models') {
            html = '<div class="news-list px-1">';
            data.forEach(item => {
                if (item.error) {
                    html += `<div class="text-danger small">${item.error}</div>`;
                } else {
                    html += `
                        <div class="news-item">
                            <a href="${item.link}" target="_blank" rel="noopener noreferrer">${item.title}</a>
                        </div>
                    `;
                }
            });
            html += '</div>';
        }
        else if (type === 'weather') {
            html = `
                <div class="text-center px-1">
                    <h6 class="fw-bold mb-1">${data.city}</h6>
                    <div class="fs-2 my-1">${data.description.split(' ')[0]}</div>
                    <div class="text-muted small mb-1">${data.description.substring(data.description.indexOf(' ') + 1)}</div>
                    <div class="d-flex justify-content-around">
                        <div class="small">
                            <span class="text-muted d-block">Мин</span>
                            <span>${data.temp_min}°C</span>
                        </div>
                        <div class="small">
                            <span class="text-muted d-block">Осадки</span>
                            <span>${data.precipitation_probability}%</span>
                        </div>
                        <div class="small">
                            <span class="text-muted d-block">Макс</span>
                            <span class="text-danger">${data.temp_max}°C</span>
                        </div>
                    </div>
                    <div class="mt-3" style="height: 100px; width: 100%;">
                        <canvas id="weatherChart"></canvas>
                    </div>
                </div>
            `;
        }

        // Заменяем loading indicator на контент
        const el = container.querySelector('.loading-indicator');
        if (el) {
            el.outerHTML = html;
        } else {
            container.innerHTML += html;
        }

        // Инициализация графиков после вставки в DOM
        setTimeout(() => {
            const isDark = document.body.getAttribute('data-theme') === 'dark';
            const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
            const textColor = isDark ? '#a0a0a0' : '#6c757d';

            if (type === 'currency' && document.getElementById('currencyChart')) {
                const currKeys = Object.keys(data).filter(k => k !== 'date');
                if (window.widgetCharts['currency']) window.widgetCharts['currency'].destroy();
                const ctx = document.getElementById('currencyChart').getContext('2d');
                window.widgetCharts['currency'] = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: currKeys,
                        datasets: [
                            { label: 'Сегодня', data: currKeys.map(k => data[k].current), backgroundColor: '#4A90E2', borderRadius: 4 },
                            { label: 'Вчера', data: currKeys.map(k => data[k].previous), backgroundColor: isDark ? '#444' : '#e0e0e0', borderRadius: 4 }
                        ]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { x: { grid: { display: false }, ticks: { color: textColor } }, y: { display: false } }
                    }
                });
            }
            if (type === 'crypto' && document.getElementById('cryptoChart')) {
                const cryptoKeys = Object.keys(data);
                if (window.widgetCharts['crypto']) window.widgetCharts['crypto'].destroy();
                const ctx = document.getElementById('cryptoChart').getContext('2d');
                window.widgetCharts['crypto'] = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: cryptoKeys,
                        datasets: [{
                            label: 'Изменение 24ч (%)',
                            data: cryptoKeys.map(k => data[k].change),
                            backgroundColor: (ctx) => ctx.raw >= 0 ? '#198754' : '#dc3545',
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { x: { grid: { display: false }, ticks: { color: textColor } }, y: { grid: { color: gridColor }, ticks: { color: textColor } } }
                    }
                });
            }
            if (type === 'weather' && document.getElementById('weatherChart') && data.hourly_times) {
                if (window.widgetCharts['weather']) window.widgetCharts['weather'].destroy();
                const ctx = document.getElementById('weatherChart').getContext('2d');
                window.widgetCharts['weather'] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.hourly_times,
                        datasets: [{
                            label: 'Температура (°C)',
                            data: data.hourly_temps,
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 2
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { x: { grid: { display: false }, ticks: { color: textColor, maxTicksLimit: 6 } }, y: { grid: { color: gridColor }, ticks: { color: textColor } } }
                    }
                });
            }
        }, 100);
    }

    function initAnalogClock() {
        const hourHand = document.getElementById('hourHand');
        const minuteHand = document.getElementById('minuteHand');
        const secondHand = document.getElementById('secondHand');
        const digitalClock = document.getElementById('digitalClock');

        if (!hourHand || !minuteHand || !secondHand) return;

        function setClock() {
            const now = new Date();
            const seconds = now.getSeconds();
            const minutes = now.getMinutes();
            const hours = now.getHours();

            const secondsDegrees = ((seconds / 60) * 360);
            const minutesDegrees = ((minutes / 60) * 360) + ((seconds / 60) * 6);
            const hoursDegrees = ((hours / 12) * 360) + ((minutes / 60) * 30);

            secondHand.style.transform = `rotate(${secondsDegrees}deg)`;
            minuteHand.style.transform = `rotate(${minutesDegrees}deg)`;
            hourHand.style.transform = `rotate(${hoursDegrees}deg)`;

            if (digitalClock) {
                const h = String(hours).padStart(2, '0');
                const m = String(minutes).padStart(2, '0');
                const s = String(seconds).padStart(2, '0');
                digitalClock.textContent = `${h}:${m}:${s}`;
            }
        }

        setInterval(setClock, 1000);
        setClock();
    }

    function initCalendar() {
        const gridEl = document.getElementById('calGrid');
        const monthYearEl = document.getElementById('calMonthYear');
        const prevBtn = document.getElementById('prevMonthBtn');
        const nextBtn = document.getElementById('nextMonthBtn');

        if (!gridEl || !monthYearEl) return;

        const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
        const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

        let currentDate = new Date();
        let displayMonth = currentDate.getMonth();
        let displayYear = currentDate.getFullYear();

        function renderCalendar(year, month) {
            gridEl.innerHTML = '';
            monthYearEl.textContent = `${months[month]} ${year}`;

            const firstDay = new Date(year, month, 1).getDay();
            const daysInMonth = new Date(year, month + 1, 0).getDate();

            let startOffset = firstDay - 1;
            if (startOffset === -1) startOffset = 6;

            days.forEach(day => {
                const dEl = document.createElement('div');
                dEl.className = 'cal-cell cal-header text-muted small fw-bold text-center';
                dEl.textContent = day;
                gridEl.appendChild(dEl);
            });

            for (let i = 0; i < startOffset; i++) {
                const empty = document.createElement('div');
                empty.className = 'cal-cell empty';
                gridEl.appendChild(empty);
            }

            const today = new Date();
            for (let i = 1; i <= daysInMonth; i++) {
                const dEl = document.createElement('div');
                dEl.className = 'cal-cell cal-day text-center';
                if (year === today.getFullYear() && month === today.getMonth() && i === today.getDate()) {
                    dEl.classList.add('bg-primary', 'text-white', 'rounded-circle', 'fw-bold');
                }
                dEl.textContent = i;
                gridEl.appendChild(dEl);
            }
        }

        renderCalendar(displayYear, displayMonth);

        if (prevBtn) prevBtn.onclick = (e) => {
            e.stopPropagation();
            displayMonth--;
            if (displayMonth < 0) { displayMonth = 11; displayYear--; }
            renderCalendar(displayYear, displayMonth);
        };

        if (nextBtn) nextBtn.onclick = (e) => {
            e.stopPropagation();
            displayMonth++;
            if (displayMonth > 11) { displayMonth = 0; displayYear++; }
            renderCalendar(displayYear, displayMonth);
        };
    }

    function initBookmarks(container) {
        const form = container.querySelector('#add-bookmark-form');
        if (!form) return;
        form.onsubmit = (e) => {
            e.preventDefault();
            const titleInput = form.querySelector('#bm-title');
            const urlInput = form.querySelector('#bm-url');
            fetch('/api/v1/bookmarks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ title: titleInput.value, url: urlInput.value, icon: 'fa-star' })
            }).then(res => res.json()).then(data => {
                if (data.success) window.location.reload();
                else alert('Ошибка: ' + data.error);
            });
        };
    }

    const toggles = document.querySelectorAll('.widget-toggle');
    toggles.forEach(toggle => {
        toggle.onchange = (e) => {
            const widgetType = e.target.getAttribute('data-widget-type');
            const isActive = e.target.checked;
            fetch(`/api/v1/widgets/${widgetType}/toggle`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ is_active: isActive })
            }).then(res => res.json()).then(data => {
                if (data.error) { alert(`Ошибка: ${data.error}`); e.target.checked = !isActive; }
            });
        };
    });
});
