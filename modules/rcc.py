import aiohttp
import json
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# --- API Configuration ---
API_URL = "https://revangevichelinfo.vercel.app/api/rc"

# --- Main Command ---
@Client.on_message(filters.command("rc", prefix) & filters.me)
async def get_vehicle_info_detailed(client: Client, message: Message):
    """Fetches and formats vehicle registration details with extensive parsing."""
    try:
        vehicle_number = None
        if len(message.command) > 1:
            vehicle_number = message.command[1]
        elif message.reply_to_message and message.reply_to_message.text:
            vehicle_number = message.reply_to_message.text
        else:
            await message.edit(
                "<b>Usage:</b> <code>.rc [vehicle_number]</code> or reply to a message."
            )
            return

        cleaned_number = vehicle_number.strip().upper()
        await message.edit(f"<code>🔍 Fetching details for {cleaned_number}...</code>")

        async with aiohttp.ClientSession() as session:
            params = {"number": cleaned_number}
            async with session.get(API_URL, params=params) as response:
                if response.status != 200:
                    await message.edit(f"<b>API Error:</b> Status code <code>{response.status}</code>")
                    return

                try:
                    data = await response.json()
                except json.JSONDecodeError:
                    await message.edit("<b>Error:</b> The API returned an invalid response.")
                    return
                
                # --- Adaptive Parsing Logic ---
                info = {}
                if "results" in data and data["results"]:
                    info = data["results"][0]
                elif isinstance(data, dict):
                    info = data

                if not info:
                    await message.edit(f"<b>No details found for `{cleaned_number}`.</b>")
                    return

                # --- Detailed Field Extraction with Fallbacks ---
                def get_val(keys, default="N/A"):
                    for key in keys:
                        if info.get(key):
                            return info[key]
                    return default

                # Owner Details
                owner_name = get_val(['OwnerName', 'owner_name', 'ownerName'])
                father_name = get_val(['FatherName', 'father_name', 'fatherName'])
                owner_sr_no = get_val(['OwnerSerialNumber', 'owner_serial_no'])
                
                # Vehicle Specs
                model_name = get_val(['Model', 'model_name', 'modelName'])
                maker_name = get_val(['Maker', 'maker_model', 'makerName'])
                vehicle_class = get_val(['VehicleClass', 'vehicle_class'])
                fuel_type = get_val(['FuelType', 'fuel_type'])
                fuel_norms = get_val(['FuelNorms', 'fuel_norms'])

                # Registration Details
                reg_no = get_val(['RegistrationNumber', 'rc_number', 'reg_no'])
                reg_date = get_val(['RegistrationDate', 'registration_date'])
                rto_name = get_val(['rto', 'RtoName', 'rto_name'])
                address = get_val(['address', 'Address'])
                city = get_val(['city', 'City'])
                phone = get_val(['phone', 'Phone'])

                # Insurance & Finance
                insurer = get_val(['InsuranceCompanyName', 'insurance_company'])
                policy_no = get_val(['InsurancePolicyNumber', 'insurance_no'])
                financier = get_val(['Financier', 'financier_name'])

                # Dates & Validity
                fitness_upto = get_val(['FitnessUpto', 'fitness_upto'])
                insurance_upto = get_val(['InsuranceUpto', 'insurance_upto', 'insurance_expiry'])
                tax_upto = get_val(['TaxUpto', 'tax_upto'])
                puc_no = get_val(['PuccNumber', 'puc_no'])
                puc_upto = get_val(['PuccUpto', 'puc_upto'])

                # --- Build the beautifully arranged response ---
                details_text = f"✅ <b>Details for Vehicle:</b> <code>{reg_no}</code>\n\n"

                details_text += "👤 <b>Owner Information</b>\n"
                details_text += f"  - <i>Name:</i> <code>{owner_name}</code>\n"
                details_text += f"  - <i>Father's Name:</i> <code>{father_name}</code>\n"
                details_text += f"  - <i>Owner Sr No:</i> <code>{owner_sr_no}</code>\n\n"

                details_text += "🚗 <b>Vehicle Specifications</b>\n"
                details_text += f"  - <i>Model:</i> <code>{model_name}</code>\n"
                details_text += f"  - <i>Maker:</i> <code>{maker_name}</code>\n"
                details_text += f"  - <i>Class:</i> <code>{vehicle_class}</code>\n"
                details_text += f"  - <i>Fuel Type:</i> <code>{fuel_type}</code>\n"
                details_text += f"  - <i>Fuel Norms:</i> <code>{fuel_norms}</code>\n\n"

                details_text += "📄 <b>Registration & RTO</b>\n"
                details_text += f"  - <i>Registration Date:</i> <code>{reg_date}</code>\n"
                details_text += f"  - <i>RTO:</i> <code>{rto_name}</code>\n"
                details_text += f"  - <i>Address:</i> <code>{address}</code>\n"
                details_text += f"  - <i>City:</i> <code>{city}</code>\n"
                details_text += f"  - <i>Phone:</i> <code>{phone}</code>\n\n"
                
                details_text += "🏦 <b>Insurance & Finance</b>\n"
                details_text += f"  - <i>Insurer:</i> <code>{insurer}</code>\n"
                details_text += f"  - <i>Policy No:</i> <code>{policy_no}</code>\n"
                details_text += f"  - <i>Financier:</i> <code>{financier}</code>\n\n"

                details_text += "📅 <i>Validity Dates</i>\n"
                details_text += f"  - <i>Fitness Upto:</i> <code>{fitness_upto}</code>\n"
                details_text += f"  - <i>Insurance Upto:</i> <code>{insurance_upto}</code>\n"
                details_text += f"  - <i>Road Tax Upto:</> <code>{tax_upto}</code>\n"
                details_text += f"  - <i>PUCC No:</i> <code>{puc_no}</code>\n"
                details_text += f"  - <i>PUCC Upto:</i> <code>{puc_upto}</code>\n"
                details_text += f"<b><i>Credit:</i></b> <i>@lullilal</i>\n"

                await message.edit(details_text)

    except Exception as e:
        await message.edit(f"<b>An unexpected error occurred:</b> <code>{e}</code>")

# --- Add to modules_help ---
modules_help["vehicle_info"] = {
    "rc [number/reply]": "Fetches and displays detailed registration info for an Indian vehicle."
}