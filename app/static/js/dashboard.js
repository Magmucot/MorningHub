document.addEventListener("DOMContentLoaded", () => {

    // Poluch CSRF tok
    const meta_csrf = document.querySelector('meta[name="csrf-token"]');
    const tok_csrf = meta_csrf ? meta_csrf.getAttribute('content') : null;

    // GridStack (Drag & Drop, Resize)
    const kon_setka = document.querySelector('.grid-stack');
    let setka;
    if (kon_setka && typeof GridStack !== 'undefined') {
        const is_lock = kon_setka.getAttribute('data-locked') === 'true';
        setka = GridStack.init({
            cellHeight: 70,
            margin: 8,
            disableOneColumnMode: false,
            float: true,
            staticGrid: is_lock,
            handle: '.drag-handle'
        });

        setka.on('change', function (ev, i_spis) {
            if (!i_spis) return;
            const nov_layaut = [];
            setka.engine.nodes.forEach(n => {
                const el = n.el;
                const wid_kart = el.querySelector('.widget-card');
                if (!wid_kart) return;
                const w_tip = wid_kart.getAttribute('data-widget');
                nov_layaut.push({
                    widget_type: w_tip,
                    x: n.x,
                    y: n.y,
                    w: n.w,
                    h: n.h
                });
            });

            if (tok_csrf && nov_layaut.length > 0) {
                fetch('/api/v1/widgets/save-grid', {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': tok_csrf
                    },
                    body: JSON.stringify({ items: nov_layaut })
                }).catch(err => console.error('Oshibka sohran setki:', err));
            }
        });
    }

    const kn_lock = document.getElementById('lockGridBtn');
    if (kn_lock && setka) {
        kn_lock.addEventListener('click', () => {
            const is_tek_lock = kon_setka.getAttribute('data-locked') === 'true';
            const bud_lock = !is_tek_lock;

            fetch('/api/v1/user/lock-grid', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': tok_csrf
                },
                body: JSON.stringify({ is_grid_locked: bud_lock })
            })
                .then(r => r.json())
                .then(d => {
                    if (d.success) {
                        kon_setka.setAttribute('data-locked', d.is_grid_locked);
                        setka.setStatic(d.is_grid_locked);

                        if (d.is_grid_locked) {
                            kn_lock.className = 'btn btn-warning btn-sm shadow-sm me-2';
                            kn_lock.innerHTML = '<i class="fas fa-lock"></i> <span>Сетка зафиксирована</span>';
                        } else {
                            kn_lock.className = 'btn btn-light btn-sm shadow-sm me-2';
                            kn_lock.innerHTML = '<i class="fas fa-unlock"></i> <span>Зафиксировать сетку</span>';
                        }
                    }
                });
        });
    }

    const wid_kart_spis = document.querySelectorAll('.widget-card');

    wid_kart_spis.forEach(k => {
        const tip = k.getAttribute('data-widget');
        const div_kon = k.querySelector('.widget-content');

        let u = '';
        if (tip === 'currency') u = '/api/v1/widgets/currency';
        if (tip === 'it_news') u = '/api/v1/widgets/it-news';
        if (tip === 'game_news') u = '/api/v1/widgets/game-news';
        if (tip === 'politics') u = '/api/v1/widgets/politics';
        if (tip === 'ai_models') u = '/api/v1/widgets/ai-models';
        if (tip === 'ai_summary') u = '/api/v1/widgets/ai-summary';
        if (tip === 'weather') u = '/api/v1/widgets/weather';
        if (tip === 'crypto') u = '/api/v1/widgets/crypto';

        if (u) {
            fetch(u)
                .then(r => r.json())
                .then(d => {
                    risuy_wid(tip, d, div_kon);
                })
                .catch(err => {
                    const err_m = err.message ? err.message : String(err);
                    const el = div_kon.querySelector('.loading-indicator');
                    if (el) {
                        el.innerHTML = `<div class="text-danger small">Ошибка загрузки: ${err_m}</div>`;
                    }
                });
        } else if (tip === 'analog_clock') {
            init_chas(div_kon);
        } else if (tip === 'calendar') {
            init_cal();
        } else if (tip === 'bookmarks') {
            init_bm(div_kon);
        }
    });

    window.wid_graf_spis = window.wid_graf_spis || {};

    function risuy_wid(tip, d, kon) {
        if (d.error) {
            const el = kon.querySelector('.loading-indicator');
            if (el) el.innerHTML = `<div class="text-danger small">Ошибка: ${d.error}</div>`;
            return;
        }

        let html = '';

        if (tip === 'ai_summary') {
            const par_svod = typeof marked !== 'undefined' ? marked.parse(d.summary) : d.summary;
            html = `
                <div class="text-muted small p-1 ai-summary-content" style="line-height: 1.4;">${par_svod}</div>
                <div class="text-end mt-2"><a href="https://artificialanalysis.ai/models" target="_blank" class="small text-decoration-none">Источник ИИ: Artificial Analysis</a></div>
            `;
        }
        else if (tip === 'currency') {
            html = '<div class="d-flex flex-wrap justify-content-around mt-2">';
            const val_kluch_spis = Object.keys(d).filter(k => k !== 'date');
            val_kluch_spis.forEach(k => {
                const inf = d[k];
                const diff = Math.abs(inf.current - inf.previous).toFixed(2);
                const is_rost = inf.current >= inf.previous;
                html += `
                    <div class="text-center m-1">
                        <span class="text-muted d-block small">${k}</span>
                        <span class="currency-value">${inf.current} ₽</span>
                        <small class="${is_rost ? 'text-danger' : 'text-success'}">
                            ${is_rost ? '▲' : '▼'} ${diff}
                        </small>
                    </div>
                `;
            });
            html += `</div>
                <div class="mt-3 px-2" style="height: 100px; width: 100%;">
                    <canvas id="currencyChart"></canvas>
                </div>
                <div class="text-end text-muted mt-2" style="font-size: 0.7rem;">Обновлено: ${d.date ? new Date(d.date).toLocaleDateString() : 'N/A'}</div>
            `;
        }
        else if (tip === 'crypto') {
            html = '<div class="d-flex flex-wrap justify-content-around mt-2">';
            const cr_kluch_spis = Object.keys(d);
            cr_kluch_spis.forEach(k => {
                const inf = d[k];
                html += `
                    <div class="text-center m-1">
                        <span class="text-muted d-block small">${k}</span>
                        <span class="currency-value fw-bold fs-5">$${inf.price}</span>
                        <span class="small d-block ${inf.change >= 0 ? 'text-success' : 'text-danger'}">${inf.change}%</span>
                    </div>
                `;
            });
            html += `</div>
                <div class="mt-3 px-2" style="height: 120px; width: 100%;">
                    <canvas id="cryptoChart"></canvas>
                </div>
            `;
        }
        else if (tip === 'it_news' || tip === 'game_news' || tip === 'politics' || tip === 'ai_models') {
            html = '<div class="news-list px-1">';
            d.forEach(i => {
                if (i.error) {
                    html += `<div class="text-danger small">${i.error}</div>`;
                } else {
                    html += `
                        <div class="news-item">
                            <a href="${i.link}" target="_blank" rel="noopener noreferrer">${i.title}</a>
                        </div>
                    `;
                }
            });
            html += '</div>';
        }
        else if (tip === 'weather') {
            html = `
                <div class="text-center px-1">
                    <h6 class="fw-bold mb-1">${d.city}</h6>
                    <div class="fs-2 my-1">${d.description.split(' ')[0]}</div>
                    <div class="text-muted small mb-1">${d.description.substring(d.description.indexOf(' ') + 1)}</div>
                    <div class="d-flex justify-content-around">
                        <div class="small">
                            <span class="text-muted d-block">Мин</span>
                            <span>${d.temp_min}°C</span>
                        </div>
                        <div class="small">
                            <span class="text-muted d-block">Осадки</span>
                            <span>${d.precipitation_probability}%</span>
                        </div>
                        <div class="small">
                            <span class="text-muted d-block">Макс</span>
                            <span class="text-danger">${d.temp_max}°C</span>
                        </div>
                    </div>
                    <div class="mt-3" style="height: 100px; width: 100%;">
                        <canvas id="weatherChart"></canvas>
                    </div>
                </div>
            `;
        }

        const indicator = kon.querySelector('.loading-indicator');
        if (indicator) {
            indicator.outerHTML = html;
        } else {
            kon.innerHTML = html;
        }

        setTimeout(() => {
            const is_dark = document.body.getAttribute('data-theme') === 'dark';
            const setka_cvet = is_dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
            const tekst_cvet = is_dark ? '#a0a0a0' : '#6c757d';

            if (tip === 'currency' && document.getElementById('currencyChart')) {
                const kl_spis = Object.keys(d).filter(k => k !== 'date');
                if (window.wid_graf_spis['currency']) window.wid_graf_spis['currency'].destroy();
                const ctx = document.getElementById('currencyChart').getContext('2d');
                window.wid_graf_spis['currency'] = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: kl_spis,
                        datasets: [
                            { label: 'Сегодня', data: kl_spis.map(k => d[k].current), backgroundColor: '#4A90E2', borderRadius: 4 },
                            { label: 'Вчера', data: kl_spis.map(k => d[k].previous), backgroundColor: is_dark ? '#444' : '#e0e0e0', borderRadius: 4 }
                        ]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { x: { grid: { display: false }, ticks: { color: tekst_cvet } }, y: { display: false } }
                    }
                });
            }
            if (tip === 'crypto' && document.getElementById('cryptoChart')) {
                const kl_spis = Object.keys(d);
                if (window.wid_graf_spis['crypto']) window.wid_graf_spis['crypto'].destroy();
                const ctx = document.getElementById('cryptoChart').getContext('2d');
                window.wid_graf_spis['crypto'] = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: kl_spis,
                        datasets: [{
                            label: 'Изменение 24ч (%)',
                            data: kl_spis.map(k => d[k].change),
                            backgroundColor: (ctx) => ctx.raw >= 0 ? '#198754' : '#dc3545',
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { x: { grid: { display: false }, ticks: { color: tekst_cvet } }, y: { grid: { color: setka_cvet }, ticks: { color: tekst_cvet } } }
                    }
                });
            }
            if (tip === 'weather' && document.getElementById('weatherChart') && d.hourly_times) {
                if (window.wid_graf_spis['weather']) window.wid_graf_spis['weather'].destroy();
                const ctx = document.getElementById('weatherChart').getContext('2d');
                window.wid_graf_spis['weather'] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: d.hourly_times,
                        datasets: [{
                            label: 'Температура (°C)',
                            data: d.hourly_temps,
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
                        scales: { x: { grid: { display: false }, ticks: { color: tekst_cvet, maxTicksLimit: 6 } }, y: { grid: { color: setka_cvet }, ticks: { color: tekst_cvet } } }
                    }
                });
            }
        }, 100);
    }

    function init_chas(kon) {
        const strel_chas = document.getElementById('hourHand');
        const strel_min = document.getElementById('minuteHand');
        const strel_sec = document.getElementById('secondHand');
        const cifr_chas = document.getElementById('digitalClock');

        if (!strel_chas || !strel_min || !strel_sec) return;

        const stil = kon ? kon.getAttribute('data-clock-style') : 'both';
        const an_chas = document.querySelector('.analog-clock');
        if (an_chas && stil === 'digital') an_chas.style.display = 'none';
        if (cifr_chas && stil === 'analog') cifr_chas.style.display = 'none';

        function tik_tak() {
            const t = new Date();
            const s = t.getSeconds();
            const m = t.getMinutes();
            const h = t.getHours();

            const s_deg = ((s / 60) * 360);
            const m_deg = ((m / 60) * 360) + ((s / 60) * 6);
            const h_deg = ((h / 12) * 360) + ((m / 60) * 30);

            strel_sec.style.transform = `rotate(${s_deg}deg)`;
            strel_min.style.transform = `rotate(${m_deg}deg)`;
            strel_chas.style.transform = `rotate(${h_deg}deg)`;

            if (cifr_chas) {
                const hh = String(h).padStart(2, '0');
                const mm = String(m).padStart(2, '0');
                const ss = String(s).padStart(2, '0');
                cifr_chas.textContent = `${hh}:${mm}:${ss}`;
            }
        }

        setInterval(tik_tak, 1000);
        tik_tak();
    }

    function init_cal() {
        const setka_el = document.getElementById('calGrid');
        const m_y_el = document.getElementById('calMonthYear');
        const kn_prev = document.getElementById('prevMonthBtn');
        const kn_next = document.getElementById('nextMonthBtn');

        if (!setka_el || !m_y_el) return;

        const m_spis = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
        const d_spis = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

        let t = new Date();
        let tek_m = t.getMonth();
        let tek_y = t.getFullYear();

        function risuy_cal(y, m) {
            setka_el.innerHTML = '';
            m_y_el.textContent = `${m_spis[m]} ${y}`;

            const perv_d = new Date(y, m, 1).getDay();
            const d_v_m = new Date(y, m + 1, 0).getDate();

            let otst = perv_d - 1;
            if (otst === -1) otst = 6;

            d_spis.forEach(d => {
                const el = document.createElement('div');
                el.className = 'cal-cell cal-header text-muted small fw-bold text-center';
                el.textContent = d;
                setka_el.appendChild(el);
            });

            for (let i = 0; i < otst; i++) {
                const el = document.createElement('div');
                el.className = 'cal-cell empty';
                setka_el.appendChild(el);
            }

            const seg = new Date();
            for (let i = 1; i <= d_v_m; i++) {
                const el = document.createElement('div');
                el.className = 'cal-cell cal-day text-center';
                if (y === seg.getFullYear() && m === seg.getMonth() && i === seg.getDate()) {
                    el.classList.add('bg-primary', 'text-white', 'rounded-circle', 'fw-bold');
                }
                el.textContent = i;
                setka_el.appendChild(el);
            }
        }

        risuy_cal(tek_y, tek_m);

        if (kn_prev) kn_prev.onclick = (e) => {
            e.stopPropagation();
            tek_m--;
            if (tek_m < 0) { tek_m = 11; tek_y--; }
            risuy_cal(tek_y, tek_m);
        };

        if (kn_next) kn_next.onclick = (e) => {
            e.stopPropagation();
            tek_m++;
            if (tek_m > 11) { tek_m = 0; tek_y++; }
            risuy_cal(tek_y, tek_m);
        };
    }

    function init_bm(kon) {
        const form = kon.querySelector('#add-bookmark-form');
        if (!form) return;
        form.onsubmit = (e) => {
            e.preventDefault();
            const t_inp = form.querySelector('#bm-title');
            const u_inp = form.querySelector('#bm-url');
            fetch('/api/v1/bookmarks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': tok_csrf },
                body: JSON.stringify({ title: t_inp.value, url: u_inp.value, icon: 'fa-star' })
            }).then(r => r.json()).then(d => {
                if (d.success) window.location.reload();
                else alert('Ошибка: ' + d.error);
            });
        };
    }

    const kn_toggle_spis = document.querySelectorAll('.widget-toggle');
    kn_toggle_spis.forEach(kn => {
        kn.onchange = (e) => {
            const tip = e.target.getAttribute('data-widget-type');
            const akt = e.target.checked;
            fetch(`/api/v1/widgets/${tip}/toggle`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': tok_csrf },
                body: JSON.stringify({ is_active: akt })
            }).then(r => r.json()).then(d => {
                if (d.error) { alert(`Ошибка: ${d.error}`); e.target.checked = !akt; }
            });
        };
    });
});
