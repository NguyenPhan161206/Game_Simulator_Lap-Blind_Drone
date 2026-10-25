# Dự thảo đặc tả thí nghiệm đầu tiên — mức B

Ngày soạn: 2026-10-25.

Trạng thái: đề xuất để thảo luận. Chỉ định hướng mức B và các nội dung trong [bản ghi quyết định](01-y-tuong-va-quyet-dinh.md) đã được chấp nhận. Những lựa chọn cụ thể bên dưới chưa được người dùng xác nhận và chưa được triển khai.

## 1. Mục đích

Xác định một nhiệm vụ đủ rõ để đánh giá khả năng điều hướng bằng thông tin không camera, rồi khảo sát có thể giảm thông tin đầu vào đến đâu mà vẫn giữ chất lượng nhiệm vụ theo ngưỡng đã đặt.

Chưa đặt bài toán điều phối đơn hàng, mang/thả hàng, hạ cánh, quay về, nhiều phương tiện hoặc thử nghiệm thực.

## 2. Nhiệm vụ được đề xuất

> Một drone xuất phát trong trạng thái bay ổn định, nhận điểm đích và tự di chuyển tới vùng đích, giảm tốc rồi duy trì trạng thái dừng trong vùng đó, không va chạm và không vượt giới hạn thời gian hoặc không gian hoạt động.

Xuất phát khi đã bay ổn định và kết thúc bằng dừng trong không trung giúp tách nhiệm vụ điều hướng khỏi cất/hạ cánh ở thí nghiệm đầu tiên. Đây là một phần của core phương tiện, chưa phải toàn bộ chuyến bay giao hàng.

## 3. Môi trường

Đề xuất một vùng 3D hữu hạn, mặt đất phẳng, có giới hạn độ cao và vật cản tĩnh dạng khối đơn giản. Điểm xuất phát, điểm đích, vị trí và kích thước vật cản thay đổi giữa các lượt.

Các nhóm tình huống cần có:

| Nhóm | Mục đích |
|---|---|
| Không vật cản | Kiểm tra đi tới đích và dừng |
| Một vật cản chắn đường trực tiếp | Kiểm tra phát hiện và đi vòng |
| Nhiều vật cản có lối đi | Kiểm tra nhiều quyết định nối tiếp |
| Lối lệch hướng đích, ví dụ vật cản chữ U | Kiểm tra thoát ngõ cụt và tác dụng của ghi nhớ |
| Có lựa chọn đi ngang hoặc đổi độ cao | Kiểm tra điều hướng 3D |

Tập đánh giá khả năng hoàn thành chính cần các trường hợp có đường đi khả thi theo kích thước thân và giới hạn chuyển động. Khả năng có đường do bộ tạo môi trường/bộ kiểm tra đánh giá xác định, không cấp đường đó cho bộ điều khiển.

Các trường hợp không có đường đi, nếu bổ sung, được báo riêng để kiểm tra dừng hoặc từ bỏ nhiệm vụ; không trộn vào tỷ lệ thành công của nhóm có đường.

Kích thước vùng, kích thước vật cản, độ rộng lối và giới hạn độ cao cần chốt cùng tốc độ, kích thước drone và tầm cảm biến, tránh chọn độc lập tạo bài toán không khả thi.

## 4. Chuyển động và va chạm

Đề xuất bắt đầu bằng mô hình chuyển động đơn giản có trạng thái vị trí, vận tốc, hướng và các giới hạn tốc độ, gia tốc, tốc độ đổi hướng. Bộ điều khiển nhận yêu cầu chuyển động và tạo đáp ứng có giới hạn, thay vì đưa phương tiện tức thời tới tọa độ mong muốn.

Nếu mô hình giữ độ cao hoặc bù trọng lực bằng bộ điều khiển lý tưởng, phải khai báo giả định này. Chưa dùng mô hình trên để kết luận đã mô phỏng đầy đủ động lực học quadrotor hoặc đã học điều khiển từng động cơ.

Thân drone có thể xấp xỉ bằng một thể tích va chạm đơn giản. Đánh giá va chạm cần xét chuyển động giữa các bước mô phỏng để tránh bỏ sót khi phương tiện đi xuyên vật cản trong một bước lớn.

Nếu nghiên cứu năng lượng ở phiên bản sau, cần thêm mô hình riêng; quãng đường hoặc tổng độ lớn hành động chỉ là đại lượng thay thế khi chưa có mô hình đó.

## 5. Cảm biến và thông tin hợp lệ

Đề xuất cấu hình đầu tiên là cảm biến khoảng cách hình học cục bộ, kết hợp thông tin đích và trạng thái bản thân được cung cấp qua các nguồn đo đã khai báo.

| Thông tin | Cách hiểu đề xuất |
|---|---|
| Điểm đích | Tọa độ nhiệm vụ được cấp trước |
| Vị trí bản thân | Đầu ra nguồn định vị mô phỏng; bản lý tưởng có sai số bằng không phải ghi rõ |
| Vận tốc, hướng | Đầu ra đo hoặc ước lượng trạng thái mô phỏng đã khai báo |
| Khoảng cách | Một tập phép đo theo hướng có góc và tầm đo hữu hạn |
| Trạng thái không phát hiện | Chỉ có nghĩa không phát hiện trong giới hạn cảm biến, không chứng minh toàn bộ hướng đó luôn trống |
| Lịch sử quan sát | Có thể lưu; số bước và độ chi tiết là biến thí nghiệm cần kiểm soát |

Không đưa ảnh camera, tên/nhãn vật thể lấy trực tiếp từ game engine, danh sách vật cản toàn cảnh, vị trí thật của vật cản bị che hoặc đường chuẩn vào hệ thống điều hướng được đánh giá. Các dữ liệu đó có thể được dùng riêng để tạo nhãn huấn luyện hoặc chấm điểm nếu được khai báo.

Phép đo hình học lý tưởng không phải mô phỏng radar vật lý. Phiên bản đầu có thể kiểm tra thông tin khoảng cách; muốn kết luận cho radar cần xây thêm mô hình quan sát tương ứng. Không tự gán cho cảm biến hình học khả năng nhận diện người, vật liệu, vận tốc Doppler hoặc nhãn vật thể.

Camera hỗ trợ huấn luyện là nhánh thử nghiệm sau, không phải điều kiện để bắt đầu kiểm tra điều hướng.

## 6. Điều kiện kết thúc một lượt

Thành công được đề xuất là đồng thời:

1. Vào vùng đích trong thời hạn.
2. Có tốc độ nhỏ hơn ngưỡng dừng.
3. Giữ trong vùng đích với tốc độ hợp lệ suốt khoảng thời gian xác nhận.
4. Không va chạm hoặc vi phạm giới hạn hoạt động trong lượt.

Vào gần đích ở tốc độ cao rồi bay qua không được tính là hoàn thành.

Thất bại gồm va chạm, vượt biên hoặc hết thời gian trước khi hoàn thành. Nếu nhiều sự kiện cùng xuất hiện tại một bước, quy tắc đề xuất là vi phạm/va chạm được ưu tiên hơn hoàn thành.

Mắc kẹt hoặc dao động có thể được ghi nhận để phân tích; ngưỡng phát hiện và điều kiện kết thúc sớm phải khai báo trước khi dùng. Bản đầu có thể dùng hết thời gian làm điều kiện thất bại để tránh đặt tiêu chí mắc kẹt vội vàng.

Chưa chốt bán kính vùng đích, tốc độ dừng, thời gian xác nhận, thời hạn hoặc ngưỡng khoảng cách an toàn.

## 7. Thiết kế khảo sát thông tin

Thứ tự đề xuất:

1. Dựng cấu hình tham chiếu với thông tin khoảng cách tương đối đầy đủ trong giới hạn cục bộ, để xác nhận nhiệm vụ và mô hình chuyển động hoạt động.
2. Giữ nguyên bộ tình huống, lần lượt thay đổi số hướng đo hoặc tần suất đo. Ban đầu thay một yếu tố mỗi nhóm thí nghiệm để giải thích được nguyên nhân.
3. Khảo sát tác dụng của lịch sử quan sát hoặc cách chọn phép đo theo tình huống.
4. Bổ sung sai số, trễ hoặc mất phép đo để đánh giá độ vững.
5. Khi cần, so sánh huấn luyện có/không camera hỗ trợ, giữ cùng cấu hình đầu vào lúc đánh giá.

Phân biệt hai phép thử:

- Huấn luyện riêng cho mỗi cấu hình ít dữ liệu: kiểm tra khả năng đạt được với cấu hình đó.
- Bỏ bớt phép đo khi đang chạy một mô hình đã huấn luyện: kiểm tra độ vững khi thiếu dữ liệu; không đại diện đầy đủ cho khả năng của một mô hình được huấn luyện thích hợp.

Lượng dữ liệu cần báo riêng ở đầu ra cảm biến, đầu vào mô hình và phần được lưu. Với vector có số phần tử cố định, có thể báo số giá trị/giây và byte/giây theo cách mã hóa đã khai báo; chưa coi đây là phép đo đầy đủ lượng thông tin ngữ nghĩa hoặc quyền riêng tư.

## 8. So sánh và bộ đánh giá

- Có phương pháp điều hướng tham chiếu dùng cùng nguồn quan sát; chưa chọn thuật toán.
- Nếu có bộ lập đường biết toàn bản đồ, chỉ dùng làm tham chiếu biết trước hoặc tính đường chuẩn cho đánh giá, ghi rõ lợi thế thông tin.
- Tách tập huấn luyện, tập điều chỉnh và tập kiểm tra cuối theo môi trường/tình huống. Lưu cấu hình và hạt giống tạo tình huống để chạy lại.
- Chạy các phương pháp trên cùng danh sách tình huống; lặp với nhiều lần huấn luyện độc lập nếu dùng mô hình học.
- Chọn cấu hình theo tập điều chỉnh, giữ tập kiểm tra cuối cho báo cáo cuối; chưa chốt số lượt và số lần huấn luyện.
- Bộ đánh giá và giao diện quan sát được phép đọc trạng thái thật; dữ liệu đó không đi ngược vào bộ điều khiển đang được đánh giá.

## 9. Chỉ số và tiêu chí ra quyết định

| Nhóm | Chỉ số đề xuất |
|---|---|
| Hoàn thành | Tỷ lệ hoàn thành đúng định nghĩa và trong thời hạn, trên toàn bộ lượt hợp lệ |
| Thất bại | Tỷ lệ va chạm, vượt biên, hết thời gian; ghi rõ quy tắc phân loại |
| Hiệu quả | Thời gian, quãng đường; nếu chỉ tính trên lượt thành công phải ghi rõ và báo kèm tỷ lệ thành công |
| Thông tin | Số phép đo/cập nhật, cập nhật/giây, số giá trị hoặc byte/giây, độ dài lịch sử |
| Xử lý | Thời gian tính mỗi quyết định, máy và cấu hình đo |
| Khái quát hóa | Các chỉ số trên theo nhóm tình huống mới và mức khó |

Trước khi khảo sát giảm dữ liệu cần chốt ngưỡng chất lượng: tỷ lệ thành công tối thiểu, giới hạn va chạm, thời hạn và mức suy giảm chấp nhận so với tham chiếu. Các ngưỡng được đặt theo mục tiêu nghiên cứu rồi khóa trước đánh giá cuối, không suy ra tùy tiện từ kết quả đẹp nhất.

Chỉ chọn cấu hình giảm dữ liệu khi đáp ứng yêu cầu chất lượng; không dùng quãng đường đẹp của vài lượt thành công để che số lượt thất bại tăng. Nếu không cấu hình nào đạt yêu cầu thì kết luận chưa đạt và xác định nguyên nhân.

Không quan sát va chạm trong một tập thử hữu hạn không phải chứng minh an toàn tuyệt đối. Mọi kết luận chỉ áp dụng trong mô hình và bộ điều kiện được khảo sát.

## 10. Trực quan hóa cần giúp giải thích kết quả

Đề xuất giao diện có drone, vật cản, vùng đích, phép đo cảm biến, dấu vết đường đi và trạng thái kết thúc. Có thể bật/tắt lớp hiển thị toàn cảnh và phần dữ liệu mà phương tiện được nhận, để kiểm tra ranh giới thông tin.

Một lượt cần có cấu hình, tình huống/hạt giống, phiên bản thuật toán hoặc mô hình, số đo và lý do kết thúc để tái hiện hoặc phân tích. Nếu chỉ phát lại tọa độ đã ghi, cần gọi rõ là phát lại; khả năng chạy lại mô phỏng cho cùng kết quả phải được kiểm tra riêng.

## 11. Các lựa chọn cần tiếp tục thảo luận

Các đề xuất quan trọng nhất cần xem xét trước:

1. Bắt đầu từ trạng thái đang bay và kết thúc bằng dừng trong không trung ở đích.
2. Dùng môi trường 3D đơn giản, vật cản tĩnh và mô hình chuyển động có giới hạn.
3. Bắt đầu với cảm biến khoảng cách hình học cục bộ; lựa chọn mô phỏng radar chi tiết là bước riêng.

Sau đó mới chốt các con số về kích thước, tốc độ, tầm/góc đo, tần suất, ngưỡng thành công và số lượt thử theo tính khả thi của nhiệm vụ. Thuật toán, nền tảng cuối cùng và cấu trúc module được quyết định sau đặc tả này.
