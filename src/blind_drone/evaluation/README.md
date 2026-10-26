# Đánh giá

episode.py chấm dwell, tốc độ, đích, va chạm, biên và deadline; tổng hợp mọi outcome và tách đối chứng âm. Chỉ supervisor dùng bộ chấm, navigation không import nó hoặc nhận ground truth từ nó.

Xem [hợp đồng và giới hạn](../../../docs/navigation-v1.md).

study.py kiểm tra đủ cặp theo manifest ở cả development/validation/test, cùng source/protocol, metadata/pose đầu và summary đầy đủ. Nó không yêu cầu reactive thành công trên mọi fixture và không được bỏ failed episodes. Xem [seeded protocol](../../../docs/seeded-environments-v1.md).
