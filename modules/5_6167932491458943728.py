import aiohttp
import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# --- Dependency Check ---
try:
    import pubchempy as pcp
except ImportError:
    pcp = None

# A complete, internal periodic table for fast and reliable atomic data lookups.
PERIODIC_TABLE = {
    'H': {'protons': 1, 'mass': 1, 'config': '1s¹', 'valency': '±1'}, 'He': {'protons': 2, 'mass': 4, 'config': '1s²', 'valency': '0'},
    'Li': {'protons': 3, 'mass': 7, 'config': '[He] 2s¹', 'valency': '1'}, 'Be': {'protons': 4, 'mass': 9, 'config': '[He] 2s²', 'valency': '2'},
    'B': {'protons': 5, 'mass': 11, 'config': '[He] 2s² 2p¹', 'valency': '3'}, 'C': {'protons': 6, 'mass': 12, 'config': '[He] 2s² 2p²', 'valency': '±4, 2'},
    'N': {'protons': 7, 'mass': 14, 'config': '[He] 2s² 2p³', 'valency': '±3, 5, 4, 2'}, 'O': {'protons': 8, 'mass': 16, 'config': '[He] 2s² 2p⁴', 'valency': '-2'},
    'F': {'protons': 9, 'mass': 19, 'config': '[He] 2s² 2p⁵', 'valency': '-1'}, 'Ne': {'protons': 10, 'mass': 20, 'config': '[He] 2s² 2p⁶', 'valency': '0'},
    'Na': {'protons': 11, 'mass': 23, 'config': '[Ne] 3s¹', 'valency': '1'}, 'Mg': {'protons': 12, 'mass': 24, 'config': '[Ne] 3s²', 'valency': '2'},
    'Al': {'protons': 13, 'mass': 27, 'config': '[Ne] 3s² 3p¹', 'valency': '3'}, 'Si': {'protons': 14, 'mass': 28, 'config': '[Ne] 3s² 3p²', 'valency': '±4'},
    'P': {'protons': 15, 'mass': 31, 'config': '[Ne] 3s² 3p³', 'valency': '±3, 5, 4'}, 'S': {'protons': 16, 'mass': 32, 'config': '[Ne] 3s² 3p⁴', 'valency': '±2, 4, 6'},
    'Cl': {'protons': 17, 'mass': 35, 'config': '[Ne] 3s² 3p⁵', 'valency': '±1, 3, 5, 7'}, 'Ar': {'protons': 18, 'mass': 40, 'config': '[Ne] 3s² 3p⁶', 'valency': '0'},
    'K': {'protons': 19, 'mass': 39, 'config': '[Ar] 4s¹', 'valency': '1'}, 'Ca': {'protons': 20, 'mass': 40, 'config': '[Ar] 4s²', 'valency': '2'},
    'Sc': {'protons': 21, 'mass': 45, 'config': '[Ar] 3d¹ 4s²', 'valency': '3'}, 'Ti': {'protons': 22, 'mass': 48, 'config': '[Ar] 3d² 4s²', 'valency': '4, 3'},
    'V': {'protons': 23, 'mass': 51, 'config': '[Ar] 3d³ 4s²', 'valency': '5, 4, 3, 2'}, 'Cr': {'protons': 24, 'mass': 52, 'config': '[Ar] 3d⁵ 4s¹', 'valency': '2, 3, 6'},
    'Mn': {'protons': 25, 'mass': 55, 'config': '[Ar] 3d⁵ 4s²', 'valency': '2, 3, 4, 6, 7'}, 'Fe': {'protons': 26, 'mass': 56, 'config': '[Ar] 3d⁶ 4s²', 'valency': '2, 3'},
    'Co': {'protons': 27, 'mass': 59, 'config': '[Ar] 3d⁷ 4s²', 'valency': '2, 3'}, 'Ni': {'protons': 28, 'mass': 59, 'config': '[Ar] 3d⁸ 4s²', 'valency': '2, 3'},
    'Cu': {'protons': 29, 'mass': 64, 'config': '[Ar] 3d¹⁰ 4s¹', 'valency': '1, 2'}, 'Zn': {'protons': 30, 'mass': 65, 'config': '[Ar] 3d¹⁰ 4s²', 'valency': '2'},
    'Ga': {'protons': 31, 'mass': 70, 'config': '[Ar] 3d¹⁰ 4s² 4p¹', 'valency': '3'}, 'Ge': {'protons': 32, 'mass': 73, 'config': '[Ar] 3d¹⁰ 4s² 4p²', 'valency': '4'},
    'As': {'protons': 33, 'mass': 75, 'config': '[Ar] 3d¹⁰ 4s² 4p³', 'valency': '±3, 5'}, 'Se': {'protons': 34, 'mass': 79, 'config': '[Ar] 3d¹⁰ 4s² 4p⁴', 'valency': '-2, 4, 6'},
    'Br': {'protons': 35, 'mass': 80, 'config': '[Ar] 3d¹⁰ 4s² 4p⁵', 'valency': '±1, 3, 5, 7'}, 'Kr': {'protons': 36, 'mass': 84, 'config': '[Ar] 3d¹⁰ 4s² 4p⁶', 'valency': '2'},
    'Rb': {'protons': 37, 'mass': 85, 'config': '[Kr] 5s¹', 'valency': '1'}, 'Sr': {'protons': 38, 'mass': 88, 'config': '[Kr] 5s²', 'valency': '2'},
    'Y': {'protons': 39, 'mass': 89, 'config': '[Kr] 4d¹ 5s²', 'valency': '3'}, 'Zr': {'protons': 40, 'mass': 91, 'config': '[Kr] 4d² 5s²', 'valency': '4'},
    'Nb': {'protons': 41, 'mass': 93, 'config': '[Kr] 4d⁴ 5s¹', 'valency': '3, 5'}, 'Mo': {'protons': 42, 'mass': 96, 'config': '[Kr] 4d⁵ 5s¹', 'valency': '2, 3, 4, 5, 6'},
    'Tc': {'protons': 43, 'mass': 98, 'config': '[Kr] 4d⁵ 5s²', 'valency': '4, 6, 7'}, 'Ru': {'protons': 44, 'mass': 101, 'config': '[Kr] 4d⁷ 5s¹', 'valency': '2, 3, 4, 6, 8'},
    'Rh': {'protons': 45, 'mass': 103, 'config': '[Kr] 4d⁸ 5s¹', 'valency': '2, 3, 4'}, 'Pd': {'protons': 46, 'mass': 106, 'config': '[Kr] 4d¹⁰', 'valency': '2, 4'},
    'Ag': {'protons': 47, 'mass': 108, 'config': '[Kr] 4d¹⁰ 5s¹', 'valency': '1'}, 'Cd': {'protons': 48, 'mass': 112, 'config': '[Kr] 4d¹⁰ 5s²', 'valency': '2'},
    'In': {'protons': 49, 'mass': 115, 'config': '[Kr] 4d¹⁰ 5s² 5p¹', 'valency': '3'}, 'Sn': {'protons': 50, 'mass': 119, 'config': '[Kr] 4d¹⁰ 5s² 5p²', 'valency': '2, 4'},
    'Sb': {'protons': 51, 'mass': 122, 'config': '[Kr] 4d¹⁰ 5s² 5p³', 'valency': '±3, 5'}, 'Te': {'protons': 52, 'mass': 128, 'config': '[Kr] 4d¹⁰ 5s² 5p⁴', 'valency': '-2, 4, 6'},
    'I': {'protons': 53, 'mass': 127, 'config': '[Kr] 4d¹⁰ 5s² 5p⁵', 'valency': '±1, 3, 5, 7'}, 'Xe': {'protons': 54, 'mass': 131, 'config': '[Kr] 4d¹⁰ 5s² 5p⁶', 'valency': '2, 4, 6'},
    'Cs': {'protons': 55, 'mass': 133, 'config': '[Xe] 6s¹', 'valency': '1'}, 'Ba': {'protons': 56, 'mass': 137, 'config': '[Xe] 6s²', 'valency': '2'},
    'La': {'protons': 57, 'mass': 139, 'config': '[Xe] 5d¹ 6s²', 'valency': '3'}, 'Ce': {'protons': 58, 'mass': 140, 'config': '[Xe] 4f¹ 5d¹ 6s²', 'valency': '3, 4'},
    'Pr': {'protons': 59, 'mass': 141, 'config': '[Xe] 4f³ 6s²', 'valency': '3'}, 'Nd': {'protons': 60, 'mass': 144, 'config': '[Xe] 4f⁴ 6s²', 'valency': '3'},
    'Pm': {'protons': 61, 'mass': 145, 'config': '[Xe] 4f⁵ 6s²', 'valency': '3'}, 'Sm': {'protons': 62, 'mass': 150, 'config': '[Xe] 4f⁶ 6s²', 'valency': '2, 3'},
    'Eu': {'protons': 63, 'mass': 152, 'config': '[Xe] 4f⁷ 6s²', 'valency': '2, 3'}, 'Gd': {'protons': 64, 'mass': 157, 'config': '[Xe] 4f⁷ 5d¹ 6s²', 'valency': '3'},
    'Tb': {'protons': 65, 'mass': 159, 'config': '[Xe] 4f⁹ 6s²', 'valency': '3'}, 'Dy': {'protons': 66, 'mass': 163, 'config': '[Xe] 4f¹⁰ 6s²', 'valency': '3'},
    'Ho': {'protons': 67, 'mass': 165, 'config': '[Xe] 4f¹¹ 6s²', 'valency': '3'}, 'Er': {'protons': 68, 'mass': 167, 'config': '[Xe] 4f¹² 6s²', 'valency': '3'},
    'Tm': {'protons': 69, 'mass': 169, 'config': '[Xe] 4f¹³ 6s²', 'valency': '3'}, 'Yb': {'protons': 70, 'mass': 173, 'config': '[Xe] 4f¹⁴ 6s²', 'valency': '2, 3'},
    'Lu': {'protons': 71, 'mass': 175, 'config': '[Xe] 4f¹⁴ 5d¹ 6s²', 'valency': '3'}, 'Hf': {'protons': 72, 'mass': 178, 'config': '[Xe] 4f¹⁴ 5d² 6s²', 'valency': '4'},
    'Ta': {'protons': 73, 'mass': 181, 'config': '[Xe] 4f¹⁴ 5d³ 6s²', 'valency': '5'}, 'W': {'protons': 74, 'mass': 184, 'config': '[Xe] 4f¹⁴ 5d⁴ 6s²', 'valency': '2, 3, 4, 5, 6'},
    'Re': {'protons': 75, 'mass': 186, 'config': '[Xe] 4f¹⁴ 5d⁵ 6s²', 'valency': '-1, 2, 4, 6, 7'}, 'Os': {'protons': 76, 'mass': 190, 'config': '[Xe] 4f¹⁴ 5d⁶ 6s²', 'valency': '2, 3, 4, 6, 8'},
    'Ir': {'protons': 77, 'mass': 192, 'config': '[Xe] 4f¹⁴ 5d⁷ 6s²', 'valency': '2, 3, 4, 6'}, 'Pt': {'protons': 78, 'mass': 195, 'config': '[Xe] 4f¹⁴ 5d⁹ 6s¹', 'valency': '2, 4'},
    'Au': {'protons': 79, 'mass': 197, 'config': '[Xe] 4f¹⁴ 5d¹⁰ 6s¹', 'valency': '1, 3'}, 'Hg': {'protons': 80, 'mass': 201, 'config': '[Xe] 4f¹⁴ 5d¹⁰ 6s²', 'valency': '1, 2'},
    'Tl': {'protons': 81, 'mass': 204, 'config': '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p¹', 'valency': '1, 3'}, 'Pb': {'protons': 82, 'mass': 207, 'config': '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p²', 'valency': '2, 4'},
    'Bi': {'protons': 83, 'mass': 209, 'config': '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p³', 'valency': '3, 5'}, 'Po': {'protons': 84, 'mass': 209, 'config': '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p⁴', 'valency': '2, 4, 6'},
    'At': {'protons': 85, 'mass': 210, 'config': '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p⁵', 'valency': '±1, 3, 5'}, 'Rn': {'protons': 86, 'mass': 222, 'config': '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p⁶', 'valency': '2'},
    'Fr': {'protons': 87, 'mass': 223, 'config': '[Rn] 7s¹', 'valency': '1'}, 'Ra': {'protons': 88, 'mass': 226, 'config': '[Rn] 7s²', 'valency': '2'},
    'Ac': {'protons': 89, 'mass': 227, 'config': '[Rn] 6d¹ 7s²', 'valency': '3'}, 'Th': {'protons': 90, 'mass': 232, 'config': '[Rn] 6d² 7s²', 'valency': '4'},
    'Pa': {'protons': 91, 'mass': 231, 'config': '[Rn] 5f² 6d¹ 7s²', 'valency': '4, 5'}, 'U': {'protons': 92, 'mass': 238, 'config': '[Rn] 5f³ 6d¹ 7s²', 'valency': '3, 4, 5, 6'},
    'Np': {'protons': 93, 'mass': 237, 'config': '[Rn] 5f⁴ 6d¹ 7s²', 'valency': '3, 4, 5, 6'}, 'Pu': {'protons': 94, 'mass': 244, 'config': '[Rn] 5f⁶ 7s²', 'valency': '3, 4, 5, 6'},
    'Am': {'protons': 95, 'mass': 243, 'config': '[Rn] 5f⁷ 7s²', 'valency': '3, 4, 5, 6'}, 'Cm': {'protons': 96, 'mass': 247, 'config': '[Rn] 5f⁷ 6d¹ 7s²', 'valency': '3, 4'},
    'Bk': {'protons': 97, 'mass': 247, 'config': '[Rn] 5f⁹ 7s²', 'valency': '3, 4'}, 'Cf': {'protons': 98, 'mass': 251, 'config': '[Rn] 5f¹⁰ 7s²', 'valency': '3'},
    'Es': {'protons': 99, 'mass': 252, 'config': '[Rn] 5f¹¹ 7s²', 'valency': '3'}, 'Fm': {'protons': 100, 'mass': 257, 'config': '[Rn] 5f¹² 7s²', 'valency': '3'},
    'Md': {'protons': 101, 'mass': 258, 'config': '[Rn] 5f¹³ 7s²', 'valency': '3'}, 'No': {'protons': 102, 'mass': 259, 'config': '[Rn] 5f¹⁴ 7s²', 'valency': '2, 3'},
    'Lr': {'protons': 103, 'mass': 262, 'config': '[Rn] 5f¹⁴ 7s² 7p¹', 'valency': '3'}, 'Rf': {'protons': 104, 'mass': 267, 'config': '[Rn] 5f¹⁴ 6d² 7s²', 'valency': '4'},
    'Db': {'protons': 105, 'mass': 268, 'config': '[Rn] 5f¹⁴ 6d³ 7s²', 'valency': 'N/A'}, 'Sg': {'protons': 106, 'mass': 271, 'config': '[Rn] 5f¹⁴ 6d⁴ 7s²', 'valency': 'N/A'},
    'Bh': {'protons': 107, 'mass': 272, 'config': '[Rn] 5f¹⁴ 6d⁵ 7s²', 'valency': 'N/A'}, 'Hs': {'protons': 108, 'mass': 277, 'config': '[Rn] 5f¹⁴ 6d⁶ 7s²', 'valency': 'N/A'},
    'Mt': {'protons': 109, 'mass': 276, 'config': '[Rn] 5f¹⁴ 6d⁷ 7s²', 'valency': 'N/A'}, 'Ds': {'protons': 110, 'mass': 281, 'config': '[Rn] 5f¹⁴ 6d⁹ 7s¹', 'valency': 'N/A'},
    'Rg': {'protons': 111, 'mass': 280, 'config': '[Rn] 5f¹⁴ 6d¹⁰ 7s¹', 'valency': 'N/A'}, 'Cn': {'protons': 112, 'mass': 285, 'config': '[Rn] 5f¹⁴ 6d¹⁰ 7s²', 'valency': 'N/A'},
    'Nh': {'protons': 113, 'mass': 284, 'config': '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p¹', 'valency': 'N/A'}, 'Fl': {'protons': 114, 'mass': 289, 'config': '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p²', 'valency': 'N/A'},
    'Mc': {'protons': 115, 'mass': 288, 'config': '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p³', 'valency': 'N/A'}, 'Lv': {'protons': 116, 'mass': 293, 'config': '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p⁴', 'valency': 'N/A'},
    'Ts': {'protons': 117, 'mass': 294, 'config': '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p⁵', 'valency': 'N/A'}, 'Og': {'protons': 118, 'mass': 294, 'config': '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p⁶', 'valency': 'N/A'},
}

async def fetch_wiki_properties(session, term):
    """Fetches and parses physical properties from a Wikipedia infobox."""
    properties = {
        'Melting Point': 'N/A', 'Boiling Point': 'N/A', 'Dipole Moment': 'N/A'
    }
    try:
        params = {
            "action": "query", "format": "json", "prop": "revisions",
            "rvprop": "content", "titles": term.replace(' ', '_'), "redirects": 1
        }
        async with session.get("https://en.wikipedia.org/w/api.php", params=params) as resp:
            if resp.status != 200: return properties
            
            data = await resp.json()
            pages = data.get("query", {}).get("pages", {})
            if not pages: return properties
            
            content = list(pages.values())[0].get("revisions", [{}])[0].get("*", "")
            if not content: return properties

            patterns = {
                'Melting Point': r'\|\s*MeltingPoint\s*=\s*([^|\n]+)',
                'Boiling Point': r'\|\s*BoilingPoint\s*=\s*([^|\n]+)',
                'Dipole Moment': r'\|\s*DipoleMoment\s*=\s*([^|\n]+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = re.sub(r'<ref.*?>.*?</ref>|{{.*?}}', '', match.group(1)).strip()
                    properties[key] = value if value else 'N/A'

    except Exception:
        pass
    return properties

# --- Main Command ---
@Client.on_message(filters.command("chemical", prefix) & filters.me)
async def get_chemical_info_advanced(client: Client, message: Message):
    """Fetches and displays advanced, detailed information about a chemical molecule."""
    if pcp is None:
        await message.edit(
            "<b>Error: Dependency missing!</b>\n\n"
            "The <code>pubchempy</code> library is not installed.\n"
            "Please add it to your <b>requirements.txt</b> and restart the bot.",
            parse_mode=enums.ParseMode.HTML
        )
        return

    if len(message.command) < 2:
        await message.edit("<b>Usage:</b> <code>.chemical [molecule]</code>", parse_mode=enums.ParseMode.HTML)
        return

    query = " ".join(message.command[1:])
    await message.edit(f"<code>🔬 Searching PubChem for '{query}'...</code>")

    try:
        results = pcp.get_compounds(query, 'name')
        if not results:
            results = pcp.get_compounds(query, 'formula')

        if not results:
            await message.edit(f"<b>Could not find any information for '{query}'.</b>")
            return

        compound = results[0]

        # --- Data Calculation & Fetching ---
        total_protons, total_neutrons = 0, 0
        electron_config_text = ""
        
        atom_tuples = re.findall(r'([A-Z][a-z]*)(\d*)', compound.molecular_formula)
        unique_elements = {symbol for symbol, _ in atom_tuples}

        for symbol in sorted(list(unique_elements)):
            if symbol in PERIODIC_TABLE:
                data = PERIODIC_TABLE[symbol]
                electron_config_text += f"  - <b>{symbol}:</b> <code>{data['config']}</code> (Valency: {data['valency']})\n"

        for symbol, count_str in atom_tuples:
            count = int(count_str) if count_str else 1
            if symbol in PERIODIC_TABLE:
                element_data = PERIODIC_TABLE[symbol]
                total_protons += element_data['protons'] * count
                total_neutrons += (element_data['mass'] - element_data['protons']) * count
        
        magnetic_property = "<u>Likely Diamagnetic</u>" if total_protons % 2 == 0 else "<u>Likely Paramagnetic</u>"
        
        charge = getattr(compound, 'charge', 0)
        exact_mass = getattr(compound, 'exact_mass', 'N/A')
        tpsa = getattr(compound, 'tpsa', 'N/A')
        xlogp = getattr(compound, 'xlogp', 'N/A')
        
        inchi = getattr(compound, 'inchi', 'N/A')
        inchikey = getattr(compound, 'inchikey', 'N/A')
        isomeric_smiles = getattr(compound, 'isomeric_smiles', 'N/A')
        common_name = compound.synonyms[0] if compound.synonyms else 'N/A'
        
        async with aiohttp.ClientSession() as session:
            wiki_props = await fetch_wiki_properties(session, compound.iupac_name or query)
            melting_point = wiki_props['Melting Point']
            boiling_point = wiki_props['Boiling Point']
            dipole_moment = wiki_props['Dipole Moment']
            
            wiki_summary = ""
            try:
                search_term = compound.iupac_name or query
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{search_term.replace(' ', '_')}"
                async with session.get(wiki_url) as resp:
                    if resp.status == 200:
                        wiki_data = await resp.json()
                        summary = wiki_data.get('extract')
                        if summary:
                            wiki_summary = f"\n📖 <b><u>Description</u></b>\n<code>{summary[:500]}...</code>"
            except Exception:
                pass
        
        # --- Format the new, advanced output ---
        details_text = f"🧪 <b><i>Chemical Details for: <spoiler><u>{compound.iupac_name or query.title()}</u></spoiler></i></b>\n\n"
        
        details_text += "ℹ️ <b><u>General Info</u></b>\n"
        details_text += f"  - <b>Common Name:</b> <i>{common_name}</i>\n"
        details_text += f"  - <b>Formula:</b> <code>{compound.molecular_formula}</code>\n"
        details_text += f"  - <b>Molecular Weight:</b> <code>{compound.molecular_weight} g/mol</code>\n"
        details_text += f"  - <b>Charge:</b> <code>{charge}</code>\n"
        
        if charge != 0:
            details_text += f"  - <b>Ionic Nature:</b> This is a <u>polyatomic ion</u>.\n\n"
        else:
            details_text += f"  - <b>Ionic Nature:</b> This is a <u>covalent compound</u>.\n\n"

        details_text += "🌡️ <b><u>Physical Properties</u></b>\n"
        details_text += f"  - <b>Melting Point:</b> <code>{melting_point}</code>\n"
        details_text += f"  - <b>Boiling Point:</b> <code>{boiling_point}</code>\n"
        details_text += f"  - <b>Dipole Moment:</b> <code>{dipole_moment}</code>\n\n"
        
        # Re-adding all the previous sections
        details_text += "🔬 <b><u>Structural Properties</u></b>\n"
        details_text += f"  - <b>Complexity:</b> <code>{getattr(compound, 'complexity', 'N/A')}</code>\n"
        details_text += f"  - <b>Heavy Atom Count:</b> <code>{getattr(compound, 'heavy_atom_count', 'N/A')}</code>\n"
        details_text += f"  - <b>Rotatable Bonds:</b> <code>{getattr(compound, 'rotatable_bond_count', 'N/A')}</code>\n"
        details_text += f"  - <b>H-Bond Donors:</b> <code>{getattr(compound, 'h_bond_donor_count', 'N/A')}</code>\n"
        details_text += f"  - <b>H-Bond Acceptors:</b> <code>{getattr(compound, 'h_bond_acceptor_count', 'N/A')}</code>\n\n"

        details_text += "⚛️ <b><u>Atomic Composition</u></b>\n"
        details_text += f"  - <b>Total Protons:</b> <code>{total_protons}</code>\n"
        details_text += f"  - <b>Total Electrons:</b> <code>{total_protons - charge}</code>\n"
        details_text += f"  - <b>Total Neutrons (approx.):</b> <code>{total_neutrons}</code>\n"
        details_text += f"  - <b>Magnetic Property:</b> {magnetic_property}\n\n"
        details_text += "⚗️ <b>Physicochemical Properties:</b>\n"
        details_text += f"  - <b>Exact Mass:</b> <code>{exact_mass}</code>\n"
        details_text += f"  - <b>LogP (hydrophobicity):</b> <code>{xlogp}</code>\n"
        details_text += f"  - <b>Topological Polar Surface Area:</b> <code>{tpsa} Å²</code>\n\n"
        details_text += "🔑 <b>Identifiers:</b>\n"
        details_text += f"  - <b>InChI:</b> <code>{inchi}</code>\n"
        details_text += f"  - <b>InChIKey:</b> <code>{inchikey}</code>\n"
        details_text += f"  - <b>SMILES:</b> <code>{isomeric_smiles}</code>\n\n"
        

        if electron_config_text:
            details_text += "⚡ <b><u>Electron Configurations</u></b>\n" + electron_config_text + "\n"

        details_text += f"🔗 <a href='https://pubchem.ncbi.nlm.nih.gov/compound/{compound.cid}#section=3D-Conformer'>View 3D Model</a>"
        
        if wiki_summary:
            details_text += wiki_summary

        await message.edit(details_text, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        await message.edit(f"<b>An error occurred:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)

# --- Add to modules_help ---
modules_help["chemistry"] = {
    "chemical [name/formula]": "Fetches advanced details about a chemical molecule."
}

