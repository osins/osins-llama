from pydantic import ConfigDict, Field
from typing import Optional
from ..common.base_model import BaseDataModel


class StreamOptions(BaseDataModel):
    """
    Stream Options 数据模型
    表示流式响应的选项，严格遵循 OpenAI ChatCompletions API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    include_usage: Optional[bool] = Field(
        default=False,
        description="If set, an additional chunk will be streamed before the data: [DONE] message. The usage field on this chunk shows the token usage statistics for the entire request, and the choices field will be an empty array."
    )
