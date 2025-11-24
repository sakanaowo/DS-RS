# Data Audit – Intelligent Job Matching System 
 
- Audit date (UTC): 2025-11-23 
- Snapshot: data/archive (copied to data/raw trước khi xử lý). 
- Công cụ: notebooks/1_data_cleaning.ipynb + pandas." 
 
## Tổng quan postings.csv 
- Số bản ghi: 123,849 
- Số cột: 31 
 
### Top cột thiếu dữ liệu 
- closed_time: 99.1% thiếu 
- skills_desc: 98.0% thiếu 
- med_salary: 94.9% thiếu 
- remote_allowed: 87.7% thiếu 
- applies: 81.2% thiếu 
- min_salary: 75.9% thiếu 
- max_salary: 75.9% thiếu 
- currency: 70.9% thiếu 
- compensation_type: 70.9% thiếu 
- pay_period: 70.9% thiếu 
 
### Phân bố pay_period 
- Missing: 87,776 (70.9%) 
- YEARLY: 20,628 (16.7%) 
- HOURLY: 14,741 (11.9%) 
- MONTHLY: 518 (0.4%) 
- WEEKLY: 177 (0.1%) 
- BIWEEKLY: 9 (0.0%) 
 
### Phân bố formatted_work_type 
- Full-time: 98,814 (79.8%) 
- Contract: 12,117 (9.8%) 
- Part-time: 9,696 (7.8%) 
- Temporary: 1,190 (1.0%) 
- Internship: 983 (0.8%) 
- Volunteer: 562 (0.5%) 
- Other: 487 (0.4%) 
 
### remote_allowed & cách hiểu 
- Missing: 108,603 (87.7%) 
- 1.0: 15,246 (12.3%) 
 
### Top địa điểm đăng tuyển 
- United States: 8,125 (6.6%) 
- New York, NY: 2,756 (2.2%) 
- Chicago, IL: 1,834 (1.5%) 
- Houston, TX: 1,762 (1.4%) 
- Dallas, TX: 1,383 (1.1%) 
- Atlanta, GA: 1,363 (1.1%) 
- Boston, MA: 1,176 (0.9%) 
- Austin, TX: 1,083 (0.9%) 
- Charlotte, NC: 1,075 (0.9%) 
- Phoenix, AZ: 1,059 (0.9%) 
 
## Top nhóm kỹ năng 
- Information Technology: 26,137 
- Sales: 22,475 
- Management: 20,861 
- Manufacturing: 18,185 
- Health Care Provider: 17,369 
- Business Development: 14,290 
- Engineering: 13,009 
- Other: 12,608 
- Finance: 8,540 
- Marketing: 5,525 
 
## Top ngành nghề 
- Hospitals and Health Care: 18,326 
- Retail: 11,033 
- IT Services and IT Consulting: 10,396 
- Staffing and Recruiting: 9,005 
- Financial Services: 8,535 
- Software Development: 5,091 
- Manufacturing: 3,689 
- Construction: 3,445 
- Banking: 2,923 
- Insurance: 2,673 
 
## Lương 
- YEARLY: 23,768 (58.3%) 
- HOURLY: 16,289 (39.9%) 
- MONTHLY: 539 (1.3%) 
- WEEKLY: 180 (0.4%) 
- BIWEEKLY: 9 (0.0%) 
- Trung bình min_salary: 65,085 
- Trung bình max_salary: 96,210 
- Trung bình med_salary: 21,370 
 
## Benefits overview 
- Tổng bản ghi benefits: 67,943 
- Số job có >=1 benefit: 30,023 (24.2% postings) 
- Trung bình benefits/job: 2.26 
 
### Top lợi ích 
- 401(k): 24,231 
- Medical insurance: 9,873 
- Vision insurance: 9,309 
- Disability insurance: 7,930 
- Dental insurance: 6,868 
- Tuition assistance: 2,614 
- Commuter benefits: 2,226 
- Paid maternity leave: 1,808 
- Paid paternity leave: 1,540 
- Pension plan: 906 
 
## Metadata công ty 
- Tổng số công ty: 24,473 
- Công ty có thống kê employee_count: 24,473 
- Trung bình employee_count: 6,716 
- Trung bình follower_count: 201,262 
 
### Top quốc gia 
- US: 21,635 (88.4%) 
- 0: 727 (3.0%) 
- GB: 620 (2.5%) 
- CA: 258 (1.1%) 
- IN: 157 (0.6%) 
 
### Top bang/tỉnh (state) 
- 0: 2,175 (8.9%) 
- California: 1,747 (7.1%) 
- CA: 1,401 (5.7%) 
- Texas: 1,276 (5.2%) 
- NY: 977 (4.0%) 
 
### Phân bố company_size 
- 2.0: 4,956 (20.3%) 
- 1.0: 4,348 (17.8%) 
- 5.0: 3,918 (16.0%) 
- 3.0: 3,108 (12.7%) 
- Unknown: 2,774 (11.3%) 
 
### Top specialities khai báo 
- Engineering: 601 
- Recruiting: 581 
- Staffing: 578 
- Technology: 529 
- Consulting: 492 
- Healthcare: 445 
- Manufacturing: 420 
- Marketing: 416 
- Project Management: 379 
- Information Technology: 376 
 
## Insight chính 
- ~71% bản ghi thiếu thông tin lương ⇒ cần flag `has_salary_info` và chiến lược suy luận/ẩn cột khi huấn luyện. 
- Remote flag chỉ hiện diện cho ~12% job ⇒ default coi là onsite/unknown, cần bổ sung nhãn rõ ràng trong UI. 
- Nhóm kỹ năng/industry nghiêng mạnh về IT, Healthcare, Sales ⇒ nên chuẩn bị cân bằng hoặc weight theo lĩnh vực. 
- Chỉ ~24% job khai báo benefits ⇒ khi hiển thị nên ghi chú “Không cung cấp” thay vì để trống. 
- Metadata công ty phong phú (24k công ty, 169k bản ghi speciality) ⇒ có thể dùng để tạo filter/phần mô tả mở rộng. 