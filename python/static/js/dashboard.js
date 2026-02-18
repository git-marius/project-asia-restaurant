(() => {
    const apiUrl = "/api/dashboard";
    const locale = "de-DE";
    const pollMs = 30000;

    // ---------- Navigation / Views ----------
    const navButtons = Array.from(document.querySelectorAll(".nav-btn"));
    const panels = Array.from(document.querySelectorAll("[data-panel]"));

    const viewMeta = {
        dashboard: { title: "Dashboard" },
        regression: { title: "Regression" },
    };

    let activeView = "dashboard";
    let lastData = null;

    function setActiveView(view) {
        activeView = view;

        navButtons.forEach((btn) => {
            const active = btn.dataset.view === view;
            const base = btn.classList.contains("flex")
                ? "nav-btn flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium"
                : "nav-btn rounded-xl px-4 py-2 text-sm font-medium";

            btn.className = active
                ? `${base} bg-white/10 text-white`
                : `${base} text-neutral-300 hover:bg-white/5 hover:text-white`;
        });

        panels.forEach((p) => (p.hidden = p.dataset.panel !== view));

        const titleEl = document.getElementById("viewTitle");
        if (titleEl) titleEl.textContent = viewMeta[view]?.title || view;

        if (lastData) renderForView(view, lastData);
    }

    navButtons.forEach((btn) => btn.addEventListener("click", () => setActiveView(btn.dataset.view)));

    // ---------- Chart.js Defaults ----------
    function applyChartDefaults() {
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.animation = false;
        Chart.defaults.color = "rgba(255,255,255,0.60)";
        Chart.defaults.font.family =
            "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial";
        Chart.defaults.font.size = 12;

        Chart.defaults.plugins.tooltip.backgroundColor = "rgba(10,10,10,0.92)";
        Chart.defaults.plugins.tooltip.borderColor = "rgba(255,255,255,0.10)";
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.padding = 10;
        Chart.defaults.plugins.tooltip.cornerRadius = 12;
        Chart.defaults.plugins.tooltip.displayColors = false;

        Chart.defaults.interaction.mode = "index";
        Chart.defaults.interaction.intersect = false;
    }

    function chartPalette() {
        return {
            primary: "rgba(56, 189, 248, 0.95)",
            primarySoft: "rgba(56, 189, 248, 0.18)",
            gridY: "rgba(255,255,255,0.08)",
            gridX: "rgba(255,255,255,0.04)",
            ticks: "rgba(255,255,255,0.55)",
        };
    }

    function makeGradient(ctx) {
        const c = chartPalette();
        const h = ctx.canvas.height || 360;
        const g = ctx.createLinearGradient(0, 0, 0, h);
        g.addColorStop(0, c.primarySoft);
        g.addColorStop(1, "rgba(56, 189, 248, 0.00)");
        return g;
    }

    function sparseTicks(max = 8) {
        return function (value, index, ticks) {
            const n = ticks.length || 1;
            const step = Math.ceil(n / max);
            return index % step === 0 ? this.getLabelForValue(value) : "";
        };
    }

    // ---------- Data / KPI ----------
    let tempChart, scatterChart;
    let pollTimer = null;
    let inFlight = false;

    const fmtTime = (iso) =>
        new Date(iso).toLocaleString(locale, { hour: "2-digit", minute: "2-digit" });
    const fmtDateTime = (iso) => new Date(iso).toLocaleString(locale);

    async function loadDashboard(signal) {
        const res = await fetch(apiUrl, { cache: "no-store", signal });
        if (!res.ok) throw new Error("API Fehler: " + res.status);
        return await res.json();
    }

    function roundStep(value, step) {
        return Math.round(value / step) * step;
    }

    function yBounds(values) {
        if (!values.length) return { min: 0, max: 1 };
        const vMin = Math.min(...values);
        const vMax = Math.max(...values);
        const pad = Math.max(0.5, (vMax - vMin) * 0.15);
        return { min: roundStep(vMin - pad, 0.5), max: roundStep(vMax + pad, 0.5) };
    }

    function setKpis(data) {
        const cur = data.current;
        if (!cur) return;

        const tempEl = document.getElementById("kpi-temp");
        const humEl = document.getElementById("kpi-hum");
        const vocEl = document.getElementById("kpi-voc");
        const peopleEl = document.getElementById("kpi-people");
        const radarEl = document.getElementById("kpi-radar");
        const tsEl = document.getElementById("kpi-ts");
        const topLastUpdateEl = document.getElementById("top-last-update");

        if (tempEl && cur.temperature != null) tempEl.textContent = `${cur.temperature.toFixed(1)} °C`;
        if (humEl && cur.humidity != null) humEl.textContent = `${cur.humidity.toFixed(1)}`;
        if (vocEl && cur.voc != null) vocEl.textContent = `${cur.voc.toFixed(0)}`;
        if (peopleEl) peopleEl.textContent = `${cur.persons ?? "–"}`;
        if (radarEl) radarEl.textContent = cur.radar ? "Belegt" : "Leer";

        if (cur.timestamp) {
            const stamp = `Letztes Update: ${fmtDateTime(cur.timestamp)}`;
            if (tsEl) tsEl.textContent = stamp;
            if (topLastUpdateEl) topLastUpdateEl.textContent = fmtDateTime(cur.timestamp);
        }
    }

    function setRegression(data) {
        const r = data.regression || {};
        const p = data.predictions || {};

        const aEl = document.getElementById("reg-a");
        const bEl = document.getElementById("reg-b");
        const r2El = document.getElementById("reg-r2");

        const p0El = document.getElementById("pred-0");
        const p60El = document.getElementById("pred-60");
        const p120El = document.getElementById("pred-120");

        if (aEl) aEl.textContent = r.slope == null ? "–" : r.slope.toFixed(4);
        if (bEl) bEl.textContent = r.intercept == null ? "–" : r.intercept.toFixed(2);
        if (r2El) r2El.textContent = r.r2 == null ? "–" : r.r2.toFixed(3);

        if (p0El) p0El.textContent = p.p0 == null ? "–" : `${p.p0.toFixed(1)} °C`;
        if (p60El) p60El.textContent = p.p60 == null ? "–" : `${p.p60.toFixed(1)} °C`;
        if (p120El) p120El.textContent = p.p120 == null ? "–" : `${p.p120.toFixed(1)} °C`;
    }

    function renderTemp(points) {
        const c = chartPalette();
        const labels = points.map((p) => fmtTime(p.t));
        const values = points.map((p) => p.temperature);
        const bounds = yBounds(values);

        const canvas = document.getElementById("tempChart");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");

        if (tempChart) tempChart.destroy();
        tempChart = new Chart(ctx, {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        data: values,
                        tension: 0.25,
                        pointRadius: 0,
                        borderWidth: 2,
                        borderColor: c.primary,
                        fill: true,
                        backgroundColor: makeGradient(ctx),
                    },
                ],
            },
            options: {
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: (item) => ` ${item.parsed.y.toFixed(1)} °C` } },
                },
                scales: {
                    x: {
                        ticks: { color: c.ticks, callback: sparseTicks(8) },
                        grid: { color: c.gridX, drawBorder: false },
                        border: { display: false },
                    },
                    y: {
                        min: bounds.min,
                        max: bounds.max,
                        ticks: { color: c.ticks },
                        grid: { color: c.gridY, drawBorder: false },
                        border: { display: false },
                    },
                },
                elements: { line: { borderJoinStyle: "round", borderCapStyle: "round" } },
            },
        });
    }

    function renderScatter(points, regLine) {
        const c = chartPalette();
        const datasets = [
            {
                data: points,
                pointRadius: 3,
                pointHoverRadius: 5,
                backgroundColor: c.primary,
            },
        ];

        if (Array.isArray(regLine) && regLine.length >= 2) {
            datasets.push({
                type: "line",
                data: regLine,
                pointRadius: 0,
                tension: 0,
                borderWidth: 2,
                borderDash: [6, 5],
                borderColor: c.primary,
            });
        }

        const canvas = document.getElementById("scatterChart");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");

        if (scatterChart) scatterChart.destroy();
        scatterChart = new Chart(ctx, {
            type: "scatter",
            data: { datasets },
            options: {
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: { label: (item) => ` ${item.parsed.x} Pers. → ${item.parsed.y.toFixed(1)} °C` },
                    },
                },
                scales: {
                    x: {
                        title: { display: true, text: "Personenanzahl", color: c.ticks },
                        beginAtZero: true,
                        ticks: { color: c.ticks },
                        grid: { color: c.gridX, drawBorder: false },
                        border: { display: false },
                    },
                    y: {
                        title: { display: true, text: "Temperatur (°C)", color: c.ticks },
                        ticks: { color: c.ticks },
                        grid: { color: c.gridY, drawBorder: false },
                        border: { display: false },
                    },
                },
            },
        });
    }

    function renderForView(view, data) {
        const pts = data.line?.points || [];
        if (view === "dashboard") {
            renderTemp(pts);
        } else if (view === "regression") {
            renderScatter(data.scatter?.points || [], data.regression?.line_points || []);
        }
    }

    // ---------- init / polling ----------
    async function refreshOnce() {
        if (inFlight) return;
        inFlight = true;

        const controller = new AbortController();
        try {
            const data = await loadDashboard(controller.signal);
            lastData = data;
            setKpis(data);
            setRegression(data);
            renderForView(activeView, data);
        } catch (e) {
            console.error(e);
        } finally {
            inFlight = false;
        }
    }

    function startPolling() {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(() => {
            if (document.visibilityState === "visible") refreshOnce();
        }, pollMs);
    }

    // wire buttons
    const btnRefresh = document.getElementById("btnRefresh");
    const btnRefreshTop = document.getElementById("btnRefreshTop");
    if (btnRefresh) btnRefresh.addEventListener("click", refreshOnce);
    if (btnRefreshTop) btnRefreshTop.addEventListener("click", refreshOnce);

    // boot
    applyChartDefaults();
    setActiveView("dashboard");
    refreshOnce();
    startPolling();
})();
