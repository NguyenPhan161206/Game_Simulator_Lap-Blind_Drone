# Adapter Webots

drone.py là Robot adapter không camera; lab.py là Supervisor adapter cho observer, kiểm tra và reset. Quyền và dữ liệu của hai phần được tách riêng.

Kịch bản smoke gửi operator command, không cung cấp layout cho drone. Chỉ supervisor đặt pose ở fixture/reset đã khai báo. Hướng dẫn ở [docs/lab-v1.md](../../../../docs/lab-v1.md).
