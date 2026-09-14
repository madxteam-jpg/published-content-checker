import streamlit as st
from bs4 import BeautifulSoup
import re
import urllib.parse
from spellchecker import SpellChecker
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests as crequests

@st.cache_resource
def load_spell_checker():
    return SpellChecker()

spell = load_spell_checker()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Ultimate Blog QA Auditor Pro", page_icon="🛡️", layout="wide")
st.title("🛡️ Ultimate Editorial & SEO QA Auditor (Enterprise Version)")
st.write("Enter a published or staging blog URL below to run an instant enterprise compliance audit.")

url_input = st.text_input("Blog Post URL to Audit:", placeholder="https://yourdomain.com/blog-post-slug")
run_button = st.button("Run Comprehensive Audit", type="primary")

# Modern Browser Headers to Bypass Detection
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

def check_url_status(url):
    """Helper function for fast parallel link checking."""
    try:
        res = crequests.head(url, headers=DEFAULT_HEADERS, timeout=5, impersonate="chrome120", allow_redirects=True)
        if res.status_code == 405: # Fallback if HEAD is disallowed
            res = crequests.get(url, headers=DEFAULT_HEADERS, timeout=5, impersonate="chrome120", stream=True)
        return res.status_code
    except:
        return 404

if run_button and url_input:
    with st.spinner("Executing advanced structural, formatting, asset, and social meta checks..."):
        try:
            # Fetch content using impersonated TLS fingerprinting
            response = crequests.get(
                url_input, 
                headers=DEFAULT_HEADERS, 
                timeout=15, 
                impersonate="chrome120"
            )
            
            if response.status_code != 200:
                st.error(f"❌ CRITICAL: Could not fetch page. HTTP Status Code: {response.status_code}")
                st.stop()
                
            soup = BeautifulSoup(response.text, "html.parser")
            parsed_url = urllib.parse.urlparse(url_input)
            slug = parsed_url.path.strip("/")
            
            paragraphs = soup.find_all("p")
            paragraphs_text = [p.text for p in paragraphs]
            article_text = " ".join(paragraphs_text)
            
            col1, col2 = st.columns(2)
            
            # --- COLUMN 1: URL, METADATA & TECHNICAL STRUCTURE ---
            with col1:
                st.header("⚙️ Tech Stack, Meta & Layout Validation")
                
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

                # 3. Indexability & Mobile Responsiveness
                st.subheader("3. Indexability & Mobile Responsiveness")
                robots = soup.find("meta", attrs={"name": "robots"})
                if robots and "noindex" in robots.get("content", "").lower():
                    st.error("❌ Page has 'noindex' instruction! Search engines are blocked.")
                else:
                    st.success("✅ Page is configured as Indexable.")
                
                viewport = soup.find("meta", attrs={"name": "viewport"})
                if viewport and "width=device-width" in viewport.get("content", "").lower():
                    st.success("✅ Mobile Responsive framework tag present (`width=device-width` initialized).")
                else:
                    st.error("❌ Mobile Responsiveness Risk: Page is missing an optimized viewport scaling meta tag.")

                # 4. Open Graph (OG) & Social Metadata Tags
                st.subheader("4. Open Graph & Social Cards Validation")
                og_title = soup.find("meta", property="og:title")
                og_desc = soup.find("meta", property="og:description")
                og_img = soup.find("meta", property="og:image")
                twitter_card = soup.find("meta", attrs={"name": "twitter:card"}) or soup.find("meta", property="twitter:card")
                
                social_checks = [og_title, og_desc, og_img, twitter_card]
                if all(social_checks):
                    st.success("✅ All core social sharing cards are present (OG Title, Desc, Image, Twitter Card).")
                else:
                    missing_socials = []
                    if not og_title: missing_socials.append("og:title")
                    if not og_desc: missing_socials.append("og:description")
                    if not og_img: missing_socials.append("og:image")
                    if not twitter_card: missing_socials.append("twitter:card")
                    st.error(f"❌ Missing Essential Social Assets: {', '.join(missing_socials)}")

                # 5. Editorial Attribution & Reading Analytics
                st.subheader("5. Attribution & Analytics Metrics")
                author_tag = soup.find("meta", attrs={"name": "author"}) or \
                             soup.find("meta", property="article:author") or \
                             soup.find(class_=re.compile("author|byline|writer", re.I)) or \
                             soup.find(id=re.compile("author", re.I))
                if author_tag:
                    author_name = author_tag.get("content") or author_tag.text.strip()
                    st.success(f"✅ Author identity explicitly assigned: \"{author_name[:30]}\"")
                else:
                    st.error("❌ Editorial Error: No assigned Author profile or byline block detected.")

                reading_time = soup.find("meta", attrs={"name": re.compile("twitter:label1|reading|duration", re.I)}) or \
                               soup.find(class_=re.compile("reading-time|read-time|duration", re.I))
                if reading_time:
                    rt_value = reading_time.get("content") or reading_time.text.strip()
                    st.success(f"✅ Article reading duration notice is declared: {rt_value}")
                else:
                    st.warning("⚠️ Reading time estimator display notice is absent from this template.")

                # 6. Taxonomy Assignment
                st.subheader("6. Categories, Tags & Cross-Linking")
                taxonomy_container = soup.find(class_=re.compile("category|tag-list|post-tags|meta-categories|entry-categories", re.I)) or \
                                     soup.find("a", rel=re.compile("category|tag", re.I))
                related_content = soup.find(class_=re.compile("related-post|related-content|read-next|suggested", re.I)) or \
                                  soup.find(id=re.compile("related", re.I))
                
                if taxonomy_container:
                    st.success("✅ Article taxonomy organized (Classification tags/categories discovered).")
                else:
                    st.warning("⚠️ No distinct category or tag grouping modules identified on layout.")
                
                if related_content:
                    st.success("✅ Reciprocal cross-linking active (Related posts / Read next blocks are active).")
                else:
                    st.warning("⚠️ Missing 'Related Content' internal cross-linking module.")

            # --- COLUMN 2: ON-PAGE CONTENT & LINK QUALITY ---
            with col2:
                st.header("📝 Formatting, Copywriting & Media Assets")
                
                # 1. Paragraph Typographic Integrity
                st.subheader("1. Paragraph Typographic Integrity")
                formatting_errors = sum(1 for p in paragraphs if "\xa0" in p.text or p.text.startswith(" ") or p.text.endswith(" "))
                
                if formatting_errors == 0 and len(paragraphs) > 0:
                    st.success("✅ Paragraph layouts clean. Zero double spacing anomalies or broken indents detected.")
                elif len(paragraphs) > 0:
                    st.error(f"❌ Structural Alert: Found {formatting_errors} paragraphs exhibiting non-standard white-spaces or raw layout formatting.")
                else:
                    st.info("ℹ️ No readable structural `<p>` text modules found to audit layout formatting.")

                # 2. Heading Structure & Table of Contents
                st.subheader("2. Heading Structure & Table of Contents")
                h1s = soup.find_all("h1")
                if len(h1s) != 1:
                    st.error(f"❌ Structural Rule Broken: Found {len(h1s)} H1 tags. There must be exactly 1.")
                else:
                    st.success("✅ Exactly one H1 tag found.")
                
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

                h2_headings = [h2.text.strip().lower() for h2 in soup.find_all("h2")]
                toc_container = soup.find(class_=re.compile("toc|table-of-contents|content-list|rank-math-toc", re.I)) or soup.find(id=re.compile("toc", re.I))
                if toc_container and h2_headings:
                    toc_links_text = [a.text.strip().lower() for a in toc_container.find_all("a")]
                    missing_h2s = [h for h in h2_headings if not any(h in t or t in h for t in toc_links_text)]
                    if missing_h2s:
                        st.error("❌ Disconnect: Found H2 headings missing from your Table of Contents:")
                        for miss in missing_h2s[:2]: st.write(f"- *\"{miss}\"*")
                    else:
                        st.success("✅ Table of Contents perfectly mirrors active H2 headers.")

                # 3. Media Assets Audit (Parallel Execution)
                st.subheader("3. Media & Asset Health (Images & Video)")
                videos = soup.find_all(["video", "iframe", "embed"])
                video_count = sum(1 for vid in videos if (v_src := vid.get("src") or vid.get("data-src")) and any(domain in v_src for domain in ["youtube", "vimeo", "wistia", "player", "mp4"]))
                
                if video_count == 0:
                    st.info("ℹ️ Media Audit: No integrated video embeds located inside copy.")
                else:
                    st.success(f"✅ Located {video_count} video embed blocks.")

                imgs = soup.find_all("img")
                missing_alt = sum(1 for img in imgs if not img.get("alt") or img.get("alt").strip() == "")
                
                # Concurrent image availability checks
                img_urls = [urllib.parse.urljoin(url_input, img.get("src")) for img in imgs if img.get("src")]
                with ThreadPoolExecutor(max_workers=10) as executor:
                    img_statuses = list(executor.map(check_url_status, img_urls))
                
                broken_imgs = sum(1 for status in img_statuses if status >= 400)
                
                if missing_alt > 0: st.error(f"❌ {missing_alt} image(s) are missing alternative descriptive text.")
                else: st.success("✅ All image tags contain descriptive alt attributes.")
                if broken_imgs > 0: st.error(f"❌ Broken Assets: Found {broken_imgs} broken image source paths.")

                # 4. Links Audit (Parallel Execution)
                st.subheader("4. Link Profiles (404 & Nofollow)")
                links = soup.find_all("a", href=True)[:20]
                
                valid_links = []
                ext_no_nofollow = 0
                for link in links:
                    href = link.get("href")
                    rel = link.get("rel", [])
                    if href.startswith("#") or href.startswith("mailto:") or not href: continue
                    full_link = urllib.parse.urljoin(url_input, href)
                    is_ext = parsed_url.netloc not in full_link
                    if is_ext and "nofollow" not in rel: ext_no_nofollow += 1
                    valid_links.append((full_link, is_ext))

                with ThreadPoolExecutor(max_workers=10) as executor:
                    link_statuses = list(executor.map(check_url_status, [url for url, _ in valid_links]))

                broken_int = sum(1 for (url, is_ext), status in zip(valid_links, link_statuses) if status == 404 and not is_ext)
                broken_ext = sum(1 for (url, is_ext), status in zip(valid_links, link_statuses) if status == 404 and is_ext)

                if broken_int > 0: st.error(f"❌ Internal Links: Found {broken_int} broken 404 targets.")
                else: st.success("✅ No broken internal navigation targets found.")
                if broken_ext > 0 or ext_no_nofollow > 0:
                    st.warning(f"⚠️ External Links: {broken_ext} broken paths | {ext_no_nofollow} missing 'nofollow'.")

                # 5. Native Spelling Audit
                st.subheader("5. Copywriting Spelling Audit")
                if article_text.strip():
                    words = re.findall(r'\b[a-zA-Z]+\b', article_text)
                    misspelled = spell.unknown(words)
                    filtered_misspelled = [w for w in misspelled if len(w) > 2 and not w[0].isupper()]
                    if filtered_misspelled:
                        st.error(f"❌ Found {len(filtered_misspelled)} unique potential spelling blunders.")
                        with st.expander("Review Typos Found"):
                            st.write(", ".join(list(filtered_misspelled)[:15]))
                    else:
                        st.success("✅ Copy is clean. No obvious typos identified.")

        except Exception as main_err:
            st.error(f"An unexpected script interruption occurred: {main_err}")
