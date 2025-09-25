import asyncio
import json
from urllib.parse import urlparse
from typing import Dict, Any, List
import os
import re
import requests
import google.generativeai as genai
from django.core.cache import cache
from playwright.async_api import async_playwright


class ECommerceScraper:
    def __init__(self):
        self.ai_client = None
        self.browser = None
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.ai_client = genai.GenerativeModel("gemini-1.5-flash")

    async def _get_extractor_type(self, url: str, page) -> tuple:
        domain = urlparse(url).netloc.lower()

        if "pchome.com.tw" in domain:
            return self._extract_pchome, "pchome"
        elif "momoshop.com.tw" in domain:
            return self._extract_momo, "momo"

        is_shopify = await page.evaluate(
            """() => {
            return !!(
                window.Shopify ||
                document.querySelector('[data-shopify]') ||
                document.querySelector('script[src*="shopify"]') ||
                document.querySelector('meta[name="generator"][content*="Shopify"]') ||
                document.querySelector('.shopify-section') ||
                document.querySelector('[class*="shopify"]')
            );
        }"""
        )

        if is_shopify:
            return self._extract_shopify, "shopify"

        is_shopline = await page.evaluate(
            """() => {
            return !!(
                document.querySelector('[data-shopline]') ||
                document.querySelector('.shopline-product') ||
                window.ShoplineSDK ||
                document.querySelector('script[src*="shoplineapp"]') ||
                document.querySelector('meta[name="generator"][content*="Shopline"]')
            );
        }"""
        )

        if is_shopline:
            return self._extract_shopline, "shopline"

        return None, "unknown"

    def _extract_momo_from_html(self, html_content: str):
        """從 HTML 內容中提取 MoMo 商品資訊"""

        data = {}

        desc_match = re.search(
            r'<meta name="Description" content="推薦([^,]+),', html_content
        )
        if desc_match:
            data["name"] = desc_match.group(1).strip()
        else:
            title_match = re.search(
                r'<meta property="og:title" content="([^"]+)"', html_content
            )
            if title_match:
                data["name"] = title_match.group(1).strip()

        price_match = re.search(
            r'<meta property="product:price:amount" content="([^"]+)"', html_content
        )
        if price_match:
            try:
                data["price"] = int(price_match.group(1))
            except Exception:
                data["price"] = None

        brand_match = re.search(
            r'<meta property="product:brand" content="([^"]+)"', html_content
        )
        if brand_match:
            data["brand"] = brand_match.group(1).strip()

        image_match = re.search(
            r'<meta property="og:image" content="([^"]+)"', html_content
        )
        if image_match:
            data["images"] = [image_match.group(1)]
            data["main_image"] = image_match.group(1)
        else:
            data["images"] = []
            data["main_image"] = None

        full_desc_match = re.search(
            r'<meta name="Description" content="推薦[^,]+,([^"]+)"', html_content
        )
        if full_desc_match:
            desc = (
                full_desc_match.group(1)
                .replace("momo購物網總是優惠便宜好價格,值得推薦！", "")
                .strip()
            )
            data["description"] = desc

        currency_match = re.search(
            r'<meta property="product:price:currency" content="([^"]+)"', html_content
        )
        data["currency"] = currency_match.group(1) if currency_match else "TWD"

        stock_match = re.search(
            r'<meta property="product:availability" content="([^"]+)"', html_content
        )
        data["in_stock"] = (
            stock_match and "in stock" in stock_match.group(1).lower()
            if stock_match
            else True
        )

        data["spec_variants"] = {}

        return data

    async def _extract_momo(self, page):
        return await page.evaluate(
            """() => {
            const data = {};

            // 基本資訊從 JSON-LD 提取
            const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (let script of jsonLdScripts) {
                try {
                    const jsonData = JSON.parse(script.textContent);
                    const products = Array.isArray(jsonData) ? jsonData : [jsonData];

                    for (let item of products) {
                        if (item['@type'] === 'Product') {
                            data.name = item.name ? item.name.trim() : null;
                            data.price = item.offers && item.offers.price ?
                                       parseInt(item.offers.price) : null;
                            data.currency = item.offers && item.offers.priceCurrency || 'TWD';
                            data.brand = item.brand && item.brand.name || null;
                            data.description = item.description || null;
                            data.images = item.image || [];
                            data.main_image = item.image && item.image[0] || null;
                            data.in_stock = item.offers &&
                                          item.offers.availability === 'https://schema.org/InStock';

                            if (item.aggregateRating) {
                                data.rating = parseFloat(item.aggregateRating.ratingValue) || null;
                                data.review_count = item.aggregateRating.reviewCount || null;
                            }
                            break;
                        }
                    }
                } catch (e) { continue; }
            }

            // 抓取 MomoShop 的規格選項 (使用 li 清單格式)
            data.spec_variants = {};
            
            // 方法 1: 尋找 MomoShop 特有的規格格式
            const specContainers = document.querySelectorAll('[name*="spec"], [id*="spec"], .formatBlock');
            
            specContainers.forEach(container => {
                // 檢查是否有規格標題
                const specLabel = container.querySelector('b');
                const specTitle = specLabel ? specLabel.textContent.replace(':', '').trim() : '';
                
                // 尋找規格選項 li 清單
                const specList = container.querySelector('ul.colorSelect, ul[id*="spec"]');
                if (specList) {
                    const options = [];
                    const listItems = specList.querySelectorAll('li[name*="cart_spec"]');
                    
                    listItems.forEach(li => {
                        const optionText = li.querySelector('i') ? 
                                         li.querySelector('i').textContent.trim() : 
                                         li.getAttribute('alt') || 
                                         li.textContent.trim();
                        
                        if (optionText && optionText !== '請選擇') {
                            options.push(optionText);
                        }
                    });
                    
                    if (options.length > 0) {
                        const specKey = specTitle || container.getAttribute('name') || container.id || 'spec';
                        data.spec_variants[specKey] = options;
                    }
                }
            });
            
            // 方法 2: 檢查傳統的 select 元素 (作為後備)
            if (Object.keys(data.spec_variants).length === 0) {
                const selects = document.querySelectorAll('select');
                selects.forEach((select, index) => {
                    if ((select.id && (select.id.includes('spec') || select.id.includes('color'))) ||
                        (select.name && (select.name.includes('spec') || select.name.includes('color')))) {
                        
                        const options = [];
                        select.querySelectorAll('option').forEach(option => {
                            const text = option.textContent.trim();
                            const value = option.value;
                            
                            if (value && text && 
                                text !== '請選擇' && 
                                text !== '單一規格' &&
                                text !== '--請選擇--' &&
                                !text.match(/^\\d+$/)) {
                                options.push(text);
                            }
                        });
                        
                        if (options.length > 1 && options.length < 20) {
                            const selectKey = select.id || select.name || `select_${index}`;
                            data.spec_variants[selectKey] = options;
                        }
                    }
                });
            }
            
            return data;
        }"""
        )

    async def _extract_pchome(self, page):
        return await page.evaluate(
            """() => {
            const data = {};
            
            const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (let script of jsonLdScripts) {
                try {
                    const jsonData = JSON.parse(script.textContent);
                    if (jsonData['@type'] === 'Product') {
                        data.name = jsonData.name;
                        data.price = jsonData.offers && jsonData.offers.price ? 
                                   parseInt(jsonData.offers.price) : null;
                        data.brand = jsonData.brand && jsonData.brand.name || null;
                        data.description = jsonData.description || null;
                        data.images = jsonData.image || [];
                        data.main_image = jsonData.image && jsonData.image[0] || null;
                        break;
                    }
                } catch (e) { continue; }
            }
            
            if (!data.name) {
                const titleEl = document.querySelector('h1, .prod_name');
                data.name = titleEl ? titleEl.textContent.trim() : null;
            }
            
            if (!data.price) {
                const priceEl = document.querySelector('.price, [class*="price"]');
                if (priceEl) {
                    const priceMatch = priceEl.textContent.match(/\\$([\\d,]+)/);
                    if (priceMatch) {
                        data.price = parseInt(priceMatch[1].replace(/,/g, ''));
                    }
                }
            }
            
            // 如果 JSON-LD 沒有圖片，嘗試從頁面抓取
            if (!data.images || data.images.length === 0) {
                data.images = [];
                
                // 方法1: 找 alt 屬性與商品名稱相同的圖片（最精確）
                if (data.name) {
                    const productImages = document.querySelectorAll(`img[alt="${data.name}"]`);
                    productImages.forEach(img => {
                        if (img.src && !img.src.includes('data:')) {
                            data.images.push(img.src);
                        }
                    });
                }
                
                // 方法2: 如果方法1沒找到，用 PCHome 的 URL 模式
                if (data.images.length === 0) {
                    const allImages = document.querySelectorAll('img');
                    allImages.forEach(img => {
                        if (img.src && 
                            img.src.includes('img.pchome.com.tw/cs/items/') &&
                            !img.src.toLowerCase().includes('logo') &&
                            (img.width > 200 || img.naturalWidth > 200)) {
                            data.images.push(img.src);
                        }
                    });
                }
                
                data.main_image = data.images[0] || null;
            }
            
            data.currency = 'TWD';
            data.spec_variants = {};
            
            return data;
        }"""
        )

    async def _extract_shopline(self, page):
        return await page.evaluate(
            """() => {
            const data = {};
            
            // Shopline 的商品名稱通常在 h1 標籤
            const titleEl = document.querySelector('h1, [data-testid="product-title"], .product-title');
            data.name = titleEl ? titleEl.textContent.trim() : null;
            
            // 價格提取
            const priceEl = document.querySelector('[class*="price"], .product-price, [data-testid="price"]');
            if (priceEl) {
                const priceText = priceEl.textContent;
                const priceMatch = priceText.match(/([\\d,]+)/);
                if (priceMatch) {
                    data.price = parseInt(priceMatch[1].replace(/,/g, ''));
                }
            }
            
            // 圖片
            data.images = [];
            const imageEls = document.querySelectorAll('.product-image img, [class*="product-gallery"] img');
            imageEls.forEach(img => {
                if (img.src && !img.src.includes('data:')) {
                    data.images.push(img.src);
                }
            });
            data.main_image = data.images[0] || null;
            
            // 描述
            const descEl = document.querySelector('.product-description, [class*="description"]');
            data.description = descEl ? descEl.textContent.trim() : null;
            
            data.currency = 'TWD';
            data.spec_variants = {};
            
            // 嘗試提取變體選項
            const variantContainers = document.querySelectorAll('[class*="variant"], [class*="option"]');
            variantContainers.forEach(container => {
                const options = [];
                const optionEls = container.querySelectorAll('button, .option-item, [role="button"]');
                optionEls.forEach(el => {
                    const text = el.textContent.trim();
                    if (text && text.length < 50) {
                        options.push(text);
                    }
                });
                
                if (options.length > 1) {
                    const variantType = container.textContent.toLowerCase().includes('color') || 
                                     container.textContent.toLowerCase().includes('顏色') ? 'colors' : 'options';
                    data.spec_variants[variantType] = options;
                }
            });
            
            return data;
        }"""
        )

    async def _extract_shopify(self, page):
        return await page.evaluate(
            """() => {
            const data = {};
            
            // 改進商品名稱提取 - 優先從 JSON-LD 提取
            let productName = null;
            
            // 方法1: 從 JSON-LD 獲取準確的商品名稱（避免抓到導航元素）
            const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (let script of jsonLdScripts) {
                try {
                    const jsonData = JSON.parse(script.textContent);
                    const items = Array.isArray(jsonData) ? jsonData : [jsonData];
                    for (let item of items) {
                        if (item['@type'] === 'Product' && item.name && item.name.trim() && 
                            item.name.length > 3 && 
                            !item.name.toLowerCase().includes('購物車') && 
                            !item.name.toLowerCase().includes('cart')) {
                            productName = item.name.trim();
                            break;
                        }
                    }
                    if (productName) break;
                } catch (e) { continue; }
            }
            
            // 方法2: 如果 JSON-LD 沒找到，使用精確的 DOM 選擇器
            if (!productName) {
                const shopifySelectors = [
                    'h1.product__title',           // 最常見的 Shopify 商品標題
                    'h1.product-single__title',    // 單品頁標題
                    '.product__title h1',          // 標題容器內的 h1
                    '.product-single__title',      // 保留原有的
                    'h1[itemprop="name"]'          // 語意標記的商品名稱
                ];
            
                for (let selector of shopifySelectors) {
                    const el = document.querySelector(selector);
                    if (el && el.textContent.trim() && 
                        el.textContent.trim().length > 3 &&
                        !el.textContent.toLowerCase().includes('購物車') && 
                        !el.textContent.toLowerCase().includes('cart')) {
                        productName = el.textContent.trim();
                        break;
                    }
                }
            }
            
            // 方法3: 最後的通用選擇器（但要避免導航元素）
            if (!productName) {
                const titleEl = document.querySelector('h1:not(.header h1):not(.navbar h1)');
                if (titleEl && titleEl.textContent.trim() && 
                    titleEl.textContent.trim().length > 3 &&
                    !titleEl.textContent.toLowerCase().includes('購物車') && 
                    !titleEl.textContent.toLowerCase().includes('cart')) {
                    productName = titleEl.textContent.trim();
                }
            }
            
            data.name = productName;
            
            // JSON-LD 結構化數據提取
            const jsonLdScriptsData = document.querySelectorAll('script[type="application/ld+json"]');
            for (let script of jsonLdScriptsData) {
                try {
                    const jsonData = JSON.parse(script.textContent);
                    const items = Array.isArray(jsonData) ? jsonData : [jsonData];
                    
                    for (let item of items) {
                        if (item['@type'] === 'Product') {
                            // 不再從這裡設置 name，因為前面已經處理過了
                            data.price = item.offers && item.offers.price ? 
                                        parseInt(item.offers.price) : null;
                            data.currency = item.offers && item.offers.priceCurrency || 'TWD';
                            data.brand = item.brand && item.brand.name || null;
                            data.description = item.description || null;
                            
                            // 處理 image 可能是對象或數組的情況
                            if (item.image) {
                                if (Array.isArray(item.image)) {
                                    data.images = item.image;
                                    data.main_image = item.image[0] || null;
                                } else if (typeof item.image === 'object' && item.image.url) {
                                    data.images = [item.image.url];
                                    data.main_image = item.image.url;
                                } else if (typeof item.image === 'string') {
                                    data.images = [item.image];
                                    data.main_image = item.image;
                                } else {
                                    data.images = [];
                                    data.main_image = null;
                                }
                            } else {
                                data.images = [];
                                data.main_image = null;
                            }
                            
                            data.in_stock = item.offers && 
                                          item.offers.availability === 'https://schema.org/InStock';
                            
                            if (item.aggregateRating) {
                                data.rating = parseFloat(item.aggregateRating.ratingValue) || null;
                                data.review_count = item.aggregateRating.reviewCount || null;
                            }
                            break;
                        }
                    }
                } catch (e) { continue; }
            }
            
            // 補充提取：如果 JSON-LD 沒有價格
            if (!data.price) {
                const priceSelectors = [
                    '.product-price',
                    '.price',
                    '[class*="price"]',
                    '.money',
                    '[data-testid="price"]'
                ];
                
                for (let selector of priceSelectors) {
                    const priceEl = document.querySelector(selector);
                    if (priceEl) {
                        const priceText = priceEl.textContent;
                        const priceMatch = priceText.match(/([\\d,]+)/);
                        if (priceMatch) {
                            data.price = parseInt(priceMatch[1].replace(/,/g, ''));
                            break;
                        }
                    }
                }
            }
            
            // 補充提取：圖片
            if (!data.images || data.images.length === 0) {
                data.images = [];
                const imageSelectors = [
                    '.product__photos img',
                    '.product-images img', 
                    '.product-gallery img',
                    '.featured-image img'
                ];
                
                imageSelectors.forEach(selector => {
                    const imgs = document.querySelectorAll(selector);
                    imgs.forEach(img => {
                        if (img.src && !img.src.includes('data:') && 
                            !img.src.includes('.svg') && !img.src.includes('logo')) {
                            data.images.push(img.src);
                        }
                    });
                });
                
                data.main_image = data.images[0] || null;
            }
            
            // 貨幣檢測
            if (!data.currency) {
                const pageText = document.body.textContent.toLowerCase();
                if (pageText.includes('¥') || pageText.includes('jpy')) {
                    data.currency = 'JPY';
                } else if (pageText.includes('$') && pageText.includes('usd')) {
                    data.currency = 'USD';
                } else {
                    data.currency = 'TWD'; // 預設台幣
                }
            }
            
            data.spec_variants = {};
            
            return data;
        }"""
        )

    def _process_variants(self, spec_variants: Dict) -> Dict[str, List[str]]:
        variants = {}

        for spec_id, options in spec_variants.items():
            if not options or len(options) <= 1:
                continue

            if len(options) <= 8:
                if "color" in spec_id.lower():
                    variants["colors"] = options
                elif "flavor" in spec_id.lower():
                    variants["flavor"] = options
                elif "size" in spec_id.lower():
                    variants["sizes"] = options
                else:
                    variants["options"] = options

        return variants

    async def _is_product_page(self, page_html: str, url: str) -> bool:
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()

        strong_product_patterns = [
            "/products/",
            "/goods/",
            "/prod/",
            "/item/",
            "/product/",
            "/detail/",
        ]

        has_strong_product_url = any(
            pattern in path for pattern in strong_product_patterns
        )

        non_product_patterns = [
            "/collections/",
            "/category/",
            "/categories/",
            "/search",
            "/list",
            "/index",
            "/home",
        ]

        has_non_product_url = any(pattern in path for pattern in non_product_patterns)

        is_homepage = path == "/" or path == ""

        html_lower = page_html[:3000].lower()

        strong_product_indicators = [
            "add to cart",
            "加入購物車",
            "立即購買",
            "buy now",
            "現在購買",
            "product-price",
            "single-product",
            "data-product-id",
        ]

        has_strong_html_indicators = any(
            indicator in html_lower for indicator in strong_product_indicators
        )

        supporting_indicators = [
            "product-detail",
            "product-info",
            "商品詳情",
            "產品規格",
            "商品規格",
        ]

        has_supporting_indicators = any(
            indicator in html_lower for indicator in supporting_indicators
        )

        if is_homepage or has_non_product_url:
            return False
        if has_strong_product_url:
            return True
        if has_strong_html_indicators:
            return True
        if has_supporting_indicators:
            return True
        return False

    async def _ai_extract_product_info(
        self, page_html: str, url: str
    ) -> Dict[str, Any]:
        if not self.ai_client:
            return {"success": False, "error": "AI 功能未啟用"}

        try:
            truncated_html = page_html[:10000]

            prompt = f"""
請從以下電商網頁中提取商品資訊，以 JSON 格式回答：

URL: {url}
HTML 內容:
{truncated_html}

請提取以下資訊並以 JSON 格式回答：
{{
  "name": "商品名稱",
  "price": 價格數字(整數),
  "description": "商品描述",
  "images": ["圖片URL1", "圖片URL2"],
  "currency": "TWD",
  "in_stock": true/false
}}

注意事項：
1. 價格只要數字，不要包含貨幣符號
2. 圖片URL要是完整的http/https連結  
3. description 必須從 <body> 標籤內的可見內容提取，不要使用 <meta> 標籤
4. 尋找包含「產品說明」、「商品描述」、「產品介紹」、「內容物」標題的區域
5. 或尋找 class 包含 description、detail、intro、content、product-description 的 HTML 元素內的文字
6. 忽略圖片 alt 屬性和重複的品牌標誌，提取完整段落或清單
7. 如果找不到某項資訊，請設為null
8. 回答 JSON 格式

JSON:"""

            response = self.ai_client.generate_content(prompt)

            result_text = response.text.strip()

            if result_text.startswith("```json"):
                result_text = (
                    result_text.replace("```json", "").replace("```", "").strip()
                )

            if "\n\n" in result_text:
                result_text = result_text.split("\n\n")[0].strip()

            try:
                result = json.loads(result_text)

                result.update(
                    {
                        "url": url,
                        "site": urlparse(url).netloc,
                        "success": True,
                        "error": None,
                        "variants": {},
                        "has_variants": False,
                        "main_image": result.get("images")[0]
                        if result.get("images")
                        else None,
                    }
                )

                return result

            except json.JSONDecodeError as e:
                print(f"AI 回應 JSON 解析錯誤: {str(e)}")
                print(f"原始回應內容: {result_text[:500]}...")
                return {"success": False, "error": f"AI 回應格式錯誤: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_browser(self):
        """取得或創建瀏覽器實例"""
        if self.browser is None:
            self.playwright = await async_playwright().start()

            proxy_server = os.getenv("PROXY_SERVER", None)
            launch_options = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--no-zygote",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                ],
            }
            if proxy_server:
                launch_options["proxy"] = {"server": proxy_server}

            self.browser = await self.playwright.chromium.launch(**launch_options)

        return self.browser

    async def _get_html_from_api(self, url: str) -> str:
        """使用 Oxylabs API 獲取 HTML"""

        username = os.getenv("OXYLABS_USERNAME")
        password = os.getenv("OXYLABS_PASSWORD")

        if not username or not password:
            print("OXYLABS_USERNAME 或 OXYLABS_PASSWORD 環境變數未設定")
            return None

        try:
            payload = {
                "source": "universal",
                "url": url,
                "geo_location": "Taiwan Province of China",
                "locale": "zh-tw",
                "user_agent_type": "desktop_chrome",
                "render": "html",
            }

            print(f"調用 Oxylabs API: {url}")
            response = requests.post(
                "https://realtime.oxylabs.io/v1/queries",
                auth=(username, password),
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            result = response.json()
            print(f"Oxylabs API 返回結果: {result.keys()}")

            # Oxylabs 返回的 JSON 結構中，HTML 內容在 results[0].content
            if result.get("results") and len(result["results"]) > 0:
                html_content = result["results"][0].get("content", "")
                print(f"成功獲取 HTML，長度: {len(html_content)} 字符")
                return html_content
            else:
                print(f"Oxylabs 返回的結果格式異常: {result}")
                return None

        except Exception as e:
            print(f"Oxylabs API 調用失敗: {str(e)}")
            return None

    async def scrape_product(self, url: str) -> Dict[str, Any]:
        cache_key = f"scraper:product:{url}"
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                print(f"從快取中獲取資料 (URL: {url})")
                cached_data["success"] = True
                return cached_data
        except Exception as e:
            print(f"讀取 Redis 快取失敗: {e}")

        final_result = None

        if not final_result:
            browser = await self._get_browser()
            page = await browser.new_page()

            try:
                await page.set_extra_http_headers(
                    {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    }
                )

                timeout = 60000 if "momoshop.com.tw" in url else 10000
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

                page_html = await page.content()

                is_product_page = await self._is_product_page(page_html, url)
                if not is_product_page:
                    raise Exception("此網址不是商品頁面")

                extractor, extractor_type = await self._get_extractor_type(url, page)
                print(f"選擇的提取器: {extractor_type}")

                if extractor:
                    try:
                        result = await extractor(page)
                        print(f"提取器結果: {result}")

                        has_sufficient_data = result.get("name") and result.get("price")
                        if not has_sufficient_data:
                            print(
                                f"資料不足，名稱: {result.get('name')}, 價格: {result.get('price')}"
                            )
                            extractor = None
                    except Exception as e:
                        print(f"專用提取器錯誤: {str(e)}")
                        extractor = None

                if not extractor and self.ai_client:
                    print(f"使用 AI 提取商品資訊: {url}")
                    ai_result = await self._ai_extract_product_info(page_html, url)
                    print(f"AI 提取結果: {ai_result}")
                    if ai_result.get("success"):
                        final_result = ai_result
                    else:
                        error_msg = ai_result.get("error", "未知錯誤")
                        raise Exception(f"AI 提取失敗: {error_msg}")
                elif not extractor:
                    raise Exception("不支援此網站的商品頁面")

                if extractor and result:
                    spec_variants = result.pop("spec_variants", {})
                    variants = self._process_variants(spec_variants)

                    result.update(
                        {
                            "url": url,
                            "site": urlparse(url).netloc,
                            "success": True,
                            "error": None,
                            "variants": variants,
                            "has_variants": len(variants) > 0,
                        }
                    )
                    final_result = result
                else:
                    raise Exception("不支援此網站或提取失敗")

            except Exception as e:
                final_result = {
                    "url": url,
                    "site": urlparse(url).netloc,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "variants": {},
                    "has_variants": False,
                }
            finally:
                await page.close()

        if final_result and final_result.get("success"):
            try:
                cache.set(cache_key, final_result, timeout=3600)
                print(f"已將結果存入快取 (Key: {cache_key})")
            except Exception as e:
                print(f"寫入 Redis 快取失敗: {e}")

        return (
            final_result if final_result else {"success": False, "error": "請稍候再試"}
        )

    async def close(self):
        """關閉瀏覽器和 Playwright"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if hasattr(self, "playwright") and self.playwright:
            await self.playwright.stop()


async def scrape_product_url(url: str) -> Dict[str, Any]:
    scraper = ECommerceScraper()
    return await scraper.scrape_product(url)


def scrape_product_url_sync(url: str) -> Dict[str, Any]:
    return asyncio.run(scrape_product_url(url))
