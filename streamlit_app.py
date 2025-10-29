from streamlit_searchbox import st_searchbox
import py3Dmol
from stmol import showmol
from streamlit_ketcher import st_ketcher
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import time
from PIL import Image
from io import BytesIO
import base64

# Page configuration
st.set_page_config(
    page_title="Molecule Visualizer",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for black and white theme with animations
st.markdown("""
<style>
    /* Main theme colors */
    .stApp {
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
        color: #ffffff;
    }
    
    /* Animated gradient border for main container */
    @keyframes borderGlow {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 255, 255, 0.2); }
        50% { box-shadow: 0 0 40px rgba(255, 255, 255, 0.4); }
    }
    
    /* Smooth fade-in animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Pulse animation for loading */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Card styling with animation */
    .molecule-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        animation: fadeIn 0.6s ease-out;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .molecule-card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.3);
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(255, 255, 255, 0.1);
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #ffffff !important;
        animation: fadeIn 0.8s ease-out;
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(255, 255, 255, 0.08);
        border-left: 3px solid #ffffff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        animation: fadeIn 0.7s ease-out;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(255, 255, 255, 0.3);
    }
    
    /* Search box styling */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #ffffff;
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Loading animation */
    .loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
    }
    
    /* Table styling */
    .dataframe {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: #ffffff;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.15);
    }
    
    /* Image container styling */
    .image-container {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .image-container:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 20px rgba(255, 255, 255, 0.1);
    }
    
    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(255, 255, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv("DB_URL"))
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# Initialize database
def init_db():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS molecule_history (
                        id SERIAL PRIMARY KEY,
                        compound_name VARCHAR(255),
                        cid INTEGER,
                        formula VARCHAR(100),
                        molecular_weight FLOAT,
                        smiles TEXT,
                        searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            st.error(f"Database initialization error: {e}")

# Search PubChem for molecules
def search_pubchem(query):
    if not query or len(query) < 2:
        return []
    
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{query}/cids/JSON?list_return=listkey"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'IdentifierList' in data:
                cids = data['IdentifierList']['CID'][:10]
                results = []
                for cid in cids:
                    prop_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/Title,MolecularFormula/JSON"
                    prop_response = requests.get(prop_url, timeout=5)
                    if prop_response.status_code == 200:
                        prop_data = prop_response.json()
                        if 'PropertyTable' in prop_data and 'Properties' in prop_data['PropertyTable']:
                            props = prop_data['PropertyTable']['Properties'][0]
                            results.append(props['Title'])
                return results
    except:
        pass
    return []

# Get molecule images from PubChem
@st.cache_data(ttl=3600)
def get_molecule_images(cid):
    try:
        # 2D Structure Image
        image_2d_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG?image_size=large"
        response_2d = requests.get(image_2d_url)
        img_2d = Image.open(BytesIO(response_2d.content))
        
        # 3D Conformer Image
        image_3d_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG?image_size=large&image_type=3d"
        response_3d = requests.get(image_3d_url)
        img_3d = Image.open(BytesIO(response_3d.content))
        
        return img_2d, img_3d
    except Exception as e:
        st.warning(f"Could not load images: {e}")
        return None, None

# Get molecule data from PubChem
@st.cache_data(ttl=3600)
def get_molecule_data(name):
    try:
        # Get CID
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON"
        response = requests.get(url)
        cid = response.json()['IdentifierList']['CID'][0]
        
        # Get properties including SMILES
        prop_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES,IsomericSMILES/JSON"
        prop_response = requests.get(prop_url)
        properties = prop_response.json()['PropertyTable']['Properties'][0]
        
        # Get 3D structure (SDF format)
        sdf_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF"
        sdf_response = requests.get(sdf_url)
        sdf_data = sdf_response.text
        
        return {
            'cid': cid,
            'formula': properties.get('MolecularFormula', 'N/A'),
            'weight': properties.get('MolecularWeight', 'N/A'),
            'iupac': properties.get('IUPACName', 'N/A'),
            'smiles': properties.get('CanonicalSMILES', properties.get('IsomericSMILES', 'N/A')),
            'sdf': sdf_data
        }
    except Exception as e:
        st.error(f"Error fetching molecule data: {e}")
        return None

# Save to database
def save_to_db(name, data):
    conn = get_db_connection()
    if conn and data:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO molecule_history (compound_name, cid, formula, molecular_weight, smiles)
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, data['cid'], data['formula'], data['weight'], data['smiles']))
                conn.commit()
        except Exception as e:
            st.error(f"Error saving to database: {e}")

# Get search history
def get_history():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT compound_name, formula, molecular_weight, searched_at
                    FROM molecule_history
                    ORDER BY searched_at DESC
                    LIMIT 10
                """)
                return cur.fetchall()
        except Exception as e:
            st.error(f"Error fetching history: {e}")
    return []

# Visualize molecule with py3Dmol
def visualize_molecule(sdf_data, style='stick'):
    view = py3Dmol.view(width=800, height=600)
    view.addModel(sdf_data, 'sdf')
    
    if style == 'stick':
        view.setStyle({'stick': {'colorscheme': 'whiteCarbon'}})
    elif style == 'sphere':
        view.setStyle({'sphere': {'colorscheme': 'whiteCarbon', 'scale': 0.3}})
    elif style == 'cartoon':
        view.setStyle({'cartoon': {'color': 'white'}})
    
    view.setBackgroundColor('#000000')
    view.zoomTo()
    view.spin(True)
    
    return view

# Main app
def main():
    init_db()
    
    # Header with animation
    st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
    st.title("🧬 Molecular Structure Visualizer")
    st.markdown("*Explore molecular structures from PubChem in stunning 2D, 3D, and interactive views*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
        st.header("⚙️ Settings")
        
        style = st.selectbox(
            "3D Visualization Style",
            ["stick", "sphere", "cartoon"],
            help="Choose how the molecule is displayed in 3D"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
        st.header("📊 Recent Searches")
        history = get_history()
        if history:
            for item in history:
                st.markdown(f"**{item['compound_name']}**")
                st.caption(f"{item['formula']} • {item['searched_at'].strftime('%Y-%m-%d %H:%M')}")
                st.divider()
        else:
            st.info("No search history yet")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content - Tabs for different modes
    tab1, tab2 = st.tabs(["🔍 Search Molecules", "✏️ Draw Molecule"])
    
    with tab1:
        # Search box with autocomplete
        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
        selected_molecule = st_searchbox(
            search_pubchem,
            key="molecule_search",
            placeholder="🔍 Search for a molecule (e.g., aspirin, caffeine, glucose)...",
            clear_on_submit=False
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if selected_molecule:
            with st.spinner("Loading molecular structure..."):
                time.sleep(0.5)
                data = get_molecule_data(selected_molecule)
                
                if data:
                    save_to_db(selected_molecule, data)
                    
                    # Create two columns for layout
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Nested tabs for different visualizations
                        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📐 2D Structure", "🔮 3D Structure", "🌐 Interactive 3D"])
                        
                        with viz_tab1:
                            st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                            st.subheader(f"2D Structure: {selected_molecule}")
                            img_2d, _ = get_molecule_images(data['cid'])
                            if img_2d:
                                st.image(img_2d, use_container_width=True)
                                
                                # Download button for 2D image
                                buf = BytesIO()
                                img_2d.save(buf, format='PNG')
                                st.download_button(
                                    label="📥 Download 2D Structure",
                                    data=buf.getvalue(),
                                    file_name=f"{selected_molecule}_2D.png",
                                    mime="image/png"
                                )
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with viz_tab2:
                            st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                            st.subheader(f"3D Picture: {selected_molecule}")
                            _, img_3d = get_molecule_images(data['cid'])
                            if img_3d:
                                st.image(img_3d, use_container_width=True)
                                
                                # Download button for 3D image
                                buf = BytesIO()
                                img_3d.save(buf, format='PNG')
                                st.download_button(
                                    label="📥 Download 3D Picture",
                                    data=buf.getvalue(),
                                    file_name=f"{selected_molecule}_3D.png",
                                    mime="image/png"
                                )
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with viz_tab3:
                            st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                            st.subheader(f"Interactive 3D: {selected_molecule}")
                            view = visualize_molecule(data['sdf'], style)
                            showmol(view, height=600, width=800)
                            
                            # Download button for SDF file
                            st.download_button(
                                label="📥 Download SDF File",
                                data=data['sdf'],
                                file_name=f"{selected_molecule}.sdf",
                                mime="chemical/x-mdl-sdfile"
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                        st.subheader("📋 Molecular Properties")
                        
                        st.metric("PubChem CID", f"{data['cid']}")
                        st.metric("Molecular Formula", data['formula'])
                        st.metric("Molecular Weight", f"{data['weight']} g/mol")
                        
                        with st.expander("🔬 IUPAC Name", expanded=False):
                            st.write(data['iupac'])
                        
                        with st.expander("🧪 SMILES Notation", expanded=False):
                            st.code(data['smiles'], language=None)
                            st.download_button(
                                label="📋 Copy SMILES",
                                data=data['smiles'],
                                file_name=f"{selected_molecule}_smiles.txt",
                                mime="text/plain"
                            )
                        
                        st.markdown(f"[🔗 View on PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/{data['cid']})")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
        st.subheader("✏️ Draw Your Own Molecule")
        st.markdown("*Use the Ketcher editor below to draw custom molecular structures*")
        
        # Ketcher molecule editor
        molecule_data = st_ketcher()
        
        if molecule_data:
            st.success("✅ Molecule drawn successfully!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                with st.expander("📄 Molecule Data (MOL format)", expanded=False):
                    st.code(molecule_data, language=None)
                    st.download_button(
                        label="📥 Download MOL File",
                        data=molecule_data,
                        file_name="custom_molecule.mol",
                        mime="chemical/x-mdl-molfile"
                    )
            
            with col2:
                st.info("💡 **Tip:** You can draw complex structures and export them for further analysis!")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()d inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
