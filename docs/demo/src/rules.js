const resolvedPattern = /hết\s+(rò|chảy)|đã\s+(xong|sửa)|không\s+còn/i;
const categories = [
  ["plumbing", /(nước|rò|ống|bồn rửa|vòi)/i, "High"],
  ["safety", /(cháy|khói|gas)/i, "High"],
  ["electrical", /(điện|mất điện|chập điện)/i, "High"],
  ["access", /(hỏng|thang máy|khóa|cửa|điều hòa|máy lạnh|mất mạng)/i, "Medium"],
];

export function classifyMessage(message, currentResidentId) {
  const text = message.text.trim();
  if (resolvedPattern.test(text)) return { kind: "resolved" };
  const match = categories.find(([, pattern]) => pattern.test(text));
  if (match) {
    return message.senderId === currentResidentId
      ? { kind: "actionable", category: match[0], priority: match[2] }
      : { kind: "report", category: match[0] };
  }
  if (/nuôi chó|làm ồn|ồn sau/i.test(text)) return { kind: "community" };
  if (/thông báo|bảo trì|mất điện/i.test(text)) return { kind: "announcement" };
  return { kind: "casual" };
}

export function createTicketPrefill(message, detection) {
  if (detection.kind !== "actionable") return null;
  const names = {
    plumbing: ["Water issue reported", "Plumbing"],
    safety: ["Safety issue reported", "Safety"],
    electrical: ["Electrical issue reported", "Electrical"],
    access: ["Building access or equipment issue reported", "Access"],
  };
  const [title, category] = names[detection.category] ?? names.access;
  return {
    title,
    category,
    priority: detection.priority,
    location: "Unit 12B · Kitchen",
    description: message.text,
    sourceMessageId: message.id,
  };
}
