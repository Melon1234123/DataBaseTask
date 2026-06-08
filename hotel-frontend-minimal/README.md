# 酒店管理系统前端

这是可独立运行、可直接提交 GitHub 的最小完整前端文件夹。

## 文件说明

```text
hotel-frontend-minimal/
  index.html
  styles.css
  app.js
  assets/
    hotel.jpg
  README.md
```

- `index.html`：页面入口
- `styles.css`：页面样式
- `app.js`：前端逻辑和 Mock API 数据
- `assets/hotel.jpg`：本地酒店图片

## 运行方式

推荐使用本地静态服务：

```bash
python3 -m http.server 4173
```

然后访问：

```text
http://127.0.0.1:4173
```

也可以直接双击打开 `index.html`。

## Mock 登录账号

```text
账号：front01
密码：123456
```

页面默认使用 Mock API，不需要后端也能演示客户、客房、预定、入住、结账、清扫任务和操作审计流程。
