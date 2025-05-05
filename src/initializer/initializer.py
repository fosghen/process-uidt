from pathlib import Path
from pydantic import BaseModel, field_validator, Field, ValidationInfo
import yaml
from typing import Literal, Annotated

class AppParams(BaseModel):
    inv: Literal[True, False, "auto"]
    point_start: float
    point_end: float
    point_cut: float
    freq_cut: int
    num_pts_norm: int
    transparency: Annotated[float, Field(ge=0, le=1)] = 0.6 
    
    @field_validator('point_start')
    def validate_point_start(cls, v: float, info: ValidationInfo) -> float:
        if 'point_end' in info.data and v > info.data['point_end']:
            raise ValueError("Начало не может быть правее конца")
        if 'point_cut' in info.data and v > info.data['point_cut']:
            raise ValueError("Начало не может быть правее среза")
        return v
    
    @field_validator('point_end')
    def validate_point_end(cls, v: float, info: ValidationInfo) -> float:
        if 'point_cut' in info.data and v < info.data['point_start']:
            raise ValueError("Конец не может быть левее старта.")
        if 'point_cut' in info.data and v < info.data['point_cut']:
            raise ValueError("Конец не может быть левее среза.")
        return v
    
class Reader:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read_init_file(self) -> AppParams:
        with self.path.open() as f:
            data = yaml.safe_load(f)
        return AppParams(**data)
