# Môi trường

minimal_lab.py tạo world và robot từ cấu hình v1. controller_config chỉ cấp các trường công khai cho drone; layout và smoke fixture ở phía supervisor. Webots giữ trạng thái vật lý duy nhất.

Kiểm tra file generated bằng python3 tools/build_lab.py --check; kiểm tra hình học/số đo thực bằng smoke Webots.

scenarios.py sinh fixture theo seed, geometry.py kiểm định AABB và witness route bảo thủ cho lát ngang. Các module này có thông tin đặc quyền, navigation không được import. Manifest/witness chỉ phục vụ tạo world và đánh giá. [Seeded suite](../../../docs/seeded-environments-v1.md).
