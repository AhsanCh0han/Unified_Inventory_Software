# sales.py
import sys
import os
import sqlite3
import json
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QDialogButtonBox, QLabel, QMessageBox,
    QStatusBar, QSpinBox, QDoubleSpinBox, QToolBar, QMenu, QMenuBar,
    QFileDialog, QGroupBox, QGridLayout, QFrame, QHeaderView, QInputDialog,
    QListWidget, QListWidgetItem, QAbstractItemView,
    QCheckBox, QTextEdit
)
from PyQt6.QtGui import (
    QColor, QAction, QIcon, QKeySequence, QFont, QPalette, 
    QBrush, QPainter, QPageSize, QShortcut, QTextDocument, QPixmap
)
from PyQt6.QtCore import Qt, QTimer, QDate, pyqtSignal, QSettings, QTextStream, QByteArray, QSizeF
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PyQt6.QtGui import QPageLayout
from PyQt6.QtCore import QMarginsF
from PyQt6.QtGui import QPageLayout
# from invoice_printer import InvoiceGenerator, prepare_bill_data_from_sale, InvoiceFactory
from invoice_printer import InvoiceGenerator, prepare_bill_data_from_sale, InvoiceFactory
import traceback
# ========== IMPORT PRINT.PY MODULE ==========
try:
    # Try to import the invoice printer module
    # Check for both possible filenames
    try:
        import invoice_printer
    except ImportError:
        # Try importing as print module
        import print as invoice_printer_test
    PRINT_MODULE_AVAILABLE = True
    print("Invoice printer module imported successfully")
except ImportError as e:
    print(f"Error importing invoice printer module: {e}")
    # Create a dummy module to avoid crashes
    class DummyInvoiceGenerator:
        def print_invoice(self, *args, **kwargs):
            return False
        def generate_invoice_pdf(self, *args, **kwargs):
            return None
        def generate_invoice_html(self, *args, **kwargs):
            return ""
    
    class DummyInvoicePreviewDialog:
        def __init__(self, *args, **kwargs):
            pass
        def exec(self):
            return 0
    
    invoice_printer = type('obj', (object,), {
        'InvoiceGenerator': InvoiceGenerator,
        'InvoicePreviewDialog': InvoicePreviewDialog
    })
    PRINT_MODULE_AVAILABLE = False


# Global exception handler
def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to prevent crashes"""
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"Unhandled exception:\n{error_msg}")
    
    # Try to show error in a message box if possible
    try:
        from PyQt6.QtWidgets import QMessageBox, QApplication
        app = QApplication.instance()
        if app:
            QMessageBox.critical(None, "Application Error", 
                               f"An unexpected error occurred:\n\n{exc_value}\n\n"
                               f"The application will continue running.")
    except:
        pass

# Install global exception handler
sys.excepthook = handle_exception

# ========== ENHANCED INTEGRATED PRINTING SYSTEM ==========
class EnhancedIntegratedPrintingSystem:
    """Class to integrate professional printing with sales system"""
    
    @staticmethod
    def prepare_bill_data(sale_window):
        """Prepare bill data in the format required by print.py"""
        if not sale_window.sale_items:
            return None
        
        # Calculate totals
        subtotal = sum(item['total_price'] for item in sale_window.sale_items)
        discount = sale_window.discount_input.value()
        discount_type = sale_window.discount_type.currentText()
        tax_rate = sale_window.tax_spinbox.value()
        
        if discount_type == "Percentage":
            discount_amount = subtotal * (discount / 100)
        else:
            discount_amount = discount
        
        tax_amount = subtotal * (tax_rate / 100)
        grand_total = max(0, subtotal - discount_amount + tax_amount)
        
        # Get current datetime
        now = datetime.now()
        
        items = []
        for item in sale_window.sale_items:
            items.append({
                'description': item['display_name'],
                'qty': item['quantity'],
                'price': item['price'],
                'total': item['total_price']
            })
        
        # Return bill data with all required fields
        return {
            'bill_number': sale_window.bill_number,
            'customer': sale_window.customer_input.text().strip() or "WALK-IN CUSTOMER",
            'items': items,
            'subtotal': subtotal,
            'discount': discount_amount,
            'discount_type': 'Amount',  # Always use Amount for consistency
            'tax_rate': tax_rate,
            'grand_total': grand_total,
            'date': now.strftime("%d/%m/%Y"),
            'time': now.strftime("%I:%M %p")
        }
    
    @staticmethod
    def print_invoice(sale_window):
        """Print invoice using professional generator"""
        if not PRINT_MODULE_AVAILABLE:
            QMessageBox.critical(sale_window, "Module Error", 
                               "Print module not available. Make sure print.py is in the same directory.")
            return False
        
        if not sale_window.sale_items:
            QMessageBox.warning(sale_window, "No Items", "No items to print!")
            return False
        
        try:
            # Prepare bill data
            bill_data = EnhancedIntegratedPrintingSystem.prepare_bill_data(sale_window)
            
            if not bill_data:
                return False
            
            # Create professional invoice generator
            generator = ProfessionalInvoiceGenerator()
            
            # Print directly
            success = generator.print_invoice(bill_data, sale_window)
            
            if success:
                sale_window.status_label.setText(f"Invoice #{bill_data['bill_number']} printed successfully!")
                return True
            else:
                sale_window.status_label.setText("Printing cancelled")
                return False
                
        except Exception as e:
            QMessageBox.critical(sale_window, "Print Error", f"Could not print invoice: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def preview_invoice(sale_window):
        """Preview invoice using professional generator"""
        if not PRINT_MODULE_AVAILABLE:
            QMessageBox.critical(sale_window, "Module Error", 
                               "Print module not available. Make sure print.py is in the same directory.")
            return False
        
        if not sale_window.sale_items:
            QMessageBox.warning(sale_window, "No Items", "No items to preview!")
            return False
        
        try:
            # Prepare bill data
            bill_data = EnhancedIntegratedPrintingSystem.prepare_bill_data(sale_window)
            
            if not bill_data:
                return False
            
            # Use ProfessionalInvoicePreviewDialog
            dialog = ProfessionalInvoicePreviewDialog(bill_data, sale_window)
            dialog.exec()
            return True
                
        except Exception as e:
            QMessageBox.critical(sale_window, "Preview Error", f"Could not preview invoice: {str(e)}")
            return False
    
    @staticmethod
    def print_invoice(sale_window):
        """Print invoice using print.py library"""
        if not PRINT_MODULE_AVAILABLE:
            QMessageBox.critical(sale_window, "Module Error", 
                               "Print module not available. Make sure print.py is in the same directory.")
            return False
        
        if not sale_window.sale_items:
            QMessageBox.warning(sale_window, "No Items", "No items to print!")
            return False
        
        try:
            # Prepare bill data
            bill_data = EnhancedIntegratedPrintingSystem.prepare_bill_data(sale_window)
            
            if not bill_data:
                return False
            
            # Create invoice generator using print.py
            generator = invoice_printer.InvoiceGenerator()
            
            # Print directly using print_invoice method
            success = generator.print_invoice(bill_data, sale_window)
            
            if success:
                sale_window.status_label.setText(f"Invoice #{bill_data['bill_number']} printed successfully!")
                return True
            else:
                sale_window.status_label.setText("Printing cancelled")
                return False
                
        except Exception as e:
            QMessageBox.critical(sale_window, "Print Error", f"Could not print invoice: {str(e)}")
            return False
    
    @staticmethod
    def preview_invoice(sale_window):
        """Preview invoice using print.py library"""
        if not PRINT_MODULE_AVAILABLE:
            QMessageBox.critical(sale_window, "Module Error", 
                               "Print module not available. Make sure print.py is in the same directory.")
            return False
        
        if not sale_window.sale_items:
            QMessageBox.warning(sale_window, "No Items", "No items to preview!")
            return False
        
        try:
            # Prepare bill data
            bill_data = EnhancedIntegratedPrintingSystem.prepare_bill_data(sale_window)
            
            if not bill_data:
                return False
            
            # Use InvoicePreviewDialog from print.py
            dialog = invoice_printer.InvoicePreviewDialog(bill_data, sale_window)
            dialog.exec()
            return True
                
        except Exception as e:
            QMessageBox.critical(sale_window, "Preview Error", f"Could not preview invoice: {str(e)}")
            return False
    
    @staticmethod
    def save_pdf_invoice(sale_window, file_path=None):
        """Save invoice as PDF using print.py library"""
        if not PRINT_MODULE_AVAILABLE:
            QMessageBox.critical(sale_window, "Module Error", 
                               "Print module not available. Make sure print.py is in the same directory.")
            return None
        
        if not sale_window.sale_items:
            QMessageBox.warning(sale_window, "No Items", "No items to save!")
            return None
        
        try:
            # Prepare bill data
            bill_data = EnhancedIntegratedPrintingSystem.prepare_bill_data(sale_window)
            
            if not bill_data:
                return None
            
            # Create invoice generator
            generator = invoice_printer.InvoiceGenerator()
            
            # Generate PDF
            if file_path:
                pdf_path = file_path
            else:
                # Generate default filename
                temp_dir = os.path.join(os.getcwd(), "invoices")
                os.makedirs(temp_dir, exist_ok=True)
                pdf_path = os.path.join(temp_dir, f"invoice_{bill_data['bill_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            
            pdf_path = generator.generate_invoice_pdf(bill_data, pdf_path)
            
            if pdf_path and os.path.exists(pdf_path):
                sale_window.status_label.setText(f"PDF saved: {os.path.basename(pdf_path)}")
                return pdf_path
            else:
                sale_window.status_label.setText("PDF generation failed")
                return None
                
        except Exception as e:
            QMessageBox.critical(sale_window, "PDF Error", f"Could not save PDF: {str(e)}")
            return None

# ========== ENHANCED DATABASE MANAGER ==========
class EnhancedDatabaseManager:
    def __init__(self):
        self.connections = {}
        self.config_file = 'sales_config.json'
        self.settings = self.load_settings()
        self.connect_databases()
    
    def load_settings(self):
        """Load persistent settings"""
        default_settings = {
            'last_bill_number': 0,
            'next_bill_number': 1,
            'bill_prefix': '',
            'bill_suffix': '',
            'auto_increment': True,
            'tax_rate': 0.0,
            'default_discount_type': 'Amount',
            'default_customer': 'WALK-IN CUSTOMER',
            # NEW: Return fee settings
            'default_return_fee': 100,
            'return_fee_enabled': True,
            'return_fee_type': 'Flat'  # Flat or PerPage
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            else:
                return default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return default_settings.copy()
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_next_bill_number(self):
        """Get next bill number with persistence"""
        next_num = self.settings.get('next_bill_number', 1)
        return next_num
    
    def increment_bill_number(self):
        """Increment and save bill number"""
        current = self.settings.get('next_bill_number', 1)
        next_num = current + 1
        self.settings['next_bill_number'] = next_num
        self.settings['last_bill_number'] = current
        self.save_settings()
        return current
    
    def format_bill_number(self, number):
        """Format bill number with prefix/suffix"""
        prefix = self.settings.get('bill_prefix', '')
        suffix = self.settings.get('bill_suffix', '')
        
        # Pad with zeros to 5 digits
        formatted = f"{number:05d}"
        return f"{prefix}{formatted}{suffix}"
    
    def connect_databases(self):
        """Connect to all databases with error handling"""
        db_files = {
            'inventory': 'inventory.db',
            'bearings': 'bearings_inventory.db',
            'seals': 'seals.db',
            'sales': 'sales.db'
        }
        
        for db_name, db_file in db_files.items():
            try:
                if db_name == 'sales':
                    # Always create sales database if it doesn't exist
                    self.create_sales_database(db_file)
                    conn = sqlite3.connect(db_file)
                    conn.row_factory = sqlite3.Row
                    self.connections[db_name] = conn
                    self.initialize_sales_tables(conn)
                    print(f"Connected to {db_file}")
                else:
                    if os.path.exists(db_file):
                        conn = sqlite3.connect(db_file)
                        conn.row_factory = sqlite3.Row
                        self.connections[db_name] = conn
                        print(f"Connected to {db_file}")
                    else:
                        print(f"Warning: {db_file} not found")
            except Exception as e:
                print(f"Error connecting to {db_file}: {e}")
    
    def create_sales_database(self, db_file):
        """Create sales database if it doesn't exist"""
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Create sales table with enhanced schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_number TEXT NOT NULL UNIQUE,
                    bill_number_numeric INTEGER NOT NULL,
                    customer TEXT NOT NULL,
                    customer_phone TEXT,
                    customer_address TEXT,
                    sale_date TEXT NOT NULL,
                    sale_time TEXT NOT NULL,
                    total_items INTEGER NOT NULL,
                    subtotal REAL NOT NULL,
                    discount REAL DEFAULT 0,
                    discount_type TEXT DEFAULT 'Amount',
                    tax REAL DEFAULT 0,
                    tax_rate REAL DEFAULT 0,
                    grand_total REAL NOT NULL,
                    payment_method TEXT DEFAULT 'Cash',
                    payment_status TEXT DEFAULT 'Paid',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create sale_items table with foreign key constraint
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    bill_number TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    unit_cost REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    profit REAL NOT NULL,
                    profit_percentage REAL NOT NULL,
                    inventory_type TEXT NOT NULL,
                    database_source TEXT NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE,
                    FOREIGN KEY (bill_number) REFERENCES sales (bill_number) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_bill_number ON sales(bill_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_items_bill_number ON sale_items(bill_number)')
            
            conn.commit()
            conn.close()
            print(f"Created/Verified sales database: {db_file}")
        except Exception as e:
            print(f"Error creating sales database: {e}")
    
    def initialize_sales_tables(self, conn):
        """Initialize tables and add missing columns if needed"""
        try:
            cursor = conn.cursor()
            
            # Check and add missing columns to sales table
            cursor.execute("PRAGMA table_info(sales)")
            columns = [col[1] for col in cursor.fetchall()]
            
            missing_columns = [
                ('bill_number_numeric', 'INTEGER'),
                ('customer_phone', 'TEXT'),
                ('customer_address', 'TEXT'),
                ('sale_time', 'TEXT'),
                ('discount_type', 'TEXT'),
                ('tax_rate', 'REAL'),
                ('payment_method', 'TEXT'),
                ('payment_status', 'TEXT'),
                ('notes', 'TEXT'),
                ('updated_at', 'TIMESTAMP'),
                # NEW: Return fee columns
                ('return_fee_amount', 'REAL'),
                ('return_fee_type', 'TEXT')
            ]
            
            for col_name, col_type in missing_columns:
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE sales ADD COLUMN {col_name} {col_type}")
                    print(f"Added column {col_name} to sales table")
            
            # Check and add missing columns to sale_items table
            cursor.execute("PRAGMA table_info(sale_items)")
            columns = [col[1] for col in cursor.fetchall()]
            
            missing_item_columns = [
                ('unit_cost', 'REAL'),
                ('total_cost', 'REAL'),
                ('profit', 'REAL'),
                ('profit_percentage', 'REAL')
            ]
            
            for col_name, col_type in missing_item_columns:
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE sale_items ADD COLUMN {col_name} {col_type}")
                    print(f"Added column {col_name} to sale_items table")
            
            conn.commit()
        except Exception as e:
            print(f"Error initializing tables: {e}")
    
    def get_connection(self, db_name):
        return self.connections.get(db_name)
    
    def search_item_by_id(self, item_id):
        """Search item across all databases"""
        print(f"DEBUG: Searching for item ID: '{item_id}'")  # Debug line
        item_id = str(item_id).strip().upper()
        print(f"DEBUG: After processing: '{item_id}'")  # Debug line
        
        databases = [
            ('inventory', self.search_inventory),
            ('bearings', self.search_bearings),
            ('seals', self.search_seals)
        ]
        
        for db_name, search_func in databases:
            if db_name in self.connections:
                print(f"DEBUG: Searching in {db_name} database...")  # Debug line
                item = search_func(item_id)
                if item:
                    print(f"DEBUG: Found item in {db_name}: {item['item_id']}")  # Debug line
                    return item
                else:
                    print(f"DEBUG: Not found in {db_name}")  # Debug line
        
        print(f"DEBUG: Item not found in any database")  # Debug line
        return None
    
    def search_inventory(self, item_id):
        """Search in inventory database with multiple query attempts"""
        print(f"DEBUG: search_inventory called with: '{item_id}'")  # Debug line
        try:
            conn = self.connections['inventory']
            cursor = conn.cursor()
            
            # Try multiple query patterns to match different schemas
            queries = [
                "SELECT item_id, item as display_name, quantity, price, cost FROM Inventory WHERE item_id = ?",
                "SELECT item_id, name as display_name, quantity, price, cost FROM inventory WHERE item_id = ?",
                "SELECT id as item_id, name as display_name, quantity, price, cost FROM inventory WHERE id = ?",
                "SELECT code as item_id, name as display_name, quantity, selling_price as price, cost_price as cost FROM products WHERE code = ?",
                "SELECT sku as item_id, product_name as display_name, stock as quantity, price, cost FROM items WHERE sku = ?"
            ]
            
            for i, query in enumerate(queries):
                try:
                    print(f"DEBUG: Trying query #{i+1}: {query}")  # Debug line
                    cursor.execute(query, (item_id,))
                    row = cursor.fetchone()
                    if row:
                        print(f"DEBUG: Found item with query #{i+1}")  # Debug line
                        return {
                            'item_id': str(row['item_id']),
                            'display_name': row['display_name'],
                            'quantity': int(row['quantity']) if row['quantity'] else 0,
                            'price': float(row['price']) if row['price'] else 0.0,
                            'cost': float(row['cost']) if row['cost'] else 0.0,
                            'inventory_type': 'General Inventory',
                            'database': 'inventory'
                        }
                    else:
                        print(f"DEBUG: Query #{i+1} returned no results")  # Debug line
                except Exception as e:
                    print(f"DEBUG: Query #{i+1} failed: {e}")  # Debug line
                    continue
                    
            # Also try case-insensitive search
            print(f"DEBUG: Trying case-insensitive search...")  # Debug line
            queries_case_insensitive = [
                "SELECT item_id, item as display_name, quantity, price, cost FROM Inventory WHERE UPPER(item_id) = UPPER(?)",
                "SELECT item_id, name as display_name, quantity, price, cost FROM inventory WHERE UPPER(item_id) = UPPER(?)",
                "SELECT code as item_id, name as display_name, quantity, selling_price as price, cost_price as cost FROM products WHERE UPPER(code) = UPPER(?)"
            ]
            
            for i, query in enumerate(queries_case_insensitive):
                try:
                    print(f"DEBUG: Trying case-insensitive query #{i+1}")  # Debug line
                    cursor.execute(query, (item_id,))
                    row = cursor.fetchone()
                    if row:
                        print(f"DEBUG: Found item with case-insensitive query #{i+1}")  # Debug line
                        return {
                            'item_id': str(row['item_id']),
                            'display_name': row['display_name'],
                            'quantity': int(row['quantity']) if row['quantity'] else 0,
                            'price': float(row['price']) if row['price'] else 0.0,
                            'cost': float(row['cost']) if row['cost'] else 0.0,
                            'inventory_type': 'General Inventory',
                            'database': 'inventory'
                        }
                except Exception as e:
                    print(f"DEBUG: Case-insensitive query #{i+1} failed: {e}")  # Debug line
                    continue
        except Exception as e:
            print(f"DEBUG: Error searching inventory: {e}")  # Debug line
        
        return None
    
    def search_bearings(self, item_id):
        try:
            conn = self.connections['bearings']
            cursor = conn.cursor()
            
            queries = [
                "SELECT bearing_id as item_id, inner_diameter, outer_diameter, width, type, brand, quantity, price, cost FROM bearings WHERE UPPER(bearing_id) = UPPER(?)",
                "SELECT id as item_id, inner_diameter, outer_diameter, width, type, brand, quantity, price, cost FROM bearings WHERE UPPER(id) = UPPER(?)",
                "SELECT code as item_id, inner_diameter, outer_diameter, width, type, brand, quantity, price, cost FROM bearings WHERE UPPER(code) = UPPER(?)"
            ]
            
            for query in queries:
                try:
                    cursor.execute(query, (item_id,))
                    row = cursor.fetchone()
                    if row:
                        inner_d = row['inner_diameter']
                        outer_d = row['outer_diameter']
                        width = row['width']
                        brand = row['brand'] if row['brand'] else ""
                        bearing_type = row['type'] if row['type'] else ""
                        
                        display_name = f"Bearing {inner_d}x{outer_d}x{width}"
                        if brand:
                            display_name += f" {brand}"
                        if bearing_type:
                            display_name += f" ({bearing_type})"
                        
                        return {
                            'item_id': str(row['item_id']),
                            'display_name': display_name,
                            'quantity': int(row['quantity']) if row['quantity'] else 0,
                            'price': float(row['price']) if row['price'] else 0.0,
                            'cost': float(row['cost']) if row['cost'] else 0.0,
                            'inventory_type': 'Bearings',
                            'database': 'bearings'
                        }
                except:
                    continue
        except Exception as e:
            print(f"Error searching bearings: {e}")
        
        return None

    def search_seals(self, item_id):
        try:
            conn = self.connections['seals']
            cursor = conn.cursor()
            
            query = """
                SELECT s.item_id, s.od, s.idd, s.b, c.name as category, 
                       s.qty as quantity, s.price, s.cost, q.name as quality
                FROM seals s
                LEFT JOIN categories c ON s.category_id = c.id
                LEFT JOIN qualities q ON s.quality_id = q.id
                WHERE UPPER(s.item_id) = UPPER(?)
            """
            
            cursor.execute(query, (item_id,))
            row = cursor.fetchone()
            
            if row:
                od = row['od']
                idd = row['idd']
                b = row['b']
                quality = row['quality'] if row['quality'] else ""
                category = row['category'] if row['category'] else ""
                
                display_name = f"Oil Seal {od}x{idd}x{b}"
                if quality:
                    display_name += f" {quality}"
                if category:
                    display_name += f" ({category})"
                
                return {
                    'item_id': str(row['item_id']),
                    'display_name': display_name,
                    'quantity': int(row['quantity']) if row['quantity'] else 0,
                    'price': float(row['price']) if row['price'] else 0.0,
                    'cost': float(row['cost']) if row['cost'] else 0.0,
                    'inventory_type': 'Seals',
                    'database': 'seals'
                }
        except Exception as e:
            print(f"Error searching seals: {e}")
        
        return None
    
    def get_all_items(self):
        """Get all items from all databases for search"""
        all_items = []
        
        if 'inventory' in self.connections:
            try:
                conn = self.connections['inventory']
                cursor = conn.cursor()
                cursor.execute("SELECT item_id, item as display_name, quantity, price, cost FROM Inventory")
                for row in cursor.fetchall():
                    all_items.append({
                        'item_id': str(row['item_id']),
                        'display_name': row['display_name'],
                        'quantity': int(row['quantity']) if row['quantity'] else 0,
                        'price': float(row['price']) if row['price'] else 0.0,
                        'cost': float(row['cost']) if row['cost'] else 0.0,
                        'inventory_type': 'General Inventory',
                        'database': 'inventory'
                    })
            except Exception as e:
                print(f"Error getting inventory items: {e}")
        
        if 'bearings' in self.connections:
            try:
                conn = self.connections['bearings']
                cursor = conn.cursor()
                cursor.execute("SELECT bearing_id, inner_diameter, outer_diameter, width, type, brand, quantity, price, cost FROM bearings")
                for row in cursor.fetchall():
                    inner_d = row['inner_diameter']
                    outer_d = row['outer_diameter']
                    width = row['width']
                    brand = row['brand'] if row['brand'] else ""
                    bearing_type = row['type'] if row['type'] else ""
                    
                    display_name = f"Bearing {inner_d}x{outer_d}x{width}"
                    if brand:
                        display_name += f" {brand}"
                    if bearing_type:
                        display_name += f" ({bearing_type})"
                    
                    all_items.append({
                        'item_id': str(row['bearing_id']),
                        'display_name': display_name,
                        'quantity': int(row['quantity']) if row['quantity'] else 0,
                        'price': float(row['price']) if row['price'] else 0.0,
                        'cost': float(row['cost']) if row['cost'] else 0.0,
                        'inventory_type': 'Bearings',
                        'database': 'bearings'
                    })
            except Exception as e:
                print(f"Error getting bearing items: {e}")
        
        if 'seals' in self.connections:
            try:
                conn = self.connections['seals']
                cursor = conn.cursor()
                query = """
                    SELECT s.item_id, s.od, s.idd, s.b, c.name as category, 
                           s.qty as quantity, s.price, s.cost, q.name as quality
                    FROM seals s
                    LEFT JOIN categories c ON s.category_id = c.id
                    LEFT JOIN qualities q ON s.quality_id = q.id
                """
                cursor.execute(query)
                for row in cursor.fetchall():
                    od = row['od']
                    idd = row['idd']
                    b = row['b']
                    quality = row['quality'] if row['quality'] else ""
                    category = row['category'] if row['category'] else ""
                    
                    display_name = f"Oil Seal {od}x{idd}x{b}"
                    if quality:
                        display_name += f" {quality}"
                    if category:
                        display_name += f" ({category})"
                    
                    all_items.append({
                        'item_id': str(row['item_id']),
                        'display_name': display_name,
                        'quantity': int(row['quantity']) if row['quantity'] else 0,
                        'price': float(row['price']) if row['price'] else 0.0,
                        'cost': float(row['cost']) if row['cost'] else 0.0,
                        'inventory_type': 'Seals',
                        'database': 'seals'
                    })
            except Exception as e:
                print(f"Error getting seal items: {e}")
        
        return all_items
    
    def save_sale(self, bill_number, bill_number_numeric, customer, customer_phone, 
                  customer_address, sale_items, discount, discount_type, 
                  tax, tax_rate, grand_total, payment_method, payment_status, notes, return_fee_type, return_fee_amount):
        """Save sale with transaction and proper error handling"""
        try:
            if 'sales' not in self.connections:
                return False, "Sales database not connected"
            
            conn = self.connections['sales']
            cursor = conn.cursor()
            
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # Get current datetime
                now = datetime.now()
                sale_date = now.strftime("%Y-%m-%d")
                sale_time = now.strftime("%H:%M:%S")
                
                # Calculate totals
                subtotal = sum(item['total_price'] for item in sale_items)
                total_cost = sum(item['total_cost'] for item in sale_items)
                
                # Insert sale header
                cursor.execute('''
                    INSERT INTO sales (
                        bill_number, bill_number_numeric, customer, customer_phone, customer_address,
                        sale_date, sale_time, total_items, subtotal, discount, discount_type,
                        tax, tax_rate, grand_total, payment_method, payment_status, notes,
                        return_fee_type, return_fee_amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bill_number, bill_number_numeric, customer, customer_phone, customer_address,
                    sale_date, sale_time, len(sale_items), subtotal, discount, discount_type,
                    tax, tax_rate, grand_total, payment_method, payment_status, notes,
                    return_fee_type, return_fee_amount
                ))
                
                sale_id = cursor.lastrowid
                
                # Insert sale items with profit calculations
                for item in sale_items:
                    profit = item['profit']
                    profit_percentage = (profit / item['total_cost'] * 100) if item['total_cost'] > 0 else 0
                    
                    cursor.execute('''
                        INSERT INTO sale_items (
                            sale_id, bill_number, item_id, display_name, quantity,
                            unit_price, total_price, unit_cost, total_cost,
                            profit, profit_percentage, inventory_type, database_source
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sale_id, bill_number, item['item_id'], item['display_name'], item['quantity'],
                        item['price'], item['total_price'], item['cost'], item['total_cost'],
                        profit, profit_percentage, item['inventory_type'], item['database']
                    ))
                
                # Update stock for each item
                stock_updates = []
                for item in sale_items:
                    if not self.update_stock(item['database'], item['item_id'], item['quantity']):
                        # Record failed updates but continue with transaction
                        stock_updates.append(f"Failed to update stock for {item['item_id']}")
                
                # Commit transaction
                conn.commit()
                
                # Verify insertion
                cursor.execute("SELECT COUNT(*) FROM sales WHERE bill_number = ?", (bill_number,))
                if cursor.fetchone()[0] == 1:
                    if stock_updates:
                        return True, f"Sale saved with warnings: {', '.join(stock_updates)}"
                    else:
                        return True, "Sale saved successfully"
                else:
                    return False, "Sale verification failed"
                    
            except sqlite3.IntegrityError as e:
                # Rollback on integrity error (duplicate bill number)
                conn.rollback()
                return False, f"Bill number {bill_number} already exists!"
            except Exception as e:
                # Rollback on other errors
                conn.rollback()
                return False, f"Error saving sale: {str(e)}"
                
        except Exception as e:
            print(f"Error in save_sale: {e}")
            return False, f"Database error: {str(e)}"
    
    def update_stock(self, database, item_id, quantity_sold):
        """Update stock quantity with proper error handling"""
        try:
            if database not in self.connections:
                return False
            
            conn = self.connections[database]
            cursor = conn.cursor()
            
            if database == 'inventory':
                cursor.execute("UPDATE Inventory SET quantity = quantity - ? WHERE item_id = ?", 
                             (quantity_sold, item_id))
            elif database == 'bearings':
                cursor.execute("UPDATE bearings SET quantity = quantity - ? WHERE bearing_id = ?", 
                             (quantity_sold, item_id))
            elif database == 'seals':
                cursor.execute("UPDATE seals SET qty = qty - ? WHERE item_id = ?", 
                             (quantity_sold, item_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating stock for {item_id}: {e}")
            return False
    
    def close_all(self):
        """Close all database connections"""
        for db_name, conn in self.connections.items():
            if conn:
                try:
                    conn.close()
                    print(f"Closed connection to {db_name}")
                except:
                    pass

# ========== ITEM SEARCH DIALOG ==========
class ItemSearchDialog(QDialog):
    item_selected = pyqtSignal(str)
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.items = []
        self.setWindowTitle("Search Items - Enter to Select | F1 to Close")
        self.setGeometry(200, 100, 1000, 600)
        
        self.setup_ui()
        self.load_items()

        # Set initial selection to first row
        if self.items_table.rowCount() > 0:
            self.items_table.setCurrentCell(0, 0)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add filter options above table
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Bearings", "Seals", "General Inventory"])
        self.type_filter.currentTextChanged.connect(self.filter_items)
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(QLabel("In Stock Only:"))
        self.stock_checkbox = QCheckBox()
        self.stock_checkbox.toggled.connect(self.filter_items)
        filter_layout.addWidget(self.stock_checkbox)
        
        # Enhanced search input
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID, name, or any keywords...")
        self.search_input.textChanged.connect(self.filter_items)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        layout.insertLayout(1, filter_layout)
        
        # Convert to TABLE view instead of list
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "S.No.", "Item ID", "Item Name", "Price", "Stock"
        ])
        
        # HIDE VERTICAL HEADER (row numbers) - LIKE BEARINGS.PY
        self.items_table.verticalHeader().setVisible(False)
        
        # SET CUSTOM COLUMN WIDTHS - NOT ALL STRETCH
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # S.No. - fixed
        self.items_table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Item ID - fixed
        self.items_table.setColumnWidth(1, 120)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Item Name - stretch
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Price - fixed
        self.items_table.setColumnWidth(3, 100)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Stock - fixed
        self.items_table.setColumnWidth(4, 80)
        
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.items_table.doubleClicked.connect(self.select_item)
        self.items_table.keyPressEvent = self.table_keyPressEvent
        
        layout.addWidget(self.items_table)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.select_item)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_items(self):
        self.items = self.db_manager.get_all_items()
        self.update_table()
        
    def update_table(self, items=None):
        """Update table with items - SIMILAR TO BEARINGS.PY APPROACH"""
        display_items = items if items is not None else self.items
        self.items_table.setRowCount(len(display_items))
        
        for row, item in enumerate(display_items):
            # S.No.
            sno_item = QTableWidgetItem(str(row + 1))
            sno_item.setFlags(sno_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            sno_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_table.setItem(row, 0, sno_item)
            
            # Item ID
            id_item = QTableWidgetItem(item['item_id'])
            id_item.setData(Qt.ItemDataRole.UserRole, item['item_id'])
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.items_table.setItem(row, 1, id_item)
            
            # Item Name
            name_item = QTableWidgetItem(item['display_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.items_table.setItem(row, 2, name_item)
            
            # Price
            price_item = QTableWidgetItem(f"Rs{item['price']:.2f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.items_table.setItem(row, 3, price_item)
            
            # Stock
            stock_item = QTableWidgetItem(str(item['quantity']))
            stock_item.setFlags(stock_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_table.setItem(row, 4, stock_item)
        
    def filter_items(self):
        """Enhanced search with multiple filters"""
        search_text = self.search_input.text().lower().strip()
        type_filter = self.type_filter.currentText()
        in_stock_only = self.stock_checkbox.isChecked()
        
        # Split search into keywords
        keywords = search_text.split() if search_text else []
        
        filtered = []
        for item in self.items:
            # Type filter
            if type_filter != "All" and item['inventory_type'] != type_filter:
                continue
                
            # Stock filter
            if in_stock_only and item['quantity'] <= 0:
                continue
                
            # Keyword search
            if keywords:
                searchable_text = (
                    f"{item['item_id']} "
                    f"{item['display_name']} "
                    f"{item['inventory_type']}"
                ).lower()
                
                if not all(keyword in searchable_text for keyword in keywords):
                    continue
                    
            filtered.append(item)
            
        self.update_table(filtered)
        
    def select_item(self):
        """Get selected item from table"""
        selected_row = self.items_table.currentRow()
        if selected_row >= 0:
            item_id = self.items_table.item(selected_row, 1).data(Qt.ItemDataRole.UserRole)
            self.item_selected.emit(item_id)
            self.accept()
        
    def keyPressEvent(self, event):
        """Handle keyboard navigation - SIMPLIFIED and FIXED"""
        # Handle Escape and F1 to close
        if event.key() == Qt.Key.Key_Escape or event.key() == Qt.Key.Key_F1:
            self.reject()
            return
        
        # Handle Enter/Return to select item
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.search_input.hasFocus() and self.search_input.text().strip():
                # If typing in search, don't do anything - let user continue
                event.ignore()
                return
            elif self.items_table.rowCount() > 0:
                self.select_item()
                return
        
        # Handle arrow keys - SIMPLIFIED APPROACH
        elif event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
            # If search has focus, move focus to table
            if self.search_input.hasFocus():
                if self.items_table.rowCount() > 0:
                    self.items_table.setFocus()
                    # Select first row if none selected
                    if self.items_table.currentRow() < 0:
                        self.items_table.setCurrentCell(0, 0)
                    # Now process the arrow key in the table
                    self.items_table.keyPressEvent(event)
            else:
                # Table already has focus, just pass the event
                self.items_table.keyPressEvent(event)
            return
        
        # Handle PageUp/PageDown
        elif event.key() in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            if self.items_table.rowCount() > 0:
                self.items_table.setFocus()
                self.items_table.keyPressEvent(event)
            return
        
        # Handle Home/End
        elif event.key() == Qt.Key.Key_Home:
            if self.items_table.rowCount() > 0:
                self.items_table.setFocus()
                self.items_table.setCurrentCell(0, 0)
            return
        
        elif event.key() == Qt.Key.Key_End:
            if self.items_table.rowCount() > 0:
                self.items_table.setFocus()
                self.items_table.setCurrentCell(self.items_table.rowCount() - 1, 0)
            return
        
        # Handle Tab/Backtab - standard focus navigation
        elif event.key() == Qt.Key.Key_Tab:
            if self.search_input.hasFocus():
                if self.items_table.rowCount() > 0:
                    self.items_table.setFocus()
                    if self.items_table.currentRow() < 0:
                        self.items_table.setCurrentCell(0, 0)
                else:
                    # Move to next widget in dialog
                    super().keyPressEvent(event)
            else:
                # Move to next widget in dialog
                super().keyPressEvent(event)
            return
        
        elif event.key() == Qt.Key.Key_Backtab:
            if self.items_table.hasFocus():
                self.search_input.setFocus()
                self.search_input.selectAll()
            else:
                # Move to previous widget in dialog
                super().keyPressEvent(event)
            return
        
        # For all other keys, if they are printable and search doesn't have focus,
        # move focus to search and pass the key
        elif event.text() and event.text().isprintable() and not event.text().isspace():
            if not self.search_input.hasFocus():
                self.search_input.setFocus()
                # Insert the typed character
                current_text = self.search_input.text()
                cursor_position = self.search_input.cursorPosition()
                new_text = current_text[:cursor_position] + event.text() + current_text[cursor_position:]
                self.search_input.setText(new_text)
                self.search_input.setCursorPosition(cursor_position + 1)
            else:
                # Search already has focus, let Qt handle normal typing
                super().keyPressEvent(event)
            return
        
        # For modifier keys and other special keys, just ignore
        elif event.key() in (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, 
                           Qt.Key.Key_Meta, Qt.Key.Key_CapsLock, Qt.Key.Key_AltGr):
            event.ignore()
            return
        
        # Default: let Qt handle it
        else:
            super().keyPressEvent(event)

    def table_keyPressEvent(self, event):
        """Handle keyboard events specifically for the table"""
        try:
            # Handle Enter/Return in table
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.select_item()
                return
            
            # Handle Escape in table
            elif event.key() == Qt.Key.Key_Escape:
                self.reject()
                return
            
            # Handle F1 in table
            elif event.key() == Qt.Key.Key_F1:
                self.reject()
                return
            
            # Handle arrow keys in table
            elif event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
                # Call the parent QTableWidget's keyPressEvent to handle navigation
                QTableWidget.keyPressEvent(self.items_table, event)
                return
            
            # Handle PageUp/PageDown
            elif event.key() in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
                QTableWidget.keyPressEvent(self.items_table, event)
                return
            
            # Handle Home/End
            elif event.key() in (Qt.Key.Key_Home, Qt.Key.Key_End):
                QTableWidget.keyPressEvent(self.items_table, event)
                return
            
            # For printable characters, move focus to search box
            elif event.text() and event.text().isprintable() and not event.text().isspace():
                self.search_input.setFocus()
                # Insert the typed character
                current_text = self.search_input.text()
                cursor_position = self.search_input.cursorPosition()
                new_text = current_text[:cursor_position] + event.text() + current_text[cursor_position:]
                self.search_input.setText(new_text)
                self.search_input.setCursorPosition(cursor_position + 1)
                return
            
            # For all other keys, use default behavior
            else:
                QTableWidget.keyPressEvent(self.items_table, event)
                
        except Exception as e:
            print(f"Error in table_keyPressEvent: {e}")
            # Ignore the event to prevent crash
            event.ignore()
    
    def showEvent(self, event):
        """Focus search input when dialog appears"""
        super().showEvent(event)
        self.search_input.setFocus()

# ========== ENHANCED SALES WINDOW ==========
class EnhancedSalesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sale_items = []
        self.bill_number_numeric = 0
        self.bill_number = "00001"
        self.cost_visible = True
        self.profit_visible = True
        self.is_closing = False
        
        self.db_manager = EnhancedDatabaseManager()
        self.load_bill_number()
        
        self.setup_ui()
        self.setup_shortcuts()
        self.start_timer()
        
        # Update datetime immediately
        self.update_datetime()
        
        QTimer.singleShot(100, lambda: self.item_id_input.setFocus())
    
    def load_bill_number(self):
        """Load bill number from persistent storage"""
        self.bill_number_numeric = self.db_manager.get_next_bill_number()
        self.bill_number = self.db_manager.format_bill_number(self.bill_number_numeric)
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)
        
        layout.addWidget(self.create_header_section())
        layout.addWidget(self.create_input_section())
        layout.addWidget(self.create_table_section())
        layout.addWidget(self.create_summary_section())
        
        self.setup_status_bar()
    
    def create_header_section(self):
        header_frame = QFrame()
        header_frame.setMaximumHeight(60)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        company_info = QLabel("TOOLTREK - ENHANCED SALES")
        company_info.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: white;
            padding: 5px;
        """)
        
        bill_info_widget = QWidget()
        bill_layout = QVBoxLayout(bill_info_widget)
        bill_layout.setContentsMargins(0, 0, 0, 0)
        bill_layout.setSpacing(2)
        
        self.bill_number_label = QLabel(f"Bill #: {self.bill_number}")
        self.bill_number_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #e74c3c;
            background-color: white;
            padding: 3px 8px;
            border-radius: 3px;
        """)
        
        self.datetime_label = QLabel()
        self.update_datetime()
        self.datetime_label.setStyleSheet("""
            font-size: 11px; 
            color: #bdc3c7;
            padding: 2px;
        """)
        
        bill_layout.addWidget(self.bill_number_label)
        bill_layout.addWidget(self.datetime_label)
        
        header_layout.addWidget(company_info)
        header_layout.addStretch()
        header_layout.addWidget(bill_info_widget)
        
        return header_frame
    
    def create_input_section(self):
        input_frame = QFrame()
        input_frame.setMaximumHeight(50)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)
        
        input_layout.addWidget(QLabel("Customer:"))
        self.customer_input = QLineEdit("WALK-IN CUSTOMER")
        self.customer_input.setFixedHeight(32)
        self.customer_input.setMaximumWidth(200)
        input_layout.addWidget(self.customer_input)
        
        input_layout.addWidget(QLabel("Item ID:"))
        self.item_id_input = QLineEdit()
        self.item_id_input.setPlaceholderText("Scan or Type Item ID (Enter to add)")
        self.item_id_input.setFixedHeight(32)
        self.item_id_input.returnPressed.connect(self.add_item_by_id)
        input_layout.addWidget(self.item_id_input)
        
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(3)
        
        search_btn = QPushButton("🔍 Search (F1)")
        search_btn.setToolTip("Search Items")
        search_btn.setFixedHeight(32)
        search_btn.clicked.connect(self.show_item_search)
        action_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("Clear (Esc)")
        clear_btn.setToolTip("Clear Input")
        clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self.clear_inputs)
        action_layout.addWidget(clear_btn)
        
        input_layout.addWidget(action_widget)
        
        return input_frame
    
    def create_table_section(self):
        """CREATE TABLE WITH PROPER ALIGNMENT AND NAVIGATION"""
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(1, 1, 1, 1)
        
        self.sales_table = QTableWidget()
        
        # 8 columns (removed profit column from display)
        self.sales_table.setColumnCount(8)
        self.sales_table.setHorizontalHeaderLabels([
            "S.No.", "Item ID", "Item Name", "Stock", "Qty", "Price", "Cost", "Total"
        ])
        
        # HIDE VERTICAL HEADER
        self.sales_table.verticalHeader().setVisible(False)
        
        # SET CUSTOM COLUMN WIDTHS - FIXED VALUES
        header = self.sales_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # S.No.
        self.sales_table.setColumnWidth(0, 70)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Item ID
        self.sales_table.setColumnWidth(1, 200)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Item Name
        self.sales_table.setColumnWidth(2, 500)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Stock
        self.sales_table.setColumnWidth(3, 80)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Qty
        self.sales_table.setColumnWidth(4, 120)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Price
        self.sales_table.setColumnWidth(5, 120)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Cost
        self.sales_table.setColumnWidth(6, 100)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Total
        self.sales_table.setColumnWidth(7, 150)
        
        # Set alternating row colors with specific colors
        self.sales_table.setAlternatingRowColors(True)
        
        # Apply stylesheet for better selection and alternating colors
        table_style = """
            QTableWidget {
                alternate-background-color: #f8f9fa;
                background-color: white;
                gridline-color: #e0e0e0;
                border: 1px solid #d0d0d0;
            }
            QTableWidget::item {
                padding: 3px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
                border: 1px solid #34495e;
                font-weight: bold;
            }
        """
        self.sales_table.setStyleSheet(table_style)
        
        # Selection behavior
        self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        table_layout.addWidget(self.sales_table)
        
        return table_frame
    
    def create_summary_section(self):
        summary_frame = QFrame()
        summary_frame.setMaximumHeight(140)
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(5, 5, 5, 5)
        summary_layout.setSpacing(10)
        
        sales_summary = QGroupBox("Sales Summary")
        sales_summary.setMaximumHeight(130)
        sales_layout = QGridLayout(sales_summary)
        sales_layout.setContentsMargins(8, 15, 8, 8)
        sales_layout.setSpacing(5)
        
        sales_layout.addWidget(QLabel("Subtotal:"), 0, 0)
        self.subtotal_label = QLabel("Rs 0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        sales_layout.addWidget(self.subtotal_label, 0, 1)
        
        sales_layout.addWidget(QLabel("Tax:"), 0, 2)
        tax_layout = QHBoxLayout()
        self.tax_spinbox = QDoubleSpinBox()
        self.tax_spinbox.setMinimum(0)
        self.tax_spinbox.setMaximum(100)
        self.tax_spinbox.setValue(0)
        self.tax_spinbox.setSuffix(" %")
        self.tax_spinbox.setFixedHeight(24)
        self.tax_spinbox.setFixedWidth(70)
        self.tax_spinbox.valueChanged.connect(self.calculate_totals)
        tax_layout.addWidget(self.tax_spinbox)
        sales_layout.addLayout(tax_layout, 0, 3)
        
        sales_layout.addWidget(QLabel("Discount:"), 1, 0)
        discount_layout = QHBoxLayout()
        
        self.discount_type = QComboBox()
        self.discount_type.addItems(["Amount", "Percentage"])
        self.discount_type.setFixedHeight(24)
        self.discount_type.setFixedWidth(90)
        self.discount_type.currentTextChanged.connect(self.on_discount_type_changed)
        discount_layout.addWidget(self.discount_type)
        
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setMinimum(0)
        self.discount_input.setMaximum(100000)
        self.discount_input.setValue(0)
        self.discount_input.setFixedHeight(24)
        self.discount_input.setFixedWidth(100)
        self.discount_input.valueChanged.connect(self.calculate_totals)
        discount_layout.addWidget(self.discount_input)
        
        sales_layout.addLayout(discount_layout, 1, 1, 1, 3)

        # Add Return Fee section (NEW)
        sales_layout.addWidget(QLabel("Return Fee:"), 2, 0)
        return_fee_layout = QHBoxLayout()

        self.return_fee_type = QComboBox()
        self.return_fee_type.addItems(["Flat", "Per Page"])
        self.return_fee_type.setFixedHeight(24)
        self.return_fee_type.setFixedWidth(90)
        self.return_fee_type.currentTextChanged.connect(self.on_return_fee_type_changed)
        return_fee_layout.addWidget(self.return_fee_type)

        self.return_fee_input = QDoubleSpinBox()
        self.return_fee_input.setMinimum(0)
        self.return_fee_input.setMaximum(1000)
        self.return_fee_input.setValue(self.db_manager.settings.get('default_return_fee', 100))
        self.return_fee_input.setFixedHeight(24)
        self.return_fee_input.setFixedWidth(100)
        self.return_fee_input.valueChanged.connect(self.calculate_totals)
        return_fee_layout.addWidget(self.return_fee_input)

        sales_layout.addLayout(return_fee_layout, 2, 1, 1, 3)

        # Move Grand Total to row 3 (was row 2)
        sales_layout.addWidget(QLabel("Grand Total:"), 3, 0)
        self.grand_total_label = QLabel("Rs 0.00")
        self.grand_total_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #e74c3c;
            padding: 3px;
        """)
        sales_layout.addWidget(self.grand_total_label, 3, 1, 1, 3)
        
        self.profit_summary = QGroupBox("Profit Summary")
        self.profit_summary.setMaximumHeight(130)
        self.profit_summary.setCheckable(True)
        self.profit_summary.setChecked(True)
        self.profit_summary.toggled.connect(self.toggle_profit_section)
        profit_layout = QGridLayout(self.profit_summary)
        profit_layout.setContentsMargins(8, 15, 8, 8)
        profit_layout.setSpacing(5)
        
        profit_layout.addWidget(QLabel("Total Cost:"), 0, 0)
        self.total_cost_label = QLabel("Rs 0.00")
        self.total_cost_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        profit_layout.addWidget(self.total_cost_label, 0, 1)
        
        profit_layout.addWidget(QLabel("Profit:"), 1, 0)
        profit_value_layout = QHBoxLayout()
        self.profit_label = QLabel("Rs 0.00")
        self.profit_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #27ae60;")
        profit_value_layout.addWidget(self.profit_label)
        
        self.profit_percent_label = QLabel("0.0%")
        self.profit_percent_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #27ae60;")
        profit_value_layout.addWidget(self.profit_percent_label)
        profit_layout.addLayout(profit_value_layout, 1, 1)
        
        toggle_btn = QPushButton("Hide Profit")
        toggle_btn.setFixedHeight(24)
        toggle_btn.clicked.connect(self.toggle_profit_section_btn)
        profit_layout.addWidget(toggle_btn, 2, 0, 1, 2)
        
        action_layout = QVBoxLayout()
        action_layout.setSpacing(3)
        
        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(3)
        
        btn_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
                min-height: 28px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ca0;
            }
        """
        
        # UPDATED BUTTONS - Using EnhancedIntegratedPrintingSystem
        buttons = [
            ("Print Invoice (F9)", self.print_invoice, 0, 0),
            ("Preview (F8)", self.preview_invoice, 0, 1),
            ("Save PDF (F7)", self.save_pdf_invoice, 0, 2),
            ("Save Sale (Ctrl+S)", self.save_sale, 1, 0),
            ("New Bill (F2)", self.new_bill, 1, 1),
            ("Clear Sale (Ctrl+C)", self.clear_sale, 1, 2),
            ("Close (ESC)", self.close, 2, 0, 1, 3)
        ]
        
        for btn_info in buttons:
            if len(btn_info) == 4:
                text, handler, row, col = btn_info
                colspan = 1
                rowspan = 1
            else:
                text, handler, row, col, rowspan, colspan = btn_info
                
            btn = QPushButton(text)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(handler)
            
            # Style specific buttons
            if "New Bill" in text:
                btn.setStyleSheet(btn_style.replace("#3498db", "#27ae60"))
            elif "Clear Sale" in text:
                btn.setStyleSheet(btn_style.replace("#3498db", "#e67e22"))
            elif "Close" in text:
                btn.setStyleSheet(btn_style.replace("#3498db", "#e74c3c"))
            elif "Preview" in text or "Save PDF" in text:
                btn.setStyleSheet(btn_style.replace("#3498db", "#9b59b6"))
                
            buttons_grid.addWidget(btn, row, col, rowspan, colspan)
        
        action_layout.addLayout(buttons_grid)
        
        summary_layout.addWidget(sales_summary, 40)
        summary_layout.addWidget(self.profit_summary, 30)
        summary_layout.addLayout(action_layout, 30)
        
        return summary_frame

    def on_return_fee_type_changed(self, fee_type):
        """Handle return fee type change"""
        if fee_type == "Per Page":
            self.return_fee_input.setSuffix(" /page")
            # Load per page fee from settings if available
            per_page_fee = self.db_manager.settings.get('return_fee_per_page', 50)
            self.return_fee_input.setValue(per_page_fee)
        else:
            self.return_fee_input.setSuffix("")
            # Load flat fee from settings
            flat_fee = self.db_manager.settings.get('default_return_fee', 100)
            self.return_fee_input.setValue(flat_fee)

    def update_return_fee_from_settings(self):
        """Update return fee input from saved settings"""
        settings = self.db_manager.settings
        fee_type = settings.get('return_fee_type', 'Flat')
        self.return_fee_type.setCurrentText(fee_type)
        
        if fee_type == 'Per Page':
            self.return_fee_input.setValue(settings.get('return_fee_per_page', 50))
        else:
            self.return_fee_input.setValue(settings.get('default_return_fee', 100))
    
    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready - Enter Item ID or scan barcode")
        self.status_bar.addWidget(self.status_label, 70)
        
        self.items_count_label = QLabel("Items: 0")
        self.status_bar.addPermanentWidget(self.items_count_label)
        
        # UPDATED SHORTCUT LABEL
        shortcut_label = QLabel("F1:Search | F2:New Bill | F7:Save PDF | F8:Preview | F9:Print | Ctrl+S:Save | Del:Remove | Ctrl+C:Clear | Ctrl+H:Toggle Cost/Profit")
        self.status_bar.addPermanentWidget(shortcut_label)
    
    def setup_shortcuts(self):
        search_action = QAction("Item Search", self)
        search_action.setShortcut(QKeySequence("F1"))
        search_action.triggered.connect(self.show_item_search)
        self.addAction(search_action)
        
        new_bill_action = QAction("New Bill", self)
        new_bill_action.setShortcut(QKeySequence("F2"))
        new_bill_action.triggered.connect(self.new_bill)
        self.addAction(new_bill_action)
        
        # Print invoice shortcut
        print_action = QAction("Print Invoice", self)
        print_action.setShortcut(QKeySequence("F9"))
        print_action.triggered.connect(self.print_invoice)  # Changed from print_professional_invoice
        self.addAction(print_action)
        
        # Preview invoice shortcut
        preview_action = QAction("Preview Invoice", self)
        preview_action.setShortcut(QKeySequence("F8"))
        preview_action.triggered.connect(self.preview_invoice)
        self.addAction(preview_action)
        
        # Save PDF shortcut
        pdf_action = QAction("Save PDF", self)
        pdf_action.setShortcut(QKeySequence("F7"))
        pdf_action.triggered.connect(self.save_pdf_invoice)
        self.addAction(pdf_action)
        
        save_action = QAction("Save Sale", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_sale)
        self.addAction(save_action)
        
        remove_action = QAction("Remove Item", self)
        remove_action.setShortcut(QKeySequence("Delete"))
        remove_action.triggered.connect(self.remove_selected_item)
        self.addAction(remove_action)
        
        clear_sale_action = QAction("Clear Sale", self)
        clear_sale_action.setShortcut(QKeySequence("Ctrl+C"))
        clear_sale_action.triggered.connect(self.clear_sale)
        self.addAction(clear_sale_action)
        
        focus_item_action = QAction("Focus Item ID", self)
        focus_item_action.setShortcut(QKeySequence("Ctrl+I"))
        focus_item_action.triggered.connect(lambda: self.item_id_input.setFocus())
        self.addAction(focus_item_action)
        
        toggle_cost_profit_action = QAction("Toggle Cost/Profit", self)
        toggle_cost_profit_action.setShortcut(QKeySequence("Ctrl+H"))
        toggle_cost_profit_action.triggered.connect(self.toggle_cost_profit)
        self.addAction(toggle_cost_profit_action)
        
        # Table navigation shortcuts
        quantity_focus_action = QAction("Focus Quantity", self)
        quantity_focus_action.setShortcut(QKeySequence("Ctrl+Q"))
        quantity_focus_action.triggered.connect(self.focus_on_current_quantity)
        self.addAction(quantity_focus_action)
        
        price_focus_action = QAction("Focus Price", self)
        price_focus_action.setShortcut(QKeySequence("Ctrl+P"))
        price_focus_action.triggered.connect(self.focus_on_current_price)
        self.addAction(price_focus_action)

    def update_sale_items_table(self):
        """UPDATE TABLE WITH PROPER ALIGNMENT"""
        self.sales_table.setRowCount(len(self.sale_items))
        total = 0
        
        # Define spinbox styles
        spinbox_style = """
            QSpinBox, QDoubleSpinBox {
                border: 1px solid #d0d0d0;
                border-radius: 2px;
                padding: 2px;
                background-color: #EFECE3;
                selection-background-color: #3498db;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #3498db;
            }
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow,
            QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
                width: 0px;
                height: 0px;
            }
        """
        
        for row, item in enumerate(self.sale_items):
            # Column 0: Serial Number (S.No.)
            sno_item = QTableWidgetItem(str(row + 1))
            sno_item.setFlags(sno_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            sno_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sales_table.setItem(row, 0, sno_item)
            
            # Column 1: Item ID
            item_id_item = QTableWidgetItem(item['item_id'])
            item_id_item.setFlags(item_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_id_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.sales_table.setItem(row, 1, item_id_item)
            
            # Column 2: Item Name
            name_item = QTableWidgetItem(item['display_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.sales_table.setItem(row, 2, name_item)
            
            # Column 3: Stock
            stock_item = QTableWidgetItem(str(item['available_stock']))
            stock_item.setFlags(stock_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sales_table.setItem(row, 3, stock_item)
            
            # Column 4: Quantity
            quantity_spin = QSpinBox()
            quantity_spin.setRange(1, 10000)
            quantity_spin.setValue(item['quantity'])
            quantity_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            quantity_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            quantity_spin.setStyleSheet(spinbox_style)
            
            # Connect Enter key using lambda with default argument
            quantity_spin.lineEdit().returnPressed.connect(
                lambda checked=False, r=row: self.handle_quantity_enter(r)
            )
            
            # Connect value change using lambda with default argument
            quantity_spin.valueChanged.connect(
                lambda value, r=row: self.update_item_quantity(r, value)
            )
            
            self.sales_table.setCellWidget(row, 4, quantity_spin)
            
            # Column 5: Price
            price_spin = QDoubleSpinBox()
            price_spin.setRange(0.01, 100000.00)
            price_spin.setDecimals(2)
            price_spin.setValue(item['price'])
            price_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            price_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
            price_spin.setStyleSheet(spinbox_style)
            
            # Connect Enter key using lambda with default argument
            price_spin.lineEdit().returnPressed.connect(
                lambda checked=False, r=row: self.handle_price_enter(r)
            )
            
            # Connect value change using lambda with default argument
            price_spin.valueChanged.connect(
                lambda value, r=row: self.update_item_price(r, value)
            )
            
            self.sales_table.setCellWidget(row, 5, price_spin)
            
            # Column 6: Cost
            cost_item = QTableWidgetItem(f"{item['cost']:.2f}")
            cost_item.setFlags(cost_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.sales_table.setItem(row, 6, cost_item)
            
            # Column 7: Total
            item_total = item['quantity'] * item['price']
            item['total_price'] = item_total
            item['total_cost'] = item['cost'] * item['quantity']
            item['profit'] = (item['price'] - item['cost']) * item['quantity']
            
            total_item = QTableWidgetItem(f"{item_total:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.sales_table.setItem(row, 7, total_item)
            
            total += item_total
        
        # Clear selection after updating table
        self.sales_table.clearSelection()
        
        # Update summary
        self.calculate_totals()
        self.update_items_count()

    def handle_quantity_enter(self, row):
        """Handle Enter key in quantity spinbox"""
        spin = self.sales_table.cellWidget(row, 4)
        if spin:
            self.update_item_quantity(row, spin.value())
            self.focus_on_price_cell(row)

    def handle_price_enter(self, row):
        """Handle Enter key in price spinbox"""
        spin = self.sales_table.cellWidget(row, 5)
        if spin:
            self.update_item_price(row, spin.value())
            self.item_id_input.setFocus()

    def focus_on_price_cell(self, row):
        """Focus on price spinbox for given row"""
        if row < self.sales_table.rowCount():
            price_widget = self.sales_table.cellWidget(row, 5)
            if price_widget:
                price_widget.lineEdit().setFocus()
                price_widget.lineEdit().selectAll()

    def update_item_quantity(self, row, quantity):
        """Update quantity with validation"""
        if row < len(self.sale_items):
            # Stock validation
            if quantity > self.sale_items[row]['available_stock']:
                QMessageBox.warning(self, "Stock Error", 
                                  f"Only {self.sale_items[row]['available_stock']} items available!")
                # Reset to max available
                quantity = self.sale_items[row]['available_stock']
            
            self.sale_items[row]['quantity'] = quantity
            
            # Auto-calculate total price for this item
            price = self.sale_items[row]['price']
            self.sale_items[row]['total_price'] = quantity * price
            self.sale_items[row]['total_cost'] = self.sale_items[row]['cost'] * quantity
            self.sale_items[row]['profit'] = (price - self.sale_items[row]['cost']) * quantity
            
            # Update the total cell
            if row < self.sales_table.rowCount():
                total_item = QTableWidgetItem(f"{quantity * price:.2f}")
                total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.sales_table.setItem(row, 7, total_item)
            
            # Update totals
            self.calculate_totals()

    def update_item_price(self, row, price):
        """Update price with auto-recalculation"""
        if row < len(self.sale_items):
            self.sale_items[row]['price'] = price
            
            # Auto-calculate total price for this item
            quantity = self.sale_items[row]['quantity']
            self.sale_items[row]['total_price'] = quantity * price
            self.sale_items[row]['profit'] = (price - self.sale_items[row]['cost']) * quantity
            
            # Update the total cell
            if row < self.sales_table.rowCount():
                total_item = QTableWidgetItem(f"{quantity * price:.2f}")
                total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.sales_table.setItem(row, 7, total_item)
            
            # Update totals
            self.calculate_totals()

    def focus_on_current_quantity(self):
        """Focus on quantity of currently selected row"""
        current_row = self.sales_table.currentRow()
        if current_row >= 0:
            quantity_widget = self.sales_table.cellWidget(current_row, 4)
            if quantity_widget:
                quantity_widget.lineEdit().setFocus()
                quantity_widget.lineEdit().selectAll()

    def focus_on_current_price(self):
        """Focus on price of currently selected row"""
        current_row = self.sales_table.currentRow()
        if current_row >= 0:
            price_widget = self.sales_table.cellWidget(current_row, 5)
            if price_widget:
                price_widget.lineEdit().setFocus()
                price_widget.lineEdit().selectAll()
    
    def update_datetime(self):
        """Update datetime label"""
        # Simply update the datetime label with current time
        current_datetime = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
        self.datetime_label.setText(current_datetime)
    
    def start_timer(self):
        """Start timer for datetime updates"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)  # Connect to self.update_datetime
        self.timer.start(1000)
    
    def show_item_search(self):
        if not self.db_manager.connections:
            QMessageBox.warning(self, "Database Error", "No databases connected")
            return
            
        # Clear table selection before opening dialog
        self.sales_table.clearSelection()
        
        dialog = ItemSearchDialog(self.db_manager, self)
        dialog.item_selected.connect(self.on_item_selected_from_search)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Clear table selection after dialog closes
            self.item_id_input.setFocus()
            self.item_id_input.selectAll()
    
    def on_item_selected_from_search(self, item_id):
        """Handle item selection from search dialog"""
        # Set the item ID input
        self.item_id_input.setText(item_id)
        
        # Instead of calling a separate method, let's process it directly
        # Get the item details directly from the search dialog
        # But since we don't have access to the dialog's selected item data,
        # we need to search for it again using the database manager
        
        item_details = self.db_manager.search_item_by_id(item_id)
        
        if item_details:
            # Check if item already exists in sale_items list
            for row, item in enumerate(self.sale_items):
                if item['item_id'] == item_id:
                    # Increment quantity
                    quantity_widget = self.sales_table.cellWidget(row, 4)
                    if quantity_widget:
                        current_qty = quantity_widget.value()
                        new_qty = current_qty + 1
                        
                        # Check stock
                        if new_qty > self.sale_items[row]['available_stock']:
                            QMessageBox.warning(self, "Stock Limit", 
                                              f"Only {self.sale_items[row]['available_stock']} items available!")
                            quantity_widget.setValue(self.sale_items[row]['available_stock'])
                            # Focus on this row's quantity
                            self.sales_table.setCurrentCell(row, 4)
                            self.focus_on_quantity_cell(row)
                            return
                        
                        quantity_widget.setValue(new_qty)
                        self.update_item_quantity(row, new_qty)
                        
                        # Clear selection and focus on this row
                        self.sales_table.clearSelection()
                        self.sales_table.setCurrentCell(row, 4)
                        self.focus_on_quantity_cell(row)
                        
                    self.status_label.setText(f"Incremented {item_id} quantity to {new_qty}")
                    # Clear the item ID input
                    self.item_id_input.clear()
                    return
            
            # If item doesn't exist, add it
            if item_details['quantity'] <= 0:
                QMessageBox.warning(self, "Stock Warning", 
                                  f"Item '{item_id}' is out of stock!")
                self.item_id_input.selectAll()
                self.item_id_input.setFocus()
                return
            
            # Add new item to sale_items list
            self.sale_items.append({
                "item_id": item_details["item_id"],
                "display_name": item_details["display_name"],
                "quantity": 1,
                "price": item_details["price"],
                "cost": item_details["cost"],
                "total_price": item_details["price"],
                "total_cost": item_details["cost"],
                "profit": item_details["price"] - item_details["cost"],
                "inventory_type": item_details["inventory_type"],
                "database": item_details["database"],
                "available_stock": item_details["quantity"]
            })
            
            # Update table
            self.update_sale_items_table()
            
            # Set current row to the new item and focus on quantity
            row = len(self.sale_items) - 1
            self.sales_table.setCurrentCell(row, 4)
            self.focus_on_quantity_cell(row)
            
            self.status_label.setText(f"Added {item_details['display_name']}")
            # Clear the input
            self.item_id_input.clear()
        else:
            QMessageBox.warning(self, "Item Not Found", 
                              f"No inventory found with ID: {item_id}")
            self.item_id_input.selectAll()
            self.item_id_input.setFocus()

    def add_item_from_popup(self, item_id):
        """Special method for adding items from pop-up window"""
        item_id = item_id.strip().upper()
        
        # Check if item already exists in sale_items list
        for row, item in enumerate(self.sale_items):
            if item['item_id'] == item_id:
                # Get quantity widget and increment
                quantity_widget = self.sales_table.cellWidget(row, 4)
                if quantity_widget:
                    current_qty = quantity_widget.value()
                    new_qty = current_qty + 1
                    
                    # Check stock
                    if new_qty > self.sale_items[row]['available_stock']:
                        QMessageBox.warning(self, "Stock Limit", 
                                          f"Only {self.sale_items[row]['available_stock']} items available!")
                        quantity_widget.setValue(self.sale_items[row]['available_stock'])
                        # Focus on this row's quantity
                        self.sales_table.setCurrentCell(row, 4)
                        self.focus_on_quantity_cell(row)
                        return
                    
                    quantity_widget.setValue(new_qty)
                    self.update_item_quantity(row, new_qty)
                    
                    # Clear selection and focus on this row
                    self.sales_table.clearSelection()
                    self.sales_table.setCurrentCell(row, 4)
                    self.focus_on_quantity_cell(row)
                    
                self.status_label.setText(f"Incremented {item_id} quantity to {new_qty}")
                # Clear the item ID input
                self.item_id_input.clear()
                return
        
        # If item doesn't exist, add it
        item_details = self.db_manager.search_item_by_id(item_id)
        
        if item_details:
            if item_details['quantity'] <= 0:
                QMessageBox.warning(self, "Stock Warning", 
                                  f"Item '{item_id}' is out of stock!")
                self.item_id_input.selectAll()
                self.item_id_input.setFocus()
                return
            
            self.add_item_to_table_from_popup(item_details, item_id)
            self.status_label.setText(f"Added {item_details['display_name']}")
            
            # Clear the input
            self.item_id_input.clear()
        else:
            QMessageBox.warning(self, "Item Not Found", 
                              f"No inventory found with ID: {item_id}")
            self.item_id_input.selectAll()
            self.item_id_input.setFocus()

    def add_item_to_table_from_popup(self, item_details, item_id):
        """Add item to table from pop-up (with proper navigation)"""
        # Add new item to sale_items list
        self.sale_items.append({
            "item_id": item_details["item_id"],
            "display_name": item_details["display_name"],
            "quantity": 1,
            "price": item_details["price"],
            "cost": item_details["cost"],
            "total_price": item_details["price"],
            "total_cost": item_details["cost"],
            "profit": item_details["price"] - item_details["cost"],
            "inventory_type": item_details["inventory_type"],
            "database": item_details["database"],
            "available_stock": item_details["quantity"]
        })
        
        # Update table
        self.update_sale_items_table()
        
        # Set current row to the new item and focus on quantity
        row = len(self.sale_items) - 1
        self.sales_table.setCurrentCell(row, 4)
        self.focus_on_quantity_cell(row)

    def add_item_by_id(self):
        item_id = self.item_id_input.text().strip().upper()
        
        if not item_id:
            self.status_label.setText("Please enter an Item ID")
            return
        
        # Check if item already exists in sale_items list
        for row, item in enumerate(self.sale_items):
            if item['item_id'] == item_id:
                # Get quantity widget and increment
                quantity_widget = self.sales_table.cellWidget(row, 4)
                if quantity_widget:
                    current_qty = quantity_widget.value()
                    new_qty = current_qty + 1
                    
                    # Check stock
                    if new_qty > self.sale_items[row]['available_stock']:
                        QMessageBox.warning(self, "Stock Limit", 
                                          f"Only {self.sale_items[row]['available_stock']} items available!")
                        quantity_widget.setValue(self.sale_items[row]['available_stock'])
                        return
                    
                    quantity_widget.setValue(new_qty)
                    self.update_item_quantity(row, new_qty)
                    
                    # Clear selection and focus on this row
                    self.sales_table.clearSelection()
                    self.sales_table.setCurrentCell(row, 4)
                    self.focus_on_quantity_cell(row)
                    
                self.status_label.setText(f"Incremented {item_id} quantity to {new_qty}")
                self.item_id_input.clear()
                return
        
        item_details = self.db_manager.search_item_by_id(item_id)
        
        if item_details:
            if item_details['quantity'] <= 0:
                QMessageBox.warning(self, "Stock Warning", 
                                  f"Item '{item_id}' is out of stock!")
                self.item_id_input.selectAll()
                self.item_id_input.setFocus()
                return
            
            self.add_item_to_table(item_details)
            self.status_label.setText(f"Added {item_details['display_name']}")
            
            self.item_id_input.clear()
        else:
            QMessageBox.warning(self, "Item Not Found", 
                              f"No inventory found with ID: {item_id}")
            self.item_id_input.selectAll()
            self.item_id_input.setFocus()

    def add_item_to_table(self, item_details):
        """Add item to sales table"""
        # Add new item to sale_items list
        self.sale_items.append({
            "item_id": item_details["item_id"],
            "display_name": item_details["display_name"],
            "quantity": 1,
            "price": item_details["price"],
            "cost": item_details["cost"],
            "total_price": item_details["price"],
            "total_cost": item_details["cost"],
            "profit": item_details["price"] - item_details["cost"],
            "inventory_type": item_details["inventory_type"],
            "database": item_details["database"],
            "available_stock": item_details["quantity"]
        })
        
        # Update table
        self.update_sale_items_table()
        
        # Clear any existing selection
        self.sales_table.clearSelection()
        
        # Set current row to the new item and select it
        row = len(self.sale_items) - 1
        self.sales_table.setCurrentCell(row, 4)  # Focus on quantity column
        
        # Focus on the quantity cell for the new item
        self.focus_on_quantity_cell(row)

    def focus_on_quantity_cell(self, row):
        """Focus on quantity spinbox for given row"""
        if row < self.sales_table.rowCount():
            quantity_widget = self.sales_table.cellWidget(row, 4)
            if quantity_widget:
                quantity_widget.lineEdit().setFocus()
                quantity_widget.lineEdit().selectAll()

    def focus_on_price_cell(self, row):
        """Focus on price spinbox for given row"""
        if row < self.sales_table.rowCount():
            price_widget = self.sales_table.cellWidget(row, 5)
            if price_widget:
                price_widget.lineEdit().setFocus()
                price_widget.lineEdit().selectAll()
    
    def remove_selected_item(self):
        current_row = self.sales_table.currentRow()
        if current_row >= 0 and current_row < len(self.sale_items):
            item_name = self.sale_items[current_row]['display_name']
            self.sale_items.pop(current_row)
            self.update_sale_items_table()
            self.status_label.setText(f"Removed: {item_name}")
            self.item_id_input.setFocus()

    def verify_sale_saved(self, bill_number):
        """Verify that sale was actually saved to database"""
        try:
            if 'sales' in self.db_manager.connections:
                conn = self.db_manager.connections['sales']
                cursor = conn.cursor()
                
                # Check if sale exists
                cursor.execute("SELECT COUNT(*) FROM sales WHERE bill_number = ?", (bill_number,))
                sale_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sale_items WHERE sale_id IN (SELECT id FROM sales WHERE bill_number = ?)", (bill_number,))
                items_count = cursor.fetchone()[0]
                
                return sale_count > 0 and items_count == len(self.sale_items)
        except Exception as e:
            print(f"Error verifying sale: {e}")
            return False
        
        return False

    def save_sale(self):
        """Save sale with verification"""
        if not self.sale_items:
            QMessageBox.warning(self, "No Items", "No items to save!")
            return
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Confirm Sale", 
            f"Save sale with {len(self.sale_items)} items?\nTotal: Rs{self.grand_total_label.text().replace('Rs', '')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Calculate totals
        subtotal = sum(item['total_price'] for item in self.sale_items)
        total_cost = sum(item['total_cost'] for item in self.sale_items)
        
        # Calculate discount
        if self.discount_type.currentText() == "Amount":
            discount = self.discount_input.value()
        else:
            discount = subtotal * (self.discount_input.value() / 100)
        
        # Calculate tax
        tax_rate = self.tax_spinbox.value()
        tax = subtotal * (tax_rate / 100)
        grand_total = max(0, subtotal - discount + tax)
        
        # Get customer info
        customer = self.customer_input.text().strip()
        if not customer:
            customer = "WALK-IN CUSTOMER"
        
        # Save to database
        # Get return fee settings
        return_fee_type = self.return_fee_type.currentText()
        return_fee_amount = self.return_fee_input.value()

        # Save to database
        try:
            success, message = self.db_manager.save_sale(
                self.bill_number,
                self.bill_number_numeric,
                customer,
                "",  # customer_phone
                "",  # customer_address
                self.sale_items,
                discount,
                self.discount_type.currentText(),
                tax,
                tax_rate,
                grand_total,
                "Cash",  # Default payment method
                "Paid",  # Default payment status
                "",  # Notes
                return_fee_type,   # NEW: Return fee type
                return_fee_amount  # NEW: Return fee amount
            )
            if success:
                # Verify the sale was saved
                if self.verify_sale_saved(self.bill_number):
                    self.status_label.setText(f"Sale #{self.bill_number} saved successfully!")
                    
                    # Ask if user wants to print
                    print_reply = QMessageBox.question(
                        self,
                        "Sale Saved",
                        f"Sale #{self.bill_number} saved successfully!\n\nPrint invoice now?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    
                    if print_reply == QMessageBox.StandardButton.Yes:
                        # Use EnhancedIntegratedPrintingSystem to print
                        EnhancedIntegratedPrintingSystem.print_invoice(self)
                    
                    # Generate next bill number
                    self.db_manager.increment_bill_number()
                    self.bill_number_numeric = self.db_manager.get_next_bill_number()
                    self.bill_number = self.db_manager.format_bill_number(self.bill_number_numeric)
                    self.bill_number_label.setText(f"Bill #: {self.bill_number}")
                    
                    # Clear for next sale
                    self.clear_sale()
                else:
                    QMessageBox.warning(self, "Verification Failed", 
                                      "Sale was not properly saved to database!")
            else:
                QMessageBox.critical(self, "Save Error", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving sale: {str(e)}")
    
    def print_invoice(self):
        """Print professional invoice using EnhancedIntegratedPrintingSystem"""
        return EnhancedIntegratedPrintingSystem.print_invoice(self)

    def preview_invoice(self):
        """Preview invoice using EnhancedIntegratedPrintingSystem"""
        return EnhancedIntegratedPrintingSystem.preview_invoice(self)
    
    def save_pdf_invoice(self):
        """Save invoice as PDF using EnhancedIntegratedPrintingSystem"""
        if not self.sale_items:
            QMessageBox.warning(self, "No Items", "No items to save!")
            return
        
        # Ask for file location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Invoice as PDF",
            f"invoice_{self.bill_number}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            # Use the professional generator to save PDF
            bill_data = EnhancedIntegratedPrintingSystem.prepare_bill_data(self)
            if bill_data:
                # Note: This will need the actual invoice generator from your module
                # You might need to import and use it properly
                try:
                    if PRINT_MODULE_AVAILABLE:
                        generator = invoice_printer.InvoiceGenerator()
                        pdf_path = generator.generate_invoice_pdf(bill_data, file_path)
                        if pdf_path:
                            QMessageBox.information(self, "PDF Saved", 
                                                  f"Invoice saved as PDF:\n{pdf_path}")
                except Exception as e:
                    QMessageBox.critical(self, "PDF Error", f"Could not save PDF: {str(e)}")
    
    def clear_sale(self):
        if not self.sale_items:
            return
            
        reply = QMessageBox.question(self, "Clear Sale", 
                                   "Clear all items from sale?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.sales_table.setRowCount(0)
            self.sale_items.clear()
            self.discount_input.setValue(0)
            self.tax_spinbox.setValue(0)
            self.customer_input.setText("WALK-IN CUSTOMER")
            self.calculate_totals()
            self.update_items_count()
            self.status_label.setText("Sale cleared")
            self.item_id_input.setFocus()
    
    def clear_inputs(self):
        self.item_id_input.clear()
        self.item_id_input.setFocus()
    
    def calculate_totals(self):
        if not self.sale_items:
            self.subtotal_label.setText("Rs 0.00")
            self.grand_total_label.setText("Rs 0.00")
            self.total_cost_label.setText("Rs 0.00")
            self.profit_label.setText("Rs 0.00")
            self.profit_percent_label.setText("0.0%")
            return
            
        subtotal = sum(item['total_price'] for item in self.sale_items)
        total_cost = sum(item['total_cost'] for item in self.sale_items)
        
        discount = 0
        if self.discount_type.currentText() == "Amount":
            discount = self.discount_input.value()
        else:
            discount = subtotal * (self.discount_input.value() / 100)
        
        tax = subtotal * (self.tax_spinbox.value() / 100)
        # Show return fee in status bar for reference
        return_fee = self.return_fee_input.value()
        fee_type = self.return_fee_type.currentText()
        if return_fee > 0:
            if fee_type == "Per Page":
                self.status_label.setText(f"Return fee: Rs{return_fee:,.2f} per page (for multi-page invoices)")
            else:
                self.status_label.setText(f"Return fee: Rs{return_fee:,.2f} for full invoice return")
        
        grand_total = max(0, subtotal - discount + tax)
        
        profit = grand_total - total_cost
        profit_percent = (profit / total_cost * 100) if total_cost > 0 else 0
        
        self.subtotal_label.setText(f"Rs{subtotal:,.2f}")
        self.grand_total_label.setText(f"Rs{grand_total:,.2f}")
        self.total_cost_label.setText(f"Rs{total_cost:,.2f}")
        self.profit_label.setText(f"Rs{profit:,.2f}")
        self.profit_percent_label.setText(f"{profit_percent:.1f}%")
        
        if profit >= 0:
            self.profit_label.setStyleSheet("font-weight: bold; color: #27ae60; font-size: 12px;")
            self.profit_percent_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        else:
            self.profit_label.setStyleSheet("font-weight: bold; color: #e74c3c; font-size: 12px;")
            self.profit_percent_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
    
    def on_discount_type_changed(self, discount_type):
        if discount_type == "Percentage":
            self.discount_input.setMaximum(100)
            self.discount_input.setSuffix(" %")
        else:
            self.discount_input.setMaximum(100000)
            self.discount_input.setSuffix("")
        self.calculate_totals()
    
    def toggle_profit_section(self, checked):
        self.profit_visible = checked
        for i in range(self.profit_summary.layout().count()):
            widget = self.profit_summary.layout().itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setText("Show Profit" if not checked else "Hide Profit")
                break
    
    def toggle_profit_section_btn(self):
        self.profit_visible = not self.profit_visible
        self.profit_summary.setChecked(self.profit_visible)
        self.status_label.setText(f"Profit section {'shown' if self.profit_visible else 'hidden'}")
    
    def toggle_cost_profit(self):
        """Toggle cost column and profit summary - Ctrl+H shortcut"""
        self.cost_visible = not self.cost_visible
        self.profit_visible = not self.profit_visible
        
        # Toggle cost column visibility
        self.sales_table.setColumnHidden(6, not self.cost_visible)
        
        # Toggle profit summary visibility
        self.profit_summary.setVisible(self.profit_visible)
        self.profit_summary.setChecked(self.profit_visible)
        
        # Update status
        cost_status = "shown" if self.cost_visible else "hidden"
        profit_status = "shown" if self.profit_visible else "hidden"
        self.status_label.setText(f"Cost column {cost_status}, Profit summary {profit_status}")
    
    def update_items_count(self):
        count = len(self.sale_items)
        self.items_count_label.setText(f"Items: {count}")

    def keyPressEvent(self, event):
        """Handle keyboard events for smarter navigation - WITH PROTECTION"""
        try:
            if event.key() == Qt.Key.Key_Delete:
                self.remove_selected_item()
            elif event.key() == Qt.Key.Key_F1:
                self.show_item_search()
            elif event.key() == Qt.Key.Key_F2:
                self.new_bill()
            elif event.key() == Qt.Key.Key_F7:
                self.save_pdf_invoice()
            elif event.key() == Qt.Key.Key_F8:
                self.preview_invoice()
            elif event.key() == Qt.Key.Key_F9:
                self.print_invoice()  # Changed from print_professional_invoice
            elif event.key() == Qt.Key.Key_Escape:
                # ESC clears table selection first, then clears input
                if self.sales_table.selectedItems():
                    self.sales_table.clearSelection()
                else:
                    self.clear_inputs()
            elif event.key() == Qt.Key.Key_Tab:
                # Tab navigation
                if self.item_id_input.hasFocus():
                    # Move to first quantity cell if there are items
                    if self.sale_items:
                        self.sales_table.setCurrentCell(0, 4)
                        self.focus_on_quantity_cell(0)
                    else:
                        super().keyPressEvent(event)
                else:
                    super().keyPressEvent(event)
            elif event.key() == Qt.Key.Key_Backtab:
                # Shift+Tab navigation
                if self.sales_table.hasFocus():
                    self.item_id_input.setFocus()
                else:
                    super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
        except Exception as e:
            print(f"Error in window keyPressEvent: {e}")
            # Ignore the event to prevent crash
            event.ignore()

    def mousePressEvent(self, event):
        """Handle mouse clicks for smarter selection"""
        # Check if click is on the sales table
        table_rect = self.sales_table.geometry()
        table_rect = self.sales_table.mapTo(self, table_rect.topLeft())
        table_rect = (table_rect.x(), table_rect.y(), 
                      self.sales_table.width(), self.sales_table.height())
        
        # Check if click is inside table
        is_inside_table = (table_rect[0] <= event.pos().x() <= table_rect[0] + table_rect[2] and
                           table_rect[1] <= event.pos().y() <= table_rect[1] + table_rect[3])
        
        if is_inside_table:
            # Get the row and column at the click position
            pos_in_table = self.sales_table.mapFrom(self, event.pos())
            row = self.sales_table.rowAt(pos_in_table.y())
            col = self.sales_table.columnAt(pos_in_table.x())
            
            # If click is on an empty area (no row), clear selection
            if row == -1:
                self.sales_table.clearSelection()
            else:
                # Get the current selection
                current_selection = self.sales_table.selectedItems()
                
                # Check if this row is already selected
                is_row_selected = False
                for item in current_selection:
                    if item.row() == row:
                        is_row_selected = True
                        break
                
                # If row is already selected, clear selection
                if is_row_selected:
                    self.sales_table.clearSelection()
                    # Don't process further - let the table handle the click normally
                    pass
                else:
                    # Select the entire row
                    self.sales_table.selectRow(row)
        else:
            # Click is outside table - clear selection
            self.sales_table.clearSelection()
        
        super().mousePressEvent(event)
    
    def new_bill(self):
        if self.sale_items:
            reply = QMessageBox.question(self, "New Bill", 
                                       "Start a new bill? Current items will be cleared.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.clear_sale()
        self.status_label.setText("New bill started - Enter Item ID")
        self.item_id_input.setFocus()
    
    def closeEvent(self, event):
        if self.sale_items:
            reply = QMessageBox.question(self, "Unsaved Sale", 
                                       "You have unsaved items. Close anyway?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        
        self.db_manager.close_all()
        event.accept()

    # Add this method to the EnhancedSalesWindow class:

    def setParent(self, parent):
        """Override setParent to maintain functionality"""
        super().setParent(parent)
        # Re-establish focus after parent change
        if hasattr(self, 'item_id_input'):
            QTimer.singleShot(50, lambda: self.item_id_input.setFocus())

# In sales.py, add this class at the end before the main block:

# In sales.py, update the EnhancedSalesWidget class:

# class EnhancedSalesWidget(QWidget):
#     """Sales widget designed for integration into dashboard"""
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.sales_window = EnhancedSalesWindow()
        
#         # Get the central widget
#         central_widget = self.sales_window.centralWidget()
#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.addWidget(central_widget)
        
#         # Hide the main window frame
#         self.sales_window.hide()
        
#         # Disable closing the window when widget is closed
#         self.sales_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
class EnhancedSalesWidget(QWidget):
    """Sales widget designed for integration into dashboard"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create a new EnhancedSalesWindow but don't show it
        self.sales_window = EnhancedSalesWindow()
        self.sales_window.setParent(self)  # Set parent
        
        # Get the central widget
        central_widget = self.sales_window.centralWidget()
        
        # Create a new layout for this widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(central_widget)
        
        # Hide the main window frame (keep it alive for shortcuts)
        self.sales_window.hide()
        
        # Set focus policy to accept focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Transfer shortcuts from the window to this widget
        self.transfer_shortcuts()
        
        # Set initial focus to item ID input
        QTimer.singleShot(100, self.set_initial_focus)
        
        # DON'T create a new timer here - use the sales_window's timer
        # The sales_window already has its own timer for datetime updates

    def set_initial_focus(self):
        """Set initial focus to item ID input"""
        if hasattr(self.sales_window, 'item_id_input'):
            self.sales_window.item_id_input.setFocus()

    def transfer_shortcuts(self):
        """Transfer shortcuts from the sales window to this widget"""
        # Get all actions from the sales window
        for action in self.sales_window.actions():
            # Create a new action for this widget
            new_action = QAction(action.text(), self)
            new_action.setShortcut(action.shortcut())
            new_action.triggered.connect(action.trigger)
            self.addAction(new_action)

    def keyPressEvent(self, event):
        """Handle keyboard events in the widget"""
        # Pass key events to the sales window's keyPressEvent
        if hasattr(self.sales_window, 'keyPressEvent'):
            self.sales_window.keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse events in the widget"""
        # Pass mouse events to the sales window's mousePressEvent
        if hasattr(self.sales_window, 'mousePressEvent'):
            self.sales_window.mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def showEvent(self, event):
        """When widget is shown, set focus and ensure sales window timer is running"""
        super().showEvent(event)
        self.set_initial_focus()
        
        # Ensure the sales window's timer is running
        if hasattr(self.sales_window, 'timer') and self.sales_window.timer:
            if not self.sales_window.timer.isActive():
                self.sales_window.timer.start(1000)
    
    def hideEvent(self, event):
        """When widget is hidden, stop the sales window's timer to save resources"""
        super().hideEvent(event)
        if hasattr(self.sales_window, 'timer') and self.sales_window.timer:
            self.sales_window.timer.stop()
    
    def closeEvent(self, event):
        """Handle close event within dashboard"""
        # Close database connections if needed
        if hasattr(self.sales_window, 'db_manager') and self.sales_window.db_manager:
            self.sales_window.db_manager.close_all()
        
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = EnhancedSalesWindow()
    window.show()
    
    sys.exit(app.exec())
