from pydantic import BaseModel


class IndicatorRecord(BaseModel):
    year: int
    gdp_growth: float | None = None
    inflation: float | None = None
    unemployment: float | None = None
    poverty: float | None = None