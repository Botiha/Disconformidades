import asyncio
from datetime import datetime, timedelta
import calendar
from playwright.async_api import async_playwright
from app.config import URL, USERNAME, PASSWORD, OUTPUT_DIR

def get_date_range():
    """
    Calculates the start and end dates for the search.
    Start: ~2 weeks ago (14 days).
    End: Last day of the current month.
    """
    today = datetime.now()
    
    # Start date: 14 days ago
    start_date = today - timedelta(days=14)
    
    # End date: Last day of the current month
    last_day = calendar.monthrange(today.year, today.month)[1]
    end_date = today.replace(day=last_day)
    
    # Format as DD/MM/YYYY (Standard for Chilean sites)
    return start_date.strftime("%d/%m/%Y"), end_date.strftime("%d/%m/%Y")

async def run_bot():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"Navigating to {URL}...")
        await page.goto(URL)
        
        # --- Login Flow ---
        # The page might redirect to the SSO (hub.coordinador.cl)
        try:
            print("Checking for login form...")
            # We use selectors from the user's recording
            # Wait for the username field to be visible
            await page.wait_for_selector("role=textbox[name='Nombre de usuario']", timeout=10000)
            
            print("Login form detected. Logging in...")
            await page.get_by_role("textbox", name="Nombre de usuario").fill(USERNAME)
            await page.get_by_role("textbox", name="Contraseña").fill(PASSWORD)
            await page.get_by_text("Ingresar").click()
            print("Login credentials submitted.")
            
            # Wait for navigation after login
            await page.wait_for_load_state('networkidle')
            
        except Exception as e:
            print(f"Login step skipped or failed (might be already logged in?): {e}")

        # --- Navigation ---
        print("Navigating to 'Consulta Disconformidades'...")
        try:
            await page.locator("a").filter(has_text="Consultas").click()
            await page.get_by_text("> Consultas Aplicación").click()
            await page.get_by_role("listitem").filter(has_text="Consulta Disconformidades").click()
        except Exception as e:
             print(f"Navigation failed: {e}")
             await browser.close()
             return

        # --- Form Filling ---
        start_str, end_str = get_date_range()
        print(f"Filling dates: {start_str} - {end_str}")
        
        # Fill dates
        # We try to fill directly. If the site enforces a picker, this might need adjustment.
        await page.get_by_role("textbox", name="Fecha Creación del caso desde:").fill(start_str)
        await page.get_by_role("textbox", name="Fecha Creación del caso desde:").press("Enter")
        
        await page.get_by_role("textbox", name="Fecha Creación del caso hasta:").fill(end_str)
        await page.get_by_role("textbox", name="Fecha Creación del caso hasta:").press("Enter")
        
        # Fill Rut Deudor (from recording)
        # Assuming this is a constant requirement for the user's search
        rut_deudor = "77316204" 
        await page.get_by_role("textbox", name="Rut Deudor:").fill(rut_deudor)
        
        # Search
        print("Searching...")
        await page.get_by_role("button", name="Buscar").click()
        
        # --- Download ---
        print("Waiting for download button...")
        # Wait for the export button to be available (search might take a moment)
        try:
            # We wait for the download event before clicking
            async with page.expect_download(timeout=60000) as download_info:
                await page.get_by_title("Exportar a Excel").click()
                
            download = await download_info.value
            
            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"disconformidades_{timestamp}.xlsx"
            save_path = OUTPUT_DIR / filename
            
            await download.save_as(save_path)
            print(f"SUCCESS: File saved to: {save_path}")
            
        except Exception as e:
            print(f"Download failed: {e}")
            
        # Optional: Wait a bit to see the result
        await asyncio.sleep(5)
        await browser.close()
