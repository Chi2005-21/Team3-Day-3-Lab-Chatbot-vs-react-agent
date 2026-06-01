# Use Case Examples — `search_flights` & `generate_invoice`

---

## Use Case 1: Tìm chuyến bay một chiều và tạo hóa đơn

**Kịch bản:** Khách muốn bay từ Hà Nội (HAN) → TP.HCM (SGN), 1 người, ngày 2026-07-10.

```python
from src.tools.flight_tools import search_flights
from src.tools.invoice_tools import generate_invoice

# Bước 1 — Tìm chuyến bay
result = search_flights(
    departure_airport="HAN",
    arrival_airport="SGN",
    departure_date="2026-07-10",
    passengers=1,
    travel_class="economy",
    currency="USD",
)

# Bước 2 — Khách chọn chuyến đầu tiên
chosen = result["flights"][0]

# Bước 3 — Tạo hóa đơn
invoice = generate_invoice(
    passenger_name="Nguyen Van A",
    passenger_email="vana@email.com",
    passenger_phone="0901234567",
    flight_id=chosen["flight_id"],
    airline=chosen["airline"],
    departure_airport=chosen["departure_airport"] if "departure_airport" in chosen else "HAN",
    arrival_airport=chosen["arrival_airport"] if "arrival_airport" in chosen else "SGN",
    departure_time=chosen["departure_time"],
    arrival_time=chosen["arrival_time"],
    duration=chosen["duration"],
    stops=chosen["stops"],
    stop_info=chosen.get("stop_info"),
    travel_class="economy",
    passengers=1,
    price_per_person=chosen["price"],
    currency=chosen["currency"],
    booking_link=chosen["booking_link"],
)

print(invoice["receipt_text"])
# → In hóa đơn đẹp ra chat
# → invoice["booking_ref"] = "BK-A1B2C3D4"
```

---

## Use Case 2: Tìm vé Business Class cho 2 người

**Kịch bản:** Cặp đôi bay từ Hà Nội (HAN) → Paris (CDG), hạng thương gia.

```python
result = search_flights(
    departure_airport="HAN",
    arrival_airport="CDG",
    departure_date="2026-08-15",
    passengers=2,
    travel_class="business",
    currency="USD",
)

chosen = result["flights"][0]

invoice = generate_invoice(
    passenger_name="Tran Thi B",
    passenger_email="thib@email.com",
    flight_id=chosen["flight_id"],
    airline=chosen["airline"],
    departure_airport="HAN",
    arrival_airport="CDG",
    departure_time=chosen["departure_time"],
    arrival_time=chosen["arrival_time"],
    duration=chosen["duration"],
    stops=chosen["stops"],
    stop_info=chosen.get("stop_info"),
    travel_class="business",
    passengers=2,                        # ← 2 người
    price_per_person=chosen["price"],    # giá/người, tổng tự tính
    currency=chosen["currency"],
    booking_link=chosen["booking_link"],
)

# Tổng tiền = price_per_person × 2 + 5% phí dịch vụ
print(invoice["invoice_data"]["pricing"]["total_price"])
```

---

## Use Case 3: Tìm + Tạo hóa đơn + Xuất PDF

**Kịch bản:** Khách muốn nhận file PDF để lưu lại.

```python
from src.tools.invoice_tools import generate_invoice, generate_invoice_pdf

result = search_flights(
    departure_airport="SGN",
    arrival_airport="NRT",   # Tokyo Narita
    departure_date="2026-09-01",
    passengers=1,
    travel_class="economy",
    currency="USD",
)

chosen = result["flights"][0]

# Bước 1 — Tạo hóa đơn text
invoice = generate_invoice(
    passenger_name="Le Van C",
    passenger_email="levanc@email.com",
    passenger_phone="0912345678",
    flight_id=chosen["flight_id"],
    airline=chosen["airline"],
    departure_airport="SGN",
    arrival_airport="NRT",
    departure_time=chosen["departure_time"],
    arrival_time=chosen["arrival_time"],
    duration=chosen["duration"],
    stops=chosen["stops"],
    stop_info=chosen.get("stop_info"),
    travel_class="economy",
    passengers=1,
    price_per_person=chosen["price"],
    currency=chosen["currency"],
    booking_link=chosen["booking_link"],
)

# Bước 2 — Xuất PDF
pdf_result = generate_invoice_pdf(
    invoice_result=invoice,
    output_path=f"invoices/{invoice['booking_ref']}.pdf",
)

print(f"PDF đã lưu tại: {pdf_result['pdf_path']}")
# → "PDF đã lưu tại: D:\...\invoices\BK-XXXX.pdf"
```

---

## Use Case 4: Không tìm thấy chuyến bay — xử lý lỗi

**Kịch bản:** Agent cần bắt trường hợp không có kết quả.

```python
result = search_flights(
    departure_airport="HAN",
    arrival_airport="LAX",
    departure_date="2026-12-25",
    passengers=1,
    travel_class="first",
    currency="USD",
)

if result["count"] == 0:
    print(result["message"])
    # → "Không tìm thấy chuyến bay phù hợp với yêu cầu."
else:
    # tiếp tục flow đặt vé...
    chosen = result["flights"][0]
```