from pathlib import Path
from pydantic import BaseModel, field_validator, Field, ValidationInfo
import yaml
from typing import Literal, Annotated

class AppParams(BaseModel):
    inv: Literal[True, False, "auto"] = "auto"
    point_start: float = 0
    point_end: float = 5000
    point_cut: float = 2500
    freq_cut: int = 10800
    num_pts_norm: int = 20
    data_type: str = "refl"
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
    
    def write_default_init_file(self) -> None:
        config = AppParams()
        data = config.model_dump(mode='json', exclude_none=True)

        with open(self.path, 'w') as f:
            yaml.dump(
                data,
                f,
                sort_keys=False,
                default_flow_style=False,
                allow_unicode=True,
                encoding='utf-8'
            )
