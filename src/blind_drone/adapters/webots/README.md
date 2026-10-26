# Adapter Webots

drone.py là Robot adapter không camera; lab.py là Supervisor adapter cho observer, kiểm tra và reset. Quyền và dữ liệu của hai phần được tách riêng.

Kịch bản smoke gửi operator command, không cung cấp layout cho drone. Chỉ supervisor đặt pose ở fixture/reset đã khai báo. Hướng dẫn ở [docs/lab-v1.md](../../../../docs/lab-v1.md).

navigation_lab.py là supervisor riêng cho chế độ tự hành: chuẩn bị fixture, reset trước lượt, gửi mission rồi chỉ chấm/quan sát. Không gửi motion/route trong lượt. drone.py tự gọi baseline từ quan sát thiết bị. [Cách chạy và giới hạn](../../../../docs/navigation-v1.md).

drone_v2.py/lab_v2.py là adapter versioned cho quan sát-grid/guard/planner mới, giữ nguyên v1 đã khóa. World/PROTO v2 dùng cùng vật lý/cảm biến, thay controller/customData qua whitelist. Failure snapshot tách public observation và ground truth chấm điểm; không trả dữ liệu này lại drone. [Chạy v2](../../../../docs/navigation-v2.md).
