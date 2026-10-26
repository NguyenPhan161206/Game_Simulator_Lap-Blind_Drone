# Hợp đồng dữ liệu

runtime.py hiện có VehicleState và MotionCommand, quy ước world ENU/body FLU. Operator packet có danh sách trường cho phép, kiểm tra hữu hạn và giới hạn vận tốc. Các hợp đồng đầy đủ cho policy/huấn luyện còn cần phát triển theo [đặc tả](../../../docs/architecture/data-contracts.md).

navigation.py có NavigationMission với whitelist goal_m/policy và NavigationObservation/RangeReading. Kiểm tra validity, timestamp, frame, dữ liệu hữu hạn và đúng bộ sensor trước khi baseline sinh lệnh. [Chi tiết v1](../../../docs/navigation-v1.md).
