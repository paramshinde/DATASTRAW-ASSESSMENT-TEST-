const ticketId = window.TICKET_ID;
const toast = document.getElementById("toast");
const statusPill = document.getElementById("ticket-status-pill");
const notesList = document.getElementById("notes-list");
const notesCount = document.getElementById("notes-count");
const updateForm = document.getElementById("update-ticket-form");
const updateMessage = document.getElementById("update-message");

function fmtDate(iso) {
  return new Date(iso).toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(window.__detailToastTimer);
  window.__detailToastTimer = setTimeout(() => toast.classList.add("hidden"), 2800);
}

function statusClass(status) {
  if (status === "Closed") return "status-closed";
  if (status === "In Progress") return "status-progress";
  return "status-open";
}

function renderNotes(notes) {
  notesList.innerHTML = "";
  notesCount.textContent = `${notes.length} note${notes.length === 1 ? "" : "s"}`;

  if (!notes.length) {
    notesList.innerHTML = '<div class="rounded-2xl border border-dashed border-white/10 p-4 text-sm text-slate-400">No notes yet. Add the first update from the form on the right.</div>';
    return;
  }

  for (const note of notes) {
    const article = document.createElement("article");
    article.className = "note-card";
    article.innerHTML = `
      <div class="note-meta">${fmtDate(note.created_at)}</div>
      <p class="mt-2 whitespace-pre-wrap leading-7 text-slate-200">${note.note_text}</p>
    `;
    notesList.appendChild(article);
  }
}

async function loadTicket() {
  const response = await fetch(`/api/tickets/${ticketId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Ticket not found");
  }

  const ticket = await response.json();
  document.getElementById("ticket-subject").textContent = ticket.subject;
  document.getElementById("ticket-id").textContent = ticket.ticket_id;
  document.getElementById("ticket-customer").textContent = ticket.customer_name;
  document.getElementById("ticket-email").textContent = ticket.customer_email;
  document.getElementById("ticket-created").textContent = fmtDate(ticket.created_at);
  document.getElementById("ticket-updated").textContent = fmtDate(ticket.updated_at);
  document.getElementById("ticket-description").textContent = ticket.description;
  statusPill.innerHTML = `<span class="status-pill ${statusClass(ticket.status)}">${ticket.status}</span>`;
  renderNotes(ticket.notes || []);
}

updateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(updateForm);
  const payload = Object.fromEntries(formData.entries());

  if (!payload.status) delete payload.status;
  if (!payload.notes || !payload.notes.trim()) delete payload.notes;

  if (!Object.keys(payload).length) {
    updateMessage.textContent = "Pick a status or add a note before saving.";
    return;
  }

  updateMessage.textContent = "Saving changes...";

  const response = await fetch(`/api/tickets/${ticketId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    updateMessage.textContent = error.detail || "Update failed.";
    showToast("Could not update ticket");
    return;
  }

  updateForm.reset();
  updateMessage.textContent = "Update saved successfully.";
  showToast("Ticket updated");
  await loadTicket();
});

loadTicket().catch((error) => {
  showToast(error.message);
  document.getElementById("ticket-subject").textContent = "Ticket not found";
});

