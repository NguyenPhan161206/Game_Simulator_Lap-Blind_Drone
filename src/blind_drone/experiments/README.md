# Quản lý thí nghiệm

Nạp cấu hình, chia tập, quản lý hạt giống và danh sách tình huống ghép cặp, provenance và kết quả.

protocol.py đã triển khai xác minh checksum code/config/manifest và chọn split đã khóa. Thay đổi file khóa phải version protocol và xem lại test exposure. Module chỉ dành runner/supervisor, không import vào drone. Xem [protocol seeded v1](../../../docs/seeded-environments-v1.md).
