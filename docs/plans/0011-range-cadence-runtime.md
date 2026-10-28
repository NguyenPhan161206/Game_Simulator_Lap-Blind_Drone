# Mốc 7A — runtime cadence v3 trên development

Ngày 2026-10-28. Tiếp tục mốc 6 tại `cf55b5d`; không thay thiết kế, thresholds, planner hoặc các file v1/v2 đã khóa.

1. Tạo adapter/world/controller v3 cạnh v2. Đặt range 32/64 ms trên thiết bị; GPS/IMU/Gyro 32 ms và control 16 ms ở cả hai arm. Packet giữ pose tại acquisition; grid chiếu bằng pose đó, điều khiển dùng pose đo gần nhất.
2. Kế toán unique acquisition, policy read/reuse, map/search/RSS và payload/log bytes riêng. Lưu raw timestamps/pose/validity, CPU từng decision, warmup và failure trong artifacts ignored.
3. Evaluator v3 chấm path/contact/bounds mỗi physics tick theo deadline/dwell đã đăng ký. Chạy pair liền nhau, hai repeat đảo order theo case hash; giữ mọi attempt. Chỉ retry khi có chứng cứ infrastructure, unresolved chặn kết luận.
4. Test hành vi các biên thời gian, stale/invalid, pose lúc đo, accounting, repeat collapse/gates, retry và runtime-lock drift. Chạy make check, smoke/navigation v1 và Webots development v3 thật; ghi exposure trước/sau mỗi vòng.
5. Tạo inventory/hash runtime riêng tham chiếu design lock, source commit và development evidence. Chỉ khóa khi implementation có kiểm chứng. Runner validation/test phải kiểm cả hai lock; test còn cần validation gate đạt. Phiên này bàn giao 7A, không tự mở held-out.
6. Cập nhật hai checklist, hướng dẫn và báo cáo phân biệt unit/local/CI, kết quả development và kết luận nghiên cứu. Commit/push feature branch; chỉ tích hợp main sau CI và simulator evidence phù hợp.

Nếu phát hiện reference/candidate không đạt trên development: giữ kết quả, không đổi tham số đã đăng ký để cứu giả thuyết. Sửa lỗi implementation phải có nguyên nhân và thêm kiểm tra; không sửa planner v2 hoặc tái sinh lock cũ.
