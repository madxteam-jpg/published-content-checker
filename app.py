import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from spellchecker import SpellChecker

# Initialize a native Python spell checker (No Java Required!)
@st.cache_resource
def load_spell_checker():
    return SpellChecker()

spell = load_spell_checker()

# --- CONFIGURATION & UI STYLING ---
st.set_page_config(page_title="Blog QA Auditor", page_icon="📝", layout="wide")
st.title("📝 Editorial & SEO QA One-Stop Tool")
st.write("Enter a published or staging blog URL below to run an instant compliance audit.")

url_input = st.text_input("Blog Post URL:", placeholder="https://yourdomain.com/blog-post-slug")
run_button = st.button("Run QA Audit", type="primary")

if run_button and url_input:
    with st.spinner("Analyzing page structure, links, and text..."):
        try:
            response = requests.get(url_input, timeout=15, headers={"User-Agent": "QA-Audit-Bot/1.0"})
            if response.status_code != 200:
                st.error(f"Failed to fetch page. Server returned status code: {response.status_code}")
                st.stop()
                
            soup = BeautifulSoup(response.text, "html.parser")
            parsed_url = urllib.parse.urlparse(url_input)
            slug = parsed_url.path.strip("/")
            
            col1, col2 = st.columns(2)
            
            # --- COLUMN 1: URL, METADATA & STRUCTURE ---
            with col1:
                st.header("🔍 SEO & URL Audits")
                
                # 1. Slug Check
                st.subheader("URL Slug Check")
                year_pattern = r"\b(19|20)\d{2}\b"
                number_pattern = r"\b\d+\b"
                if re.search(year_pattern, slug) or re.search(number_pattern, slug):
                    st.error("❌ Slug contains a year or list number (e.g., '2026' or '10'). Risk for future updates.")
                else:
                    st.success("✅ Slug is clean (evergreen; no years or numbers found).")
                
                # 2. Meta Title
                st.subheader("Meta Title")
                title_tag = soup.find("title")
                if title_tag:
                    t_len = len(title_tag.text.strip())
                    if 50 <= t_len <= 60:
                        st.success(f"✅ Title is {t_len} characters (Perfect range).")
                    else:
                        st.warning(f"⚠️ Title is {t_len} characters (Target: 50-60). Text: '{title_tag.text}'")
                else:
                    st.error("❌ Missing <title> tag.")
                    
                # 3. Meta Description
                st.subheader("Meta Description")
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and meta_desc.get("content"):
                    d_len = len(meta_desc.get("content").strip())
                    if 150 <= d_len <= 160:
                        st.success(f"✅ Description is {d_len} characters (Perfect range).")
                    else:
                        st.warning(f"⚠️ Description is {d_len} characters (Target: 150-160).")
                else:
                    st.error("❌ Missing Meta Description tag.")

                # 4. Heading Structure
                st.subheader("Headings & Structure")
                h1s = soup.find_all("h1")
                if len(h1s) != 1:
                    st.error(f"❌ Strict Rule Broken: Found {len(h1s)} H1 tags. There must be exactly 1.")
                else:
                    st.success("✅ Exactly one H1 tag found.")
                
                # Look for ToC container
                h2s = [h2.text.strip() for h2 in soup.find_all("h2")]
                toc_container = soup.find(class_=re.compile("toc|table-of-contents|content-list", re.I))
                if toc_container:
                    toc_links = [a.text.strip() for a in toc_container.find_all("a")]
                    missing_in_toc = [h for h in h2s if h not in toc_links]
                    if missing_in_toc and len(h2s) > 0:
                        st.warning(f"⚠️ Table of Contents might be missing these H2s: {missing_in_toc[:2]}...")
                    else:
                        st.success("✅ Table of Contents matches your H2 headings.")
                else:
                    st.info("ℹ️ No distinct Table of Contents container identified automatically.")

                # 5. Indexability
                st.subheader("Indexability")
                robots = soup.find("meta", attrs={"name": "robots"})
                if robots and "noindex" in robots.get("content", "").lower():
                    st.error("❌ Page has 'noindex' instruction.")
                else:
                    st.success("✅ Page is indexable.")

            # --- COLUMN 2: LINKS & IMAGES & SPELLING ---
            with col2:
                st.header("🖼️ Content & Quality Audits")
                
                # 1. Images Validation
                st.subheader("Images & Alt Text")
                imgs = soup.find_all("img")
                missing_alt = 0
                broken_imgs = 0
                
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
                        
                if missing_alt > 0: st.error(f"❌ {missing_alt} images are missing alternative text.")
                else: st.success("✅ All images have alt text attributes.")
                
                if broken_imgs > 0: st.error(f"❌ Found {broken_imgs} broken/404 images.")
                else: st.success("✅ All images resolve successfully.")

                # 2. Link Health
                st.subheader("Hyperlink Health")
                links = soup.find_all("a", href=True)
                broken_int, broken_ext, ext_no_nofollow = 0, 0, 0
                
                for link in links[:20]:
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
                        
                if broken_int > 0: st.error(f"❌ Broken Internal Links (404): {broken_int}")
                else: st.success("✅ No broken internal links found.")
                
                if broken_ext > 0 or ext_no_nofollow > 0:
                    st.warning(f"⚠️ External Links: {broken_ext} broken | {ext_no_nofollow} missing 'nofollow'.")
                else:
                    st.success("✅ External links are healthy and follow 'nofollow' rules.")

                # 3. Spelling Check (Pure Python implementation)
                st.subheader("Spelling Check")
                paragraphs = [p.text for p in soup.find_all("p")]
                article_text = " ".join(paragraphs)
                
                if article_text.strip():
                    # Clean punctuation and split into individual words
                    words = re.findall(r'\b[a-zA-Z]+\b', article_text)
                    misspelled = spell.unknown(words)
                    
                    # Ignore common short web noise or proper nouns capitalized in text
                    filtered_misspelled = [w for w in misspelled if len(w) > 2 and not w[0].isupper()]
                    
                    if filtered_misspelled:
                        st.error(f"❌ Found {len(filtered_misspelled)} unique potential spelling mistake(s).")
                        with st.expander("Review Typos Found"):
                            st.write(", ".join(list(filtered_misspelled)[:15]))
                    else:
                        st.success("✅ Spelling clean! No obvious typos found.")
                else:
                    st.info("ℹ️ Could not locate standard text paragraphs to evaluate.")

        except Exception as main_err:
            st.error(f"An unexpected error occurred during processing: {main_err}")
