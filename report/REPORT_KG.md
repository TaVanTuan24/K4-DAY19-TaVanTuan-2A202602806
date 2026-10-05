# Báo cáo Day 19 — Flat RAG vs GraphRAG

**Họ tên:** Tạ Văn Tuấn  **MSSV:** 2A202602806  **Ngày:** 2026-10-05

> Kỳ vọng và thang điểm: `SUBMISSION.md`. Mọi số liệu phải khớp với `ket_qua_benchmark_kg.txt`. Bản thiết kế ontology nộp riêng ở `report/ONTOLOGY.md`.

## 1. Chi phí (10 điểm)

Dán 2 bảng `Indexing` và `Querying` từ `ket_qua_benchmark_kg.txt`:

```
== Indexing (one-off)
pipeline  calls    in_tok  out_tok       USD  seconds
flat        176         0        0   0.00000    161.9
graph       196     35699     5745   0.00440    203.6

== Querying (mean per question)
pipeline  recall  judge   in_tok  out_tok       USD  seconds
flat        0.51   1.50      696       68   0.00007     4.31
graph       1.00   2.00     2859      170   0.00027     4.56
```

| Chỉ số | Flat | Graph | Graph / Flat |
| --- | --- | --- | --- |
| Indexing USD | $0.00000 | $0.00440 | +$0.00440 |
| Indexing giây | 161.9s | 203.6s | ×1.26 |
| Mỗi câu: USD | $0.00007 | $0.00027 | ×3.86 |
| Mỗi câu: giây | 4.31s | 4.56s | ×1.06 |
| Mỗi câu: in_tok | 696 | 2859 | ×4.11 |

**Chi phí tăng thêm đến từ đâu?** (2–3 câu)
> Chi phí xây dựng hệ thống (Indexing) của GraphRAG cao hơn Flat RAG 1.26 lần về thời gian (203.6s so với 161.9s) và tiêu tốn thêm $0.00440 chi phí LLM chat (35.699 input tokens và 5.745 output tokens) do bước trích xuất thực thể, vụ án và quan hệ bằng LLM (`extract_news_cases` trên 20 bài báo tin tức), trong khi Flat RAG chỉ thực hiện embedding thuần túy. Ở pha trả lời (Querying), chi phí mỗi câu hỏi của GraphRAG cao gấp 3.86 lần ($0.00027 so với $0.00007) và số input tokens tăng 4.11 lần (2.859 so với 696) do prompt được mở rộng thêm các dữ kiện đồ thị có cấu trúc (các node vụ án, nhân vật, đối tượng liên quan, tội danh, điều luật và các khoản tương ứng) nhằm cung cấp ngữ cảnh liên kết đầy đủ và chính xác cho LLM.

## 2. Từng câu hỏi (10 điểm)

| Câu | Loại | Flat recall / judge | Graph recall / judge | Thắng | Vì sao (1 câu) |
| --- | --- | --- | --- | --- | --- |
| Q1 | single-hop-law | 1.00 / 2 | 1.00 / 2 | Hòa | Định nghĩa tiền chất nằm trọn vẹn trong một đoạn văn bản của Điều 2 Luật Phòng, chống ma túy 2021 nên Flat RAG đã đủ để trích xuất đầy đủ và chính xác. |
| Q2 | single-hop-news | 1.00 / 2 | 1.00 / 2 | Hòa | Thông tin án tử hình của Trần Thanh Tuấn và Trần Minh Tâm nằm trọn trong một bài báo tin tức, vector search lấy đúng chunk là trả lời tốt. |
| Q3 | cross-kb | 0.33 / 1 | 1.00 / 2 | GraphRAG | Thông tin mức án (36 tháng) nằm ở tin tức trong khi Điều luật và khung phạt cơ bản (Điều 251 khoản 1: 02 năm đến 07 năm) nằm ở luật; Flat RAG thiếu liên kết và chỉ trích được một phần, còn GraphRAG kết nối chính xác và đầy đủ qua node Crime ('mua bán trái phép chất ma túy') sang Điều 251 BLHS. |
| Q4 | cross-kb | 0.33 / 1 | 1.00 / 2 | GraphRAG | Flat RAG chỉ nhận biết hành vi bắt giữ ban đầu mà không xác định được khung hình phạt tối đa, trong khi GraphRAG đã đi từ Hoàng Nato (Dương Minh Tuấn) sang tội tổ chức sử dụng trái phép chất ma túy (Điều 255 BLHS) và lấy đúng khoản 4 với khung tối đa là tù chung thân. |
| Q5 | cross-kb-multi-hop | 0.40 / 1 | 1.00 / 2 | GraphRAG | GraphRAG kết nối chính xác Cái Quang Huy với hành vi vận chuyển trái phép chất ma túy theo đúng Điều 250 BLHS, xác định khối lượng MDMA hơn 9,6kg thuộc Khoản 4 và khung hình phạt cao nhất là 20 năm, tù chung thân hoặc tử hình; trong khi Flat RAG thiếu thông tin điều luật và khung phạt. |
| Q6 | aggregation | 0.00 / 2 | 1.00 / 2 | GraphRAG | GraphRAG tổng hợp toàn bộ các vụ việc liên quan đến MDMA trên đồ thị kèm theo đầy đủ các đối tượng và địa điểm liên quan (Cái Quang Huy, Lê Minh Thành, Viện Pháp y tâm thần Trung ương...), đạt recall tuyệt đối 1.00 và judge 2. |

## 3. Phân tích lỗi (20 điểm)

Chọn ít nhất 2 nhóm lỗi trong E1–E6 (`LAB_GUIDE.md` Bước 8.4).

### Lỗi E1: Cầu nối gãy (Broken Bridge)

- **Hiện tượng:** Vụ án ma túy được trích xuất từ tin tức báo chí nhưng không thể liên kết sang Bộ luật Hình sự qua node cầu nối `Crime` (không có quan hệ `CHARGED_WITH`).
- **Bằng chứng:** Truy vấn Cypher kiểm tra các `Case` không có quan hệ `CHARGED_WITH`:

```cypher
MATCH (k:Case) WHERE NOT (k)-[:CHARGED_WITH]->() RETURN k.name, k.doc_id;
```

```
[{'k.name': 'Vụ vận chuyển ma túy qua sân bay Nội Bài', 'k.doc_id': 'news-100260918080821054'},
 {'k.name': 'Vụ tông cảnh sát giao thông tại An Giang', 'k.doc_id': 'news-100260926112415229'},
 {'k.name': 'Vụ triệt phá chuyên án A3-626P', 'k.doc_id': 'news-100261002184934505'}]
```

- **Nguyên nhân:**
  1. Bài báo `news-100260926112415229` phản ánh vụ việc đối tượng lái xe tông CSGT khi bị dừng kiểm tra ma túy; cơ quan điều tra khởi tố tội danh chống người thi hành công vụ hoặc chưa khởi tố tội danh ma túy thuộc Chương XX BLHS.
  2. Bài báo `news-100260918080821054` đề cập việc Cái Quang Huy vận chuyển ma túy nhưng bài báo chỉ tường thuật tóm tắt việc truy nã mà chưa nêu rõ tội danh pháp lý cụ thể trong danh mục `known_crimes`, khiến hàm `link_entity` trả về None.
  3. Do KB Luật trong phạm vi lab chỉ crawl Chương XX BLHS, hàm `link_entity` với danh sách `known_crimes` không tìm thấy tội danh tương ứng để ánh xạ, dẫn đến vụ án không có cạnh `CHARGED_WITH` và cầu nối sang KB Luật bị ngắt hoàn toàn.
- **Đề xuất sửa:** Mở rộng phạm vi crawl thêm các điều luật liên quan trong BLHS (như Điều 330 BLHS - Tội chống người thi hành công vụ), hoặc thiết kế quan hệ fallback cho phép `Case` gắn nhãn `Crime {name: 'chưa xác định tội danh'}` kèm cờ cảnh báo, hoặc cho phép liên kết trực tiếp `Case -> Article` khi bài báo có viện dẫn điều luật. Đánh đổi: Làm tăng chi phí indexing và độ phức tạp của ontology.

### Lỗi E3: Trùng thực thể (Entity Duplication)

- **Hiện tượng:** Cùng một vụ việc trong đời thực nhưng bị phân mảnh thành nhiều node `Case` riêng biệt trên Knowledge Graph.
- **Bằng chứng:** Truy vấn kiểm tra các vụ việc gắn liền với nhân vật Cái Quang Huy:

```cypher
MATCH (p:Person {name: 'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case) RETURN p.name, k.name, k.doc_id;
```

```
[{'p.name': 'Cái Quang Huy', 'k.name': 'Vụ vận chuyển ma túy qua sân bay Nội Bài', 'k.doc_id': 'news-100260918080821054'},
 {'p.name': 'Cái Quang Huy', 'k.name': 'Vụ vận chuyển hơn 10kg ma túy từ Đức về Việt Nam qua sân bay Nội Bài', 'k.doc_id': 'news-100260917203001265'}]
```

- **Nguyên nhân:** Cùng một vụ việc đời thực (Cái Quang Huy vận chuyển ma túy từ Đức về Việt Nam qua sân bay Nội Bài) được hai bài báo khác nhau đưa tin (`news-100260918080821054` và `news-100260917203001265`). LLM đặt tên Case hơi khác nhau giữa 2 bài, nên câu lệnh `MERGE (k:Case {name: $name})` đã tạo thành hai node `Case` riêng biệt thay vì gộp lại thành một vụ án thống nhất.
- **Đề xuất sửa:** Bổ sung bước entity resolution / record linkage cho các vụ án trước khi nạp đồ thị (dựa trên sự tương đồng về ngày tháng, địa điểm, các đối tượng bị can tham gia và loại tang vật), hoặc dùng thuật toán cosine similarity trên vector tóm tắt nội dung vụ án để gộp các node Case trùng lặp. Đánh đổi: Tăng chi phí tính toán và thời gian indexing.

## 4. Kết luận (5 điểm)

Khi nào nên dùng KG, khi nào Flat RAG là đủ? Dẫn số liệu ở mục 1–2:
> **1. Khi nào Flat RAG là đủ:** Với các bài toán tra cứu thông tin đơn bước (single-hop) như câu Q1 (định nghĩa luật) và Q2 (tin tức đơn lẻ), Flat RAG đạt độ chính xác hoàn hảo (recall 1.00, judge 2/2) mà không cần cấu trúc đồ thị. Ở kịch bản này, Flat RAG tối ưu hơn: chi phí rẻ hơn 3.86 lần ($0.00007 so với $0.00027 mỗi câu), thời gian phản hồi tương đương (4.31s so với 4.56s), và không phải chịu chi phí indexing ban đầu tốn kém.
>
> **2. Khi nào GraphRAG đáng tiền:** Với các bài toán đòi hỏi tổng hợp dữ liệu liên cơ sở tri thức (cross-KB) và lập luận đa bước (multi-hop) như Q3, Q4, Q5, Q6. Tại Q3, Q4, Q5, Q6, Flat RAG hoàn toàn thất thế (recall chỉ đạt 0.00 - 0.40) vì không một đoạn văn bản đơn lẻ nào chứa trọn vẹn cả diễn biến vụ án trong tin tức và điều khoản định khung trong luật; ngược lại, GraphRAG đạt điểm tuyệt đối 1.00 recall và 2/2 judge trên toàn bộ các câu này nhờ khả năng đi xuyên qua node cầu nối Crime và Article. Trung bình toàn bộ benchmark, GraphRAG nâng recall từ 0.51 lên 1.00 (tuyệt đối 100%) và điểm judge từ 1.50 lên 2.00 (tuyệt đối 2.00).
>
> **3. Đánh đổi thực tế:** GraphRAG yêu cầu thời gian dựng đồ thị ban đầu cao hơn 1.26 lần (203.6s vs 161.9s) và tiêu tốn thêm token đầu vào cho việc trích xuất và mở rộng đồ thị. Do đó, Knowledge Graph là khoản đầu tư hoàn toàn xứng đáng cho các hệ thống pháp lý, tài chính hoặc y tế phức tạp — nơi mà tính chính xác, khả năng giải trình và tính liên kết xuyên nguồn thông tin là yếu tố sống còn mà Flat RAG không thể đáp ứng.

## 5. Tự kiểm (5 điểm)

```
$ pytest tests/ -q
................................................                         [100%]
48 passed in 0.09s

$ python bench_kg.py --check
[OK] Dữ liệu: 18 điều luật, 20 bài báo
[OK] KG-1 link_entity
[OK] Neo4j kết nối được
[provider] chat = gemini:gemini-3.5-flash-lite | embedding = gemini:gemini-embedding-001
[OK] KG-2 build_graph: 148 node / 294 cạnh, đường xuyên 2 KB dài 2 cạnh
[OK] KG-3 context: 9 dữ kiện, có Điều 251
[OK] KG-4 GraphRAGAgent.answer
[OK] Chi phí check: 1 lần gọi LLM, $0.00041. Graph nhỏ (luật + 1 bài) vẫn còn trong Neo4j để bạn xem; chạy --judge để dựng graph đầy đủ.
```

Ảnh Neo4j: `report/img/kg_count.png`, `report/img/kg_cross_kb.png`, `report/img/kg_my_case.png`.
Người đã chọn cho `kg_my_case.png`: `Cái Quang Huy` (vụ vận chuyển ma túy từ Đức về Việt Nam, truy tố tội vận chuyển trái phép chất ma túy theo Điều 250 BLHS, tang vật gồm MDMA và Ketamine tại Hà Nội).

## Vấn đề gặp phải (không tính điểm)

Lỗi chưa giải quyết được: lệnh đã chạy, toàn bộ thông báo lỗi, những gì đã thử.
> Trong quá trình chạy benchmark với OpenRouter API, nhà cung cấp yêu cầu kiểm tra số dư credit dựa trên tham số `max_tokens` dự kiến tối đa (mặc định 16384 tokens nếu không khai báo). Khi số dư tài khoản còn dưới ngưỡng 16384 tokens, API trả về lỗi HTTP 402 (`Payment Required: You requested up to 16384 tokens, but can only afford 14903`). Vấn đề đã được khắc phục hoàn toàn bằng cách cấu hình tường minh `max_tokens=2048` trong phương thức `MeteredLLM.chat` (`src/llm.py`), đảm bảo yêu cầu phù hợp với dung lượng đầu ra thực tế của bài toán và giúp hệ thống hoàn thành benchmark trơn tru.
