import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError, field_validator

# ---------------------------------------------------------------------------
# Tìm data.json: ưu tiên thư mục gốc dự án (2 cấp trên src/tools/)
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent          # src/tools/
_MOCK_DATA_PATH = _THIS_DIR.parent.parent / "data.json"  # project_root/data.json

_MOCK_DATA: Dict[str, Any] = {}
if _MOCK_DATA_PATH.exists():
    with open(_MOCK_DATA_PATH, encoding="utf-8") as _f:
        _MOCK_DATA = json.load(_f)
else:
    import warnings
    warnings.warn(f"[flight_tools] Không tìm thấy mock data tại {_MOCK_DATA_PATH}")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class FlightSearchParams(BaseModel):
    departure_airport: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="IATA code sân bay khởi hành",
    )
    arrival_airport: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="IATA code sân bay đến",
    )
    departure_date: str = Field(
        ...,
        description="Ngày khởi hành theo định dạng YYYY-MM-DD",
    )
    return_date: Optional[str] = Field(
        None,
        description="Ngày về theo định dạng YYYY-MM-DD nếu có",
    )
    passengers: int = Field(
        default=1,
        ge=1,
        le=9,
        description="Số hành khách",
    )
    travel_class: str = Field(
        default="economy",
        description="Hạng vé: economy, business, first, premium_economy",
    )
    currency: str = Field(
        default="USD",
        description="Đơn vị tiền tệ trả về kết quả",
    )

    @field_validator("departure_airport", "arrival_airport", mode="before")
    @classmethod
    def _normalize_airport(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("Mã sân bay phải là chuỗi")
        code = value.strip().upper()
        if len(code) != 3 or not code.isalpha():
            raise ValueError("Mã sân bay phải là 3 chữ cái IATA, ví dụ HAN, SGN")
        return code

    @field_validator("departure_date", "return_date", mode="before")
    @classmethod
    def _validate_date_format(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Ngày phải là chuỗi theo định dạng YYYY-MM-DD")
        try:
            datetime.strptime(value.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Ngày phải có định dạng YYYY-MM-DD")
        return value.strip()

    @field_validator("travel_class", mode="before")
    @classmethod
    def _validate_travel_class(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("Hạng vé phải là chuỗi")
        normalized = value.strip().lower()
        valid = {"economy", "business", "first", "premium_economy"}
        if normalized not in valid:
            raise ValueError(f"Hạng vé phải là một trong: {', '.join(sorted(valid))}")
        return normalized

    @field_validator("currency", mode="before")
    @classmethod
    def _normalize_currency(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("Đơn vị tiền tệ phải là chuỗi")
        return value.strip().upper()

    def validate_business_rules(self) -> None:
        departure = datetime.strptime(self.departure_date, "%Y-%m-%d").date()
        if departure < datetime.now().date():
            raise ValueError("Ngày khởi hành không được ở quá khứ")
        if self.return_date:
            return_date = datetime.strptime(self.return_date, "%Y-%m-%d").date()
            if return_date <= departure:
                raise ValueError("Ngày về phải sau ngày khởi hành")


class FlightResult(BaseModel):
    flight_id: str = Field(..., description="ID chuyến bay")
    airline: str = Field(..., description="Hãng hàng không")
    departure_time: str = Field(..., description="Giờ cất cánh")
    arrival_time: str = Field(..., description="Giờ hạ cánh")
    duration: str = Field(..., description="Thời gian bay")
    stops: int = Field(..., ge=0, description="Số điểm dừng")
    stop_info: Optional[str] = Field(None, description="Thông tin điểm dừng")
    price: float = Field(..., gt=0, description="Giá vé")
    currency: str = Field(..., description="Đơn vị tiền tệ")
    booking_link: str = Field(..., description="Link đặt vé")
    airline_logo: Optional[str] = Field(None, description="Logo hãng hàng không")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Đánh giá hãng hàng không")


class FlightSearchException(Exception):
    pass


# ---------------------------------------------------------------------------
# Helpers để parse một item trong best_flights / other_flights của data.json
# ---------------------------------------------------------------------------

def _minutes_to_hhmm(minutes: int) -> str:
    """Chuyển số phút thành chuỗi 'Xh Ym'."""
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m}m" if m else f"{h}h"


def _parse_mock_option(option: Dict[str, Any], params: FlightSearchParams) -> Optional[FlightResult]:
    """
    Parse một phần tử từ best_flights / other_flights của data.json thành FlightResult.
    Cấu trúc mỗi option:
      {
        "flights": [ { "departure_airport": {...}, "arrival_airport": {...},
                       "airline": "...", "airline_logo": "...", "duration": <int minutes>, ... }, ... ],
        "layovers": [ { "name": "...", "id": "..." }, ... ],
        "total_duration": <int minutes>,
        "price": <number>,
        "airline_logo": "...",
        "booking_token": "..."
      }
    """
    segments: List[Dict[str, Any]] = option.get("flights", [])
    if not segments:
        return None

    price = option.get("price")
    if price is None:
        return None
    try:
        price = float(price)
    except (TypeError, ValueError):
        return None

    first_seg = segments[0]
    last_seg = segments[-1]

    departure_time = (first_seg.get("departure_airport") or {}).get("time", "Unknown")
    arrival_time = (last_seg.get("arrival_airport") or {}).get("time", "Unknown")

    total_duration = option.get("total_duration")
    duration_str = _minutes_to_hhmm(total_duration) if total_duration else "N/A"

    stops = max(0, len(segments) - 1)

    layovers = option.get("layovers", [])
    stop_info = None
    if layovers:
        stop_info = ", ".join(lay.get("name", lay.get("id", "?")) for lay in layovers)

    # Lấy hãng hàng không từ segment đầu tiên
    airline = first_seg.get("airline", "Unknown")

    # Logo ưu tiên từ option-level, fallback về segment đầu
    airline_logo = option.get("airline_logo") or first_seg.get("airline_logo")

    # booking_token dùng làm booking_link (không có URL thực trong mock data)
    booking_token = option.get("booking_token", "")
    booking_link = (
        f"https://www.google.com/travel/flights?booking_token={booking_token}"
        if booking_token
        else "https://www.google.com/travel/flights"
    )

    # Tạo flight_id duy nhất từ hash option
    flight_id = f"flight-{abs(hash(booking_token or str(option))) % 1_000_000}"

    return FlightResult(
        flight_id=flight_id,
        airline=airline,
        departure_time=departure_time,
        arrival_time=arrival_time,
        duration=duration_str,
        stops=stops,
        stop_info=stop_info,
        price=price,
        currency=params.currency,
        booking_link=booking_link,
        airline_logo=airline_logo,
        rating=None,
    )


def _load_flights_from_mock(params: FlightSearchParams) -> List[FlightResult]:
    """
    Đọc dữ liệu từ _MOCK_DATA (data.json) và trả về danh sách FlightResult.
    Gộp best_flights + other_flights, tối đa 10 kết quả.
    """
    results: List[FlightResult] = []
    for section_key in ("best_flights", "other_flights"):
        for option in _MOCK_DATA.get(section_key, []):
            parsed = _parse_mock_option(option, params)
            if parsed:
                results.append(parsed)
            if len(results) >= 10:
                break
        if len(results) >= 10:
            break
    return results


# ---------------------------------------------------------------------------
# Public API — giữ nguyên signature để không phá vỡ các caller hiện có
# ---------------------------------------------------------------------------

# Các giá trị hợp lệ cho sort_by
_VALID_SORT_BY = {"price", "airline", "departure_time", "duration_minutes"}


def search_flights(
    departure_airport: str,
    arrival_airport: str,
    departure_date: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
    travel_class: str = "economy",
    currency: str = "USD",
    sort_by: str = "price",
) -> Dict[str, Any]:
    """
    Tìm kiếm chuyến bay từ mock data (data.json).
    Không gọi bất kỳ API bên ngoài nào.

    Args:
        sort_by: Sắp xếp kết quả theo tiêu chí.
                 Các giá trị hợp lệ:
                   - "price"           — giá tăng dần (mặc định)
                   - "airline"         — tên hãng A→Z
                   - "departure_time"  — giờ cất cánh sớm nhất
                   - "duration_minutes"— thời gian bay ngắn nhất
    """
    # --- Validate sort_by ---
    sort_by = sort_by.strip().lower()
    if sort_by not in _VALID_SORT_BY:
        raise FlightSearchException(
            f"sort_by không hợp lệ: '{sort_by}'. Chọn một trong: {', '.join(sorted(_VALID_SORT_BY))}"
        )

    # --- Validate params ---
    try:
        params = FlightSearchParams(
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            departure_date=departure_date,
            return_date=return_date,
            passengers=passengers,
            travel_class=travel_class,
            currency=currency,
        )
        params.validate_business_rules()
    except ValidationError as exc:
        raise FlightSearchException(f"Tham số tìm kiếm không hợp lệ: {exc}")
    except ValueError as exc:
        raise FlightSearchException(str(exc))

    if not _MOCK_DATA:
        raise FlightSearchException(
            f"Không tìm thấy mock data. Đảm bảo file data.json tồn tại tại: {_MOCK_DATA_PATH}"
        )

    # --- Load từ mock data ---
    flights = _load_flights_from_mock(params)

    # --- Sort ---
    if sort_by == "price":
        flights.sort(key=lambda f: f.price)
    elif sort_by == "airline":
        flights.sort(key=lambda f: f.airline.lower())
    elif sort_by == "departure_time":
        flights.sort(key=lambda f: f.departure_time)
    elif sort_by == "duration_minutes":
        # _MOCK_DATA lưu total_duration theo phút; parse lại từ chuỗi "Xh Ym"
        def _parse_duration(s: str) -> int:
            h = m = 0
            hm = re.match(r"(\d+)h(?:\s*(\d+)m)?", s)
            if hm:
                h = int(hm.group(1))
                m = int(hm.group(2) or 0)
            return h * 60 + m
        flights.sort(key=lambda f: _parse_duration(f.duration))

    if not flights:
        return {
            "status": "success",
            "count": 0,
            "message": "Không tìm thấy chuyến bay phù hợp với yêu cầu.",
            "query": params.model_dump(),
            "flights": [],
        }

    sort_label = {
        "price": "giá tăng dần",
        "airline": "tên hãng A→Z",
        "departure_time": "giờ khởi hành sớm nhất",
        "duration_minutes": "thời gian bay ngắn nhất",
    }[sort_by]

    return {
        "status": "success",
        "count": len(flights),
        "message": f"Tìm thấy {len(flights)} chuyến bay, sắp xếp theo {sort_label}.",
        "query": {**params.model_dump(), "sort_by": sort_by},
        "flights": [flight.model_dump() for flight in flights],
    }
