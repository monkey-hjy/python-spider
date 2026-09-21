# 某音接口签名逆向：可复现的工程流程

> 适用对象：协议逆向、客户端安全、数据采集基础设施工程师。  
> 交付目标：用纯代码复现指定 APK 版本的接口签名，并提供可回放的证据链、回归样本和版本覆盖结论。  
> 本文不包含真实密钥、设备标识、凭据或抓包数据。

## 交付标准

不是“跑通过一次”，而是满足以下条件：

| 项目 | 通过条件 |
|---|---|
| 定位 | 每个结论可回落到 `文件:行号`；不能回落的标记为推测 |
| 输入 | 保存真机原始 query、顺序、请求头和时间戳 |
| 输出 | 本地签名与 capture 逐字节一致 |
| 泛化 | 更换时间戳、参数、样本后仍一致，而非拟合单条数据 |
| 运行 | 成品不依赖 APK、Java、so、Frida 或模拟执行环境 |
| 交付 | 代码、测试、证据表、覆盖矩阵、版本适配记录齐全 |

## 工具链

| 用途 | 工具 | 备注 |
|---|---|---|
| dex 反编译 | jadx 1.5+ | 使用 CLI，便于批量检索 |
| 资源与 manifest | apktool | 获取 `versionCode`、SDK、so 清单 |
| 大目录检索 | ripgrep | 优先于 `grep` |
| so 分析 | Ghidra / IDA | 先用 `readelf`、`nm` 建立结构 |
| 运行时观测 | Frida + frida-server | `objection` 可辅助 |
| 抓包 | mitmproxy / Burp | 需要系统信任证书 |
| so 模拟执行 | unidbg | 用于对答案，不用于生产 |
| 实现与测试 | Python 3.11+ / pytest | 最终交付形态 |

---

## 阶段 0：固定样本与基线

所有结论必须绑定到明确的 APK 版本。

```bash
# 样本指纹（Linux / macOS）
sha256sum app.apk          # Linux
shasum -a 256 app.apk      # macOS
ls -l app.apk

# 版本与 so 清单
apktool d -f -o apktool_out app.apk
rg -n "versionCode|versionName|targetSdkVersion" apktool_out/apktool.yml
unzip -l app.apk | rg 'lib/.*\.so'
```

写入 `docs/sample.md`：

```yaml
apk_sha256: <sha256>
version_code: <versionCode>
version_name: <versionName>
target_sdk: <targetSdkVersion>
abis:
  - arm64-v8a
  - armeabi-v7a
packer: <none-or-name>
```

如果 `classes.dex` 很小，但 `lib/` 中存在未知 so，先判断是否为加固包。加固情况下，直接分析 jadx 输出通常没有意义，应先完成脱壳。

---

## 阶段 1：静态拆分与索引

### 1.1 批量反编译

```bash
jadx -d jadx_out --show-bad-code -j 8 app.apk
```

`--show-bad-code` 会保留反编译失败的方法边界。后续检索以 `jadx_out/sources/` 为根目录。

### 1.2 以接口路径为入口

混淆类名不可依赖，接口路径必须原样发送，更适合作为入口锚点。

```bash
rg -n --no-heading "aweme/v2/comment/list" jadx_out/sources
```

目标是用最小搜索面得到接口定义、参数封装和调用链，而不是从混淆类名猜测入口。

### 1.3 建立坐标表

每个关键发现都要绑定到源坐标：

| ID | 发现 | 坐标 | 置信度 |
|---|---|---|---|
| E1 | 接口声明 10 个 query 参数 | `…/comment/api/CommentApi.java:49` | 确定 |
| E2 | 参数由封装层动态组装 | `…/CommentApi.java:214-218` | 确定 |
| E3 | 请求头拍平后传入 native | `…/ms/bd/c/u1.java:32-73` | 确定 |
| E4 | 签名入口是 native 方法 | `…/ms/bd/c/h.java:8-10` | 确定 |
| E5 | 实现位于目标 so | `lib/<abi>/<SIGN_LIB>.so` | 确定 |

这张表是交付证据，不只是分析笔记。对接方可通过它判断分析是否真正落到 native 实现。

---

## 阶段 2：提取接口契约

Retrofit 注解可直接还原为参数模型。

| 注解 | 含义 | 实现处理 |
|---|---|---|
| `@Query("k")` | 单个 query 参数 | 保持声明顺序 |
| `@QueryMap` | 批量 query | 顺序不可控，尽量避免 |
| `@Field("k")` | 表单字段 | 进入 body，签名口径可能与 GET 不同 |
| `@Header` / `@HeaderMap` | 请求头 | 部分头可能参与签名 |
| `@GET` / `@POST` | 方法与路径 | 路径作为静态检索锚点 |

### 2.1 参数顺序必须与声明顺序一致

签名摘要的对象通常是最终 query 字符串。先放入 dict 再 `urlencode` 会丢失声明顺序，即使只有一个参数顺序不同，也会导致签名失败。

### 2.2 `0` 与 `null` 的行为不同

| 声明类型 | 运行时值 | 是否发送 |
|---|---|---|
| `int` / `long` | `0` | 发送，例如 `count=0` |
| `Integer` / `Long` | `null` | 不发送 |
| `String` | `null` | 不发送 |
| `String` | `""` | 逐接口验证 |

空字符串是否保留不能靠推断。相同工程中的不同接口可能采用不同策略，必须以 capture 为准。

### 2.3 参数模型与编码

```python
from dataclasses import dataclass, fields
from typing import Optional
from urllib.parse import quote


@dataclass(frozen=True)
class CommentListParams:
    aweme_id: str
    cursor: int = 0
    count: int = 20
    insert_ids: Optional[str] = None
    # 其余字段严格按接口注解顺序声明


def build_pairs(p: CommentListParams) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for field in fields(p):
        value = getattr(p, field.name)
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        out.append((field.name, str(value)))
    return out


def encode_query(pairs: list[tuple[str, str]]) -> str:
    return "&".join(
        f"{quote(key, safe='')}={quote(value, safe='')}"
        for key, value in pairs
    )
```

参数名应先经过白名单校验。未知字段直接抛出异常，避免未经确认的参数进入请求并污染 capture 对比。

---

## 阶段 3：定位签名边界

### 3.1 从请求链反向定位

不要顺着业务接口逐层向下阅读。优先从 OkHttp 拦截器、请求构造器和 header 写入点反查。

```bash
rg -n "Interceptor" jadx_out/sources --files-with-matches | head -50
rg -n "addHeader|header\(" jadx_out/sources | rg -i "sign|gorgon|token" | head -30
```

典型调用链：

```text
请求构造
  -> 拦截器将 headers 转为有序 key/value
  -> dispatch(int, Object...) 执行 native 路由
  -> 返回新的 key/value
  -> 合并回请求头
```

### 3.2 判定 native 边界

只有声明、没有方法体的方法即为 native 边界。

```java
public static native Object dispatch(int id, Object... args);
```

```bash
rg -n "\bnative\b" jadx_out/sources | rg -v "//|^\s*\*" | head -40
```

### 3.3 提取并检查 so

```bash
unzip -l app.apk | rg 'lib/'
unzip -o app.apk 'lib/arm64-v8a/*' -d libs

readelf -d libs/lib/<abi>/<SIGN_LIB>.so | rg NEEDED
nm -D --defined-only libs/.../<SIGN_LIB>.so | head -50
readelf -sW libs/.../<SIGN_LIB>.so | rg FUNC | wc -l
```

| 注册方式 | 特征 | 定位方法 |
|---|---|---|
| 静态注册 | 导出 `Java_<pkg>_<Class>_<method>` | `nm -D` 搜索 `Java_` |
| 动态注册 | 无 `Java_`，存在 `JNI_OnLoad` | 分析 `RegisterNatives` 方法表 |

动态注册时，方法名、JNI 签名和函数指针位于注册表中。先解析注册表，再分析实现函数，通常比直接阅读 `JNI_OnLoad` 更高效。

### 3.4 选择实现路径

| 指标 | unidbg 模拟执行 | 算法还原 |
|---|---|---|
| 上手时间 | 半天至两天 | 数天至数周 |
| 产物 | JVM、so 与依赖，体积大 | 单一语言源文件 |
| 冷启动 | 秒级 | 毫秒级 |
| 并发 | 受运行时限制 | 可按普通服务横向扩展 |
| 适用场景 | 对答案、短期验证 | 线上服务、长期维护 |

推荐流程：先用 unidbg 验证 capture 和函数边界，再完成纯代码实现。跳过验证直接还原，最大的风险是把大量时间投入到错误函数上。

---

## 阶段 4：动态取证

静态分析提供结构，运行时提供签名真值。目标是生成可长期回放的 capture。

### 4.1 启动 Frida

```bash
adb push frida-server-<ver>-android-arm64 /data/local/tmp/fs
adb shell "su -c 'chmod 755 /data/local/tmp/fs'"
adb shell "su -c '/data/local/tmp/fs &'"
frida-ps -U | head
```

### 4.2 由外向内 Hook

按以下顺序观测，避免一开始就陷入最终算法：

1. 拦截器入口：确认本次请求实际携带的 header。
2. `dispatch` 出入口：建立输入与输出的精确配对。
3. 最终签名函数：确认算法边界和内存布局。

Java 层：

```javascript
Java.perform(function () {
  var C = Java.use("<包名>.<类名>");
  C.dispatch.overload("int", "[Ljava.lang.Object;").implementation = function (id, args) {
    console.log("[in ] id=" + id);
    var result = this.dispatch(id, args);
    console.log("[out] " + result);
    return result;
  };
});
```

Native 层：

```javascript
var base = Module.findBaseAddress("<SIGN_LIB>.so");
Interceptor.attach(base.add(0x<OFFSET>), {
  onEnter: function (args) {
    console.log("in :", hexdump(args[1], { length: 64 }));
  },
  onLeave: function (retval) {
    console.log("out:", hexdump(retval, { length: 64 }));
  }
});
```

使用 spawn 模式，确保在目标进程初始化前完成注入：

```bash
frida -U -f <包名> -l hook.js
```

### 4.3 抓包

```bash
mitmdump -p 8080 -w flow.dump

# 系统证书区，需要 root
openssl x509 -inform PEM -subject_hash_old -in mitm.pem | head -1
adb push <hash>.0 /sdcard/
adb shell "su -c 'mount -o rw,remount /system && cp /sdcard/<hash>.0 /system/etc/security/cacerts/'"
```

存在证书绑定时应单独处理。抓包不可用时，Frida 仍可获取 query、header 和签名结果。

### 4.4 capture 必须保存原始输入

```json
{
  "id": "comment_list_001",
  "apk_version": "<versionName>",
  "endpoint": "/aweme/v2/comment/list/",
  "method": "GET",
  "query_raw": "<完整 query 字符串，原样保存>",
  "headers_ordered": [["<header>", "<value>"]],
  "sign_input": "<hook 观测到的签名输入>",
  "sign_output": "<expected header value>",
  "response_ok": true
}
```

`query_raw` 必须是原始字符串，不能只保存 dict。否则参数顺序、空值策略和编码细节都会丢失，而这三项正是签名差异的主要来源。

---

## 阶段 5：算法还原

### 5.1 定位实现函数

1. 从 `RegisterNatives` 获取实现地址，或从 `Java_` 导出获取静态注册入口。
2. 检查字符串引用和常量表。风控 so 通常包含固定常量数组，并在多处被引用。
3. 查看调用图。典型结构为多段摘要、流密码、字节变换的组合。
4. 先确认输入输出边界，再阅读算法细节。

### 5.2 验收标准

不要以“看懂伪代码”作为完成标准。必须满足：

- 同一输入下，本地实现与 capture 输出逐字节相等。
- 更换时间戳和 query 后仍相等，排除样本拟合。
- 真实请求返回业务数据，而非防护层空壳。

### 5.3 endpoint 可能使用不同 profile

同一个签名函数在不同接口上，可能使用不同常量、配置或输出前缀。只在单接口验证时，这一问题通常不会暴露。

```text
endpoint A  profile=<P_A>  prefix=<X_A>
endpoint B  profile=<P_B>  prefix=<X_B>
endpoint C  profile=<P_C>  prefix=<X_C>
```

每新增一个 endpoint，都要单独抓取 capture 并重新验证，不能复用其他接口的常量假设。

### 5.4 摘要输入必须与最终发出内容一致

“先编码再摘要”和“先摘要再编码”都可能产生看似合理的代码，但结果不同。唯一判据是：摘要输入必须与真实发出的字符串逐字节一致。实现时直接记录两串并 diff，不依赖推理。

---

## 阶段 6：回归测试

目标是让实现具备版本适配能力，而不是只成功运行一次。

```python
import json
from pathlib import Path
import pytest

from signer import sign

CAPTURE_DIR = Path("captures")
CASES = [
    json.loads(path.read_text(encoding="utf-8"))
    for path in CAPTURE_DIR.glob("*.json")
]


@pytest.mark.parametrize("cap", CASES, ids=lambda cap: cap["id"])
def test_capture(cap: dict) -> None:
    got = sign(
        query=cap["query_raw"],
        ts=int(dict(cap["headers_ordered"])["X-Khronos"]),
    )
    assert got == cap["sign_output"]
```

失败时输出字节级差异，而不是只返回“签名错误”：

```python
def diff(expected: str, got: str) -> str:
    if expected == got:
        return "identical"

    lines: list[str] = []
    for index, (left, right) in enumerate(zip(expected, got)):
        if left != right:
            lines.append(f"offset={index} expected={left!r} got={right!r}")

    if len(expected) != len(got):
        lines.append(f"length differs: {len(expected)} vs {len(got)}")

    return "\n".join(lines[:20])
```

query 逐段对比通常能直接定位参数顺序问题：

```python
def diff_query(mine: str, real: str) -> str:
    mine_parts = mine.split("&")
    real_parts = real.split("&")

    for index, (left, right) in enumerate(zip(mine_parts, real_parts)):
        if left != right:
            return f"segment[{index}] mine={left} real={right}"

    return f"segment count: {len(mine_parts)} vs {len(real_parts)}"
```

最后执行端到端请求：

```python
response = session.get(url, params=params, headers=headers)
print(response.status_code, response.text[:200])
```

必须检查响应体是否包含真实业务数据。防护层拦截请求时常返回 HTTP 200 和空壳结构，不能用 `response.ok` 判断成功。

---

## 阶段 7：剥离依赖与交付

### 7.1 依赖验收

最终实现不得读取 APK、不得启动 Java、不得加载 so、不得连接 Frida。验证方式是将 APK、JDK 和 frida-server 全部移出运行环境后重新执行全部测试。

### 7.2 交付结构

```text
project/
├── docs/
│   ├── sample.md            # APK 哈希、版本、ABI
│   ├── evidence.md          # 结论到源码坐标的映射
│   └── coverage.md          # 覆盖矩阵
├── captures/                # 脱敏后的抓包样本
├── src/
│   ├── params.py            # endpoint 参数模型
│   ├── signer.py            # 签名实现
│   └── client.py            # 请求封装
└── tests/
    └── test_capture.py
```

### 7.3 CLI 分离确定性与实时路径

```bash
python client.py --sample     # 复现指定 capture，用于回归
python client.py --fetch      # 使用当前时间戳发起请求
python client.py --capture    # 只计算签名，不发送请求
```

`--sample` 必须完全确定，时间戳只能来自 capture；默认模式必须使用实时时间。两条路径混用会使回归测试失去意义。

### 7.4 覆盖矩阵

| 模块 | 状态 | 依据 |
|---|---|---|
| 参数名与空值处理 | 已覆盖 | E1；单元测试 |
| 参数顺序与编码 | 已覆盖 | capture 逐字符比对 |
| 样本签名复现 | 已覆盖 | pytest 全绿 |
| 端到端请求 | 已覆盖 | 返回体包含业务数据 |
| 其他 APK 版本 | 未覆盖 | 待补样本 |
| 带 body / cookie 的接口 | 部分覆盖 | 代码已实现，缺少样本 |

明确写出未覆盖范围比全部标记“已覆盖”更可靠。真正需要评估的是：版本变化、平台分支和新 endpoint 会在什么条件下导致失败。

---

## 排错手册

| 症状 | 高概率原因 | 验证方法 |
|---|---|---|
| 签名长度正确、内容错误 | 参数顺序或摘要输入口径错误 | 打印本地 query 与 capture 原串，逐字符 diff |
| 服务端返回空壳 | 时间戳过期或缺少设备参数 | 使用 capture 中的原始时间戳重放 |
| 样本通过、新请求失败 | 时间戳参与运算，但取值方式错误 | 使用三个不同时间戳分别验证 |
| 更换接口后全部失效 | endpoint 使用不同常量或 profile | 每个接口单独抓取 capture |
| Frida 无法注入 | 反调试或端口检测 | 使用 spawn 模式，调整默认端口与文件名 |
| so 加载失败 | 缺少依赖或存在运行环境检测 | `readelf -d` 检查 `NEEDED`，补齐依赖 |
| iOS 或另一版本行为不同 | 算法按平台或版本分支 | 分别抓取 capture，不跨端复用 |

## 命令速查

```bash
# 反编译
jadx -d jadx_out --show-bad-code -j 8 app.apk
apktool d -f -o apktool_out app.apk

# 检索
rg -n "<接口路径>" jadx_out/sources
rg -n "\bnative\b" jadx_out/sources | head -40

# so
unzip -l app.apk | rg 'lib/'
unzip -o app.apk 'lib/arm64-v8a/*' -d libs
readelf -d libs/.../x.so | rg NEEDED
nm -D --defined-only libs/.../x.so | rg 'Java_|JNI_OnLoad'
strings -a -n 8 libs/.../x.so | head -40

# 运行时
frida-ps -U
frida -U -f <包名> -l hook.js

# 抓包
mitmdump -p 8080 -w flow.dump

# 测试
pytest -q tests/
```

---

## 可交付服务

| 服务项 | 交付内容 |
|---|---|
| 签名还原 | 纯 Python 签名、参数模型、请求封装，不依赖 APK、Java、so |
| 版本适配 | 新 APK 版本差分、capture 回归、版本映射记录 |
| 客户端 Hook | Android Xposed 模块开发与适配 |
| 定制逆向 | 指定 endpoint、body、cookie、设备参数或风控链路分析 |
| 交付验收 | 源码、pytest 回归集、证据表、覆盖矩阵、部署说明 |

已有评论、用户、作品列表方向的参数建模与签名还原实现，可提供源码交付、私有化调用服务和新接口定制。新版本、新接口及定制协议按范围评估。

Telegram：`@bk_coder`

仅接合法授权范围内的项目。
