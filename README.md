# BuyBuddy

<div align="center">
    <img src="https://buy-buddy.s3.amazonaws.com/avatars/logo.jpg" alt="BuyBuddy Logo">
</div>

## 簡介

BuyBuddy 是一個專為團購愛好者打造的平台，致力於提供簡單、高效且安全的團購體驗。

**為什麼做「BuyBuddy」？**

在現今追求效率與更多優惠的時代，團購成了日漸盛行的消費模式。\
然而一般消費者卻缺乏更加輕鬆開團、跟團的管道。\

BuyBuddy，正是一個為團購而生的平台，我們的目標是幫助使用者更快速揪團、跟團，讓每一次團購都變得輕鬆愉快。\
一起在 BuyBuddy 裡找到跟你一起 Buy 的 Buddy 吧！

<p align="center">
  <a href="https://buybuddy.site/" target="_blank">專案網址</a>
</p>
<p align="center">
  <a href="#" target="_blank">簡報介紹 Comming Soon</a>
</p>

## 技術架構

### 後端技術

- **LANGUAGE**: Python
- **Framework**: Django 5.2.6
- **Database**: PostgreSQL
- **Authentication**: Django Allauth
- **Task Queue**: Celery with RabbitMQ
- **State Machine**: Django FSM
- **Storage**: AWS S3

### 前端技術

- **Templates**: Django Templates
- **CSS Framework**: TailwindCSS
- **JavaScript**: JS, Alpine.js, HTMX
- **Rich Text Editor**: TinyMCE

### 部署與基礎設施

- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx
- **Application Server**: Gunicorn
- **雲端服務**: AWS (EC2, RDS)

## 功能簡介

1. **簡潔的開、跟團購管理系統 - 簡化團購流程:**
   <div align="center">
     <img src="https://buy-buddy.s3.amazonaws.com/avatars/%E9%96%8B%E8%B7%9F%E5%9C%98%E7%B3%BB%E7%B5%B1.png" alt="開跟團系統">
   </div>

2. **第三方登入 - 輕鬆使用平台服務:**
   <div align="center">
     <img src="https://buy-buddy.s3.amazonaws.com/avatars/%E7%AC%AC%E4%B8%89%E6%96%B9%E7%99%BB%E5%85%A5.png" alt="第三方登入">
   </div>

3. **清晰 UI 呈現 - 進度條、剩餘數量顯示省下雙方溝通成本:**
   <div align="center">
     <img src="https://buy-buddy.s3.amazonaws.com/avatars/UI%E5%91%88%E7%8F%BE.png" alt="UI呈現">
   </div>

4. **通知系統 - 雙方同時掌握團購資訊:**
   <div align="center">
     <img src="https://buy-buddy.s3.amazonaws.com/avatars/%E9%80%9A%E7%9F%A5%E7%B3%BB%E7%B5%B1.png" alt="通知系統">
   </div>

5. **跟團者資訊的整理/匯出 - 開團者查找更方便:**
   <div align="center">
     <img src="https://buy-buddy.s3.amazonaws.com/avatars/%E8%B7%9F%E5%9C%98%E8%80%85%E8%B3%87%E8%A8%8A%E6%95%B4%E7%90%86.png" alt="跟團者資訊整理">
   </div>

6. **智能開團 - 附上連結、自動幫你填表單:**
   <div align="center">
     <img src="https://buy-buddy.s3.amazonaws.com/avatars/%E6%99%BA%E8%83%BD%E9%96%8B%E5%9C%98.png" alt="智能開團">
   </div>

## 版本及套件

- `Python` 版本：3.11+
- `pip` / `uv` 套件管理
- `Docker` & `Docker Compose` (用於容器化部署)

## 安裝設定

1. **安裝相依套件**

   ```bash
   # 使用 pip
   pip install -r requirements.txt
   # 或使用 uv
   uv pip install -r requirements.txt
   ```

2. **設定環境變數**

   ```bash
   cp .env.example .env
   # 編輯 .env 檔案，填入必要的設定
   ```

3. **資料庫遷移**

   ```bash
   make migrate
   # 或
   uv run python manage.py migrate
   ```

4. **運行開發伺服器**
   ```bash
   make runserver
   # 或
   uv run python manage.py runserver
   ```

## 團隊成員

- 陳聖中 [GitHub](https://github.com/custarder)

  - 跟團系統
  - 圖片上傳功能
  - 富文本串接
  - 智能開團
  - 部署

- 邱雅琪 [GitHub](https://github.com/Qiu1996)

  - 團購新增編輯功能
  - 第三方登入功能
  - 我開團的訂單頁
  - 圖片上傳功能
  - 藍新金流串接

- 陳家儀 [GitHub](https://github.com/jiayichen6)

  - 會員驗證信、地址功能
  - 站內通知系統
  - 訂單系統
  - LINE pay 金流串接
  - 留言板
  - UIUX 設計

- 蔡少宏 [GitHub](https://github.com/Tsaishaohung)

  - 銷售頁面串接
  - 站內通知系統
  - 站外 mail 通知

- 江威翰 [GitHub](https://github.com/Vince6113)
  - 商品頁面
  - 團購有限狀態機
  - 忘記密碼功能
