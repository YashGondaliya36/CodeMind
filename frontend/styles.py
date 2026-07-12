"""
frontend/styles.py — Modern Premium CSS Stylesheet for Streamlit
================================================================
Defines CSS injection strings and HTML helpers to override default
Streamlit styles, delivering a dark-theme glassmorphism experience.
"""

import streamlit as st


def inject_custom_css():
    """Injects custom stylesheet overrides into the Streamlit application."""
    css = """
    <style>
    /* ── Import Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700&display=swap');

    /* ── Global Font Overrides ── */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-weight: 600 !important;
    }

    /* ── Glassmorphism Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: rgba(17, 19, 26, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* ── Clean Main App Area ── */
    .main {
        background-color: #0d0e12 !important;
    }

    /* ── Premium Gradient Text & Headers ── */
    .gradient-text {
        background: linear-gradient(135deg, #a855f7 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* ── Glassmorphic Cards ── */
    .glass-card {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
    }
    
    /* ── Connection Status Pill ── */
    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-online {
        background-color: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .status-offline {
        background-color: rgba(239, 68, 68, 0.1);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }
    
    /* ── Source File Tags ── */
    .source-tag {
        display: inline-block;
        background-color: rgba(59, 130, 246, 0.08) !important;
        color: #60a5fa !important;
        border: 1px solid rgba(59, 130, 246, 0.15) !important;
        padding: 2px 8px !important;
        border-radius: 4px !important;
        font-size: 0.75rem !important;
        margin-right: 6px !important;
        margin-bottom: 6px !important;
        font-family: monospace;
    }

    /* ── Custom Divider ── */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(168, 85, 247, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%);
        margin: 20px 0;
    }
    
    /* Hide default Streamlit header/footer for premium feel */
    header[data-testid="stHeader"] {
        background: rgba(13, 14, 18, 0.6) !important;
        backdrop-filter: blur(8px) !important;
    }
    footer {
        visibility: hidden;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def glass_card_start(title=None, subtitle=None):
    """HTML string helper to begin a glassmorphic content block."""
    header_html = ""
    if title:
        header_html += f"<h3 style='margin-top:0;margin-bottom:4px;'>{title}</h3>"
    if subtitle:
        header_html += f"<p style='color:rgba(255,255,255,0.6);margin-bottom:16px;font-size:0.9rem;'>{subtitle}</p>"
        
    return f"""
    <div class="glass-card">
        {header_html}
    """


def glass_card_end():
    """HTML string helper to close a glassmorphic content block."""
    return "</div>"


def connection_badge(online: bool):
    """Displays a status pill indicating backend availability."""
    if online:
        return '<span class="status-pill status-online">🟢 System Online</span>'
    return '<span class="status-pill status-offline">🔴 System Offline</span>'
