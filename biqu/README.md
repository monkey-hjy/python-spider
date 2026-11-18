# biqu.py - 笔趣阁下载脚本

最后更新：2026-11-18
当前状态：已验证可用（apibi.cc 后端）

## 一、脚本说明

- 文件：biqu.py
- 运行：`python biqu.py`
- 依赖：Python 3.11、requests、pycryptodome
- 输出：当前目录下 `书名.txt`，UTF-8 编码

流程与交互：

1. `input('输入书名：')`，交互点 1
2. GET `https://apibi.cc/api/search?q=书名`
3. 打印候选列表（编号、作者、书名）
4. `input('输入需要的书籍编号：')`，交互点 2
5. GET `/api/booklist?token=...` 取章节名列表
6. 逐章 GET `/api/chapter?token=...` 取正文
7. 追加写入 `书名.txt`：章节名一行、正文、空行

除上述两次输入外全自动。接口偶发 403 时脚本自动重试 3 次，间隔 1.2 秒。

## 二、数据源现状

| 站点 | 角色 | 2026-11-18 状态 |
|---|---|---|
| apibi.cc | 实际数据接口（搜索/目录/正文） | 可用 |
| m.bqg787.cc / www.bqg787.cc | SPA 前端，提供接口逻辑与 token 算法 | 可用 |
| www.bqgsp.cc | 旧静态站，搜索/目录可用，正文页失效 | 半可用 |
| www.biqooge.com | 旧脚本数据源 | 全站 403（Cloudflare 人机验证） |

关键结论：**bqgsp.cc 静态站与 apibi.cc 后端不是同一套书号，不能混用。**

实测：完美世界在 apibi.cc 是 `id=455`，在 bqgsp.cc 静态站是 `/book/10508/`；用 10508 调正文接口拿到的是另一本书《暮色沉沉夕向晚》。

apibi.cc 是前端配置的第三方接口域名。站点换域名时，优先从 `read.js` 的 `gethost()` 返回值里找新地址。

## 三、接口

### 3.1 搜索（无需 token）

```
GET https://apibi.cc/api/search?q=完美世界
```

```json
{
  "title": "搜索结果",
  "data": [
    {"id": 455, "title": "完美世界", "author": "辰东", "intro": "..."}
  ]
}
```

### 3.2 目录

```
GET https://apibi.cc/api/booklist?token=<token>
```

token 由 `{"id": 455}` 加密得到。

```json
{"list": ["第1章 序章 大荒", "第2章 朝气蓬勃", "..."]}
```

### 3.3 正文

```
GET https://apibi.cc/api/chapter?token=<token>
```

token 由 `{"id": 455, "chapterid": 1}` 加密得到，chapterid 从 1 开始，对应目录顺序。

```json
{
  "id": 455,
  "chapterid": 1,
  "title": "完美世界",
  "author": "辰东",
  "chaptername": "第1章 序章 大荒",
  "cs": 2079,
  "txt": "..."
}
```

注意：响应头 `Content-Type` 是 `text/html`，但内容是 UTF-8 JSON。

### 3.4 token 算法

前端 `read.js` 用常量种子做 AES：

```python
import base64
import hashlib
import json

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

_code = hashlib.md5(b'book@token.html').hexdigest()
# 394c2c3202da6270a3dc22cf70418a51
IV, KEY = _code[:16].encode(), _code[16:].encode()


def token(params):
    data = json.dumps(params, separators=(',', ':')).encode()
    return base64.b64encode(
        AES.new(KEY, AES.MODE_CBC, IV).encrypt(pad(data, 16))
    ).decode()
```

- 参数 JSON 必须紧凑（无空格），键顺序与前端一致
- 加密结果直接作为 `token` 查询参数，requests 会自动 URL 编码
- 种子 `book@token.html` 与站点版本绑定（当前 `read.js?v=1.2606`）。站点升级后若开始 403，按第五节重新提取

## 四、2026-11-18 修改记录

按发现顺序：

1. **biqooge 全站 403**
   搜索接口返回 403，响应头 `Cf-Mitigated: challenge`，页面 `<title>Just a moment...</title>`，是 Cloudflare 人机验证，requests 无法直连。

2. **bqgsp.cc 首页可用，无 Cloudflare 挑战**
   首页 200、UTF-8。搜索框由 `/js/compc.js` 动态注入，实际请求 `GET /s?q=书名`，结果由 `GET /user/search.html?q=书名` 以 JSON 返回，字段为 `url_list/articlename/author/intro`。

3. **bqgsp.cc 书籍页目录可用**
   章节链接在 `.listmain dd a`，静态 HTML 可直接解析。

4. **bqgsp.cc 章节页失效**
   `/book/{id}/{chapterid}.html` 只返回约 1 KB 的"加载中……"页面，JS 跳 `/userverify`，最终落到 `https://www.bqg787.cc/#/` 的 SPA，静态解析拿不到正文。

5. **两套书号不一致（关键坑）**
   bqgsp.cc 书页的 id 不能直接喂给 SPA 接口。完美世界：bqgsp=10508，API=455；API 里的 10508 是另一本书。因此 bqgsp.cc 无法整体替换，只能放弃它的书号。

6. **SPA 正文需要 token**
   移动版章节页 `/book/{id}/{chapterid}.html` 加载 `/js/readtxt.js`，正文通过 `get_api('chapter', {id, chapterid})` 请求 `apibi.cc/api/chapter?token=...`。token 由混淆过的 `read.js` 生成。

7. **还原 token**
   用 Node 的 `vm` 加载 `read.js`，拦截 `CryptoJS.AES.encrypt` 和 `CryptoJS.MD5`，打印出明文、key、iv 和 MD5 种子，得到 `book@token.html`，再用 pycryptodome 复现，输出与 JS 逐字节一致。

8. **偶发 403**
   同一 token 短时间内多次请求会返回 403 空响应，间隔后恢复。脚本用 3 次重试解决。

9. **目录尾部可能有重复条目**
   个别书（如 id=10508）的目录最后一条是 `第1章 无爱纠缠_47` 这类填充项，是站点源数据，不是脚本越界，按目录原样写入。

10. **旧脚本自身缺陷（已随改写消除）**
    - `download_book` 使用未定义的 `self.book`，搜索成功后第一次写文件就会 `AttributeError`
    - 编号输入直接 `int()`，输入书名会抛 `ValueError`
    - 搜索参数用 GBK 编码，只适配旧站

## 五、站点变动后的排查步骤

### 1. 判断接口是否还活着

```bash
curl -sS -o /dev/null -w '%{http_code}\n' 'https://apibi.cc/api/search?q=完美世界'
```

- 200 且返回 JSON：接口正常
- 403 且响应头有 `Cf-Mitigated`：Cloudflare 挑战，换搜索入口或换站

### 2. 找新站的搜索与目录

- 搜索框常见于首页 HTML 的 `<form action="/s">`，或 JS 注入的 `$(".search").html(...)`
- 目录通常在书籍页的 `.listmain dd a`、`#list dl dd a`
- 优先找返回 JSON 的接口（浏览器开发者工具 Network，过滤 XHR/Fetch）

### 3. 找正文接口

- 章节页若是静态 HTML，正文一般在 `#content`、`#chaptercontent`、`.Readarea`
- 若页面只有"加载中"，看它加载的 JS（`readtxt.js`、`read.js`、`common.js`），搜索 `get_api`、`/api/`、`chapter`
- SPA 站常见接口：`/api/chapter`、`/api/booklist`、`/api/book`、`/api/search`

### 4. 重新提取 token 密钥

下载当前版本的 `read.js`：

```bash
curl -o read.js 'https://m.bqg787.cc/js/read.js?v=1.2606'
```

用 Node 加载并拦截加密参数：

```js
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync('read.js', 'utf8');
const noop = () => {};
const el = () => ({ style: {}, classList: { add: noop, remove: noop }, appendChild: noop, addEventListener: noop });
const jq = () => ({ ...el(), html: noop, on: noop, ready: noop, each: noop, attr: noop, click: noop, show: noop, hide: noop, find: () => jq(), parent: () => jq() });
jq.getJSON = noop; jq.get = noop; jq.post = noop;
const s = {
  console: { log: noop, warn: noop, error: noop },
  document: { cookie: '', getElementById: el, getElementsByTagName: () => [el()], querySelector: el, createElement: el, addEventListener: noop, body: el(), head: el() },
  location: { href: 'https://m.bqg787.cc/', pathname: '/', hash: '', protocol: 'https:', host: 'm.bqg787.cc' },
  navigator: { userAgent: 'Mozilla/5.0' },
  localStorage: { getItem: () => null, setItem: noop, removeItem: noop },
  Image: function () { return {}; },
  setTimeout, clearTimeout, setInterval, clearInterval,
  $: jq, jQuery: jq, history: { go: noop, back: noop }, scrollTo: noop,
};
s.window = s; s.self = s; s.global = s; s.globalThis = s;
vm.createContext(s);
vm.runInContext(code, s, { timeout: 8000 });

const C = s.CryptoJS;
const enc = C.AES.encrypt;
C.AES.encrypt = function (msg, key, cfg) {
  console.log('PLAINTEXT:', String(msg));
  console.log('KEY:', key.toString());
  console.log('IV:', cfg && cfg.iv ? cfg.iv.toString() : null);
  return enc.apply(this, arguments);
};
const md5 = C.MD5;
C.MD5 = function (x) { console.log('MD5 INPUT:', String(x)); return md5.apply(this, arguments); };

console.log('gethost:', s.gethost());
console.log('URL:', s.get_api('chapter', { id: 455, chapterid: 1 }));
```

- `KEY`、`IV` 输出的是十六进制 ASCII，转成字符串后即为 AES-128 的 key 和 iv
- `MD5 INPUT` 就是种子明文（当前为 `book@token.html`）
- `gethost()` 返回当前接口域名（当前为 `https://apibi.cc`）

### 5. 验证新 token

在 biqu 目录下运行：

```python
import requests

from biqu import token

r = requests.get(
    'https://apibi.cc/api/chapter',
    params={'token': token({'id': 455, 'chapterid': 1})},
    headers={'user-agent': 'Mozilla/5.0'},
    timeout=20,
)
data = r.json()
print(r.status_code, data['chaptername'], len(data['txt']))
```

## 六、验证记录

| 日期 | 书籍 | id | 目录数 | 结果 |
|---|---|---|---|---|
| 2026-11-18 | 完美世界 | 455 | 2079 | 第 1 章正文 923 字 |
| 2026-11-18 | 遮天 | 708 | 1820 | 第 1 章正文 9678 字 |
| 2026-11-18 | 暮色沉沉夕向晚 | 10508 | 47 | 端到端下载成功，154,729 字节 |

环境：Windows 11、Python 3.11、requests、pycryptodome 3.23.0。
