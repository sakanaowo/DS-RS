Dưới đây là tài liệu đặc tả kỹ thuật và lộ trình triển khai chi tiết (Project Specification & Implementation Plan) định dạng Markdown (`.md`).

Bạn có thể copy nội dung này, lưu thành file `README.md` hoặc `SPEC.md` trong thư mục gốc của dự án để tiện theo dõi tiến độ và dùng làm sườn cho báo cáo cuối kỳ.

---

````markdown
# SPECIFICATION & PLAN: JOB RECOMMENDATION SYSTEM

**Project Name:** Intelligent Job Matching System
**Author:** [Tên Của Bạn]
**Date:** [Ngày bắt đầu]
**Tech Stack:** Python, Streamlit, Scikit-learn, Sentence-Transformers, Pandas.

---

## I. TỔNG QUAN (Overview)

Xây dựng hệ thống gợi ý việc làm dựa trên nội dung (Content-Based Filtering). Hệ thống phân tích mô tả công việc (Job Description) và so khớp với kỹ năng/mong muốn của người dùng để đưa ra các gợi ý phù hợp nhất bằng công nghệ Vector Search (Embeddings).

### Mục tiêu

1.  **Input:** Người dùng nhập kỹ năng hoặc tiêu đề mong muốn (ví dụ: "Python Backend Developer").
2.  **Process:** Hệ thống vector hóa input và tìm kiếm trong cơ sở dữ liệu việc làm.
3.  **Output:** Danh sách Top-K công việc phù hợp nhất, kèm theo độ tương đồng (Similarity Score).

---

## II. KIẾN TRÚC HỆ THỐNG (System Architecture)

### 1. Cấu trúc thư mục (Directory Structure)

Tuân thủ mô hình Clean Architecture đơn giản hóa cho Data Science.

```text
job-recommendation-system/
├── data/
│   ├── raw/                 # Chứa file CSV gốc (VD: linkedin_jobs.csv)
│   └── processed/           # Chứa file đã làm sạch & file vectors (.pkl)
├── notebooks/               # Jupyter Notebooks để nháp và vẽ biểu đồ
├── src/                     # Source code logic chính
│   ├── loader.py            # Hàm load dữ liệu
│   ├── preprocessing.py     # Hàm xử lý text (NLP cleaning)
│   └── recommender.py       # Hàm tính toán Similarity & Vectorization
├── app.py                   # Main UI (Streamlit)
├── requirements.txt         # Danh sách thư viện
└── README.md                # Tài liệu này
```
````

### 2\. Công nghệ sử dụng (Tech Stack)

- **Ngôn ngữ:** Python 3.9+
- **Data Processing:** Pandas, NumPy.
- **NLP & Vectorization:**
  - _Cơ bản:_ Scikit-learn (TF-IDF).
  - _Nâng cao:_ Sentence-Transformers (HuggingFace models).
- **Recommendation Core:** Cosine Similarity.
- **User Interface:** Streamlit.
- **Visualization:** Matplotlib / Seaborn.

---

## III. LUỒNG XỬ LÝ DỮ LIỆU (Data Pipeline)

### Bước 1: Thu thập & Tiền xử lý (Data Preprocessing)

- **Nguồn dữ liệu:** LinkedIn Job Postings (\> 2.000 bản ghi).
- **Làm sạch (Cleaning):**
  - Xử lý giá trị `NULL` (Fill 'Unknown').
  - Loại bỏ các bản ghi trùng lặp (Drop duplicates).
  - Gộp các cột text quan trọng: `content = job_title + " " + job_description`.
- **Chuẩn hóa Text (NLP):**
  - Chuyển về chữ thường (Lowercase).
  - Loại bỏ ký tự đặc biệt, dấu câu, HTML tags.
  - Loại bỏ Stop-words (the, a, an, is...).

### Bước 2: Vector hóa (Feature Engineering)

- Sử dụng mô hình **`all-MiniLM-L6-v2`** (hoặc TF-IDF) để biến đổi cột `content` thành ma trận Vector.
- Lưu trữ ma trận này (hoặc tính toán in-memory khi chạy app) để tái sử dụng.

### Bước 3: Cơ chế Gợi ý (Inference)

1.  Nhận `user_query` từ giao diện.
2.  Tiền xử lý & Vector hóa `user_query` (dùng cùng model với Bước 2).
3.  Tính **Cosine Similarity** giữa `vector_query` và `Matrix_Jobs`.
4.  Sắp xếp giảm dần theo điểm số (Score).
5.  Lấy Top 5-10 kết quả.

---

## IV. KẾ HOẠCH TRIỂN KHAI CHI TIẾT (10 Ngày)

### Giai đoạn 1: Dữ liệu & Phân tích (Ngày 1 - 3)

- [ ] **Ngày 1: Setup & Load Data**
  - Tạo cấu trúc thư mục git.
  - Tải dataset LinkedIn Jobs từ Kaggle.
  - Viết hàm `load_data()` trong `src/loader.py`.
- [ ] **Ngày 2: Làm sạch dữ liệu (Data Cleaning)**
  - Xử lý Missing Values & Duplicates.
  - Viết hàm `clean_text()` trong `src/preprocessing.py`.
  - Lưu file sạch vào `data/processed/clean_jobs.csv`.
- [ ] **Ngày 3: EDA & Trực quan hóa**
  - Vẽ biểu đồ phân bố Job theo Location.
  - Vẽ WordCloud các kỹ năng phổ biến.
  - Xuất biểu đồ ra folder `images/` để làm báo cáo.

### Giai đoạn 2: Xây dựng Model (Ngày 4 - 6)

- [ ] **Ngày 4: Vector hóa (Core Logic)**
  - Cài đặt `sentence-transformers`.
  - Viết logic tạo embeddings cho toàn bộ dataset.
- [ ] **Ngày 5: Xây dựng hàm Recommend**
  - Viết hàm `get_recommendations(query, df, vectors)` trong `src/recommender.py`.
  - Tính toán Cosine Similarity.
  - Test thử nghiệm trong Notebook với các input mẫu.
- [ ] **Ngày 6: Tối ưu & Đánh giá**
  - Kiểm tra kết quả thủ công (Human Evaluation).
  - Điều chỉnh tiền xử lý nếu kết quả chưa chính xác.

### Giai đoạn 3: Giao diện & Hoàn thiện (Ngày 7 - 9)

- [ ] **Ngày 7: Streamlit UI cơ bản**
  - Tạo Input Box (Search).
  - Hiển thị kết quả dạng Bảng (DataFrame) hoặc Cards.
- [ ] **Ngày 8: Tính năng Nâng cao (Context-Aware)**
  - Thêm bộ lọc Sidebar: Chọn Location, Chọn mức lương (nếu có).
  - Kết hợp logic: `Recommend List` AND `Filter Conditions`.
- [ ] **Ngày 9: Viết báo cáo**
  - Soạn thảo file Word/PDF.
  - Chụp ảnh màn hình App.
  - Giải thích thuật toán Vector Search.

### Giai đoạn 4: Đóng gói (Ngày 10)

- [ ] **Ngày 10: Final Polish**
  - Quay video demo (3-5 phút).
  - Clean code, thêm comments.
  - Zip toàn bộ project theo đúng quy cách nộp bài.

---

## V. YÊU CẦU PHẦN MỀM (Dependencies)

Nội dung file `requirements.txt`:

```text
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
sentence-transformers==2.2.2
streamlit==1.25.0
matplotlib==3.7.2
seaborn==0.12.2
wordcloud==1.9.2
```

```

```
