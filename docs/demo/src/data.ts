export type ViewMode = "resident" | "management";
export type DemoTab = "landing" | "onboarding" | "zalo" | "ticket";

export const resident = {
  name: "Nguyễn Minh Anh",
  unit: "A-1204",
  project: "The River Residence",
  handover: "12/06/2026",
  zaloId: "minhanh_1204",
};

export const checklist = [
  { id: "welcome", step: "01", label: "Chào mừng cư dân", detail: "Xác nhận thông tin bàn giao và nhận diện căn hộ" },
  { id: "utilities", step: "02", label: "Kích hoạt tiện ích", detail: "Điện, nước, internet và thẻ cư dân" },
  { id: "handbook", step: "03", label: "Khám phá sổ tay", detail: "Nội quy, tiện ích và các đầu mối hỗ trợ" },
  { id: "inspection", step: "04", label: "Kiểm tra căn hộ", detail: "Ghi nhận các vấn đề cần đội vận hành xử lý" },
];

export const conciergeAnswer = {
  question: "Tôi cần làm gì để đăng ký thẻ cư dân?",
  answer: "Anh/chị mở bước 02 trong checklist, tải ảnh CCCD và điền biển số xe. Ban quản lý sẽ xác nhận trong giờ làm việc.",
  source: "Sổ tay cư dân · Mục 2.1",
};

export const request = {
  id: "REQ-12345",
  title: "Rò nước tại khu vực bếp",
  category: "Nước / Plumbing",
  priority: "Cao",
  created: "Hôm nay, 09:42",
  scheduled: "Đang chờ xác nhận",
};

export const workflowSteps = [
  { id: "engage", number: "01", title: "Tiếp nhận", detail: "Gặp cư dân ở nơi họ đang trò chuyện, từ app đến Zalo." },
  { id: "understand", number: "02", title: "Thấu hiểu", detail: "Nhận diện ý định và giữ lại ngữ cảnh cần thiết." },
  { id: "act", number: "03", title: "Hành động", detail: "Chuẩn bị tác vụ có cấu trúc để đội vận hành phê duyệt." },
  { id: "delight", number: "04", title: "Cập nhật", detail: "Thông báo rõ ràng để cư dân luôn biết bước tiếp theo." },
  { id: "improve", number: "05", title: "Cải thiện", detail: "Biến mỗi cuộc trò chuyện thành một mối quan hệ bền vững." },
];

export const capabilities = [
  { label: "Conversational", description: "AI hiểu ngữ cảnh, trả lời tự nhiên và hướng dẫn cư dân từng bước." },
  { label: "Connected", description: "Checklist, Zalo, ticket và đội vận hành được nối trong một luồng." },
  { label: "Compliant", description: "Mọi cam kết và ticket đều có phân loại, người duyệt và lịch sử rõ ràng." },
];

export type ZaloMessage = {
  id: number;
  sender: "Cư dân" | "Ban quản lý";
  text: string;
  time: string;
  important?: boolean;
  issueType?: string;
};

export const zaloMessages: ZaloMessage[] = [
  { id: 1, sender: "Cư dân", text: "Anh chị ơi cuối tuần này hồ bơi mở đến mấy giờ vậy ạ?", time: "08:14" },
  { id: 2, sender: "Ban quản lý", text: "Hồ bơi mở từ 06:00 đến 21:00 mỗi ngày, riêng thứ Hai bảo trì đến 14:00 nhé anh/chị.", time: "08:16" },
  { id: 3, sender: "Cư dân", text: "Có ai biết tối nay khu BBQ còn chỗ không ạ?", time: "08:18" },
  { id: 4, sender: "Cư dân", text: "Mọi người cho mình xin số hotline lễ tân với ạ.", time: "08:23" },
  { id: 5, sender: "Ban quản lý", text: "Hotline vận hành: 028 7300 2026. Trường hợp khẩn cấp vui lòng gọi trực tiếp.", time: "08:25" },
  { id: 6, sender: "Cư dân", text: "Thang máy block A hôm nay hơi đông nhỉ :)", time: "08:29" },
  { id: 7, sender: "Cư dân", text: "Mình đang tìm chỗ nhận hàng, shipper có thể lên sảnh không?", time: "08:33" },
  { id: 8, sender: "Ban quản lý", text: "Shipper gửi hàng tại quầy lễ tân tầng trệt, bảo vệ sẽ gọi cư dân xuống nhận.", time: "08:35" },
  { id: 9, sender: "Cư dân", text: "Wifi ở phòng khách nhà mình hơi yếu, có ai bị giống vậy không?", time: "08:43" },
  { id: 10, sender: "Cư dân", text: "Mất mạng từ sáng tới giờ rồi ạ, nhờ ban quản lý kiểm tra giúp căn A-1204.", time: "08:47", important: true, issueType: "Mất mạng" },
  { id: 11, sender: "Ban quản lý", text: "Ban quản lý đã ghi nhận, kỹ thuật sẽ kiểm tra tuyến mạng của block A.", time: "08:52" },
  { id: 12, sender: "Cư dân", text: "Có thông báo gì về lịch phun thuốc tuần này không ạ?", time: "09:01" },
  { id: 13, sender: "Cư dân", text: "Ai để quên ô màu xanh ở khu vực thang máy thì báo mình với nha.", time: "09:08" },
  { id: 14, sender: "Cư dân", text: "Tối qua nhà mình có mùi khét nhẹ ở hành lang tầng 12.", time: "09:17", important: true, issueType: "Mùi khét / nguy cơ cháy" },
  { id: 15, sender: "Ban quản lý", text: "Đội an toàn đang kiểm tra khu vực tầng 12. Cư dân vui lòng không tự ý mở tủ kỹ thuật.", time: "09:19" },
  { id: 16, sender: "Cư dân", text: "Cho mình hỏi phí gửi xe tháng này đóng ở đâu?", time: "09:26" },
  { id: 17, sender: "Cư dân", text: "Mất nước ở nhà tắm từ khoảng 10 phút trước, bếp vẫn có nước.", time: "09:34", important: true, issueType: "Mất nước cục bộ" },
  { id: 18, sender: "Ban quản lý", text: "Bên mình đã ghi nhận mất nước cục bộ tại một số căn, đang kiểm tra van tầng.", time: "09:37" },
  { id: 19, sender: "Cư dân", text: "Mưa to quá, mọi người nhớ đóng cửa ban công nhé.", time: "09:42" },
  { id: 20, sender: "Cư dân", text: "Cửa phòng kho tầng hầm bị hỏng khóa thì báo ai ạ?", time: "09:56", important: true, issueType: "Hỏng khóa cửa" },
  { id: 21, sender: "Ban quản lý", text: "Anh/chị gửi lại vị trí cụ thể để đội kỹ thuật tạo phiếu xử lý ạ.", time: "09:59" },
  { id: 22, sender: "Cư dân", text: "Sảnh đẹp quá, cảm ơn các anh chị vận hành nhiều nha.", time: "10:05" },
  { id: 23, sender: "Cư dân", text: "Mình thấy một vết nứt nhỏ ở tường hành lang tầng 10, nhờ kiểm tra giúp.", time: "10:12", important: true, issueType: "Nứt tường" },
  { id: 24, sender: "Cư dân", text: "Có lớp yoga sáng Chủ nhật không mọi người?", time: "10:20" },
  { id: 25, sender: "Ban quản lý", text: "Lớp yoga thử nghiệm tổ chức tại phòng cộng đồng lúc 08:00 Chủ nhật.", time: "10:22" },
  { id: 26, sender: "Cư dân", text: "Đèn hành lang block B tầng 3 tối quá ạ.", time: "10:31", important: true, issueType: "Mất điện / đèn hỏng" },
  { id: 27, sender: "Cư dân", text: "Ai có contact bên vệ sinh máy lạnh không cho mình xin với.", time: "10:37" },
  { id: 28, sender: "Ban quản lý", text: "Dịch vụ vệ sinh máy lạnh có trong danh sách đối tác tại sảnh, anh/chị ghé lấy nhé.", time: "10:39" },
  { id: 29, sender: "Cư dân", text: "Ngày mai ban quản lý có làm việc không nhỉ?", time: "10:45" },
  { id: 30, sender: "Cư dân", text: "Cảm ơn mọi người, chúc cả nhà một ngày vui vẻ!", time: "10:52" },
];

export const issueKeywords = [
  { keyword: "nước", category: "Cấp thoát nước" },
  { keyword: "điện", category: "Điện / chiếu sáng" },
  { keyword: "cháy", category: "An toàn / nguy cơ cháy" },
  { keyword: "nứt", category: "Kết cấu / hoàn thiện" },
  { keyword: "hỏng", category: "Thiết bị / tài sản" },
  { keyword: "mất mạng", category: "Internet / kết nối" },
];

export const ticketCategories = ["Cấp thoát nước", "Điện / chiếu sáng", "An toàn / nguy cơ cháy", "Kết cấu / hoàn thiện", "Thiết bị / tài sản", "Internet / kết nối"];

export const agentSummary = [
  { issueType: "Mất nước cục bộ", count: 12, severity: "Cao", detail: "Các căn A-1204, A-1206 và A-1210 cùng báo mất nước nhà tắm." },
  { issueType: "Mất điện / đèn hỏng", count: 7, severity: "Trung bình", detail: "Đèn hành lang block B tầng 3 và 4 cần kiểm tra mạch cấp điện." },
  { issueType: "Mùi khét / nguy cơ cháy", count: 2, severity: "Khẩn cấp", detail: "Đã chuyển cảnh báo an toàn tới ca trực vận hành." },
  { issueType: "Nứt tường", count: 3, severity: "Trung bình", detail: "Các điểm nứt nhỏ tại hành lang tầng 10, cần chụp ảnh xác minh." },
];
