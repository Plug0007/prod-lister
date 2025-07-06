# 🛍️ Advanced E‑commerce Catalogue Scraper

Scrape product listings from **WooCommerce**, **Shopify**, or any **custom product page** using CSS selectors.  Exports a polished Excel workbook with filters, clickable links, ₹‑formatted prices, full product descriptions, and a category summary chart.

---

## 🔧 Features

- ✅ Full catalog export to Excel
- 📦 Fields: **Category | Catalogue | Price | URL | Image | Description**
- 🛒 WooCommerce – visits each product page to pull real descriptions
- 🏪 Shopify – scrapes via `/products/<handle>.js` (works even if `/products.json` is blocked)
- 🧩 Generic mode – scrape *any* site with your own CSS selectors
- 💄 Excel styling: tables, filters, ₹ currency, hyperlinks, summary chart
- 🖥️ Optional GUI with Streamlit (no coding required)

---

## ⚙️ Requirements

```bash
pip install -r requirements.txt
```

`requirements.txt`

```
beautifulsoup4
pandas
requests
lxml
openpyxl
xlsxwriter
streamlit
```

*Python ≥ 3.7*

---

## 🔌 Installation

1. **Clone / download** this repo.
2. **Ensure Python 3.7+** is installed.
3. **Open a terminal** in the project folder.
4. **Install dependencies** as shown above.

---

## 🚀 How to Use

### ▶️ Option 1 – CLI (Command‑Line)

#### 🛒 WooCommerce

```bash
python product_lister.py woocommerce "https://example.com/shop/" --pages 5
```

- Replace the URL with your shop link.
- `--pages` is optional (`0` = scrape *all* pages).
- ✅ Pulls full descriptions from each product page.

---

#### 🏪 Shopify

```bash
python product_lister.py shopify "https://yourstore.myshopify.com"
```

- Automatically reads the sitemap and fetches all product details.

---

#### 🧩 Generic / Custom Site

```bash
python product_lister.py generic "https://example.com/products" "li.card" \
                               ".title" ".price" \
                               --category_sel ".cat" --image_sel "img"
```

**Positional arguments**

| Argument      | Description                              |
| ------------- | ---------------------------------------- |
| `product_sel` | CSS selector for the entire product card |
| `name_sel`    | CSS selector for product title           |
| `price_sel`   | CSS selector for price element           |

**Optional flags**

| Flag             | Description                |
| ---------------- | -------------------------- |
| `--category_sel` | CSS selector for category  |
| `--image_sel`    | CSS selector for image tag |

---

### ▶️ Option 2 – GUI (Streamlit)

```bash
streamlit run product_lister.py
```

1. Select platform in the sidebar.
2. Enter the store URL (and selectors for Generic mode).
3. Click **Scrape**.
4. Click **Download Excel** once finished.

---

## 💡 Examples

```bash
# Example 1 – WooCommerce, scrape every page
python product_lister.py woocommerce "https://khojati.in/shop" --pages 0

# Example 2 – Shopify store
python product_lister.py shopify "https://mybrand.myshopify.com"

# Example 3 – Generic site
python product_lister.py generic \
  "https://demo.store/all-products" \
  "div.product-box" ".name" ".amount" \
  --category_sel ".type" --image_sel "img"
```

---

## 📦 Excel Output

### Sheet `Catalog`

| Category | Catalogue    | Price | URL     | Image       | Description                           |
| -------- | ------------ | ----- | ------- | ----------- | ------------------------------------- |
| Surma    | Herbal Kajal | ₹120  | 🔗 Link | (image URL) | Soothing herbal kajal with almond oil |

### Sheet `Summary`

*Bar chart of product count by category.*

---

## 🔍 Finding CSS Selectors (Generic Mode)

1. Open the page in Chrome/Edge/Firefox.
2. **Right‑click** the element (title, price, etc.) → **Inspect**.
3. Note the class / tag shown in DevTools (e.g. `<span class="product-title">`).
4. Prefix with a dot to form the CSS selector (`.product-title`).

---

## 🙋 FAQ

| Question                                  | Answer                                                                                                                             |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Description is empty for WooCommerce?** | The scraper visits each product page. If still empty, the site may load descriptions via JavaScript (requires a headless browser). |
| **PermissionError saving Excel?**         | Close the Excel file if it’s open or remove write protection. Delete `catalog.xlsx` if it’s locked.                                |
| **How many pages can I scrape?**          | Use `--pages 0` to scrape all pages (WooCommerce).                                                                                 |

---

## 👨‍💻 Author

**Raelyaan** – Student, builder, creator of Cre8treds & JOJ (Jar of Joy)

GitHub → [https://github.com/raelyaan](https://github.com/raelyaan)

---

## 📄 License

MIT License – Free to use, modify, and distribute.

