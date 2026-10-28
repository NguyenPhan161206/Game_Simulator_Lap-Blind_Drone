# Mốc 7A tiếp — validation cadence v3 đóng băng

Ngày 2026-10-28. Tiếp tục source bàn giao `7c45705`; cả năm workflow main đã đạt. Runtime implementation vẫn `0c75ce2`, design hash `968c59e193336c49a015a62f87bf6f0ac834c6131bdb348105b5fcd950ad1474`, runtime hash `bcc938bb18acd9bd829f43e6f0f722f204a5c7702e5fa3b20c82b6171a080c3d`.

1. Giữ nguyên tất cả file trong inventory runtime và các khóa v1/v2/v3. Development 45/50 và 46/50 không đáp ứng 95%; không thay planner, lấy mẫu, seeds hoặc ngưỡng để cải thiện chúng. Thiết kế không đặt development success làm điều kiện cấm validation; điều kiện mở validation là implementation và hai khóa hợp lệ. Validation là phép thử xác nhận độc lập của cấu hình duy nhất đã đăng ký, không là tập tune.
2. Bổ sung workflow **chỉ workflow_dispatch**, chạy trên một host CI với Xvfb: 120 validation case (100 feasible + 20 negative), 2 arms × 2 repeats = 480 lượt. Không shard hoặc ghép CPU từ nhiều host; không mở Webots trên laptop.
3. Workflow kiểm tra locks/source sạch và ghi exposure intent trước khi khởi động runner đã khóa. Giữ result, mọi attempt/trace và snapshot ledger sau chạy. Thêm công cụ review hậu kiểm ngoài runtime: kiểm hash raw, đường dẫn artifact, replay mọi pair và aggregate bằng evaluator đã khóa, phân biệt `complete/not_met` với `incomplete`.
4. Review không đổi raw result hoặc source runtime. Chuyển đường dẫn artifact khi tải về chỉ trong bộ nhớ; ghi hash file gốc và nguồn CI. Test tool review bằng fault injection và một artifact development đã exposed trước khi dispatch validation.
5. Ghi kế hoạch/ý định vào ledger, commit/push workflow và checks trước exposure. Dispatch validation đúng một đợt trên source đã ghi. Nếu lỗi hạ tầng: tuân thủ retry đã đăng ký, không tự dispatch lại toàn validation để tìm kết quả tốt. Thiếu bằng chứng phải báo incomplete.
6. Nếu validation đủ dữ liệu và bất kỳ gate không đạt: báo kết luận âm theo thiết kế, giữ test chưa mở. Nếu tất cả gate đạt: review đủ raw evidence, giữ nguyên inventory/source, ghi/commit exposure trước khi dùng test; test cuối cần workflow riêng hoặc lượt kế tiếp có gate validation được đối chiếu lại, không bỏ qua yêu cầu source sạch.
7. Cập nhật hai checklist, README/AGENTS và báo cáo với nguồn đã chạy, số ca/lượt/gates/thất bại/giới hạn. Commit/push theo mốc; main chỉ fast-forward khi checks liên quan đã đạt. Các lần CI development tự chạy vẫn chỉ là reproduction, không tăng n.

Phạm vi này không sửa lỗi coverage, không chuyển radar, không mở ML hoặc phần cứng. GOAL-22 vẫn là đề xuất cần version nghiên cứu phù hợp.
