# Quan sát

Tập hợp dữ liệu đo/ước lượng hợp lệ và lịch sử đã khai báo. Không nhận toàn cảnh hoặc nhãn vật thể từ scene.

range_grid.py đã có grid hữu hạn, free/occupied/unknown, chiếu ray qua RPY đo được và guard theo hull/điểm đo. Grid chỉ nhận NavigationObservation, không đọc config world hoặc scene. Chi phí primary/derived cells được báo riêng; không coi map số là bảo đảm riêng tư. [Cơ chế v2](../../../docs/navigation-v2.md).
