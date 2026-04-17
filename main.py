import time
import json
import os
import requests
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_FILE = 'config.json'

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

class ZPLHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.watch_folder = config.get('watch_folder', './labels')
        self.printer_name = config.get('printer_name', 'Tu_Impresora')
        self.width = config.get('label_width_inches', 4)
        self.height = config.get('label_height_inches', 8)
        self.dpmm = config.get('print_density_dpmm', 8)
        self.zoom = config.get('zoom_percentage', 80) / 100.0
        
        # Ensure the watch directory exists
        if not os.path.exists(self.watch_folder):
            os.makedirs(self.watch_folder)

    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        if filepath.endswith('.txt') or filepath.endswith('.zpl'):
            # Wait a brief moment to ensure file is fully written by the OS before reading
            time.sleep(0.5)
            self.process_file(filepath)

    def on_moved(self, event):
        if event.is_directory:
            return
        
        # event.dest_path contains the new file name/path
        filepath = event.dest_path
        if filepath.endswith('.txt') or filepath.endswith('.zpl'):
            time.sleep(0.5)
            self.process_file(filepath)

    def process_file(self, filepath):
        print(f"Processing new file: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                zpl_data = f.read()

            pdf_path = filepath + '.pdf'
            
            # Use Labelary API to convert ZPL to PDF
            print("Converting ZPL to PDF via Labelary...")
            success = self.convert_zpl_to_pdf(zpl_data, pdf_path)
            
            if success:
                print(f"PDF generated successfully: {pdf_path}")
                if self.zoom != 1.0:
                    self.scale_pdf(pdf_path, self.zoom)
                
                self.print_pdf(pdf_path)
                
                # Change file extension to .printed
                new_filepath = filepath + '.printed'
                os.replace(filepath, new_filepath)
                print(f"File marked as printed: {new_filepath}")
            else:
                print("Failed to convert ZPL to PDF.")
                
        except Exception as e:
            print(f"Error processing file {filepath}: {e}")

    def convert_zpl_to_pdf(self, zpl_data, output_pdf_path):
        """
        Labelary API is an excellent choice for this. It is widely used, standard, 
        and very reliable for generating PDFs or PNGs from ZPL code.
        """
        url = f'http://api.labelary.com/v1/printers/{self.dpmm}dpmm/labels/{self.width}x{self.height}/0/'
        headers = {'Accept': 'application/pdf'}
        
        try:
            response = requests.post(url, headers=headers, data=zpl_data.encode('utf-8'))
            response.raise_for_status()
            
            with open(output_pdf_path, 'wb') as f:
                f.write(response.content)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Labelary API request failed: {e}")
            return False

    def scale_pdf(self, pdf_path, scale_factor):
        print(f"Scaling PDF to {scale_factor * 100}% ...")
        try:
            # Import inline to avoid forcing it if not installed yet
            from pypdf import PdfReader, PdfWriter, Transformation
            
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            
            for page in reader.pages:
                w = float(page.mediabox.width)
                h = float(page.mediabox.height)
                
                # Center the scaled content
                tx = (w - (w * scale_factor)) / 2
                ty = (h - (h * scale_factor)) / 2
                
                transform = Transformation().scale(sx=scale_factor, sy=scale_factor).translate(tx=tx, ty=ty)
                page.add_transformation(transform)
                writer.add_page(page)
                
            with open(pdf_path, "wb") as f:
                writer.write(f)
            print("PDF scaled successfully.")
        except ImportError:
            print("Error: The 'pypdf' package is not installed. Skipping zoom scaling.")
            print("Please install it using: pip install pypdf")
        except Exception as e:
            print(f"Failed to scale PDF: {e}")

    def print_pdf(self, pdf_path):
        print(f"Sending to printer: {self.printer_name}")
        
        if sys.platform == 'win32':
            # Windows approach
            try:
                import win32api
                
                # Get absolute path for Windows ShellExecute
                abs_pdf_path = os.path.abspath(pdf_path)
                
                # Using 'printto' verb to print via the default application registered for PDFs
                win32api.ShellExecute(0, "printto", abs_pdf_path, f'"{self.printer_name}"', ".", 0)
                print("Print job submitted successfully via Windows spooler.")
            except ImportError:
                print("Error: The 'pywin32' package is required for Windows printing.")
                print("Please install it using: pip install pywin32")
            except Exception as e:
                print(f"Failed to submit Windows print job: {e}")
                
        else:
            # macOS / Linux approach
            try:
                # Using 'lp' which is the standard CUPS command available on macOS and Linux
                subprocess.run(["lp", "-d", self.printer_name, pdf_path], check=True)
                print("Print job submitted successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to submit print job: {e}")
            except FileNotFoundError:
                print("The 'lp' command was not found. Are you on macOS/Linux with CUPS installed?")

def main():
    if not os.path.exists(CONFIG_FILE):
        print(f"Configuration file '{CONFIG_FILE}' not found. Creating a default one.")
        default_config = {
            "watch_folder": "./labels",
            "printer_name": "Tu_Impresora",
            "label_width_inches": 4,
            "label_height_inches": 8,
            "print_density_dpmm": 8,
            "zoom_percentage": 80
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        print("Please edit 'config.json' with your specifics and run again.")
        return

    config = load_config()
    watch_folder = config.get('watch_folder', './labels')
    
    if not os.path.exists(watch_folder):
        os.makedirs(watch_folder)

    event_handler = ZPLHandler(config)
    observer = Observer()
    observer.schedule(event_handler, watch_folder, recursive=False)
    observer.start()
    
    print(f"Watching folder: {watch_folder}")
    print(f"Printer configured: {config.get('printer_name')}")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping observer...")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
