import streamlit as st
import py3Dmol
from stmol import showmol
from streamlit_ketcher import st_ketcher
import pubchempy as pcp
from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import time
from PIL import Image
from io import BytesIO
import requests
import pandas as pd

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
    
    /* Rotate animation */
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
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
    
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.7) !important;
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
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        color: #ffffff !important;
    }
    
    /* Success/Info/Warning boxes */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_db_connection():
    try:
        db_url = os.getenv("DB_URL")
        if db_url:
            conn = psycopg2.connect(db_url)
            return conn
        else:
            return None
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
                        inchi TEXT,
                        logp FLOAT,
                        tpsa FLOAT,
                        searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            st.error(f"Database initialization error: {e}")

# Get molecule from PubChem using pubchempy
@st.cache_data(ttl=3600)
def get_molecule_data(name):
    try:
        # Search for compounds
        compounds = pcp.get_compounds(name, 'name')
        
        if not compounds:
            return None
        
        compound = compounds[0]
        
        # Get properties
        mol_data = {
            'cid': compound.cid,
            'formula': compound.molecular_formula,
            'weight': compound.molecular_weight,
            'iupac': compound.iupac_name if compound.iupac_name else 'N/A',
            'smiles': compound.canonical_smiles if compound.canonical_smiles else 'N/A',
            'inchi': compound.inchi if compound.inchi else 'N/A',
            'inchikey': compound.inchikey if compound.inchikey else 'N/A',
        }
        
        # Get additional properties if available
        try:
            mol_data['xlogp'] = compound.xlogp if compound.xlogp else 'N/A'
            mol_data['tpsa'] = compound.tpsa if compound.tpsa else 'N/A'
            mol_data['complexity'] = compound.complexity if compound.complexity else 'N/A'
            mol_data['h_bond_donor'] = compound.h_bond_donor_count if compound.h_bond_donor_count else 'N/A'
            mol_data['h_bond_acceptor'] = compound.h_bond_acceptor_count if compound.h_bond_acceptor_count else 'N/A'
            mol_data['rotatable_bonds'] = compound.rotatable_bond_count if compound.rotatable_bond_count else 'N/A'
        except:
            pass
        
        # Get 3D SDF
        try:
            sdf_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{compound.cid}/SDF?record_type=3d"
            sdf_response = requests.get(sdf_url, timeout=10)
            if sdf_response.status_code == 200:
                mol_data['sdf'] = sdf_response.text
            else:
                mol_data['sdf'] = None
        except:
            mol_data['sdf'] = None
        
        return mol_data
        
    except Exception as e:
        st.error(f"Error fetching molecule data: {e}")
        return None

# Get RDKit molecule from SMILES
@st.cache_data
def get_rdkit_mol(smiles):
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return mol
        return None
    except:
        return None

# Calculate molecular descriptors using RDKit
def calculate_descriptors(mol):
    if not mol:
        return {}
    
    try:
        descriptors = {
            'LogP': round(Descriptors.MolLogP(mol), 2),
            'TPSA': round(Descriptors.TPSA(mol), 2),
            'Mol Weight': round(Descriptors.MolWt(mol), 2),
            'Num H Donors': Descriptors.NumHDonors(mol),
            'Num H Acceptors': Descriptors.NumHAcceptors(mol),
            'Num Rotatable Bonds': Descriptors.NumRotatableBonds(mol),
            'Num Aromatic Rings': Descriptors.NumAromaticRings(mol),
            'Num Aliphatic Rings': Descriptors.NumAliphaticRings(mol),
        }
        return descriptors
    except Exception as e:
        st.error(f"Error calculating descriptors: {e}")
        return {}

# Get molecule images from PubChem
@st.cache_data(ttl=3600)
def get_molecule_images(cid):
    try:
        # 2D Structure Image
        image_2d_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG?image_size=large"
        response_2d = requests.get(image_2d_url, timeout=10)
        img_2d = Image.open(BytesIO(response_2d.content))
        
        # 3D Conformer Image
        image_3d_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG?image_size=large&image_type=3d"
        response_3d = requests.get(image_3d_url, timeout=10)
        img_3d = Image.open(BytesIO(response_3d.content))
        
        return img_2d, img_3d
    except Exception as e:
        return None, None

# Save to database
def save_to_db(name, data):
    conn = get_db_connection()
    if conn and data:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO molecule_history 
                    (compound_name, cid, formula, molecular_weight, smiles, inchi, logp, tpsa)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, 
                    data['cid'], 
                    data['formula'], 
                    data['weight'], 
                    data['smiles'],
                    data.get('inchi', None),
                    data.get('xlogp', None),
                    data.get('tpsa', None)
                ))
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
            return []
    return []

# Visualize molecule with py3Dmol
def visualize_molecule(sdf_data, style='stick'):
    try:
        view = py3Dmol.view(width=800, height=600)
        view.addModel(sdf_data, 'sdf')
        
        if style == 'stick':
            view.setStyle({'stick': {'colorscheme': 'whiteCarbon', 'radius': 0.15}})
        elif style == 'sphere':
            view.setStyle({'sphere': {'colorscheme': 'whiteCarbon', 'scale': 0.3}})
        elif style == 'ball_stick':
            view.setStyle({'stick': {'colorscheme': 'whiteCarbon'}, 'sphere': {'scale': 0.3, 'colorscheme': 'whiteCarbon'}})
        
        view.setBackgroundColor('#000000')
        view.zoomTo()
        view.spin(True)
        
        return view
    except Exception as e:
        st.error(f"Error creating 3D visualization: {e}")
        return None

# Main app
def main():
    init_db()
    
    # Header with animation
    st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
    st.title("🧬 Advanced Molecular Structure Visualizer")
    st.markdown("*Powered by PubChemPy, RDKit, and Py3Dmol for comprehensive molecular analysis*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
        st.header("⚙️ Visualization Settings")
        
        style = st.selectbox(
            "3D Style",
            ["stick", "sphere", "ball_stick"],
            help="Choose how the molecule is displayed in 3D"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
        st.header("📊 Recent Searches")
        history = get_history()
        if history:
            for item in history:
                if st.button(f"🔄 {item['compound_name']}", key=f"hist_{item['compound_name']}"):
                    st.session_state.search_query = item['compound_name']
                st.caption(f"{item['formula']} • {item['searched_at'].strftime('%Y-%m-%d %H:%M')}")
                st.divider()
        else:
            st.info("No search history yet")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content - Tabs for different modes
    tab1, tab2 = st.tabs(["🔍 Search Molecules", "✏️ Draw Molecule"])
    
    with tab1:
        # Simple text input for search
        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
        
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        
        search_query = st.text_input(
            "🔍 Search for a molecule",
            value=st.session_state.search_query,
            placeholder="Enter molecule name (e.g., aspirin, caffeine, glucose)...",
            help="Type the name of any molecule to search PubChem"
        )
        
        # Popular molecules quick access
        st.markdown("**Quick Access:**")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("💊 Aspirin"):
                search_query = "aspirin"
        with col2:
            if st.button("☕ Caffeine"):
                search_query = "caffeine"
        with col3:
            if st.button("🍬 Glucose"):
                search_query = "glucose"
        with col4:
            if st.button("💧 Water"):
                search_query = "water"
        with col5:
            if st.button("🧪 Ethanol"):
                search_query = "ethanol"
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if search_query:
            with st.spinner("🔬 Analyzing molecular structure..."):
                time.sleep(0.3)
                data = get_molecule_data(search_query)
                
                if data:
                    save_to_db(search_query, data)
                    
                    # Get RDKit molecule for additional analysis
                    rdkit_mol = get_rdkit_mol(data['smiles']) if data['smiles'] != 'N/A' else None
                    
                    # Create layout
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Nested tabs for different visualizations
                        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📐 2D Structure", "🔮 3D Picture", "🌐 Interactive 3D"])
                        
                        with viz_tab1:
                            st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                            st.subheader(f"2D Structure: {search_query.title()}")
                            
                            img_2d, _ = get_molecule_images(data['cid'])
                            if img_2d:
                                st.image(img_2d, use_container_width=True)
                                buf = BytesIO()
                                img_2d.save(buf, format='PNG')
                                st.download_button(
                                    label="📥 Download 2D Structure",
                                    data=buf.getvalue(),
                                    file_name=f"{search_query}_2D.png",
                                    mime="image/png"
                                )
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with viz_tab2:
                            st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                            st.subheader(f"3D Picture: {search_query.title()}")
                            _, img_3d = get_molecule_images(data['cid'])
                            if img_3d:
                                st.image(img_3d, use_container_width=True)
                                buf = BytesIO()
                                img_3d.save(buf, format='PNG')
                                st.download_button(
                                    label="📥 Download 3D Picture",
                                    data=buf.getvalue(),
                                    file_name=f"{search_query}_3D.png",
                                    mime="image/png"
                                )
                            else:
                                st.warning("3D image not available for this molecule")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with viz_tab3:
                            st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                            st.subheader(f"Interactive 3D: {search_query.title()}")
                            
                            if data.get('sdf'):
                                view = visualize_molecule(data['sdf'], style)
                                if view:
                                    showmol(view, height=600, width=800)
                                    st.download_button(
                                        label="📥 Download SDF File",
                                        data=data['sdf'],
                                        file_name=f"{search_query}.sdf",
                                        mime="chemical/x-mdl-sdfile"
                                    )
                            else:
                                st.warning("3D structure not available for this molecule")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                        st.subheader("📋 Basic Properties")
                        
                        st.metric("PubChem CID", f"{data['cid']}")
                        st.metric("Molecular Formula", data['formula'])
                        st.metric("Molecular Weight", f"{data['weight']:.2f} g/mol")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Display molecular descriptors
                        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                        st.subheader("🔬 Molecular Descriptors")
                        
                        # Use RDKit descriptors if available
                        if rdkit_mol:
                            rdkit_descriptors = calculate_descriptors(rdkit_mol)
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("LogP", rdkit_descriptors.get('LogP', 'N/A'))
                                st.metric("H Donors", rdkit_descriptors.get('Num H Donors', 'N/A'))
                                st.metric("Aromatic Rings", rdkit_descriptors.get('Num Aromatic Rings', 'N/A'))
                            
                            with col_b:
                                st.metric("TPSA", f"{rdkit_descriptors.get('TPSA', 'N/A')} Ų")
                                st.metric("H Acceptors", rdkit_descriptors.get('Num H Acceptors', 'N/A'))
                                st.metric("Rotatable Bonds", rdkit_descriptors.get('Num Rotatable Bonds', 'N/A'))
                        else:
                            # Fallback to PubChem properties
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("XLogP", data.get('xlogp', 'N/A'))
                                st.metric("H Donors", data.get('h_bond_donor', 'N/A'))
                                st.metric("Complexity", data.get('complexity', 'N/A'))
                            
                            with col_b:
                                st.metric("TPSA", f"{data.get('tpsa', 'N/A')}" + (" Ų" if data.get('tpsa') != 'N/A' else ""))
                                st.metric("H Acceptors", data.get('h_bond_acceptor', 'N/A'))
                                st.metric("Rotatable Bonds", data.get('rotatable_bonds', 'N/A'))
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                        st.subheader("🧪 Chemical Identifiers")
                        
                        with st.expander("🔬 IUPAC Name", expanded=False):
                            st.code(data['iupac'], language=None)
                        
                        with st.expander("🧪 SMILES", expanded=False):
                            st.code(data['smiles'], language=None)
                            st.download_button(
                                label="📋 Download SMILES",
                                data=data['smiles'],
                                file_name=f"{search_query}_smiles.txt",
                                mime="text/plain",
                                key="smiles_download"
                            )
                        
                        with st.expander("🔑 InChI", expanded=False):
                            st.code(data.get('inchi', 'N/A'), language=None)
                        
                        with st.expander("🔐 InChIKey", expanded=False):
                            st.code(data.get('inchikey', 'N/A'), language=None)
                        
                        st.markdown(f"[🔗 View on PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/{data['cid']})")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error(f"❌ Could not find molecule: {search_query}")
                    st.info("💡 Try searching with a different name or chemical formula")
    
    with tab2:
        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
        st.subheader("✏️ Draw Your Own Molecule")
        st.markdown("*Use the Ketcher editor below to draw custom molecular structures*")
        
        # Ketcher molecule editor
        molecule_data = st_ketcher()
        
        if molecule_data:
            st.success("✅ Molecule drawn successfully!")
            
            # Try to convert to RDKit mol
            try:
                mol = Chem.MolFromMolBlock(molecule_data)
                if mol:
                    smiles = Chem.MolToSmiles(mol)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                        st.subheader("📊 Calculated Properties")
                        descriptors = calculate_descriptors(mol)
                        
                        for key, value in descriptors.items():
                            st.metric(key, value)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
                        st.subheader("🧪 Generated SMILES")
                        st.code(smiles, language=None)
                        st.download_button(
                            label="📋 Download SMILES",
                            data=smiles,
                            file_name="custom_molecule_smiles.txt",
                            mime="text/plain",
                            key="custom_smiles"
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
            except:
                st.warning("Could not analyze the drawn structure")
            
            st.markdown('<div class="molecule-card">', unsafe_allow_html=True)
            with st.expander("📄 Molecule Data (MOL format)", expanded=False):
                st.code(molecule_data, language=None)
                st.download_button(
                    label="📥 Download MOL File",
                    data=molecule_data,
                    file_name="custom_molecule.mol",
                    mime="chemical/x-mdl-molfile"
                )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("💡 **Tip:** Draw a molecule above to see its properties and generate SMILES notation!")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
