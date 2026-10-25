# Ý tưởng và các quyết định đã thống nhất

Ngày ghi: 2026-10-25, múi giờ Asia/Ho_Chi_Minh.

Tài liệu tổng hợp có thứ tự cuộc trao đổi trong phiên hiện tại. Đây là hồ sơ định hướng dự án trong workspace AI_Lap, không phải báo cáo thực nghiệm hay bản chép nguyên văn hội thoại.

## 1. Ý tưởng gốc

Người dùng muốn xây một phòng lab mô phỏng việc sử dụng thiết bị, xe hoặc drone để giao hàng bằng cảm biến không dựa trên camera, hướng tới nghiên cứu tự hành, logistics và hạn chế thu thập thông tin không cần thiết.

Nguồn cảm hứng là dự án cá nhân Snake_ANN: dùng dữ liệu số mô tả vùng xung quanh để hỗ trợ tìm đường trong trò chơi rắn săn mồi.

Nguồn dự án: https://github.com/NguyenPhan161206/Snake_ANN

## 2. Làm rõ điều kiện không camera

Người dùng xác nhận có thể thu đồng bộ camera và radar trong giai đoạn tạo dữ liệu, hoặc dùng hình ảnh hỗ trợ huấn luyện. Yêu cầu quyết định là hệ thống tự hành khi vận hành và khi đánh giá khả năng tự hành trong lab không phụ thuộc vào vision.

Một hướng học được thảo luận là camera hỗ trợ tạo nhãn hoặc làm nguồn hướng dẫn, còn mô hình triển khai chỉ nhận các cảm biến không camera. Đây là hướng thử nghiệm tùy chọn, chưa chọn phương pháp huấn luyện cụ thể.

Không được hiểu rằng chỉ cần huấn luyện mô hình với cả camera và radar rồi rút camera ra là đáp ứng yêu cầu. Cấu hình triển khai không camera phải được huấn luyện và đánh giá tương ứng.

Các cảm biến khác và nguồn định vị, ví dụ GPS, có thể được kết hợp. Chưa chốt bộ cảm biến cụ thể, việc dùng LiDAR, hoặc loại radar cần mô phỏng.

## 3. Nguyên tắc thông tin

Người dùng diễn đạt mong muốn là phương tiện không thấy những điều không nên thấy, và giảm dữ liệu không cần thiết để thực hiện đúng nhiệm vụ một cách xuất sắc.

Cách hiểu làm việc:

> Cung cấp cho hệ thống tự hành lượng thông tin môi trường vừa đủ để hoàn thành nhiệm vụ tốt, đồng thời hạn chế thu nhận các chi tiết không cần thiết.

Phân biệt các mục tiêu:

- Không thu ảnh camera trong cấu hình vận hành.
- Giảm dữ liệu cảm biến cần thu hoặc cập nhật.
- Giảm dữ liệu đưa vào mô hình.
- Giảm dữ liệu truyền hoặc lưu trữ.
- Hạn chế khả năng suy ra thông tin nhạy cảm.

Các mục tiêu này không đồng nhất. Không camera không tự chứng minh bảo vệ toàn bộ thông tin nhạy cảm. Thiết kế bảo mật chi tiết được để sau theo ưu tiên của người dùng.

## 4. Thứ tự ưu tiên

1. Drone là đối tượng ưu tiên một.
2. Xe là đối tượng ưu tiên hai; người dùng muốn giữ hướng mở rộng để sau này cân nhắc thử nghiệm thực và luận tốt nghiệp. Chưa xác định xe mô hình hay ô tô kích thước thật, chưa đánh giá chi phí.
3. Giải quyết core phương tiện trước: cảm nhận, di chuyển, tìm đường và tránh vật cản.
4. Mở rộng tới một chuyến giao hàng, rồi điều phối logistics.

Không yêu cầu mọi phần của core đều phải là mô hình học máy. Cách phân chia giữa thuật toán học, lập đường và điều khiển còn cần thiết kế.

## 5. Phạm vi phòng lab

Người dùng làm rõ rằng hiện tại phòng lab hoàn toàn trong mô phỏng, phục vụ làm rõ ý tưởng và tạo nền tảng cho phát triển sau này.

- Mã mô tả chức năng các module cảm biến, phương tiện và nền tảng vật lý.
- Thuật toán xử lý dữ liệu và tạo hành động.
- Mô phỏng tính kết quả của hành động theo các mô hình đã khai báo.
- Giao diện như game dùng để quan sát kết quả và diễn biến sau huấn luyện.
- Unity là nền tảng ứng viên, chưa phải lựa chọn triển khai cuối cùng.
- Thực nghiệm ngoài đời chưa thuộc phạm vi hiện tại.

Hình ảnh hiển thị cho người quan sát không phải đầu vào camera của phương tiện. Phần trình diễn cần phản ánh cùng quá trình mô phỏng được dùng để đánh giá, không thay kết quả thuật toán bằng đường đi dựng sẵn.

Mô hình chức năng của cảm biến hoặc chuyển động chưa tự chứng minh độ chính xác so với phần cứng thật. Mọi kết quả phải gắn với giả định và độ chi tiết của mô hình.

## 6. Kết quả kiểm tra Snake_ANN trong cuộc trao đổi

Phiên kiểm tra đã đọc mã nguồn nhánh main tại commit e5ac4d598b84a5e8393bab514a844b22f18c56e5. Các nhận xét dưới đây là kết quả được báo trong phiên, không phải lần kiểm tra lại mới khi ghi tài liệu này.

| Nội dung | Kết quả đọc mã |
|---|---|
| Đầu vào ANN | Cửa sổ 7×7 cộng tọa độ tương đối của thức ăn, tổng 51 số |
| Đầu ra ANN | Một số dự đoán khoảng cách tới thức ăn |
| Huấn luyện | Học có giám sát bằng nhãn khoảng cách BFS |
| Tìm đường | A* sử dụng dự đoán ANN làm heuristic |
| Phạm vi bản đồ trong cấu hình | 10×10, 20×20 và 50×50; game có vật cản ngẫu nhiên |
| Thông tin của A* | Nhận toàn bộ tập vật cản và thân rắn |
| ANN khi chạy | Tính trước heuristic cho nhiều vị trí giả định, không chỉ vị trí đầu rắn hiện tại |
| Hạn chế đầu vào ANN | Phần dựng đầu vào khi chạy không đưa vật cản cố định của game vào grid |
| Hạn chế dữ liệu huấn luyện | Bộ sinh hiện tại không tạo vật cản cố định ngẫu nhiên như game |
| Hạn chế benchmark | Win là ăn ít nhất một mồi; hai phương pháp chưa chạy ghép cặp cùng tình huống; số bước tính cho lượt chơi |

Các kiểm tra hành vi nhỏ trong thư mục tạm đã được báo:

- Chèn một vật cản cố định vào ma trận trong cửa sổ không làm đổi vector của hàm trích dữ liệu huấn luyện hiện tại.
- Trong 200 mẫu tạo thử, không có ô vật cản cố định ngoài các ô thuộc rắn.
- A* thay đổi đường đi khi có tường ngoài cửa sổ quanh đầu rắn: đường thử từ 13 thành 31 cạnh.
- Kiểm tra luồng precompute trên lưới 20×20 với ba ô thân rắn tạo 397 vector cho vị trí giả định. Kiểm tra này dùng mô hình giả để ghi nhận đầu vào, không chạy trọng số ANN đã huấn luyện.

Giới hạn bằng chứng: chưa tái huấn luyện, chưa chạy lại mạng đã lưu, chưa tái lập hiệu năng trong báo cáo của repo. Không sửa dự án Snake_ANN. Các đoạn kiểm tra được tạo trong /tmp; không triển khai core AI_Lap.

Người dùng đã hỏi khi thấy có code. Trợ lý giải thích đó là kiểm tra tạm và dừng phần kiểm tra bằng mã; người dùng sau đó cho tiếp tục trao đổi. Khi bắt đầu triển khai sau này cần phân biệt rõ ghi tài liệu, kiểm tra nguồn và xây sản phẩm.

Bài học kế thừa: quan sát giới hạn và tìm đường bằng dữ liệu số. Không coi cửa sổ 7×7 là radar vật lý; không coi toàn bộ hệ thống Snake hiện tại là tự hành chỉ bằng cảm biến cục bộ.

Nguồn chính đã đọc trong phiên:

- [Cấu hình](https://github.com/NguyenPhan161206/Snake_ANN/blob/e5ac4d598b84a5e8393bab514a844b22f18c56e5/config.py)
- [Sinh dữ liệu](https://github.com/NguyenPhan161206/Snake_ANN/blob/e5ac4d598b84a5e8393bab514a844b22f18c56e5/data_generation/generate_BFS_maze.py)
- [ANN heuristic](https://github.com/NguyenPhan161206/Snake_ANN/blob/e5ac4d598b84a5e8393bab514a844b22f18c56e5/integration/heuristic_ann.py)
- [A*](https://github.com/NguyenPhan161206/Snake_ANN/blob/e5ac4d598b84a5e8393bab514a844b22f18c56e5/integration/astar_solver.py)
- [Benchmark](https://github.com/NguyenPhan161206/Snake_ANN/blob/e5ac4d598b84a5e8393bab514a844b22f18c56e5/evaluation/benchmark.py)

## 7. Các mức nhiệm vụ đã thảo luận

| Mức | Nhiệm vụ | Vai trò |
|---|---|---|
| A | Giữ ổn định, đổi hướng, tăng giảm tốc và dừng | Nền tảng chuyển động |
| B | Từ điểm xuất phát đến điểm đích, tránh vật cản tĩnh | Điểm bắt đầu đã được người dùng chấp nhận |
| C | Vật cản động, đường bị chặn, cảm biến thiếu hoặc nhiễu | Hướng mở rộng độ vững |
| D | Xuất phát, tới điểm giao, dừng/hạ cánh, giao nhận giả lập, quay về | Một chuyến giao hàng |
| E | Chọn đơn, sắp thứ tự, phân công phương tiện và sạc | Điều phối logistics |

## 8. Quyết định đã được chấp nhận

Người dùng xác nhận: “chấp nhận lấy đề xuất mức B làm thời điểm ban đầu. Đồng ý với định hướng đề xuất”.

Phạm vi khởi đầu:

- Một drone trong mô phỏng.
- Điểm xuất phát và điểm đích được cung cấp.
- Vật cản tĩnh; phương tiện chưa biết đầy đủ bố trí môi trường.
- Vận hành bằng cảm biến không camera và nguồn định vị được cho phép.
- Không cấp trực tiếp toàn bộ vật cản chưa được quan sát.
- Camera hỗ trợ huấn luyện là hướng tùy chọn.
- Đánh giá trên những bố trí chưa dùng để huấn luyện.
- Ưu tiên core phương tiện; logistics mở rộng sau.

Định hướng đã chấp nhận:

> Phòng lab mô phỏng điều hướng tự hành bằng cảm biến không camera, ưu tiên drone; nghiên cứu cách sử dụng thông tin cảm biến tiết kiệm mà vẫn đến đích an toàn và hiệu quả trong môi trường chưa biết đầy đủ.

Câu hỏi nghiên cứu làm việc:

> Trong môi trường mô phỏng xác định, drone có thể sử dụng ít thông tin cảm biến đến mức nào mà vẫn đến đích, tránh va chạm và di chuyển hiệu quả trên những bố trí chưa dùng để huấn luyện?

“Ít đến mức nào” được hiểu trong các cấu hình và điều kiện được thử, không phải khẳng định mức tối thiểu tuyệt đối.

## 9. Đánh giá dự kiến

Hai nhóm bằng chứng được thống nhất làm định hướng:

1. Chất lượng nhiệm vụ: đến đích, va chạm, mắc kẹt, hết thời gian, thời gian và quãng đường.
2. Lượng thông tin: số phép đo, tần suất, độ chi tiết và thông tin cần ghi nhớ.

Cần so sánh các cấu hình trên cùng bộ tình huống; tách huấn luyện và đánh giá. Phương pháp tham chiếu sử dụng cùng nguồn thông tin để tránh nhầm lợi ích thuật toán với lợi ích được biết nhiều hơn.

Chưa chốt ngưỡng thành công, bộ chỉ số cuối cùng, số lần thử, cấu hình cảm biến hoặc thuật toán.

## 10. Các điểm còn mở và bước tiếp theo

- Không gian, kích thước, loại vật cản và độ khó của thí nghiệm đầu tiên.
- Mức chi tiết mô hình chuyển động, va chạm và cảm biến.
- Bộ quan sát hợp lệ, dữ liệu định vị và thông tin được ghi nhớ.
- Điều kiện đến đích, dừng, thất bại và kết thúc một lượt.
- Cấu hình dữ liệu tham chiếu và các cách giảm dữ liệu.
- Phương pháp tham chiếu, cách chia tập môi trường và ngưỡng đánh giá.
- Nền tảng triển khai, thuật toán và thiết kế module sau khi đặc tả đủ rõ.

Yêu cầu mới nhất của người dùng: ghi lại trước, rồi mới làm rõ bước tiếp theo. Tài liệu này đáp ứng phần ghi lại; các đề xuất tiếp theo phải được đánh dấu là dự thảo, chưa tự chuyển thành quyết định đã chấp nhận.

## 11. Nguồn ngoài đã được nhắc trong cuộc trao đổi

Các nguồn dưới đây cung cấp bối cảnh; không chứng minh AI_Lap đã có các chức năng hoặc kết quả tương ứng. Chưa tra cứu lại trong bước ghi tài liệu.

- [RODNet](https://arxiv.org/abs/2003.01816): ví dụ học phát hiện đối tượng bằng radar với giám sát hỗ trợ từ camera–radar.
- [Unity ML-Agents Overview](https://github.com/Unity-Technologies/ml-agents/blob/develop/com.unity.ml-agents/Documentation~/ML-Agents-Overview.md): môi trường học, huấn luyện và các khả năng công cụ.
- [Unity — Agents](https://unity-technologies.github.io/ml-agents/Learning-Environment-Design-Agents/): các kiểu quan sát số, raycast và hình ảnh.

## 12. Bổ sung sau khi ghi bản ban đầu

Người dùng yêu cầu ưu tiên tạo lập môi trường trước khi viết và train model. Sau khi so sánh các nền mã nguồn mở, người dùng chấp nhận khảo sát Webots trước. Unity tiếp tục là lựa chọn có thể xem lại nếu kết quả khảo sát cần thay đổi nền tảng.

Kiến trúc đã được thảo luận gồm môi trường, phương tiện, cảm biến, quan sát, điều hướng, điều khiển, quản lý/đánh giá thí nghiệm và trực quan hóa, với ranh giới rõ giữa trạng thái thật và quan sát runtime.

Yêu cầu triển khai tiếp theo đã được người dùng cho phép: tạo cây thư mục dựa trên kiến trúc hệ thống, các cấu hình dành riêng cho Codex và agent khác, sau đó commit/push lên `git@github.com:NguyenPhan161206/Game_Simulator_Lap-Blind_Drone.git`.

Đợt này là khởi tạo repository và tooling. Chưa đồng nghĩa đã chấp nhận các thông số thí nghiệm dự thảo hoặc đã triển khai simulator/huấn luyện. Xem [ADR nền tảng](decisions/0001-foundation.md) và [kiến trúc](architecture/system.md).
