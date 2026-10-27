# Đối chiếu nguồn chính — nghiên cứu range cadence v3

Ngày truy cập: 2026-10-27. Đây là khảo sát có mục tiêu để định vị thí nghiệm đầu tiên, không phải tổng quan hệ thống hay chứng minh không tồn tại công trình tương tự. Chỉ đọc/tóm tắt nguồn; không nhập mã, asset hoặc dữ liệu ngoài.

| Nguồn chính | Điều đã được nghiên cứu | Liên hệ và giới hạn đối với lab |
|---|---|---|
| Alberto Elfes, [Occupancy Grids: A Stochastic Spatial Representation for Active Robot Perception](https://arxiv.org/abs/1304.1098), bản lưu arXiv 2013 | Tích hợp range thành biểu diễn occupancy xác suất để phục vụ cảm nhận/điều hướng. | Grid từ range không là ý tưởng mới. Grid v2 của lab là biểu diễn free/occupied đơn giản, không tự tương đương mô hình xác suất đầy đủ. |
| Alberto Elfes, [Dynamic Control of Robot Perception Using Multi-Property Inference Grids](https://www.ri.cmu.edu/publications/dynamic-control-of-robot-perception-using-multi-property-inference-grids/), ICRA 1992 | Lập kế hoạch hoạt động cảm nhận theo nhu cầu thông tin nhiệm vụ và chọn cảm biến. | Giảm thông tin theo nhiệm vụ đã có nền tảng; v3 chỉ thử cadence cố định, chưa phát minh active sensing hoặc tối ưu thông tin. |
| Arias-Perez và cộng sự, [ExploreBug](https://arxiv.org/html/2407.06706v1), 2024, bản v1; DOI liên quan 10.1109/LRA.2024.3486212 | Mapping/exploration/navigation với cảm biến hạn chế trên nano-drone, có mô phỏng và thử thực. | Cho thấy không camera/cảm biến ít đã là hướng có tiền lệ. Bài toán nhiều drone khám phá khác một drone đến đích; không dùng kết quả của họ làm bằng chứng chất lượng cho lab, không nhập fleet vào phạm vi. |
| Patterson, Neumann, White, White, [Empirical Design in Reinforcement Learning](https://jmlr.org/papers/v25/23-0183.html), JMLR 25(318), 2024 | Thiết kế thực nghiệm, biến thiên, lựa chọn tham số và bias người thực nghiệm. | Áp dụng nguyên tắc khóa tiêu chí, phân chia dữ liệu và báo thất bại. V3 chưa huấn luyện RL; không cần nhập framework từ tài liệu. |
| NIST, [Exact binomial confidence limits](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm) | Giới hạn xác suất binomial bằng đảo CDF, có giới hạn một phía. | V3 dùng upper bound cho xác suất cặp reference thành công/candidate thất bại. Giả định đơn vị độc lập là case từ hỗn hợp generator; không coi control tick hoặc lượt lặp là mẫu độc lập. |
| Cyberbotics, [DistanceSensor, tag R2025a](https://raw.githubusercontent.com/cyberbotics/webots/R2025a/docs/reference/distancesensor.md) | `enable(samplingPeriod)` đặt chu kỳ đo bằng ms; `getValue` trả phép đo gần nhất; cảm biến generic dựa trên giao ray với bounding objects. | Adapter v3 tương lai phải đặt chu kỳ trên thiết bị và kiểm tra `getSamplingPeriod`, không chỉ bớt gọi policy. Đây là range hình học, không là radar RF, Doppler hay đo năng lượng phần cứng. |

## Đóng góp được nhắm tới

- **Ứng dụng/thực nghiệm:** định lượng ảnh hưởng của giảm một nửa nhịp thu nhận range đối với baseline mapped cố định trong miền tĩnh đã khai báo. Kết quả âm vẫn có giá trị.
- **Thuật toán:** chưa có đóng góp thuật toán mới ở mốc 6; giữ cùng grid/guard/planner. Nếu cần đổi thuật toán sau khi xem kết quả, lập nghiên cứu/test version khác.
- **Dữ liệu/benchmark:** thêm bộ case mới có provenance, chứng chỉ, commitments và exposure ledger. Chưa gọi là bộ dữ liệu cảm biến thực hoặc bằng chứng OOD.
- **Hạ tầng:** kế toán riêng mẫu sensor, lần đọc observation, trạng thái bộ nhớ, payload và log; khóa thiết kế trước khóa runtime.

Đây là định vị do dự án suy ra từ các nguồn trên. Chưa đủ để khẳng định tính mới khoa học cho luận văn, tối thiểu thông tin tuyệt đối, bảo mật/riêng tư, hoặc khả năng chạy drone thật.
