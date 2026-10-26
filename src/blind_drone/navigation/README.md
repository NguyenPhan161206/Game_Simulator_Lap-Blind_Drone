# Điều hướng

baseline.py nhận NavigationObservation và NavigationMission có schema cố định. Có direct và reactive tiếp tuyến trái; không truy cập scene, world, evaluator hoặc file cấu hình thế giới. Có thể thay baseline bằng mô hình học qua cùng hợp đồng sau.

Xem [hợp đồng và giới hạn](../../../docs/navigation-v1.md).

observed.py thêm MissionV2 và ba comparator reactive/guarded/mapped. Planner A* chỉ đọc grid tự đo, không nhận witness/oracle layout; segment unknown không được thực thi như free. Runtime v2 có checksum riêng, không sửa baseline v1. [Protocol/giới hạn v2](../../../docs/navigation-v2.md).
