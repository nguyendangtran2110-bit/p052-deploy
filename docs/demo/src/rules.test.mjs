import test from "node:test";
import assert from "node:assert/strict";

import { classifyMessage, createTicketPrefill } from "./rules.js";

test("classifies Nguyễn Minh's kitchen leak as an actionable plumbing incident", () => {
  const message = {
    id: "zalo-18",
    senderId: "resident-minh",
    text: "Nước đang rò dưới bồn rửa bếp căn 12B, sàn ướt rồi ạ.",
  };

  const detection = classifyMessage(message, "resident-minh");

  assert.equal(detection.kind, "actionable");
  assert.equal(detection.category, "plumbing");
  assert.equal(detection.priority, "High");
  assert.deepEqual(createTicketPrefill(message, detection), {
    title: "Water issue reported",
    category: "Plumbing",
    priority: "High",
    location: "Unit 12B · Kitchen",
    description: "Nước đang rò dưới bồn rửa bếp căn 12B, sàn ướt rồi ạ.",
    sourceMessageId: "zalo-18",
  });
});

test("detects Vietnamese electrical, safety, and equipment reports case-insensitively", () => {
  const cases = [
    ["ĐiỆn căn 12B bị mất", "electrical", "High"],
    ["Có KHÓI ở hành lang tầng 12", "safety", "High"],
    ["Thang máy bị hỏng từ sáng", "access", "Medium"],
  ];

  for (const [text, category, priority] of cases) {
    const detection = classifyMessage({ id: text, senderId: "resident-minh", text }, "resident-minh");
    assert.equal(detection.kind, "actionable");
    assert.equal(detection.category, category);
    assert.equal(detection.priority, priority);
  }
});

test("keeps neighbor disputes, pet-rule reports, and resolved leaks out of ticket creation", () => {
  const samples = [
    "Phòng 314 nuôi chó phạm quy, ban quản lý kiểm tra giúp.",
    "212 đề nghị 312 không làm ồn sau 12h ảnh hưởng tầng dưới.",
    "Nước ở bồn rửa nhà em hết rò rồi, cảm ơn ban quản lý.",
  ];

  for (const text of samples) {
    const detection = classifyMessage({ id: text, senderId: "resident-other", text }, "resident-minh");
    assert.notEqual(detection.kind, "actionable");
  }
});
