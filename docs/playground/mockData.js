// Mock Data for EduHub Playground Demo (docs/playground)
window.EduHubData = {
  users: [
    {
      id: "user-std-1",
      full_name: "Nguyễn Văn A",
      email: "nguyenvana@vnu.edu.vn",
      role: "STUDENT",
      avatar: "🎓"
    },
    {
      id: "user-lec-1",
      full_name: "TS. Trần Thị B",
      email: "tranthib@vnu.edu.vn",
      role: "LECTURER",
      avatar: "👨‍🏫"
    }
  ],

  currentUserRole: "STUDENT",

  schools: [
    { id: "ALL", name: "TẤT CẢ CÁC TRƯỜNG" },
    { id: "UFT", name: "UFT - Trường Khoa học & Công nghệ Trí tuệ" },
    { id: "UET", name: "UET - Trường Đại học Công nghệ VNU" },
    { id: "ULI", name: "ULIS - Trường Đại học Ngoại ngữ VNU" },
    { id: "USSH", name: "USSH - Trường ĐH Khoa học Xã hội & Nhân văn" }
  ],

  subjects: [
    { id: "subj-1", code: "INT3202", name: "Tín hiệu và Hệ thống", school: "UFT" },
    { id: "subj-2", code: "PHY1001", name: "Vật lý đại cương 1 + 2", school: "UET" },
    { id: "subj-3", code: "POL1001", name: "Giáo trình Triết học Mác-Lênin", school: "UET" },
    { id: "subj-4", code: "MAT1005", name: "Toán rời rạc & Tối ưu hóa", school: "ULI" },
    { id: "subj-5", code: "POL1002", name: "Tư tưởng Hồ Chí Minh", school: "UFT" },
    { id: "subj-6", code: "LAW1001", name: "Nhà nước và Pháp luật đại cương", school: "UFT" }
  ],

  documents: [
    {
      id: "doc-1",
      school: "UFT",
      subject_id: "subj-1",
      subject_name: "Tín hiệu và Hệ thống",
      title: "Oppenheim, Willsky, Nawab - Signals & Systems [2nd Edition]",
      description: "Giáo trình chuẩn quốc tế về Tín hiệu và Hệ thống, biên soạn bởi Oppenheim, bao gồm các chương về Biến đổi Fourier, LTI, Laplace và Z-transform.",
      document_type: "Giáo trình",
      file_url: "Oppenheim_Signals_Systems_2nd.pdf",
      owner_id: "user-lec-1",
      owner_name: "TS. Trần Thị B",
      visibility: "PUBLIC",
      approval_status: "APPROVED",
      approved_by: "user-lec-1",
      rejection_reason: null,
      semester: "Học kỳ 1",
      academic_year: "2025-2026",
      created_at: "22/07/2026",
      downloads: 342,
      pages: 950,
      chunks: [
        {
          id: "chunk-1-1",
          page_number: 42,
          content: "Hệ thống Tuyến tính Dừng (LTI - Linear Time-Invariant Systems) có tính chất quan trọng: Phản ứng của hệ thống đối với một tín hiệu đầu vào bất kỳ có thể được tính bằng phép Cuộn (Convolution) giữa tín hiệu đầu vào x(t) và phản ứng xung h(t)."
        },
        {
          id: "chunk-1-2",
          page_number: 178,
          content: "Biến đổi Fourier liên tục biểu diễn tín hiệu trong miền tần số. Công thức biến đổi Fourier thuận X(w) = integral(x(t) * e^(-jwt) dt). Miền hội tụ (ROC) phụ thuộc vào tính ổn định và khả năng nhân quả của hệ thống."
        }
      ]
    },
    {
      id: "doc-2",
      school: "UFT",
      subject_id: "subj-1",
      subject_name: "Tín hiệu và Hệ thống",
      title: "[SOLUTION] Oppenheim, Willsky, Nawab - Signals & Systems [2nd Edition]",
      description: "Lời giải chi tiết bài tập tất cả các chương sách Oppenheim. Hỗ trợ sinh viên ôn thi cuối kỳ môn Tín hiệu hệ thống.",
      document_type: "Đề thi & Đáp án",
      file_url: "Oppenheim_Signals_Solution.pdf",
      owner_id: "user-std-1",
      owner_name: "Nguyễn Văn A",
      visibility: "PUBLIC",
      approval_status: "APPROVED",
      approved_by: "user-lec-1",
      rejection_reason: null,
      semester: "Học kỳ 1",
      academic_year: "2025-2026",
      created_at: "22/07/2026",
      downloads: 512,
      pages: 420,
      chunks: [
        {
          id: "chunk-2-1",
          page_number: 15,
          content: "Lời giải Bài 2.1: Phép tích phân cuộn y(t) = x(t) * h(t). Với x(t) = u(t) và h(t) = e^(-2t)u(t), ta tính được y(t) = 0.5 * (1 - e^(-2t)) u(t)."
        }
      ]
    },
    {
      id: "doc-3",
      school: "UFT",
      subject_id: "subj-5",
      subject_name: "Tư tưởng Hồ Chí Minh",
      title: "Giáo Trình Tư Tưởng Hồ Chí Minh (không chuyên)",
      description: "Tài liệu giảng dạy chính thức dành cho sinh viên khối ngành kỹ thuật & công nghệ.",
      document_type: "Giáo trình",
      file_url: "GiaoTrinh_TT_HoChiMinh.pdf",
      owner_id: "user-lec-1",
      owner_name: "TS. Trần Thị B",
      visibility: "PUBLIC",
      approval_status: "APPROVED",
      approved_by: "user-lec-1",
      rejection_reason: null,
      semester: "Học kỳ 2",
      academic_year: "2025-2026",
      created_at: "18/07/2026",
      downloads: 189,
      pages: 210,
      chunks: [
        {
          id: "chunk-3-1",
          page_number: 88,
          content: "Tư tưởng Hồ Chí Minh về đại đoàn kết dân tộc: 'Đoàn kết, đoàn kết, đại đoàn kết / Thành công, thành công, đại thành công'."
        }
      ]
    },
    {
      id: "doc-4",
      school: "UFT",
      subject_id: "subj-6",
      subject_name: "Nhà nước và Pháp luật đại cương",
      title: "Đề cương Nhà nước và Pháp luật đại cương có đáp án",
      description: "Tổng hợp 50 câu hỏi trắc nghiệm và tự luận môn Nhà nước Pháp luật đại cương.",
      document_type: "Đề cương",
      file_url: "DeCuong_PhapLuatDaiCuong.pdf",
      owner_id: "user-std-1",
      owner_name: "Nguyễn Văn A",
      visibility: "PUBLIC",
      approval_status: "APPROVED",
      approved_by: "user-lec-1",
      rejection_reason: null,
      semester: "Học kỳ 2",
      academic_year: "2025-2026",
      created_at: "08/07/2026",
      downloads: 278,
      pages: 45,
      chunks: [
        {
          id: "chunk-4-1",
          page_number: 12,
          content: "Quy phạm pháp luật gồm 3 bộ phận cấu thành: Giả định, Quy định, và Chế tài."
        }
      ]
    },
    {
      id: "doc-5",
      school: "UET",
      subject_id: "subj-3",
      subject_name: "Giáo trình Triết học Mác-Lênin",
      title: "Giáo trình Triết học Mác - Lênin chuẩn Bộ Giáo Dục",
      description: "Giáo trình bắt buộc đối với tất cả sinh viên VNU.",
      document_type: "Giáo trình",
      file_url: "TrietHoc_MacLenin.pdf",
      owner_id: "user-lec-1",
      owner_name: "TS. Trần Thị B",
      visibility: "PUBLIC",
      approval_status: "APPROVED",
      approved_by: "user-lec-1",
      rejection_reason: null,
      semester: "Học kỳ 1",
      academic_year: "2025-2026",
      created_at: "07/07/2026",
      downloads: 630,
      pages: 340,
      chunks: [
        {
          id: "chunk-5-1",
          page_number: 65,
          content: "Quy luật chuyển hóa từ những thay đổi về lượng dẫn đến những thay đổi về chất và ngược lại."
        }
      ]
    },
    {
      id: "doc-6",
      school: "UET",
      subject_id: "subj-2",
      subject_name: "Vật lý đại cương 1 + 2",
      title: "Đề thi cuối kỳ Vật lý đại cương 2 UET 2025-2026 đề 2",
      description: "Đề thi tự luận chính thức kèm lời giải tham khảo phần Điện học và Từ học.",
      document_type: "Đề thi & Đáp án",
      file_url: "DeThi_VatLy2_UET_2026.pdf",
      owner_id: "user-std-1",
      owner_name: "Nguyễn Văn A",
      visibility: "PUBLIC",
      approval_status: "APPROVED",
      approved_by: "user-lec-1",
      rejection_reason: null,
      semester: "Học kỳ 2",
      academic_year: "2025-2026",
      created_at: "06/07/2026",
      downloads: 410,
      pages: 8,
      chunks: [
        {
          id: "chunk-6-1",
          page_number: 3,
          content: "Bài toán 2: Tính từ trường B tại tâm của vòng dây tròn bán kính R mang dòng điện I: B = (mu_0 * I) / (2 * R)."
        }
      ]
    }
  ],

  // Multiple Learning Paths Dashboard Dataset
  learningPaths: [
    {
      id: "path-1",
      user_id: "user-std-1",
      subject_id: "subj-1",
      subject_name: "Tín hiệu và Hệ thống",
      title: "Lộ trình Ôn thi Cuối kỳ Tín hiệu & Hệ thống",
      goal: "Đạt điểm A môn Tín hiệu và Hệ thống bằng cách làm chủ phép Cuộn, Biến đổi Fourier và Biến đổi Laplace.",
      duration_days: 7,
      status: "ACTIVE",
      progress_percent: 33,
      sessions: [
        {
          id: "sess-1-1",
          session_order: 1,
          title: "Buổi 1: Khái niệm Tín hiệu & Hệ thống LTI",
          objectives: "Nắm vững phân loại tín hiệu liên tục/rời rạc, tính tuyến tính, bất biến và tính chất phép cuộn.",
          document_id: "doc-1",
          document_title: "Oppenheim, Willsky, Nawab - Signals & Systems [2nd Edition]",
          page_range: "Trang 20 - 55",
          theory_content: "Hệ thống LTI được đặc trưng bởi phản ứng xung h(t). Phản ứng đầu ra y(t) = integral(x(tau) * h(t - tau) dtau).",
          exercise_content: "Bài tập 1: Cho x(t) = u(t) và h(t) = e^(-3t)u(t). Hãy tính y(t) = x(t) * h(t).",
          status: "COMPLETED"
        },
        {
          id: "sess-1-2",
          session_order: 2,
          title: "Buổi 2: Biến đổi Fourier Liên tục (CTFT)",
          objectives: "Hiểu bản chất phân tích tần số của tín hiệu và áp dụng các tính chất của CTFT.",
          document_id: "doc-1",
          document_title: "Oppenheim, Willsky, Nawab - Signals & Systems [2nd Edition]",
          page_range: "Trang 175 - 220",
          theory_content: "Biến đổi Fourier X(w) = integral(x(t) e^(-jwt) dt). Tính chất dịch thời gian: x(t - t0) <=> X(w) e^(-j w t0).",
          exercise_content: "Bài tập 2: Cho tín hiệu hình chữ nhật x(t) = rect(t/T). Tìm X(w).",
          status: "IN_PROGRESS"
        },
        {
          id: "sess-1-3",
          session_order: 3,
          title: "Buổi 3: Biến đổi Laplace & Hàm truyền H(s)",
          objectives: "Ứng dụng biến đổi Laplace để giải phương trình vi phân và khảo sát tính ổn định.",
          document_id: "doc-2",
          document_title: "[SOLUTION] Oppenheim - Signals & Systems",
          page_range: "Trang 110 - 145",
          theory_content: "Biến đổi Laplace X(s) mở rộng miền hội tụ ROC. Hệ thống LTI ổn định khi tất cả cực của H(s) nằm bên trái trục ảo.",
          exercise_content: "Bài tập 3: Khảo sát tính ổn định của hệ thống có H(s) = 1 / (s^2 + 4s + 3).",
          status: "NOT_STARTED"
        }
      ]
    },
    {
      id: "path-2",
      user_id: "user-std-1",
      subject_id: "subj-3",
      subject_name: "Triết học Mác-Lênin",
      title: "Lộ trình Cấp tốc Triết học Mác-Lênin (5 Ngày)",
      goal: "Làm chủ 2 Nguyên lý, 3 Quy luật cơ bản và Duy vật lịch sử để chuẩn bị cho bài thi giữa kỳ.",
      duration_days: 5,
      status: "ACTIVE",
      progress_percent: 60,
      sessions: [
        {
          id: "sess-2-1",
          session_order: 1,
          title: "Buổi 1: Vấn đề cơ bản của Triết học & Chủ nghĩa Duy vật",
          objectives: "Nắm được 2 mặt câu hỏi lớn của triết học và định nghĩa vật chất của Lênin.",
          document_id: "doc-5",
          document_title: "Giáo trình Triết học Mác - Lênin",
          page_range: "Trang 15 - 40",
          theory_content: "Vật chất là một danh mục triết học dùng để chỉ thực tại khách quan được đem lại cho con người trong cảm giác.",
          exercise_content: "Bài tập: Trắc nghiệm nhận diện quan điểm duy vật và duy tâm.",
          status: "COMPLETED"
        },
        {
          id: "sess-2-2",
          session_order: 2,
          title: "Buổi 2: Hai Nguyên lý & Quy luật Lượng - Chất",
          objectives: "Hiểu quy luật chuyển hóa từ những thay đổi về lượng dẫn đến sự thay đổi về chất.",
          document_id: "doc-5",
          document_title: "Giáo trình Triết học Mác - Lênin",
          page_range: "Trang 60 - 95",
          theory_content: "Lượng là chỉ số quy mô. Chất là tổng hợp thuộc tính. Tích lũy về lượng đến Điểm nút gặp Bước nhảy sẽ làm thay đổi về chất.",
          exercise_content: "Bài tập tự luận: Phân tích ý nghĩa phương pháp luận của Quy luật Lượng - Chất.",
          status: "COMPLETED"
        },
        {
          id: "sess-2-3",
          session_order: 3,
          title: "Buổi 3: Quy luật Mâu thuẫn & Quy luật Phủ định của Phủ định",
          objectives: "Nắm vững mâu thuẫn là động lực của sự phát triển.",
          document_id: "doc-5",
          document_title: "Giáo trình Triết học Mác - Lênin",
          page_range: "Trang 100 - 140",
          theory_content: "Mặt đối lập, sự thống nhất và đấu tranh giữa các mặt đối lập là nguồn gốc bên trong của sự phát triển.",
          exercise_content: "Bài tập: Phân tích mâu thuẫn trong quá trình học tập của bản thân.",
          status: "COMPLETED"
        },
        {
          id: "sess-2-4",
          session_order: 4,
          title: "Buổi 4: Lý luận Nhận thức & Thực tiễn",
          objectives: "Hiểu thực tiễn là cơ sở, động lực và tiêu chuẩn của chân lý.",
          document_id: "doc-5",
          document_title: "Giáo trình Triết học Mác - Lênin",
          page_range: "Trang 145 - 180",
          theory_content: "Nhận thức là quá trình phản ánh năng động, sáng tạo thế giới khách quan vào bộ óc con người trên cơ sở thực tiễn.",
          exercise_content: "Bài tập: Phân tích câu nói 'Lý thuyết mà không có thực tiễn là lý thuyết suông'.",
          status: "NOT_STARTED"
        },
        {
          id: "sess-2-5",
          session_order: 5,
          title: "Buổi 5: Hình thái Kinh tế - Xã hội & Tổng ôn đề thi",
          objectives: "Hệ thống hóa toàn bộ chương trình và giải đề trắc nghiệm tổng hợp.",
          document_id: "doc-5",
          document_title: "Giáo trình Triết học Mác - Lênin",
          page_range: "Trang 185 - 240",
          theory_content: "Sự phát triển của các hình thái kinh tế - xã hội là một quá trình lịch sử - tự nhiên.",
          exercise_content: "Bài tập: Giải 30 câu trắc nghiệm tổng hợp.",
          status: "NOT_STARTED"
        }
      ]
    },
    {
      id: "path-3",
      user_id: "user-std-1",
      subject_id: "subj-2",
      subject_name: "Vật lý đại cương 1 + 2",
      title: "Lộ trình Tổng ôn Vật lý Đại cương 2 UET",
      goal: "Giải thuần thục các dạng bài Điện tích - Điện trường và Từ trường trong đề thi chính thức.",
      duration_days: 3,
      status: "COMPLETED",
      progress_percent: 100,
      sessions: [
        {
          id: "sess-3-1",
          session_order: 1,
          title: "Buổi 1: Định luật Gauss & Tính Điện thế V",
          objectives: "Làm chủ phương pháp tính điện trường E và điện thế V cho các vật dẫn đối xứng.",
          document_id: "doc-6",
          document_title: "Đề thi cuối kỳ Vật lý đại cương 2 UET",
          page_range: "Trang 1 - 4",
          theory_content: "Thông lượng điện trường Phi_E qua mặt kín bằng tổng điện tích chứa trong chia cho epsilon_0.",
          exercise_content: "Bài tập: Tính điện trường E của quả cầu tích điện đều.",
          status: "COMPLETED"
        },
        {
          id: "sess-3-2",
          session_order: 2,
          title: "Buổi 2: Định luật Biot-Savart-Laplace & Từ trường",
          objectives: "Tính từ trường B tạo bởi dây dẫn thẳng dài và vòng dây tròn.",
          document_id: "doc-6",
          document_title: "Đề thi cuối kỳ Vật lý đại cương 2 UET",
          page_range: "Trang 5 - 8",
          theory_content: "Từ trường tại tâm vòng dây tròn B = (mu_0 * I)/(2R).",
          exercise_content: "Bài tập: Giải Bài 2 đề thi 2026.",
          status: "COMPLETED"
        }
      ]
    }
  ]
};
