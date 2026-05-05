(function () {
  const charts = {
    users: null,
    bookings: null,
    spaces: null,
  };

  let refreshTimerId = null;

  function getConfig() {
    return window.adminDashboardConfig || {
      apiUrl: "/admin-panel/api/dashboard/",
      refreshMs: 60000,
      defaultPeriod: 30,
    };
  }

  function setLoading(loading) {
    const loader = document.getElementById("dashboard-loader");
    if (loader) {
      loader.classList.toggle("d-none", !loading);
    }
  }

  function setError(message) {
    const errorNode = document.getElementById("dashboard-error");
    if (!errorNode) {
      return;
    }
    if (!message) {
      errorNode.classList.add("d-none");
      errorNode.textContent = "";
      return;
    }
    errorNode.textContent = message;
    errorNode.classList.remove("d-none");
  }

  function safeDestroy(chart) {
    if (chart) {
      chart.destroy();
    }
  }

  function updateKpi(data) {
    const totalUsers = (data.users_by_role || []).reduce((sum, row) => sum + row.count, 0);
    const totalBookings = (data.bookings_by_day || []).reduce((sum, row) => sum + row.count, 0);
    const totalRevenue = data.revenue?.period_total || 0;
    const topSpacesCount = (data.top_spaces || []).length;

    const usersEl = document.getElementById("kpi-users");
    const bookingsEl = document.getElementById("kpi-bookings");
    const revenueEl = document.getElementById("kpi-revenue");
    const spacesEl = document.getElementById("kpi-spaces");

    if (usersEl) usersEl.textContent = String(totalUsers);
    if (bookingsEl) bookingsEl.textContent = String(totalBookings);
    if (revenueEl) revenueEl.textContent = `${totalRevenue} ${data.revenue?.currency || "RUB"}`;
    if (spacesEl) spacesEl.textContent = String(topSpacesCount);
  }

  function renderUsersChart(data) {
    const canvas = document.getElementById("usersByRoleChart");
    if (!canvas || !window.Chart) {
      return;
    }

    const labels = (data.users_by_role || []).map((row) => row.role);
    const values = (data.users_by_role || []).map((row) => row.count);

    safeDestroy(charts.users);
    charts.users = new window.Chart(canvas.getContext("2d"), {
      type: "doughnut",
      data: {
        labels,
        datasets: [
          {
            data: values,
            backgroundColor: ["#4f46e5", "#0891b2", "#f59e0b", "#16a34a", "#ef4444"],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
      },
    });
  }

  function renderBookingsChart(data) {
    const canvas = document.getElementById("bookingsByDayChart");
    if (!canvas || !window.Chart) {
      return;
    }

    const labels = (data.bookings_by_day || []).map((row) => row.date);
    const values = (data.bookings_by_day || []).map((row) => row.count);

    safeDestroy(charts.bookings);
    charts.bookings = new window.Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Бронирования",
            data: values,
            borderColor: "#0ea5e9",
            backgroundColor: "rgba(14, 165, 233, 0.15)",
            fill: true,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  }

  function renderTopSpacesChart(data) {
    const canvas = document.getElementById("topSpacesChart");
    if (!canvas || !window.Chart) {
      return;
    }

    const labels = (data.top_spaces || []).map((row) => row.space_name);
    const values = (data.top_spaces || []).map((row) => row.bookings_count);

    safeDestroy(charts.spaces);
    charts.spaces = new window.Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Кол-во бронирований",
            data: values,
            backgroundColor: "rgba(34, 197, 94, 0.7)",
            borderColor: "#16a34a",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0 },
          },
        },
      },
    });
  }

  function updateMeta(data) {
    const meta = document.getElementById("dashboard-meta");
    if (!meta || !data.meta) {
      return;
    }
    meta.textContent = `Период: ${data.meta.period_days} дней. Обновлено: ${new Date(data.meta.generated_at).toLocaleString()}`;
  }

  async function fetchDashboardData(period) {
    const config = getConfig();
    const endpoint = `${config.apiUrl}?period=${encodeURIComponent(period)}`;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(endpoint, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      updateKpi(data);
      renderUsersChart(data);
      renderBookingsChart(data);
      renderTopSpacesChart(data);
      updateMeta(data);
    } catch (_err) {
      setError("Не удалось загрузить данные дашборда. Попробуйте обновить страницу.");
    } finally {
      setLoading(false);
    }
  }

  function getCurrentPeriod() {
    const select = document.getElementById("dashboard-period");
    return select ? Number(select.value) : getConfig().defaultPeriod;
  }

  function initEvents() {
    const select = document.getElementById("dashboard-period");
    if (select) {
      select.addEventListener("change", () => fetchDashboardData(getCurrentPeriod()));
    }
  }

  function initAutoRefresh() {
    const config = getConfig();
    if (refreshTimerId) {
      window.clearInterval(refreshTimerId);
    }
    refreshTimerId = window.setInterval(() => {
      fetchDashboardData(getCurrentPeriod());
    }, config.refreshMs);
  }

  function init() {
    initEvents();
    initAutoRefresh();
    fetchDashboardData(getCurrentPeriod());
  }

  document.addEventListener("DOMContentLoaded", init);
})();
