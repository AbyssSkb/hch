import random
from base64 import b64encode

import httpx
import typer
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from selectolax.parser import HTMLParser

from .config import Config
from .console import console
from .error import GetCookieError

AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"


def random_string(length: int) -> str:
    """生成指定长度的随机字符串

    该函数通过从 AES_CHARS 中随机选择字符来创建字符串。

    Args:
        length (int): 需要生成的随机字符串长度

    Returns:
        str: 指定长度的随机字符串
    """
    return "".join(random.choice(AES_CHARS) for _ in range(length))


def get_aes_string(data: str, key: str, iv: str) -> str:
    """使用 AES CBC 模式和 PKCS7 填充加密数据

    该函数对输入的明文数据使用 AES 算法进行加密，采用 CBC 工作模式和 PKCS7 填充方式，
    最后将加密结果编码为 Base64 字符串以便于传输和存储。

    Args:
        data (str): 要加密的明文数据。
        key (str): 加密密钥。
        iv (str): 初始化向量 (IV)。

    Returns:
        str: Base64 编码的密文。
    """
    key_bytes = key.encode("utf-8")
    iv_bytes = iv.encode("utf-8")
    data_bytes = data.encode("utf-8")

    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    padded_data = pad(data_bytes, AES.block_size, style="pkcs7")
    encrypted_bytes = cipher.encrypt(padded_data)

    return b64encode(encrypted_bytes).decode("utf-8")


def encrypt_password(password: str, salt: str) -> str:
    """使用 AES 加密密码

    该函数通过添加随机前缀、结合盐值和初始化向量来加密密码。
    主要用于确保密码在传输过程中的安全性。

    Args:
        password (str): 需要加密的密码明文
        salt (str): 用于加密的盐值

    Returns:
        str: 经过 Base64 编码的加密密码
    """
    prefix_random = random_string(64)
    combined_data = prefix_random + password
    iv = random_string(16)
    encrypted_result = get_aes_string(combined_data, salt, iv)
    return encrypted_result


def get_cookies(config: Config) -> str:
    username = config.username
    password = config.password

    if username is None:
        username = typer.prompt("请输入校园网账号用户名")
        config.username = username

    if password is None:
        password = typer.prompt("请输入校园网账号密码", hide_input=True)
        config.password = password

    with httpx.Client(follow_redirects=True) as client:
        response = client.get(
            "https://ids.hit.edu.cn/authserver/login",
            params={"service": "http://jw.hitsz.edu.cn/casLogin"},
        )

        tree = HTMLParser(response.text)

        selector = "div#pwdLoginDiv"
        node = tree.css_first(selector)
        if node is None:
            raise GetCookieError(f"找不到匹配选择器 '{selector}' 的元素")

        event_id_selector = "input#_eventId"
        event_id_node = node.css_first(event_id_selector)
        if event_id_node is None:
            raise GetCookieError(f"找不到匹配选择器 '{event_id_selector}' 的元素")

        cllt_selector = "input#cllt"
        cllt_node = node.css_first(cllt_selector)
        if cllt_node is None:
            raise GetCookieError(f"找不到匹配选择器 '{cllt_selector}' 的元素")

        dllt_selector = "input#dllt"
        dllt_node = node.css_first(dllt_selector)
        if dllt_node is None:
            raise GetCookieError(f"找不到匹配选择器 '{dllt_selector}' 的元素")

        lt_selector = "input#lt"
        lt_node = node.css_first(lt_selector)
        if lt_node is None:
            raise GetCookieError(f"找不到匹配选择器 '{lt_selector}' 的元素")

        salt_selector = "input#pwdEncryptSalt"
        salt_node = node.css_first(salt_selector)
        if salt_node is None:
            raise GetCookieError(f"找不到匹配选择器 '{salt_selector}' 的元素")

        execution_selector = "input#execution"
        execution_node = node.css_first(execution_selector)
        if execution_node is None:
            raise GetCookieError(f"找不到匹配选择器 '{execution_selector}' 的元素")

        event_id = event_id_node.attributes["value"]
        cllt = cllt_node.attributes["value"]
        dllt = dllt_node.attributes["value"]
        lt = lt_node.attributes["value"]
        salt = salt_node.attributes["value"]
        if salt is None:
            raise GetCookieError("元素中没有 'value' 属性的值")

        execution = execution_node.attributes["value"]

        encrypted_password = encrypt_password(password, salt)
        client.post(
            "https://ids.hit.edu.cn/authserver/login",
            params={"service": "http://jw.hitsz.edu.cn/casLogin"},
            data={
                "username": username,
                "password": encrypted_password,
                "captcha": "",
                "_eventId": event_id,
                "cllt": cllt,
                "dllt": dllt,
                "lt": lt,
                "execution": execution,
            },
        )
        route = client.cookies.get("route", domain="jw.hitsz.edu.cn")
        jsessionid = client.cookies.get("JSESSIONID", domain="jw.hitsz.edu.cn")
        cookies = f"route={route}; JSESSIONID={jsessionid}"
        config.cookies = cookies

    console.print("[green]成功获取 Cookies")
    return cookies


def get_headers(cookies: str) -> dict[str, str]:
    """生成 HTTP 请求头

    根据提供的 Cookie 构造 HTTP 请求头字典。
    使用预设的 User-Agent 确保请求行为与浏览器一致。

    Args:
        cookies (str): 用于身份验证的Cookie字符串

    Returns:
        dict[str, str]: 包含 User-Agent 和 Cookie 的请求头字典:
    """
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "Cookie": cookies,
    }
