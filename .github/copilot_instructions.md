## 1. Tổng quan nhanh

- Mục tiêu: xây dựng hệ gợi ý việc làm dựa trên nội dung (vector search trên mô tả công việc) cùng giao diện Streamlit.
- Phạm vi: nạp dữ liệu dạng LinkedIn (~124k dòng), làm sạch + khám phá, tạo embeddings (TF-IDF hoặc MiniLM), cung cấp gợi ý có bộ lọc và hoàn thiện báo cáo/asset như yêu cầu trong `documents/FinalProject_recommendation_system.md`.
- Công nghệ chính: Python ≥3.9, Pandas/Numpy, scikit-learn, sentence-transformers, Streamlit, Matplotlib/Seaborn, WordCloud.

## 2. Cấu trúc thư mục chính

```
data/
  archive/           # snapshot gốc đã có (jobs, companies, mappings…)
  raw/               # bản sao làm việc (tạo khi cần)
  processed/         # dữ liệu đã làm sạch, file parquet, cache vector
documents/
  plan.md            # đặc tả & timeline chính (luôn đồng bộ)
  codex_instructions.md (file này)
images/              # biểu đồ xuất từ EDA
notebooks/           # phân tích/EDA thử nghiệm
src/
  loader.py          # tải dữ liệu tập trung + join nhiều bảng
  preprocessing.py   # làm sạch, chuẩn hoá text & feature
  recommender.py     # pipeline so khớp & xử lý truy vấn
  vector_store.py    # (sẽ thêm) quản lý cache embeddings
app.py               # điểm vào Streamlit
reports/             # báo cáo audit/EDA và bản viết cuối
```

## 3. Ghi chú dataset (`data/archive/`)

- `postings.csv`: 123.849 job / 31 cột. Trường lương thiếu ~70%; `formatted_work_type` chủ yếu “Full-time”; `remote_allowed` chỉ có ~12% bản ghi (15.246 dòng). Địa điểm nổi bật: các thành phố lớn tại Mỹ.
- `jobs/*.csv`: bảng mở rộng theo `job_id`.
  - `job_skills.csv` (213.768 dòng / 126.807 job). Map qua `mappings/skills.csv` (36 nhãn, ví dụ IT → Information Technology).
  - `job_industries.csv` (164.808 dòng / 127.125 job). Map qua `mappings/industries.csv` (422 ngành).
  - `salaries.csv` (40.785 dòng). Pay period: YEARLY (23k), HOURLY (16k), còn lại ít. Dùng để suy ra lương chuẩn hoá + cờ có/th thiếu.
  - `benefits.csv` (67.943 dòng / 30.023 job).
- `companies/*.csv`: metadata công ty theo `company_id` (tên, mô tả, quy mô, chuyên môn, follower).
- Gợi ý tiền xử lý: chuẩn hoá mô tả (bỏ newline/HTML), loại trùng theo (`job_id`, `listed_time`), điền chuỗi trống bằng “Unknown”, thêm cờ boolean cho lương/remote.

## 4. Quy trình làm việc kỳ vọng

1. **Data Audit (Day 1)** – copy `data/archive` sang `data/raw` nếu cần, chạy script/notebook audit để thống kê missing, phân bố (pay_period, work_type, remote flag, top skills/industries) và lưu insight vào `reports/data_audit.md`.
2. **Cleaning (Day 2)** – hiện thực các helper `clean_text`, `prepare_features` trong `src/preprocessing.py`. Xuất bảng chuẩn `data/processed/clean_jobs.parquet` đã join kỹ năng/ngành/công ty + metadata nhãn.
3. **EDA (Day 3)** – tạo biểu đồ: top industry/skill, heatmap work type vs experience, histogram lương, tỷ lệ remote vs onsite, word cloud. Lưu ảnh vào `images/` và tóm tắt trong `reports/data_exploration.md`.
4. **Modeling (Days 4-6)** – so sánh TF-IDF với `all-MiniLM-L6-v2`; xây `src/vector_store.py` để sinh/cache embeddings kèm metadata. Viết `get_recommendations(query, filters)` dùng cosine similarity (FAISS hoặc sklearn) + unit test cho bộ lọc. Đánh giá Precision@K với bộ persona đã chọn; log độ trễ và tinh chỉnh preprocessing.
5. **UI & Reporting (Days 7-9)** – App Streamlit có sidebar filter (location, work type, experience, salary, industry/skill), khu hiển thị card gồm title, company, salary, kỹ năng khớp và panel tóm tắt dataset. Ghi lại toàn pipeline + screenshot trong báo cáo cuối.
6. **Packaging (Day 10)** – chốt code, thêm comment cần thiết, quay video demo và chuẩn bị file nộp.

## 5. Quy ước code & công cụ

- conda activate trước khi chạy lệnh với terminal.
- Tuân PEP8, ưu tiên snake_case mô tả rõ. Chỉ thêm comment ngắn cho logic khó (ví dụ chiến lược cache vector).
- Dùng Pandas cho ETL, ưu tiên Parquet cho dữ liệu xử lý; với merge lớn nên stream/chunk để tránh full RAM.
- Script phải determinisitic: không hard-code đường dẫn máy; đọc từ config/env nếu cần.
- Testing: thêm unit test nhẹ (thư mục `tests/` hoặc assert trong notebook) cho loader joins, edge case preprocessing, bộ lọc gợi ý.
- Debug:
  - thêm logging ở mức INFO/DEBUG cho bước tốn thời gian (ví dụ tính embedding, tìm kiếm).
  - nếu tạo file để debug, đặt trong `tests/debug` với tên rõ ràng kèm thông tin debug kèm timestamp
- Git hygiene: không revert thay đổi của người khác, tránh lệnh phá hoại.
- Khi báo cáo kết quả command cho user, chỉ tóm tắt điểm chính theo quy định CLI (không dump log thô).mv
- Khi tạo các file báo cáo Markdown, dùng định dạng rõ ràng với tiêu đề, danh sách, code block, nếu báo cáo tiến độ ngày thì tạo một folder dạng `day X/` trong `documents/`
- Khi tạo các file script, nếu không phải script chính thì cần đưa vào thư mục `scripts/` để tránh nhầm lẫn với module chính.
- Khi backup một file/ thư mục, tạo bản sao với hậu tố ngày tháng năm (ví dụ: `<file-name>_backup_20231125/`) trong `archive`

## 6. Lệnh hữu ích

- Cài dependencies (khi có pip): `python3 -m pip install -r requirements.txt`
- Chạy lint/test (khi đã setup): `ruff check .`, `pytest`
- Mở Streamlit: `streamlit run app.py`
- Kiểm tra nhanh dataset: `python3 scripts/data_audit.py` (sẽ tạo) hoặc dùng notebook trong `notebooks/`

## 7. Checklists deliverable

- ✅ Cập nhật `documents/plan.md` (luôn đồng bộ tiến độ).
- ✅ Báo cáo audit & EDA kèm biểu đồ.
- ✅ Bộ dữ liệu sạch + cache embeddings trong `data/processed/`.
- ✅ Module gợi ý + test.
- ✅ UI Streamlit với bộ lọc & giải thích.
- ✅ Báo cáo cuối (8–12 trang) và video demo (tùy chọn).

Tuân theo hướng dẫn này mỗi khi mở phiên Codex; cập nhật file nếu quy trình hoặc ràng buộc thay đổi.
