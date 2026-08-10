export type Message = { id: string; sender: string; senderId: string; time: string; text: string };

export const resident = { name: "Nguyễn Minh", unit: "12B", id: "resident-minh" };

export const steps = [
  ["01", "Verify profile", "Check your contact information", true],
  ["02", "Read the resident handbook", "Review the building rules", true],
  ["03", "Register access card", "Submit your preferred pickup time", true],
  ["04", "Set up utilities", "Electricity and internet activation", false],
  ["05", "Book move-in time", "Reserve a service elevator slot", false],
  ["06", "Welcome complete", "Review your move-in summary", false],
] as const;

export const handbookAnswers: Record<string, { answer: string; source: string }> = {
  pool: { answer: "Hồ bơi mở cửa hàng ngày từ 06:00 đến 21:00.", source: "Resident Handbook · Section 4.2" },
  parking: { answer: "Khách cần đăng ký với lễ tân trước khi đỗ xe qua đêm.", source: "Resident Handbook · Section 3.1" },
  default: { answer: "Mình chưa tìm thấy thông tin đó trong tài liệu demo hiện có. Bạn có thể gửi yêu cầu để ban quản lý xác nhận.", source: "No matching handbook section" },
};

export const messages: Message[] = [
  ["01","Linh · 09A","resident-linh","08:01","Mọi người ơi khu vực gửi xe khách đi lối nào ạ?"],
  ["02","Ban quản lý","management","08:04","Thông báo: thang máy B bảo trì từ 13:00 đến 15:00 hôm nay."],
  ["03","Hùng · 22C","resident-hung","08:07","Cảm ơn ban quản lý đã sửa đèn hành lang."],
  ["04","Thảo · 17A","resident-thao","08:13","Ai có số giao gas không ạ?"],
  ["05","Mai · 314","resident-mai","08:18","Phòng 314 nuôi chó phạm quy, ban quản lý kiểm tra giúp."],
  ["06","Quang · 212","resident-quang","08:21","212 đề nghị 312 không làm ồn sau 12h ảnh hưởng tầng dưới."],
  ["07","Ban quản lý","management","08:25","Lễ tân sẽ tiếp nhận đăng ký thẻ cư dân đến 18:00."],
  ["08","Dũng · 06B","resident-dung","08:28","Mạng nhà mình chập chờn từ sáng, ai bị vậy không?"],
  ["09","Vy · 08D","resident-vy","08:31","Cho hỏi phòng gym có mở Chủ nhật không?"],
  ["10","Linh · 09A","resident-linh","08:36","Cảm ơn, mình thấy bãi xe rồi."],
  ["11","Hà · 18B","resident-ha","08:43","Mọi người có ai nhận nhầm bưu kiện không?"],
  ["12","Ban quản lý","management","08:47","Nhắc lại: không để đồ cá nhân ngoài hành lang thoát hiểm."],
  ["13","Tuấn · 11C","resident-tuan","08:54","Điện căn em đã có rồi nhé."],
  ["14","Hùng · 22C","resident-hung","09:02","Tiếng khoan sáng nay ở tầng nào vậy?"],
  ["15","Hà · 18B","resident-ha","09:07","Ship đồ ăn để sảnh nào ạ?"],
  ["16","Ban quản lý","management","09:12","Nước sinh hoạt hoạt động bình thường tại tất cả các tầng."],
  ["17","Mai · 314","resident-mai","09:16","Việc chó sủa tối qua mong được nhắc nhở sớm."],
  ["18","Nguyễn Minh · 12B","resident-minh","09:18","Nước đang rò dưới bồn rửa bếp căn 12B, sàn ướt rồi ạ."],
  ["19","Quang · 212","resident-quang","09:20","312 có thể đóng cửa nhẹ hơn sau nửa đêm được không?"],
  ["20","Linh · 09A","resident-linh","09:22","Hồ bơi hôm nay mở đến mấy giờ?"],
  ["21","Ban quản lý","management","09:27","Đã ghi nhận các phản ánh về tiếng ồn. Vui lòng giữ trao đổi lịch sự."],
  ["22","Dũng · 06B","resident-dung","09:31","Router nhà mình khởi động lại thì ổn rồi."],
  ["23","Hùng · 22C","resident-hung","09:35","Ai đi chợ thì mua giúp mình đá nhé 😅"],
  ["24","Thảo · 17A","resident-thao","09:39","Thẻ thang máy của mình nhận ở đâu vậy?"],
  ["25","Ban quản lý","management","09:44","Ngày mai diễn tập PCCC lúc 10:00, vui lòng theo hướng dẫn tại sảnh."],
  ["26","Vy · 08D","resident-vy","09:47","Mình đã đăng ký chuyển đồ thứ bảy rồi."],
  ["27","Linh · 09A","resident-linh","09:52","Cám ơn nhé."],
  ["28","Phúc · 15A","resident-phuc","09:55","Nước ở bồn rửa nhà em hết rò rồi, cảm ơn ban quản lý."],
  ["29","Ban quản lý","management","09:58","Thông báo đã được ghim. Chúc mọi người một ngày tốt lành."],
  ["30","Nguyễn Minh · 12B","resident-minh","10:01","Em cần hỗ trợ kiểm tra sớm giúp ạ."],
].map(([id, sender, senderId, time, text]) => ({ id: `zalo-${id}`, sender, senderId, time, text }));
