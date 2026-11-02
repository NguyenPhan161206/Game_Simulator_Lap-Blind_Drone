# ADR 0013 — Tách acquisition theo tình huống và thiết kế sparse schema

Ngày: 2026-11-02. Thuộc yêu cầu hoàn thiện 7A và [0020](../plans/0020-complete-7a.md). Đây là hai ablation development riêng, không kết hợp với free-history TTL. Giữ legacy source/locks và test v3.

DATA-06 dùng toàn bộ mười ray, v4 full-history và cold start. Candidate thay đổi acquisition vật lý 32/64 ms theo quan sát trước đó: chỉ chọn 64 ms khi navigator đang follow observed path/detour/recovery, mọi horizontal range hợp lệ và >=2 m; trường hợp còn lại 32 ms. Quyết định chỉ áp dụng từ acquisition kế tiếp và được log trước khi lấy mẫu; không đọc thiết bị hoặc ground truth ngoài lịch. Warmup 32 ms. Đây không phải lọc bớt log sau khi đã lấy sensor.

DATA-09 tách ba arm: full schema/mười sensor; drop-at-runtime (chỉ bật 000/090/180/270/up/down nhưng giữ hợp đồng policy cũ yêu cầu mười); sparse-designed (cùng sáu sensor thực, observation contract riêng chấp nhận đúng sáu, unknown vẫn chặn). Không thêm ray giả/no-return giả. Policy sparse là v4 được thiết kế lại interface cho sáu sensor và giữ conservative planner; không huấn luyện, không tuyên bố retraining. Dropout dự kiến fail-closed theo contract là bằng chứng mất khả năng thực hiện nhiệm vụ, không loại khỏi mẫu số.

Hai study sử dụng lại đúng 12 case exposed đã đăng ký ở A/A 0019 (11 feasible/một negative), hai repeat đảo thứ tự, một process/episode. DATA-06: 48 episode; DATA-09: 72 episode, thứ tự ba arm xoay theo hash case và đảo ở repeat 1. Không chọn case từ outcome mới. Kết quả chỉ trong tập pilot này; chưa đủ tự mở held-out. [0021](../plans/0021-sensor-development.md) khóa gate và vận hành trước implementation/evaluation.
