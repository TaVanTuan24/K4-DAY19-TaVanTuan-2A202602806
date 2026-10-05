# Báo cáo Day 19 — Flat RAG vs GraphRAG

**Họ tên:** Tạ Văn Tuấn  **MSSV:** 2A202602806  **Ngày:** 2026-10-05

> Kỳ vọng và thang điểm: `SUBMISSION.md`. Mọi số liệu phải khớp với `ket_qua_benchmark_kg.txt`. Bản thiết kế ontology nộp riêng ở `report/ONTOLOGY.md`.

## 1. Chi phí (10 điểm)

Dán 2 bảng `Indexing` và `Querying` từ `ket_qua_benchmark_kg.txt`:

```
== Indexing (one-off)
pipeline  calls    in_tok  out_tok       USD  seconds
flat        176     56072        0   0.00112    116.7
graph       196     91958     4644   0.00929    227.3

== Querying (mean per question)
pipeline  recall  judge   in_tok  out_tok       USD  seconds
flat        0.43   1.00      694       48   0.00013     2.53
graph       0.69   1.33     3291       69   0.00053     3.55
```

| Chỉ số | Flat | Graph | Graph / Flat |
| --- | --- | --- | --- |
| Indexing USD | $0.00112 | $0.00929 | ×8.29 |
| Indexing giây | 116.7s | 227.3s | ×1.95 |
| Mỗi câu: USD | $0.00013 | $0.00053 | ×4.08 |
| Mỗi câu: giây | 2.53s | 3.55s | ×1.40 |
| Mỗi câu: in_tok | 694 | 3291 | ×4.74 |

**Chi phí tăng thêm đến từ đâu?** (2–3 câu)
> Chi phí xây dựng hệ thống (Indexing) của GraphRAG cao hơn Flat RAG gấp 8.29 lần về chi phí USD và 1.95 lần về thời gian chủ yếu do bước trích xuất thực thể và quan hệ bằng LLM (`extract_news_cases` trên 20 bài báo tin tức) tiêu tốn 35.886 input tokens và 4.644 output tokens của mô hình chat, trong khi Flat RAG chỉ thực hiện embedding thuần túy. Ở pha trả lời (Querying), chi phí mỗi câu hỏi của GraphRAG cao gấp 4.08 lần và số input tokens tăng 4.74 lần do prompt được mở rộng thêm các dữ kiện đồ thị có cấu trúc (các node kề, tóm tắt vụ việc, điều luật và các khoản tương ứng) nhằm cung cấp ngữ cảnh liên kết đầy đủ cho LLM.

## 2. Từng câu hỏi (10 điểm)

| Câu | Loại | Flat recall / judge | Graph recall / judge | Thắng | Vì sao (1 câu) |
| --- | --- | --- | --- | --- | --- |
| Q1 | single-hop-law | 1.00 / 2 | 1.00 / 2 | Hòa | Định nghĩa tiền chất nằm trọn vẹn trong một đoạn văn bản của Điều 2 Luật Phòng, chống ma túy 2021 nên Flat RAG đã đủ để trích xuất đầy đủ và chính xác. |
| Q2 | single-hop-news | 1.00 / 2 | 1.00 / 2 | Hòa | Thông tin án tử hình của Trần Thanh Tuấn và Trần Minh Tâm nằm trọn trong một bài báo tin tức, vector search lấy đúng chunk là trả lời tốt. |
| Q3 | cross-kb | 0.00 / 0 | 1.00 / 2 | GraphRAG | Thông tin mức án (36 tháng) nằm ở tin tức trong khi Điều luật và khung phạt cơ bản (Điều 251 khoản 1: 02 năm đến 07 năm) nằm ở luật; Flat RAG không có chunk nào chứa cả hai nên trả lời "Không đủ thông tin", còn GraphRAG kết nối thành công qua node cầu nối Crime. |
| Q4 | cross-kb | 0.00 / 0 | 0.00 / 0 | Hòa | Cả hai pipeline đều trả lời "Không đủ thông tin" do các bài báo chỉ đề cập hành vi tổ chức sử dụng đang bị điều tra ban đầu của đối tượng Hoàng Nato và vector retrieval top-3 chưa hội tụ đủ ngữ cảnh tổng hợp cho LLM suy luận khung tối đa. |
| Q5 | cross-kb-multi-hop | 0.60 / 1 | 0.80 / 1 | GraphRAG | GraphRAG kết nối chính xác tang vật hơn 9,6kg MDMA với khung hình phạt cao nhất (khoản 4: 20 năm, chung thân hoặc tử hình), trong khi Flat RAG chỉ nhận diện được tình tiết định khung chung mà nhầm sang khoản b. |
| Q6 | aggregation | 0.00 / 1 | 0.33 / 1 | GraphRAG | GraphRAG tổng hợp được cả 4 vụ án liên quan đến MDMA (bao gồm vụ tại Viện Pháp y tâm thần Trung ương) và đạt recall 0.33, trong khi Flat RAG chỉ liệt kê theo tên tắt (Đức, Thành, Đông) nên không trúng từ khóa benchmark. |

## 3. Phân tích lỗi (20 điểm)

Chọn ít nhất 2 nhóm lỗi trong E1–E6 (`LAB_GUIDE.md` Bước 8.4).

### Lỗi E1: Cầu nối gãy (Broken Bridge)

- **Hiện tượng:** Vụ án ma túy được trích xuất từ tin tức báo chí nhưng không thể liên kết sang Bộ luật Hình sự qua node cầu nối `Crime` (không có quan hệ `CHARGED_WITH`).
- **Bằng chứng:** Truy vấn Cypher kiểm tra các `Case` không có quan hệ `CHARGED_WITH`:

```cypher
MATCH (k:Case) WHERE NOT (k)-[:CHARGED_WITH]->() RETURN k.name, k.doc_id;
```

```
[{'k.name': 'Vụ tông cảnh sát giao thông ở An Giang', 'k.doc_id': 'news-100260926112415229'}]
```

- **Nguyên nhân:** Bài báo `news-100260926112415229.md` phản ánh vụ việc đối tượng lái xe tông CSGT khi bị dừng kiểm tra ma túy. Tội danh được cơ quan điều tra khởi tố ban đầu là "chống người thi hành công vụ" hoặc chưa có tội danh ma túy cụ thể theo Chương XX BLHS. Do KB Luật trong phạm vi lab chỉ crawl Chương XX BLHS, hàm `link_entity` với danh sách `known_crimes` không tìm thấy tội danh tương ứng để ánh xạ, dẫn đến vụ án không có cạnh `CHARGED_WITH` và cầu nối sang KB Luật bị ngắt hoàn toàn.
- **Đề xuất sửa:** Mở rộng phạm vi crawl thêm các điều luật liên quan trong BLHS (như Điều 330 BLHS - Tội chống người thi hành công vụ), hoặc thiết kế quan hệ fallback cho phép `Case` gắn nhãn `Crime {name: 'chưa xác định tội danh'}` kèm cờ cảnh báo, hoặc cho phép liên kết trực tiếp `Case -> Article` khi bài báo có viện dẫn điều luật. Đánh đổi: Làm tăng chi phí indexing và độ phức tạp của ontology.

### Lỗi E3: Trùng thực thể (Entity Duplication)

- **Hiện tượng:** Cùng một chất ma túy trong thực tế nhưng bị phân mảnh thành nhiều node `Substance` khác nhau trên Knowledge Graph do khác biệt cách viết hoa/thường hoặc tên lóng.
- **Bằng chứng:** Truy vấn kiểm tra danh sách tên chất ma túy sắp xếp theo thứ tự chữ cái:

```cypher
MATCH (s:Substance) RETURN s.name ORDER BY toLower(s.name);
```

```
[{'s.name': 'Amphetamine'}, {'s.name': 'chất ma túy'}, {'s.name': 'Cocaine'}, {'s.name': 'côca'}, 
 {'s.name': 'Cần sa'}, {'s.name': 'cần sa'}, {'s.name': 'etomidate'}, {'s.name': 'Heroine'}, 
 {'s.name': 'Ketamine'}, {'s.name': 'ketamine'}, {'s.name': 'ma túy'}, {'s.name': 'ma túy tổng hợp'}, 
 {'s.name': 'MDMA'}, {'s.name': 'methamphetamine'}, {'s.name': 'Methamphetamine'}, {'s.name': 'thuốc lắc'}, 
 {'s.name': 'thuốc phiện'}, {'s.name': 'XLR-11'}]
```

- **Nguyên nhân:** Ràng buộc duy nhất `REQUIRE n.name IS UNIQUE` trong Neo4j có phân biệt chữ hoa chữ thường (case-sensitive). Khi nạp KB Luật, các chất được lấy theo danh mục `SUBSTANCES` viết hoa chữ cái đầu (ví dụ: `"Ketamine"`, `"Methamphetamine"`), trong khi phía Tin tức do LLM sinh ra chữ thường (`"ketamine"`, `"cần sa"`). Hơn nữa, ontology chưa có cơ chế ánh xạ từ đồng nghĩa nên tiếng lóng `"thuốc lắc"` không được gộp vào `"MDMA"`, `"Cần sa"` bị tách với `"cần sa"`.
- **Đề xuất sửa:** Trong hàm `add_law_article` và `add_news_case`, áp dụng hàm chuẩn hóa tên chất trước khi MERGE (đồng nhất về chữ thường hoặc viết hoa đầu từ qua `normalize_substance(s)`), đồng thời xây dựng từ điển ánh xạ từ lóng sang tên hóa học chuẩn (`{"thuốc lắc": "MDMA", "hàng đá": "Methamphetamine"}`). Đánh đổi: Cần duy trì bộ từ điển từ lóng tiếng Việt và bổ sung bước chuẩn hóa làm tăng nhẹ thời gian tiền xử lý.

## 4. Kết luận (5 điểm)

Khi nào nên dùng KG, khi nào Flat RAG là đủ? Dẫn số liệu ở mục 1–2:
> **1. Khi nào Flat RAG là đủ:** Với các bài toán tra cứu thông tin đơn bước (single-hop) như câu Q1 (định nghĩa luật) và Q2 (tin tức đơn lẻ), Flat RAG đạt độ chính xác hoàn hảo (recall 1.00, judge 2/2) mà không cần cấu trúc đồ thị. Ở kịch bản này, Flat RAG tối ưu hơn vượt trội: chi phí rẻ hơn 4.08 lần ($0.00013 so với $0.00053 mỗi câu), thời gian phản hồi nhanh hơn 1.40 lần (2.53s so với 3.55s), và không phải chịu chi phí indexing ban đầu tốn kém.
>
> **2. Khi nào GraphRAG đáng tiền:** Với các bài toán đòi hỏi tổng hợp dữ liệu liên cơ sở tri thức (cross-KB) và lập luận đa bước (multi-hop) như Q3, Q5, Q6. Tại Q3, Flat RAG hoàn toàn thất bại (recall 0.00, judge 0/2) vì không một đoạn văn bản đơn lẻ nào chứa cả mức án trong tin tức và điều khoản định khung trong luật; ngược lại, GraphRAG đạt điểm tuyệt đối (recall 1.00, judge 2/2). Trung bình toàn bộ benchmark, GraphRAG nâng recall từ 0.43 lên 0.69 (+60.5%) và điểm judge từ 1.00 lên 1.33 (+33.0%).
>
> **3. Đánh đổi thực tế:** GraphRAG yêu cầu chi phí dựng đồ thị ban đầu cao gấp 8.29 lần ($0.00929 vs $0.00112) và token đầu vào mỗi câu hỏi cao gấp 4.74 lần. Do đó, Knowledge Graph là khoản đầu tư hoàn toàn xứng đáng cho các hệ thống pháp lý, tài chính hoặc y tế phức tạp — nơi mà tính chính xác, khả năng giải trình và tính liên kết xuyên nguồn thông tin là yếu tố sống còn mà Flat RAG không thể đáp ứng.

## 5. Tự kiểm (5 điểm)

```
$ pytest tests/ -q
................................................                         [100%]
48 passed in 0.16s

$ python bench_kg.py --check
[OK] Dữ liệu: 18 điều luật, 20 bài báo
[OK] KG-1 link_entity
[OK] Neo4j kết nối được
[provider] chat = openrouter:openai/gpt-4o-mini | embedding = openrouter:openai/text-embedding-3-small
[OK] KG-2 build_graph: 146 node / 289 cạnh, đường xuyên 2 KB dài 2 cạnh
[OK] KG-3 context: 13 dữ kiện, có Điều 251
[OK] KG-4 GraphRAGAgent.answer
[OK] Chi phí check: 1 lần gọi LLM, $0.00064. Graph nhỏ (luật + 1 bài) vẫn còn trong Neo4j để bạn xem; chạy --judge để dựng graph đầy đủ.
```

Ảnh Neo4j: `report/img/kg_count.png`, `report/img/kg_cross_kb.png`, `report/img/kg_my_case.png`.
Người đã chọn cho `kg_my_case.png`: `Cái Quang Huy` (vụ vận chuyển ma túy từ Đức về Việt Nam, truy tố tội vận chuyển trái phép chất ma túy theo Điều 250 BLHS, tang vật gồm MDMA và Ketamine tại Hà Nội).

## Vấn đề gặp phải (không tính điểm)

Lỗi chưa giải quyết được: lệnh đã chạy, toàn bộ thông báo lỗi, những gì đã thử.
> Trong quá trình chạy benchmark với OpenRouter API, nhà cung cấp yêu cầu kiểm tra số dư credit dựa trên tham số `max_tokens` dự kiến tối đa (mặc định 16384 tokens nếu không khai báo). Khi số dư tài khoản còn dưới ngưỡng 16384 tokens, API trả về lỗi HTTP 402 (`Payment Required: You requested up to 16384 tokens, but can only afford 14903`). Vấn đề đã được khắc phục hoàn toàn bằng cách cấu hình tường minh `max_tokens=2048` trong phương thức `MeteredLLM.chat` (`src/llm.py`), đảm bảo yêu cầu phù hợp với dung lượng đầu ra thực tế của bài toán và giúp hệ thống hoàn thành benchmark trơn tru.
