from typing import Self

import httpx
from pydantic import BaseModel

from .console import console
from .error import CookieExpiredError, GetTimeInfoError
from .login import get_headers


class TimeInfo(BaseModel):
    academic_year: str
    term: str
    current_academic_year: str
    current_term: str

    @classmethod
    def get(cls, cookies: str) -> Self:
        """获取当前及选课学年学期信息

        Args:
            cookies (str)

        Returns:
            TimeInfo

        Raises:
            CookieExpiredError: Cookie 失效时抛出
            GetTimeInfoError: 发生其它错误时抛出
        """
        headers = get_headers(cookies)
        url = "http://jw.hitsz.edu.cn/Xsxk/queryXkdqXnxq"
        data = {"mxpylx": "1"}
        response = httpx.post(url, headers=headers, data=data, follow_redirects=True)
        if response.status_code == 200:
            if "application/json" in response.headers["Content-Type"]:
                response_json = response.json()
                try:
                    current_academic_year = response_json["p_dqxn"]
                    current_term = response_json["p_dqxq"]
                    academic_year = response_json["p_xn"]
                    term = response_json["p_xq"]
                    console.print("[green]成功获取时间信息")
                    return cls(
                        current_academic_year=current_academic_year,
                        current_term=current_term,
                        academic_year=academic_year,
                        term=term,
                    )
                except KeyError:
                    message = response_json["message"]
                    raise GetTimeInfoError(f"[red]时间信息获取失败：{message}")
            elif "text/html" in response.headers["Content-Type"]:
                raise CookieExpiredError()
            else:
                raise GetTimeInfoError("[red]响应内容不是有效的 JSON 格式")
        else:
            raise GetTimeInfoError(f"[red]请求失败，状态码：{response.status_code}")
