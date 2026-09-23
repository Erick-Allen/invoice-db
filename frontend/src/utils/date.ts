const MONTH_ABBREVIATIONS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function toIsoDate(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

export function getDefaultSentInvoiceDueDate(today = new Date()) {
  const dueDate = new Date(today);
  dueDate.setDate(dueDate.getDate() + 30);

  return toIsoDate(dueDate);
}

export function getDefaultSentInvoiceIssuedDate(today = new Date()) {
  return toIsoDate(today);
}

export function formatDisplayDate(date?: string | null) {
  if (!date) {
    return "-";
  }

  const [year, month, day] = date.split("-");
  const monthIndex = Number(month) - 1;
  const dayNumber = Number(day);

  if (!year || monthIndex < 0 || monthIndex >= MONTH_ABBREVIATIONS.length || !Number.isInteger(dayNumber)) {
    return date;
  }

  return `${MONTH_ABBREVIATIONS[monthIndex]}-${dayNumber}-${year}`;
}
