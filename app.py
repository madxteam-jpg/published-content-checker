import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from spellchecker import SpellChecker
import json
from datetime import datetime, timedelta

@st.cache_resource
def load_spell_checker():
    return SpellChecker()

spell = load_spell_checker()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Ultimate Blog QA Auditor", page_icon="🚀", layout="wide")
st.title("🚀 Ultimate Editorial & SEO QA Auditor")
st.write("Your one-stop tool for automated blog post compliance before and after publishing.")

url_input = st.text_input("Blog Post URL to Audit:", placeholder="https://yourdomain.com/blog-post-slug")
run_button = st.button("Run Comprehensive Audit", type="primary")

if run_button and url_input:
    with st.spinner("Executing advanced crawler and compliance scans..."):
        try:
            # Fetch webpage content
            response = requests.get(url_input, timeout=15, headers={"User-Agent": "QA-Audit-Bot/2.0"})
            if response.status_code != 200:
                st.error(f"❌ CRITICAL: Could not fetch page. HTTP Status Code: {response.status_code}")
                st.stop()
                
            soup = BeautifulSoup(response.text, "html.parser")
            parsed_url = urllib.parse.urlparse(url_input)
            slug = parsed_url.path.strip("/")
            
            # Split screen layout
            col1, col2 = st.columns(2)
            
            # --- COLUMN 1: URL, METADATA & TECHNICAL STRUCTURE ---
            with col1:
                st.header("⚙️ URL, Meta & Schema Validation")
                
                # 1. Slug Check
                st.subheader("1. URL Slug Pattern")
                year_pattern = r"\b(19|20)\d{2}\b"
                number_pattern = r"\b\d+\b"
                if re.search(year_pattern, slug) or re.search(number_pattern, slug):
                    st.error("❌ Slug contains a year or list number (e.g., '2026' or '10'). Risk for future updates.")
                else:
                    st.success("✅ Slug is clean and evergreen (no years or numbers found).")
                
                # 2. Meta Title & Description
                st.subheader("2. Search Snippet Optimization")
                title_tag = soup.find("title")
                if title_tag:
                    t_len = len(title_tag.text.strip())
                    if 50 <= t_len <= 60:
                        st.success(f"✅ Title Length: {t_len} chars (Perfect).")
                    else:
                        st.warning(f"⚠️ Title Length: {t_len} chars (Target: 50-60). Text: '{title_tag.text.strip()}'")
                else:
                    st.error("❌ Missing <title> tag.")
                    
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and meta_desc.get("content"):
                    d_len = len(meta_desc.get("content").strip())
                    if 150 <= d_len <= 160:
                        st.success(f"✅ Description Length: {d_len} chars (Perfect).")
                    else:
                        st.warning(f"⚠️ Description Length: {d_len} chars (Target: 150-160).")
                else:
                    st.error("❌ Missing Meta Description tag.")

                # 3. Indexability & Meta Robots
                st.subheader("3. Search Engine Indexability")
                robots = soup.find("meta", attrs={"name": "robots"})
                if robots and "noindex" in robots.get("content", "").lower():
                    st.error("❌ Page has 'noindex' instruction! Search engines are blocked.")
                else:
                    st.success("✅ Page is configured as Indexable.")

                # 4. Structured Data (Schema JSON-LD) Check
                st.subheader("4. Structured Data / Schema Markup")
                schema_tags = soup.find_all("script", type="application/ld+json")
                if not schema_tags:
                    st.warning("⚠️ No JSON-LD Structured Data / Schema blocks detected on the page.")
                else:
                    valid_schemas = 0
                    for tag in schema_tags:
                        try:
                            json.loads(tag.string)  # Check if it parses as valid JSON
                            valid_schemas += 1
                        except Exception:
                            pass
                    if valid_schemas == len(schema_tags):
                        st.success(f"✅ Found {len(schema_tags)} Schema markup block(s) with zero syntax errors.")
                    else:
                        st.error(f"❌ Found errors! Out of {len(schema_tags)} Schema blocks, some have malformed JSON.")

                # 5. Published Date Recency
                st.subheader("5. Recency / Published Date")
                # Look for common article date metadata
                date_meta = soup.find("meta", property=re.compile("date|published|time", re.I)) or \
                            soup.find("meta", attrs={"name": re.compile("date|published|time", re.I)})
                
                if date_meta and date_meta.get("content"):
                    try:
                        date_str = date_meta.get("content")[:10] # Pull YYYY-MM-DD string
                        pub_date = datetime.strptime(date_str, "%Y-%m-%d")
                        days_old = (datetime.now() - pub_date).days
                        
                        if days_old <= 30:
                            st.success(f"✅ Published Date is recent: {date_str} ({days_old} days ago).")
                        else:
                            st.warning(f"⚠️ Article date is older: {date_str} ({days_old} days ago).")
                    except:
                        st.info(f"ℹ️ Found published timestamp metadata: '{date_meta.get('content')}' but format varies.")
                else:
                    st.info("ℹ️ No distinct publication timestamp metadata tag found automatically.")

            # --- COLUMN 2: ON-PAGE CONTENT & LINK QUALITY ---
            with col2:
                st.header("📝 Heading Hierarchy & Content Quality")
                
                # 1. Heading Structure (H1 -> H2 -> H3)
                st.subheader("1. Heading Structure Hierarchy")
                h1s = soup.find_all("h1")
                if len(h1s) != 1:
                    st.error(f"❌ Structural Rule Broken: Found {len(h1s)} H1 tags. There must be exactly 1.")
                else:
                    st.success("✅ Exactly one H1 tag found.")
                
                # Check for skipping heading levels (e.g., H1 straight to H3)
                all_headings = soup.find_all(["h1", "h2", "h3"])
                hierarchy_broken = False
                prev_level = 1
                
                for h in all_headings:
                    curr_level = int(h.name[1])
                    if curr_level > prev_level + 1:
                        st.error(f"❌ Hierarchy Gap: Skipped from H{prev_level} directly to {h.name} ('{h.text.strip()[:30]}...')")
                        hierarchy_broken = True
                    prev_level = curr_level
                if not hierarchy_broken and len(all_headings) > 0:
                    st.success("✅ Headings follow correct nested structure hierarchy.")

                # 2. Table of Contents vs H2 Headings
                st.subheader("2. Table of Contents vs H2 Alignment")
                h2_headings = [h2.text.strip().lower() for h2 in soup.find_all("h2")]
                toc_container = soup.find(class_=re.compile("toc|table-of-contents|content-list|rank-math-toc", re.I)) or soup.find(id=re.compile("toc", re.I))
                
                if toc_container and h2_headings:
                    toc_links_text = [a.text.strip().lower() for a in toc_container.find_all("a")]
                    missing_h2s = [h for h in h2_headings if not any(h in t or t in h for t in toc_links_text)]
                    
                    if missing_h2s:
                        st.error(f"❌ Disconnect: Found H2 headings missing from your Table of Contents:")
                        for miss in missing_h2s[:3]:
                            st.write(f"- *\"{miss}\"*")
                    else:
                        st.success("✅ All article H2 headings are accurately represented in your Table of Contents.")
                else:
                    st.info("ℹ️ Skipping: No distinct Table of Contents container or H2 headers detected to cross-reference.")

                # 3. Image Validation & Alt Text
                st.subheader("3. Media & Asset Health")
                imgs = soup.find_all("img")
                missing_alt, broken_imgs = 0, 0
                
                for img in imgs:
                    src = img.get("src")
                    alt = img.get("alt")
                    if not src: continue
                    img_url = urllib.parse.urljoin(url_input, src)
                    
                    if not alt or alt.strip() == "":
                        missing_alt += 1
                    try:
                        if requests.head(img_url, timeout=3).status_code >= 400:
                            broken_imgs += 1
                    except:
                        broken_imgs += 1
                        
                if missing_alt > 0: st.error(f"❌ {missing_alt} image(s) are missing alternative (alt) descriptive text.")
                else: st.success("✅ All image tags contain alt attributes.")
                if broken_imgs > 0: st.error(f"❌ Broken Links: Found {broken_imgs} broken/404 image paths.")
                else: st.success("✅ All images loaded and resolved successfully.")

                # 4. Internal & External Hyperlinks
                st.subheader("4. Link Profiles (404 & Nofollow)")
                links = soup.find_all("a", href=True)
                broken_int, broken_ext, ext_no_nofollow = 0, 0, 0
                
                for link in links[:20]: # Checks first 20 links to maintain rapid load speed
                    href = link.get("href")
                    rel = link.get("rel", [])
                    if href.startswith("#") or href.startswith("mailto:") or not href: continue
                    
                    full_link = urllib.parse.urljoin(url_input, href)
                    is_ext = parsed_url.netloc not in full_link
                    
                    if is_ext and "nofollow" not in rel:
                        ext_no_nofollow += 1
                        
                    try:
                        if requests.head(full_link, timeout=3, allow_redirects=True).status_code == 404:
                            if is_ext: broken_ext += 1
                            else: broken_int += 1
                    except:
                        pass
                        
                if broken_int > 0: st.error(f"❌ Internal Links: Found {broken_int} broken internal 404 links.")
                else: st.success("✅ No broken internal links found.")
                if broken_ext > 0 or ext_no_nofollow > 0:
                    st.warning(f"⚠️ External Links: {broken_ext} broken paths | {ext_no_nofollow} missing 'nofollow' attributes.")
                else:
                    st.success("✅ External links follow your mandatory 'nofollow' policies.")

                # 5. Native Spelling Audit
                st.subheader("5. Copywriting Spelling Audit")
                paragraphs = [p.text for p in soup.find_all("p")]
                article_text = " ".join(paragraphs)
                
                if article_text.strip():
                    words = re.findall(r'\b[a-zA-Z]+\b', article_text)
                    misspelled = spell.unknown(words)
                    filtered_misspelled = [w for w in misspelled if len(w) > 2 and not w[0].isupper()]
                    
                    if filtered_misspelled:
                        st.error(f"❌ Found {len(filtered_misspelled)} unique spelling typo anomalies.")
                        with st.expander("Review Typos Found"):
                            st.write(", ".join(list(filtered_misspelled)[:15]))
                    else:
                        st.success("✅ Copy is clean. No major spelling typos detected.")
                else:
                    st.info("ℹ️ Unable to isolate standard `<p>` text strings for spell checking.")

        except Exception as main_err:
            st.error(f"An unexpected script interruption occurred: {main_err}")
