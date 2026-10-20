# Kế hoạch thực hiện đồ án: Context-aware ASR

Hạn nộp: **Chủ nhật 15/11/2026**. Bắt đầu 20/10/2026, còn khoảng 26 ngày.
Hướng đồ án: **nghiên cứu** (có ablation study). Yêu cầu nộp bài: xem `project_requirements.md`. Nội dung nền: xem `topic_overview.md`.

## 1. Phân công

Tên thành viên là placeholder, thay bằng tên thật sau.

| Thành viên | Phần report/slide | Vai trò kỹ thuật | Paper kỹ thuật |
|---|---|---|---|
| TV1 | Tổng quan + Group A | **Demo** | CTC-WS (setup NeMo) |
| TV2 | Group B (B1 + B2) | **Demo** | CopyNE |
| TV3 | Group C | **Ablation** (làm sau TV1) | CTC-WS |
| TV4 | Group D (D1 + D2) | **Ablation** (làm sau TV2) | CopyNE |

- Mỗi người đọc 1-3 paper uy tín, milestone hoặc mới nhất của group mình, rồi viết phần report và slide tương ứng.
- Nhóm demo làm trước để dựng môi trường. Nhóm ablation dùng lại môi trường đó để chạy ablation.
- Phần phân tích chuyên sâu và đề xuất cải tiến làm chung cả nhóm.

## 2. Hai paper đề xuất để demo và ablation

Điều kiện chọn: thuộc Group B hoặc C, có public source code, chạy được trên Google Colab / Kaggle free (T4, khoảng 16 GB VRAM).

| | Paper 1: CTC-based Word Spotter (CTC-WS) | Paper 2: CopyNE |
|---|---|---|
| Group | C (Post-recognition Correction) | B1 (Dedicated Biasing Modules) |
| Venue | Interspeech 2024 | ACL 2024 (A\*) |
| Code | Official trong [NeMo](https://github.com/NVIDIA/NeMo) (Apache-2.0); tutorial `ASR_Context_Biasing.ipynb` | [zsLin177/CopyNE](https://github.com/zsLin177/CopyNE); README có checkpoint trên Google Drive và demo Gradio; license chưa ghi |
| Vì sao hợp T4 free | Không cần train, chỉ inference; model FastConformer cỡ vài trăm triệu tham số | Chỉ cần evaluate với checkpoint có sẵn; README dùng 1 GPU cho evaluate |
| Dữ liệu | LibriSpeech test (English) + rare-word list từ [is21_deep_bias](https://github.com/facebookresearch/fbai-speech/tree/master/is21_deep_bias) | AISHELL-1 (Mandarin) + NE dictionary từ repo |
| Ablation dự kiến | `context_score`, `beam_threshold`, `ctc_ali_token_weight`; kích thước bias list (100/500/1000 distractors); thêm hoặc bớt spelling variants; bật/tắt CTC-WS | Kích thước dictionary (số distractors); các tham số của copy-attention decoding (xác định sau khi đọc code); bật/tắt copy so với decode thường |
| Metric | WER, B-WER/U-WER, phrase precision/recall/F1, false alarm | CER, NE-CER |

**Rủi ro đã biết:**
- Chưa mở link Google Drive của checkpoint CopyNE và chưa xác nhận tutorial `ASR_Context_Biasing.ipynb` chạy được trên Colab. Việc này kiểm tra ở M0.
- CopyNE là tiếng Trung. Setup của hai paper khác nhau, nên "dùng lại setup" chỉ áp dụng cho từng cặp (TV1→TV3, TV2→TV4).
- CopyNE train cần 4 GPU. Với T4 free, ablation chỉ ở mức inference, không train lại.
- Repo CopyNE, README không nêu tên framework hay license, cần đọc code.
- AISHELL-1 nặng (khoảng 15 GB), cần lưu trên Drive/Kaggle Dataset để khỏi tải lại mỗi phiên.
- Giới hạn Colab free: phiên tối đa vài giờ và có thể ngắt; cần lưu checkpoint và kết quả ra Drive thường xuyên. Kaggle free có giới hạn giờ GPU mỗi tuần.

**Phương án dự phòng nếu M0 thất bại:**
- Thay CopyNE bằng TCPGen-Whisper ([WhisperBiasing](https://github.com/BriansIDP/WhisperBiasing)) hoặc CTC-Assisted LLM (SLAM-LLM, cần lượng tử hóa 4-bit cho Vicuna-7B và có thể dùng Kaggle 2×T4).
- Hai phương án này nặng hơn nên chỉ dùng khi CopyNE không chạy được.
- Nếu cả hai thất bại: dùng sherpa-onnx hotwords (Group A, chạy CPU).

## 3. Milestone

| # | Hạn | Mục tiêu | Sản phẩm / tiêu chí xong |
|---|---|---|---|
| **M0** | 20/10 – 23/10 | Khởi động và kiểm tra khả thi | Tạo folder `report/`, `slides/`, `code/`, `data/`, `video/`. TV1 chạy được tutorial CTC-WS trên Colab; TV2 tải được checkpoint CopyNE và chạy được `evaluate` trên vài câu. **Cuối 23/10 quyết định giữ hoặc đổi paper** |
| **M1** | 24/10 – 27/10 | Đọc paper và dựng môi trường | Mỗi người có ghi chú cho 1-3 paper của group (tóm tắt, ưu/nhược điểm). Demo chạy baseline trên tập test nhỏ. Notebook setup commit vào `code/` kèm hướng dẫn chạy lại |
| **M2** | 28/10 – 1/11 | Demo hoàn chỉnh; chốt thiết kế ablation | Demo chạy đủ trên tập test, có số liệu baseline và `README` chạy lại được. Nhóm ablation chạy lại setup độc lập để xác nhận. Tài liệu thiết kế ablation (biến số, giá trị, metric) được hai người của cặp thống nhất. Bản nháp report/slide phần group của mỗi người |
| **M3** | 2/11 – 8/11 | Chạy ablation | Bảng kết quả ablation cho cả hai paper, lưu notebook và log. Báo cáo ngắn về những điều bất thường |
| **M4** | 9/11 – 11/11 | Phân tích chuyên sâu (chung) | Chọn 1 giải pháp phân tích sâu, đề xuất cải tiến; ghép các phần vào một report và một bộ slide |
| **M5** | 12/11 – 13/11 | Video và đóng gói | Video 10-15 phút (thuyết trình + demo); report PDF (có danh sách nhóm và phân công); slide PDF; folder sản phẩm. Một người ngoài phần mình kiểm tra chạy lại code theo hướng dẫn |
| **Buffer** | 14/11 – 15/11 | Sửa lỗi cuối và nộp | Nộp trước 15/11 |

Ghi chú:
- Hai nhóm làm lệch nhau: nhóm ablation bắt đầu từ M2 (xác nhận setup), chạy chính ở M3.
- Mốc M0 là cổng quyết định. Nếu đến 23/10 một trong hai paper chưa chạy được thì chuyển sang phương án dự phòng ngay, không kéo sang M1.

## 4. Gợi ý paper đọc cho từng group

Chọn 1-3 paper cho mỗi group. Tiêu chí khảo sát (30%) cần **ít nhất 5 paper trên tạp chí Q1/Q2 hoặc hội nghị A/A\*** trong 3-5 năm gần đây. Các paper dưới đây lấy từ `topic_overview.md`; ICASSP (B) và arXiv không tính vào ngưỡng này.

| Group | Người | Gợi ý |
|---|---|---|
| Tổng quan + A | TV1 | Zhao 2019 (milestone, Interspeech); Le et al. 2021 (Interspeech); TurboBias (arXiv, chỉ để tham khảo) |
| B | TV2 | CLAS 2018 (milestone); TCPGen+MBWE (TASLP, Q1); CopyNE (ACL 2024, A\*) |
| C | TV3 | CTC-WS (Interspeech 2024); DARAG (Findings ACL 2025); Generative Annotation (EMNLP 2025) |
| D | TV4 | BR-ASR (Interspeech 2025); Retrieve and Copy (EMNLP 2023 Industry); RECAST (Findings EMNLP 2025) |

Tổng cộng có ít nhất 10 paper đủ ngưỡng A/A\*/Q1 nếu mỗi người chọn đủ 2-3 paper như trên.

## 5. Ánh xạ tiêu chí chấm điểm

| Tỉ trọng | Tiêu chí | Ai phụ trách | Hoàn thành ở |
|---|---|---|---|
| 30% | Khảo sát ≥ 5 paper, tóm tắt, ưu/nhược điểm | TV1-TV4 (mỗi người một group) | M1, M2 (bản nháp), M4 (ghép) |
| 20% | Chạy demo | TV1 (CTC-WS), TV2 (CopyNE) | M2 |
| 30% | Ablation study | TV3 (CTC-WS), TV4 (CopyNE) | M3 |
| 20% | Phân tích chuyên sâu 1 giải pháp + đề xuất cải tiến | Cả nhóm | M4 |

## 6. Cấu trúc folder nộp

```
final_project/
├── report/            # báo cáo PDF (danh sách nhóm + phân công)
├── slides/            # slide PDF
├── video/             # video 10-15 phút
├── code/
│   ├── ctc_ws/        # notebook demo + ablation
│   └── copyne/        # notebook demo + ablation
├── data/              # hoặc link tải (dữ liệu lớn để trên Drive/Kaggle)
└── README.md          # hướng dẫn chạy lại
```

## 7. Cách làm việc

- Họp ngắn hai lần mỗi tuần (ví dụ thứ 3 và thứ 6) để cập nhật tiến độ và tháo gỡ vướng mắc.
- Một repo chung. Mỗi người làm trên branch riêng và gộp qua pull request.
- Notebook phải chạy được từ đầu trên Colab hoặc Kaggle, ghi rõ phiên bản thư viện và seed.
- Kết quả và log lưu ra Drive hoặc `results/` ngay sau mỗi lần chạy.
- Số liệu nào trích từ paper phải ghi rõ là "author-reported", không trộn với số do nhóm tự chạy.
