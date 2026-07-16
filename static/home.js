const state = {
  search: "",
  status: "",
  timer: null,
};

const ticketsBody = document.getElementById("tickets-table-body");
const emptyState = document.getElementById("empty-state");
const searchInput = document.getElementById("search-input");
const statusFilter = document.getElementById("status-filter");
const createForm = document.getElementById("create-ticket-form");
const createMessage = document.getElementById("create-ticket-message");
const toast = document.getElementById("toast");

function fmtDate(iso) {
  return new Date(iso).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => toast.classList.add("hidden"), 2800);
}

function statusClass(status) {
  if (status === "Closed") return "status-closed";
  if (status === "In Progress") return "status-progress";
  return "status-open";
}

function setStats(rows) {
  document.getElementById("stat-total").textContent = rows.length;
  document.getElementById("stat-open").textContent = rows.filter((row) => row.status === "Open").length;
  document.getElementById("stat-closed").textContent = rows.filter((row) => row.status === "Closed").length;
}

function renderTickets(rows) {
  setStats(rows);
  ticketsBody.innerHTML = "";
  emptyState.classList.toggle("hidden", rows.length > 0);

  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.className = "ticket-row";
    tr.dataset.ticketId = row.ticket_id;
    tr.innerHTML = `
      <td class="px-4 py-4">
        <div class="font-semibold text-white">${row.ticket_id}</div>
        <div class="text-sm text-slate-400">${fmtDate(row.created_at)}</div>
      </td>
      <td class="px-4 py-4">
        <div class="font-medium text-slate-100">${row.customer_name}</div>
      </td>
      <td class="px-4 py-4">
        <div class="max-w-[20rem] truncate text-slate-200">${row.subject}</div>
      </td>
      <td class="px-4 py-4">
        <span class="status-pill ${statusClass(row.status)}">${row.status}</span>
      </td>
      <td class="px-4 py-4 text-slate-400">${fmtDate(row.created_at)}</td>
    `;
    tr.addEventListener("click", () => {
      window.location.href = `/tickets/${row.ticket_id}`;
    });
    ticketsBody.appendChild(tr);
  }
}

async function loadTickets() {
  const params = new URLSearchParams();
  if (state.search.trim()) params.set("search", state.search.trim());
  if (state.status) params.set("status", state.status);

  const response = await fetch(`/api/tickets?${params.toString()}`);
  const data = await response.json();
  renderTickets(data);
}

function debounceLoad() {
  clearTimeout(state.timer);
  state.timer = setTimeout(loadTickets, 160);
}

searchInput.addEventListener("input", (event) => {
  state.search = event.target.value;
  debounceLoad();
});

statusFilter.addEventListener("change", (event) => {
  state.status = event.target.value;
  loadTickets();
});

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(createForm);
  const payload = Object.fromEntries(formData.entries());

  createMessage.textContent = "Saving ticket...";

  const response = await fetch("/api/tickets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    createMessage.textContent = error.detail || "Unable to create ticket.";
    showToast("Ticket creation failed");
    return;
  }

  const data = await response.json();
  createForm.reset();
  createMessage.textContent = `Created ${data.ticket_id} at ${fmtDate(data.created_at)}.`;
  showToast(`Ticket ${data.ticket_id} created`);
  await loadTickets();
});

loadTickets().catch(() => showToast("Failed to load tickets"));

