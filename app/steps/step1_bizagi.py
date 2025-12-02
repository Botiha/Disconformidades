import asyncio
import logging
import tomllib
from datetime import datetime, timedelta
import calendar
from pathlib import Path
from playwright.async_api import async_playwright
from app.config import URL, USERNAME, PASSWORD

# --- Configuration Loading ---
def load_config():
    """Loads configuration from config.toml."""
    try:
        with open("config.toml", "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        logging.error("config.toml not found. Using default settings.")
        return {
            "fechas": {"fecha_inicio": "", "fecha_final": ""},
            "rutas": {"output_folder": "output"},
        }

# --- Logging Setup ---
def setup_logging():
    """Sets up logging to file and console."""
    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    
    # File handler
    file_handler = logging.FileHandler("bot.log")
    file_handler.setFormatter(log_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def get_date_range(config):
    """
    Calculates the start and end dates for the search based on config.
    """
    fecha_inicio_str = config["fechas"].get("fecha_inicio")
    fecha_final_str = config["fechas"].get("fecha_final")

    if fecha_inicio_str and fecha_final_str:
        logging.info(f"Using dates from config: {fecha_inicio_str} to {fecha_final_str}")
        start_date = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        end_date = datetime.strptime(fecha_final_str, "%Y-%m-%d")
    else:
        logging.info("Using default date range (last 14 days to end of month).")
        today = datetime.now()
        start_date = today - timedelta(days=14)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day)
        
    return start_date.strftime("%d/%m/%Y"), end_date.strftime("%d/%m/%Y")

async def run_step1(config):
    output_folder = Path(config["rutas"]["output_folder"])
    output_folder.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        logging.info(f"Navigating to {URL}...")
        try:
            await page.goto(URL)
        except Exception as e:
            logging.error(f"Failed to navigate to URL: {e}")
            await browser.close()
            return

        # --- Login Flow ---
        try:
            logging.info("Checking for login form...")
            await page.wait_for_selector("role=textbox[name='Nombre de usuario']", timeout=10000)
            
            logging.info("Login form detected. Logging in...")
            await page.get_by_role("textbox", name="Nombre de usuario").fill(USERNAME)
            await page.get_by_role("textbox", name="Contraseña").fill(PASSWORD)
            
            # Screenshot with credentials filled (before clicking)
            await page.screenshot(path="docs/screenshots/1_login_filled.png")
            logging.info("Screenshot taken: 1_login_filled.png")

            await page.get_by_text("Ingresar").click()
            logging.info("Login credentials submitted.")
            
            await page.wait_for_load_state('networkidle')
            
        except Exception as e:
            logging.warning(f"Login step skipped or failed (might be already logged in?): {e}")

        # --- Navigation ---
        logging.info("Navigating to 'Consulta Disconformidades'...")
        try:
            await page.locator("a").filter(has_text="Consultas").click()
            await page.get_by_text("> Consultas Aplicación").click()
            await page.get_by_role("listitem").filter(has_text="Consulta Disconformidades").click()
            await page.wait_for_load_state('networkidle')
            await page.screenshot(path="docs/screenshots/2_navigation.png")
            logging.info("Screenshot taken: 2_navigation.png")
        except Exception as e:
             logging.error(f"Navigation failed: {e}")
             await browser.close()
             return

        # --- Form Filling ---
        start_str, end_str = get_date_range(config)
        logging.info(f"Filling dates: {start_str} - {end_str}")
        
        try:
            await page.get_by_role("textbox", name="Fecha Creación del caso desde:").fill(start_str)
            await page.get_by_role("textbox", name="Fecha Creación del caso desde:").press("Enter")
            
            await page.get_by_role("textbox", name="Fecha Creación del caso hasta:").fill(end_str)
            await page.get_by_role("textbox", name="Fecha Creación del caso hasta:").press("Enter")
            
            rut_deudor = "77316204" 
            await page.get_by_role("textbox", name="Rut Deudor:").fill(rut_deudor)
            
            logging.info("Searching...")
            await page.screenshot(path="docs/screenshots/3_form_filled.png")
            await page.get_by_role("button", name="Buscar").click()
        except Exception as e:
            logging.error(f"Failed to fill or submit the search form: {e}")
            await browser.close()
            return

        # --- Download ---
        logging.info("Waiting for download button...")
        try:
            async with page.expect_download(timeout=60000) as download_info:
                await page.get_by_title("Exportar a Excel").click()
                
            download = await download_info.value
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"disconformidades_{timestamp}.xlsx"
            save_path = output_folder / filename
            
            await download.save_as(save_path)
            logging.info(f"SUCCESS: File saved to: {save_path}")
            await page.screenshot(path="docs/screenshots/4_download_complete.png")
            
        except Exception as e:
            logging.error(f"Download failed: {e}")
            
        await asyncio.sleep(5)
        await browser.close()

async def main():
    setup_logging()
    config = load_config()
    await run_bot(config)

if __name__ == "__main__":
    asyncio.run(main())
