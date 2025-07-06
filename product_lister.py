#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced E-commerce Catalogue Scraper
------------------------------------
• Scrapes WooCommerce, Shopify, or any catalogue page (via CSS selectors).  
• Exports a polished Excel workbook (filters, ₹ formatting, hyperlinks, summary chart).  
• Works in CLI mode or with a Streamlit GUI.

CLI quick-starts
----------------
python product_lister.py woocommerce "https://example.com/shop/"
python product_lister.py woocommerce "https://example.com/shop/" --pages 3
python product_lister.py shopify     "https://mystore.myshopify.com"
python product_lister.py generic     "https://demo.site/products" "li.card" ".title" ".price"
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import urljoin, urlparse, urlencode, urlunparse, parse_qs

import pandas as pd
import requests
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------#
HEADERS     = {"User-Agent": "Mozilla/5.0 (compatible; EcommerceScraper/2.0)"}
EXCEL_NAME  = "catalog.xlsx"
# -----------------------------------------------------------------------------#
# Shopify
# -----------------------------------------------------------------------------#
def scrape_shopify(store_url: str) -> pd.DataFrame:
    def _find_sitemaps(url: str) -> List[str]:
        soup = BeautifulSoup(
            requests.get(urljoin(url, "/sitemap.xml"), headers=HEADERS, timeout=20).content,
            "xml")
        return [loc.text for loc in soup.find_all("loc") if "sitemap_products" in loc.text]

    def _extract_handles(smap: str) -> List[str]:
        soup = BeautifulSoup(requests.get(smap, headers=HEADERS, timeout=20).content, "xml")
        return [Path(loc.text).name for loc in soup.find_all("loc")]

    rows: List[Tuple[str, str, float, str, str]] = []
    for sm in _find_sitemaps(store_url):
        for handle in _extract_handles(sm):
            try:
                data = requests.get(urljoin(store_url, f"/products/{handle}.js"),
                                    headers=HEADERS, timeout=20).json()
            except Exception:
                continue
            title     = data.get("title", "").strip()
            category  = data.get("type", "Uncategorised").strip()
            variants  = data.get("variants", [])
            price     = min(v["price"] for v in variants)/100 if variants else None
            prod_url  = urljoin(store_url, f"/products/{handle}")
            image     = data.get("images", [""])[0] if data.get("images") else ""
            rows.append((category, title, price, prod_url, image))

    return pd.DataFrame(rows,
                        columns=["Category", "Product Name", "Price", "URL", "Image"])

# -----------------------------------------------------------------------------#
# WooCommerce
# -----------------------------------------------------------------------------#
def _next_page_url(base: str, num: int) -> str:
    parsed = urlparse(base)
    qs = parse_qs(parsed.query)
    qs["paged"] = [str(num)]
    return urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))

def _last_page(soup: BeautifulSoup) -> int:
    pager = soup.select_one("ul.page-numbers, nav.woocommerce-pagination")
    nums  = [int(a.get_text()) for a in pager.find_all("a") if a.get_text().isdigit()] if pager else []
    return max(nums) if nums else 1

def scrape_woocommerce(shop_url: str, max_pages: Optional[int] = None) -> pd.DataFrame:
    rows: List[Tuple[str, str, float, str, str]] = []

    def _parse_cards(sp: BeautifulSoup):
        for card in sp.select("li.product"):
            try:
                name_el  = card.select_one(".woocommerce-loop-product__title, h2.woocommerce-loop-product__title")
                price_el = card.select_one("span.price")
                link_tag = card.select_one("a[href]")
                img_tag  = card.select_one("img[src]")
                if not (name_el and price_el and link_tag):
                    continue
                name  = name_el.get_text(strip=True)
                price = float(re.search(r"[\d,.]+", price_el.get_text()).group().replace(",", ""))
                url   = urljoin(shop_url, link_tag["href"])
                image = img_tag["src"] if img_tag else ""
                cat   = card.get("data-product_cat", "") or card.get("class", [""])[0]
                rows.append((cat, name, price, url, image))
            except Exception:
                continue

    first = BeautifulSoup(requests.get(shop_url, headers=HEADERS, timeout=20).content, "lxml")
    _parse_cards(first)
    total = min(_last_page(first), max_pages) if max_pages else _last_page(first)

    for p in range(2, total + 1):
        try:
            page = _next_page_url(shop_url, p)
            soup = BeautifulSoup(requests.get(page, headers=HEADERS, timeout=20).content, "lxml")
            _parse_cards(soup)
        except Exception as e:
            print(f"[!] Page {p} skipped ({e})")

    return pd.DataFrame(rows,
                        columns=["Category", "Product Name", "Price", "URL", "Image"])

# -----------------------------------------------------------------------------#
# Generic CSS
# -----------------------------------------------------------------------------#
def scrape_generic(url: str, sel_prod: str, sel_name: str, sel_price: str,
                   sel_cat: Optional[str] = None, sel_img: Optional[str] = None) -> pd.DataFrame:
    soup  = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=20).content, "lxml")
    rows: List[Tuple[str, str, float, str, str]] = []

    for card in soup.select(sel_prod):
        try:
            name_el  = card.select_one(sel_name)
            price_el = card.select_one(sel_price)
            if not (name_el and price_el):
                continue
            cat_el = card.select_one(sel_cat) if sel_cat else None
            img_el = card.select_one(sel_img) if sel_img else None

            name  = name_el.get_text(strip=True)
            cat   = cat_el.get_text(strip=True) if cat_el else "Uncategorised"
            price = float(re.search(r"[\d,.]+", price_el.get_text()).group().replace(",", ""))
            link  = card.select_one("a[href]")
            url   = urljoin(url, link["href"]) if link else url
            img   = img_el["src"] if img_el and img_el.has_attr("src") else ""
            rows.append((cat, name, price, url, img))
        except Exception:
            continue

    return pd.DataFrame(rows,
                        columns=["Category", "Product Name", "Price", "URL", "Image"])

# -----------------------------------------------------------------------------#
# Excel writer (🔥 styling)
# -----------------------------------------------------------------------------#
def save_excel(df: pd.DataFrame, path: Path = Path(EXCEL_NAME)) -> Path:
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        # --- Catalog sheet
        df.to_excel(writer, sheet_name="Catalog", index=False, startrow=1, header=False)
        wb, ws = writer.book, writer.sheets["Catalog"]

        hdr_fmt = wb.add_format({"bold": True, "bg_color": "#004B8F",
                                 "font_color": "white", "border": 1})
        cur_fmt = wb.add_format({"num_format": "₹#,##0"})

        for c, col in enumerate(df.columns):
            ws.write(0, c, col, hdr_fmt)

        ws.add_table(0, 0, len(df), len(df.columns)-1,
                     {"columns": [{"header": h} for h in df.columns],
                      "style":   "TableStyleMedium9"})
        ws.freeze_panes(1, 0)

        widths = [15, 45, 12, 45, 40]
        for i, w in enumerate(widths):
            ws.set_column(i, i, w, cur_fmt if df.columns[i] == "Price" else None)

        # make URLs clickable
        url_col = df.columns.get_loc("URL")
        for r, link in enumerate(df["URL"], start=1):
            ws.write_url(r, url_col, link, string="🔗 Link")

        # --- Summary sheet
        summary = (df.groupby("Category")["Product Name"]
                     .agg(Products="count").reset_index()
                     .sort_values("Products", ascending=False))
        summary.to_excel(writer, "Summary", index=False)
        sws = writer.sheets["Summary"]
        sws.set_column(0, 0, 25)
        sws.set_column(1, 1, 12)

        chart = wb.add_chart({"type": "column"})
        chart.add_series({"name": "Product count",
                          "categories": ["Summary", 1, 0, len(summary), 0],
                          "values":     ["Summary", 1, 1, len(summary), 1]})
        chart.set_title({"name": "Catalogue size by category"})
        chart.set_y_axis({"major_gridlines": {"visible": False}})
        sws.insert_chart("D2", chart, {"x_scale": 1.2, "y_scale": 1.2})

    return path.resolve()

# -----------------------------------------------------------------------------#
# CLI
# -----------------------------------------------------------------------------#
def main_cli() -> None:
    p = argparse.ArgumentParser(description="E-commerce Catalogue Scraper → Excel")
    sp = p.add_subparsers(dest="mode", required=True)

    wc = sp.add_parser("woocommerce", help="Scrape WooCommerce store")
    wc.add_argument("url")
    wc.add_argument("--pages", type=int, default=0)

    sh = sp.add_parser("shopify", help="Scrape Shopify store")
    sh.add_argument("url")

    ge = sp.add_parser("generic", help="Scrape any site with CSS selectors")
    ge.add_argument("url")
    ge.add_argument("product_sel")
    ge.add_argument("name_sel")
    ge.add_argument("price_sel")
    ge.add_argument("--category_sel")
    ge.add_argument("--image_sel")

    # Excel tweaks
    p.add_argument("--no-image-col", action="store_true", help="Drop Image column")
    p.add_argument("--out", default=EXCEL_NAME, help="Custom output file name")

    args = p.parse_args()

    if args.mode == "woocommerce":
        df = scrape_woocommerce(args.url, None if args.pages == 0 else args.pages)
    elif args.mode == "shopify":
        df = scrape_shopify(args.url)
    else:
        df = scrape_generic(args.url, args.product_sel, args.name_sel, args.price_sel,
                            args.category_sel, args.image_sel)

    if args.no_image_col and "Image" in df.columns:
        df = df.drop(columns=["Image"])

    print(f"[✓] Scraped {len(df)} products")
    out_path = save_excel(df, Path(args.out))
    print(f"[✓] Excel saved → {out_path}")

# -----------------------------------------------------------------------------#
# Streamlit GUI
# -----------------------------------------------------------------------------#
def run_streamlit() -> None:
    import streamlit as st

    st.set_page_config(page_title="E-commerce Scraper", layout="wide")
    st.title("🛍️ Advanced E-commerce Scraper")

    mode = st.sidebar.radio("Platform", ["WooCommerce", "Shopify", "Generic"])
    df = None

    if mode == "WooCommerce":
        url = st.sidebar.text_input("Shop/Category URL")
        pages = st.sidebar.number_input("Max pages (0 = all)", 0, step=1)
        if st.sidebar.button("Scrape") and url:
            with st.spinner("Scraping WooCommerce…"):
                df = scrape_woocommerce(url, None if pages == 0 else pages)

    elif mode == "Shopify":
        url = st.sidebar.text_input("Shopify Store URL")
        if st.sidebar.button("Scrape") and url:
            with st.spinner("Scraping Shopify…"):
                df = scrape_shopify(url)

    else:
        url = st.sidebar.text_input("Landing page URL")
        prod_sel = st.sidebar.text_input("Product card selector", "li.product")
        name_sel = st.sidebar.text_input("Name selector", ".product-title")
        price_sel = st.sidebar.text_input("Price selector", ".price")
        cat_sel = st.sidebar.text_input("Category selector (optional)", "")
        img_sel = st.sidebar.text_input("Image selector (optional)", "")
        if st.sidebar.button("Scrape") and url:
            with st.spinner("Scraping…"):
                df = scrape_generic(url, prod_sel, name_sel, price_sel,
                                    cat_sel or None, img_sel or None)

    if df is not None:
        st.success(f"Scraped {len(df)} products")
        st.dataframe(df.head(100), use_container_width=True)
        excel = save_excel(df)
        with open(excel, "rb") as f:
            st.download_button("Download Excel", data=f,
                               file_name=excel.name,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# -----------------------------------------------------------------------------#
if __name__ == "__main__":
    if "streamlit" in sys.argv[0]:
        run_streamlit()
    else:
        main_cli()
