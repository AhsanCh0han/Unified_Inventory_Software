# sales_history.py
import sys
import os
import sqlite3
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QDialogButtonBox, QLabel, QMessageBox,
    QStatusBar, QSpinBox, QDoubleSpinBox, QToolBar, QMenu, QMenuBar,
    QFileDialog, QGroupBox, QFrame, QHeaderView, QInputDialog,
    QListWidget, QListWidgetItem, QAbstractItemView,
    QCheckBox, QTextEdit, QDateEdit, QSplitter, QScrollArea
)
from PyQt6.QtGui import (
    QColor, QAction, QIcon, QKeySequence, QFont, QPalette, 
    QBrush, QPainter, QPageSize, QShortcut, QTextDocument
)
from PyQt6.QtCore import Qt, QTimer, QDate, pyqtSignal, QSettings, QSize
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog

# Import the printing system from sales.py
from sales import EnhancedIntegratedPrintingSystem

class SalesHistoryWindow(QWidget):
    """Sales History Window - View and manage past sales"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_connections = {}
        self.selected_sale_id = None
        self.sale_details = {}
        self.cost_profit_visible = True  # Track visibility of cost/profit columns
        
        self.setup_ui()
        self.connect_databases()
        self.load_sales()
        self.setup_shortcuts()
        
    def setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Search and filter section
        main_layout.addWidget(self.create_search_section())
        
        # Splitter for sales list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sales list table
        self.sales_table = self.create_sales_table()
        splitter.addWidget(self.sales_table)
        
        # Sale details panel
        self.details_panel = self.create_details_panel()
        splitter.addWidget(self.details_panel)
        
        # Set initial sizes (80% table, 20% details)
        splitter.setSizes([800, 200])
        main_layout.addWidget(splitter, 1)  # 1 = stretch factor
        
        # Status bar
        self.status_label = QLabel("Ready - Select a sale to view details")
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        # Set minimum size
        self.setMinimumSize(1200, 700)
        
    def create_search_section(self):
        """Create the search and filter section"""
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QGridLayout(search_frame)
        layout.setSpacing(10)
        
        # Row 1: Quick search
        layout.addWidget(QLabel("Quick Search:"), 0, 0)
        self.quick_search = QLineEdit()
        self.quick_search.setPlaceholderText("Search by Bill #, Customer, Item ID, or Description...")
        self.quick_search.textChanged.connect(self.filter_sales)
        layout.addWidget(self.quick_search, 0, 1, 1, 3)
        
        # Search button
        search_btn = QPushButton("🔍 Search")
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        search_btn.clicked.connect(self.filter_sales)
        layout.addWidget(search_btn, 0, 4)
        
        # Row 2: Date filters
        layout.addWidget(QLabel("Date Range:"), 1, 0)
        
        self.date_filter_combo = QComboBox()
        self.date_filter_combo.addItems([
            "All Time",
            "Today",
            "Yesterday",
            "Last 7 Days",
            "This Month",
            "Last Month",
            "Custom Range"
        ])
        self.date_filter_combo.currentIndexChanged.connect(self.on_date_filter_changed)
        layout.addWidget(self.date_filter_combo, 1, 1)
        
        layout.addWidget(QLabel("From:"), 1, 2)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setEnabled(False)
        layout.addWidget(self.date_from, 1, 3)
        
        layout.addWidget(QLabel("To:"), 1, 4)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setEnabled(False)
        layout.addWidget(self.date_to, 1, 5)
        
        # Row 3: Advanced filters
        layout.addWidget(QLabel("Customer:"), 2, 0)
        self.customer_filter = QLineEdit()
        self.customer_filter.setPlaceholderText("Filter by customer name...")
        self.customer_filter.textChanged.connect(self.filter_sales)
        layout.addWidget(self.customer_filter, 2, 1)
        
        layout.addWidget(QLabel("Item ID:"), 2, 2)
        self.item_id_filter = QLineEdit()
        self.item_id_filter.setPlaceholderText("Filter by specific item ID...")
        self.item_id_filter.textChanged.connect(self.filter_sales)
        layout.addWidget(self.item_id_filter, 2, 3)
        
        layout.addWidget(QLabel("Item Description:"), 2, 4)
        self.item_desc_filter = QLineEdit()
        self.item_desc_filter.setPlaceholderText("Filter by item description...")
        self.item_desc_filter.textChanged.connect(self.filter_sales)
        layout.addWidget(self.item_desc_filter, 2, 5)
        
        # Row 4: Action buttons
        action_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Refresh sales list")
        refresh_btn.clicked.connect(self.load_sales)
        
        export_btn = QPushButton("📊 Export")
        export_btn.setToolTip("Export to CSV")
        export_btn.clicked.connect(self.export_to_csv)
        
        clear_btn = QPushButton("❌ Clear Filters")
        clear_btn.setToolTip("Clear all filters")
        clear_btn.clicked.connect(self.clear_filters)
        
        action_layout.addWidget(refresh_btn)
        action_layout.addWidget(export_btn)
        action_layout.addWidget(clear_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout, 3, 0, 1, 6)
        
        return search_frame
    
    def create_sales_table(self):
        """Create the sales history table"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Bill #", "Date", "Time", "Customer", "Items", "Subtotal", 
            "Disc", "Total"
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Bill #
        table.setColumnWidth(0, 80)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Date
        table.setColumnWidth(1, 80)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Time
        table.setColumnWidth(2, 60)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Customer
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Items
        table.setColumnWidth(4, 40)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Subtotal
        table.setColumnWidth(5, 75)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Discount
        table.setColumnWidth(6, 50)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Total
        table.setColumnWidth(7, 80)
        
        # Style the table
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Connect selection changed
        table.itemSelectionChanged.connect(self.on_sale_selected)
        
        # Set stylesheet
        table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f8f9fa;
                background-color: white;
                gridline-color: #e0e0e0;
                border: 1px solid #d0d0d0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 8px;
                border: 1px solid #34495e;
                font-weight: bold;
            }
        """)
        
        return table
    
    def create_details_panel(self):
        """Create the sale details panel"""
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        panel.setFrameShape(QFrame.Shape.NoFrame)
        panel.setMinimumWidth(650)  # Set minimum width for details panel
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Bill info
        bill_info_group = QGroupBox("Bill Information")
        bill_info_layout = QGridLayout(bill_info_group)
        
        self.detail_bill_number = QLabel("")
        self.detail_date = QLabel("")
        self.detail_time = QLabel("")
        self.detail_customer = QLabel("")
        self.detail_payment = QLabel("")
        
        bill_info_layout.addWidget(QLabel("Bill Number:"), 0, 0)
        bill_info_layout.addWidget(self.detail_bill_number, 0, 1)
        bill_info_layout.addWidget(QLabel("Date:"), 1, 0)
        bill_info_layout.addWidget(self.detail_date, 1, 1)
        bill_info_layout.addWidget(QLabel("Time:"), 2, 0)
        bill_info_layout.addWidget(self.detail_time, 2, 1)
        bill_info_layout.addWidget(QLabel("Customer:"), 0, 2)
        bill_info_layout.addWidget(self.detail_customer, 0, 3)
        bill_info_layout.addWidget(QLabel("Payment:"), 1, 2)
        bill_info_layout.addWidget(self.detail_payment, 1, 3)
        
        layout.addWidget(bill_info_group)
        
        # Items table
        items_label = QLabel("Items Sold:")
        items_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(items_label)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "Item ID", "Description", "Qty", "Price", "Cost", "Total", "Profit"
        ])
        
        # Set column widths for items table
        items_header = self.items_table.horizontalHeader()
        items_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Item ID
        self.items_table.setColumnWidth(0, 80)
        items_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        items_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Qty
        self.items_table.setColumnWidth(2, 40)
        items_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Price
        self.items_table.setColumnWidth(3, 60)
        items_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Cost
        self.items_table.setColumnWidth(4, 80)
        items_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Total
        self.items_table.setColumnWidth(5, 90)
        items_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Profit
        self.items_table.setColumnWidth(6, 90)
        
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.items_table)
        
        # Totals section
        totals_group = QGroupBox("Totals")
        totals_layout = QGridLayout(totals_group)
        
        self.detail_subtotal = QLabel("Rs 0")
        self.detail_discount = QLabel("Rs 0")
        self.detail_grand_total = QLabel("Rs 0")
        self.detail_total_cost = QLabel("Rs 0")
        self.detail_total_profit = QLabel("Rs 0")
        
        totals_layout.addWidget(QLabel("Subtotal:"), 0, 0)
        totals_layout.addWidget(self.detail_subtotal, 0, 1)
        totals_layout.addWidget(QLabel("Discount:"), 1, 0)
        totals_layout.addWidget(self.detail_discount, 1, 1)
        totals_layout.addWidget(QLabel("Grand Total:"), 2, 0)
        totals_layout.addWidget(self.detail_grand_total, 2, 1)
        totals_layout.addWidget(QLabel("Total Cost:"), 0, 2)
        totals_layout.addWidget(self.detail_total_cost, 0, 3)
        totals_layout.addWidget(QLabel("Total Profit:"), 1, 2)
        totals_layout.addWidget(self.detail_total_profit, 1, 3)
        
        layout.addWidget(totals_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.print_btn = QPushButton("🖨️ Print Invoice")
        self.print_btn.setToolTip("Print this invoice")
        self.print_btn.clicked.connect(self.print_sale)
        self.print_btn.setEnabled(False)
        
        self.return_btn = QPushButton("↩️ Process Return")
        self.return_btn.setToolTip("Process return for this sale")
        self.return_btn.clicked.connect(self.process_return)
        self.return_btn.setEnabled(False)
        
        self.email_btn = QPushButton("📧 Email Invoice")
        self.email_btn.setToolTip("Send invoice by email")
        self.email_btn.clicked.connect(self.email_invoice)
        self.email_btn.setEnabled(False)

        self.preview_btn = QPushButton("👁️ Preview Invoice")  # Changed from preview_btn to self.preview_btn
        self.preview_btn.setToolTip("Preview invoice before printing")
        self.preview_btn.clicked.connect(self.preview_invoice)  # Connect to the method you need to create
        self.preview_btn.setEnabled(False)
        
        button_layout.addWidget(self.print_btn)
        button_layout.addWidget(self.return_btn)
        button_layout.addWidget(self.email_btn)
        button_layout.addWidget(self.preview_btn)  # Changed from preview_btn
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        panel.setWidget(content)
        return panel
    
    def connect_databases(self):
        """Connect to sales database"""
        try:
            # Connect to sales database
            sales_db = 'sales.db'
            if os.path.exists(sales_db):
                conn = sqlite3.connect(sales_db)
                conn.row_factory = sqlite3.Row
                self.db_connections['sales'] = conn
                print(f"Connected to {sales_db}")
            else:
                QMessageBox.warning(self, "Database Error", 
                                  "Sales database not found. No sales history available.")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            QMessageBox.critical(self, "Database Error", 
                               f"Could not connect to sales database: {str(e)}")
    
    def load_sales(self):
        """Load sales from database"""
        if 'sales' not in self.db_connections:
            return
        
        try:
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            # Get all sales ordered by date descending
            query = """
                SELECT 
                    id, bill_number, bill_number_numeric, customer,
                    sale_date, sale_time, total_items, subtotal,
                    discount, discount_type, grand_total,
                    payment_method, payment_status, notes
                FROM sales 
                ORDER BY sale_date DESC, sale_time DESC
            """
            
            cursor.execute(query)
            sales = cursor.fetchall()
            
            # Update table
            self.sales_table.setRowCount(len(sales))
            
            for row, sale in enumerate(sales):
                # Format date for display
                sale_date = sale['sale_date']
                if len(sale_date) == 10:  # YYYY-MM-DD format
                    try:
                        date_obj = datetime.strptime(sale_date, "%Y-%m-%d")
                        display_date = date_obj.strftime("%d/%m/%Y")
                    except:
                        display_date = sale_date
                else:
                    display_date = sale_date
                
                # Bill number
                bill_item = QTableWidgetItem(sale['bill_number'])
                bill_item.setData(Qt.ItemDataRole.UserRole, sale['id'])
                self.sales_table.setItem(row, 0, bill_item)
                
                # Date
                date_item = QTableWidgetItem(display_date)
                self.sales_table.setItem(row, 1, date_item)
                
                # Time
                time_item = QTableWidgetItem(sale['sale_time'])
                self.sales_table.setItem(row, 2, time_item)
                
                # Customer
                customer_item = QTableWidgetItem(sale['customer'])
                self.sales_table.setItem(row, 3, customer_item)
                
                # Items count
                items_item = QTableWidgetItem(str(sale['total_items']))
                items_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.sales_table.setItem(row, 4, items_item)
                
                # Subtotal - Format without extra decimals
                subtotal_str = self.format_currency(sale['subtotal'])
                subtotal_item = QTableWidgetItem(subtotal_str)
                subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.sales_table.setItem(row, 5, subtotal_item)
                
                # Discount - Format without extra decimals
                discount_str = self.format_currency(sale['discount'])
                discount_item = QTableWidgetItem(discount_str)
                discount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.sales_table.setItem(row, 6, discount_item)
                
                # Total - Format without extra decimals
                total_str = self.format_currency(sale['grand_total'])
                total_item = QTableWidgetItem(total_str)
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                total_item.setForeground(QColor("#e74c3c"))  # Red color for total
                font = total_item.font()
                font.setBold(True)
                total_item.setFont(font)
                self.sales_table.setItem(row, 7, total_item)
            
            self.status_label.setText(f"Loaded {len(sales)} sales records")
            
        except Exception as e:
            print(f"Error loading sales: {e}")
            QMessageBox.critical(self, "Database Error", 
                               f"Could not load sales: {str(e)}")
    
    def format_currency(self, value):
        """Format currency value without extra decimals"""
        if value is None:
            return "Rs 0"
        
        # Check if the value is a whole number
        if isinstance(value, (int, float)):
            if value == int(value):
                # Whole number, format without decimals
                return f"{int(value):,}"
            else:
                # Has decimals, format with 2 decimal places
                return f"{value:,}"
        else:
            # String or other type
            try:
                num_value = float(value)
                if num_value == int(num_value):
                    return f"{int(num_value):,}"
                else:
                    return f"{num_value:,}"
            except:
                return f"Rs 0"
    
    def filter_sales(self):
        """Filter sales based on criteria - now includes item search"""
        if 'sales' not in self.db_connections:
            return
        
        try:
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            # Build query with filters
            query = """
                SELECT DISTINCT
                    s.id, s.bill_number, s.bill_number_numeric, s.customer,
                    s.sale_date, s.sale_time, s.total_items, s.subtotal,
                    s.discount, s.discount_type, s.grand_total,
                    s.payment_method, s.payment_status, s.notes
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                WHERE 1=1
            """
            
            params = []
            
            # Quick search - now searches in bill_number, customer, item_id, and display_name
            search_text = self.quick_search.text().strip()
            if search_text:
                query += """
                    AND (s.bill_number LIKE ? 
                         OR s.customer LIKE ? 
                         OR si.item_id LIKE ? 
                         OR si.display_name LIKE ?)
                """
                search_param = f"%{search_text}%"
                params.extend([search_param, search_param, search_param, search_param])
            
            # Customer filter
            customer_filter = self.customer_filter.text().strip()
            if customer_filter:
                query += " AND s.customer LIKE ?"
                params.append(f"%{customer_filter}%")
            
            # Item ID filter
            item_id_filter = self.item_id_filter.text().strip()
            if item_id_filter:
                query += " AND si.item_id LIKE ?"
                params.append(f"%{item_id_filter}%")
            
            # Item Description filter
            item_desc_filter = self.item_desc_filter.text().strip()
            if item_desc_filter:
                query += " AND si.display_name LIKE ?"
                params.append(f"%{item_desc_filter}%")
            
            # Date range filter
            date_filter = self.date_filter_combo.currentText()
            today = QDate.currentDate()
            
            if date_filter == "Today":
                query += " AND s.sale_date = ?"
                params.append(today.toString("yyyy-MM-dd"))
            elif date_filter == "Yesterday":
                yesterday = today.addDays(-1)
                query += " AND s.sale_date = ?"
                params.append(yesterday.toString("yyyy-MM-dd"))
            elif date_filter == "Last 7 Days":
                seven_days_ago = today.addDays(-7)
                query += " AND s.sale_date >= ?"
                params.append(seven_days_ago.toString("yyyy-MM-dd"))
            elif date_filter == "This Month":
                query += " AND strftime('%Y-%m', s.sale_date) = strftime('%Y-%m', 'now')"
            elif date_filter == "Last Month":
                query += " AND strftime('%Y-%m', s.sale_date) = strftime('%Y-%m', 'now', '-1 month')"
            elif date_filter == "Custom Range":
                date_from = self.date_from.date().toString("yyyy-MM-dd")
                date_to = self.date_to.date().toString("yyyy-MM-dd")
                query += " AND s.sale_date BETWEEN ? AND ?"
                params.extend([date_from, date_to])
            
            # Total range filter - using the existing spinboxes (you can add these back if needed)
            # For now, we'll keep the same logic but note that we removed min/max total spinboxes
            # You can add them back if needed
            
            # Order by
            query += " ORDER BY s.sale_date DESC, s.sale_time DESC"
            
            cursor.execute(query, params)
            sales = cursor.fetchall()
            
            # Update table
            self.sales_table.setRowCount(len(sales))
            
            for row, sale in enumerate(sales):
                # Format date
                sale_date = sale['sale_date']
                if len(sale_date) == 10:
                    try:
                        date_obj = datetime.strptime(sale_date, "%Y-%m-%d")
                        display_date = date_obj.strftime("%d/%m/%Y")
                    except:
                        display_date = sale_date
                else:
                    display_date = sale_date
                
                # Populate table with formatted currency
                items = [
                    sale['bill_number'],
                    display_date,
                    sale['sale_time'],
                    sale['customer'],
                    str(sale['total_items']),
                    self.format_currency(sale['subtotal']),
                    self.format_currency(sale['discount']),
                    self.format_currency(sale['grand_total'])
                ]
                
                for col, value in enumerate(items):
                    item = QTableWidgetItem(value)
                    
                    # Set ID in first column
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, sale['id'])
                    
                    # Right align numeric columns
                    if col in [5, 6, 7]:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    
                    # Bold and color for total column
                    if col == 7:
                        item.setForeground(QColor("#e74c3c"))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                    
                    self.sales_table.setItem(row, col, item)
            
            # Update status with search info
            search_filters = []
            if search_text:
                search_filters.append(f'quick search: "{search_text}"')
            if customer_filter:
                search_filters.append(f'customer: "{customer_filter}"')
            if item_id_filter:
                search_filters.append(f'item ID: "{item_id_filter}"')
            if item_desc_filter:
                search_filters.append(f'item desc: "{item_desc_filter}"')
            
            if search_filters:
                filter_text = " | ".join(search_filters)
                self.status_label.setText(f"Found {len(sales)} sales matching {filter_text}")
            else:
                self.status_label.setText(f"Found {len(sales)} sales")
            
        except Exception as e:
            print(f"Error filtering sales: {e}")
            self.status_label.setText(f"Error filtering sales: {str(e)}")
    
    def on_date_filter_changed(self, index):
        """Handle date filter selection change"""
        is_custom = (self.date_filter_combo.currentText() == "Custom Range")
        self.date_from.setEnabled(is_custom)
        self.date_to.setEnabled(is_custom)
        
        if not is_custom:
            self.filter_sales()
    
    def on_sale_selected(self):
        """Handle sale selection from table"""
        selected_items = self.sales_table.selectedItems()
        if not selected_items:
            return
        
        # Get the sale ID from the first column
        row = selected_items[0].row()
        sale_id_item = self.sales_table.item(row, 0)
        if not sale_id_item:
            return
        
        sale_id = sale_id_item.data(Qt.ItemDataRole.UserRole)
        self.selected_sale_id = sale_id
        
        # Load sale details
        self.load_sale_details(sale_id)
        
        # Enable action buttons
        self.print_btn.setEnabled(True)
        self.return_btn.setEnabled(True)
        self.email_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
    
    def load_sale_details(self, sale_id):
        """Load detailed information for a specific sale"""
        if 'sales' not in self.db_connections:
            return
        
        try:
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            # Get sale header
            cursor.execute("""
                SELECT * FROM sales WHERE id = ?
            """, (sale_id,))
            
            sale = cursor.fetchone()
            if not sale:
                return
            
            # Store sale details
            self.sale_details = dict(sale)
            
            # Update bill info
            self.detail_bill_number.setText(sale['bill_number'])
            self.detail_date.setText(sale['sale_date'])
            self.detail_time.setText(sale['sale_time'])
            self.detail_customer.setText(sale['customer'])
            self.detail_payment.setText(f"{sale['payment_method']} ({sale['payment_status']})")
            
            # Get sale items
            cursor.execute("""
                SELECT * FROM sale_items 
                WHERE sale_id = ? 
                ORDER BY id
            """, (sale_id,))
            
            items = cursor.fetchall()
            
            # Update items table
            self.items_table.setRowCount(len(items))
            
            total_cost = 0
            total_profit = 0
            
            for row, item in enumerate(items):
                # Item ID
                id_item = QTableWidgetItem(item['item_id'])
                self.items_table.setItem(row, 0, id_item)
                
                # Description
                desc_item = QTableWidgetItem(item['display_name'])
                self.items_table.setItem(row, 1, desc_item)
                
                # Quantity
                qty_item = QTableWidgetItem(str(item['quantity']))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.items_table.setItem(row, 2, qty_item)
                
                # Price - Format without extra decimals
                price_str = self.format_currency(item['unit_price'])
                price_item = QTableWidgetItem(price_str)
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.items_table.setItem(row, 3, price_item)
                
                # Cost - Format without extra decimals
                cost_str = self.format_currency(item['unit_cost'])
                cost_item = QTableWidgetItem(cost_str)
                cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.items_table.setItem(row, 4, cost_item)
                
                # Total - Format without extra decimals
                total_str = self.format_currency(item['total_price'])
                total_item = QTableWidgetItem(total_str)
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.items_table.setItem(row, 5, total_item)
                
                # Profit - Format without extra decimals
                profit_str = self.format_currency(item['profit'])
                profit_item = QTableWidgetItem(profit_str)
                profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                profit_color = QColor("#27ae60" if item['profit'] >= 0 else "#e74c3c")
                profit_item.setForeground(profit_color)
                self.items_table.setItem(row, 6, profit_item)
                
                # Accumulate totals
                total_cost += item['total_cost']
                total_profit += item['profit']
            
            # Update totals with formatted currency
            self.detail_subtotal.setText(self.format_currency(sale['subtotal']))
            self.detail_discount.setText(self.format_currency(sale['discount']))
            self.detail_grand_total.setText(self.format_currency(sale['grand_total']))
            self.detail_total_cost.setText(self.format_currency(total_cost))
            self.detail_total_profit.setText(self.format_currency(total_profit))
            
            # Color profit based on value
            profit_color = "#27ae60" if total_profit >= 0 else "#e74c3c"
            self.detail_total_profit.setStyleSheet(f"color: {profit_color}; font-weight: bold;")
            
            self.status_label.setText(f"Loaded details for Bill #{sale['bill_number']}")
            
        except Exception as e:
            print(f"Error loading sale details: {e}")
            QMessageBox.warning(self, "Error", f"Could not load sale details: {str(e)}")
    
    def toggle_cost_profit_columns(self):
        """Toggle visibility of cost and profit columns"""
        self.cost_profit_visible = not self.cost_profit_visible
        
        # Toggle columns 4 (Cost) and 6 (Profit) - 0-based indexing
        self.items_table.setColumnHidden(4, not self.cost_profit_visible)
        self.items_table.setColumnHidden(6, not self.cost_profit_visible)
        
        # Adjust column widths when showing/hiding
        if self.cost_profit_visible:
            # Show cost and profit columns
            self.items_table.setColumnWidth(4, 80)  # Cost
            self.items_table.setColumnWidth(6, 90)  # Profit
        else:
            # Hide cost and profit, give more space to description
            self.items_table.setColumnWidth(1, 300)  # Description gets more space
        
        status = "shown" if self.cost_profit_visible else "hidden"
        self.status_label.setText(f"Cost and Profit columns {status}")
    
    def print_sale(self):
        """Print the selected sale invoice"""
        if not self.selected_sale_id:
            QMessageBox.warning(self, "No Selection", "Please select a sale to print.")
            return
        
        try:
            # Prepare bill data from sale details
            bill_data = self.prepare_bill_data_from_sale()
            
            if not bill_data:
                QMessageBox.warning(self, "Print Error", "Could not prepare bill data for printing.")
                return
            
            # Create invoice generator using invoice_printer
            from invoice_printer import InvoiceGenerator
            
            generator = InvoiceGenerator()
            
            # Print the invoice
            success = generator.print_invoice(bill_data, self)
            
            if success:
                self.status_label.setText(f"Printed invoice #{bill_data['bill_number']}")
                QMessageBox.information(self, "Print Successful", 
                                      f"Invoice #{bill_data['bill_number']} sent to printer successfully.")
            else:
                QMessageBox.warning(self, "Print", "Printing was cancelled or failed.")
                
        except Exception as e:
            print(f"Error printing sale: {e}")
            QMessageBox.critical(self, "Print Error", f"Could not print invoice: {str(e)}")

    def prepare_bill_data_from_sale(self):
        """Prepare bill data from sale details for printing"""
        if not self.sale_details:
            return None
        
        try:
            # Get sale items
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT item_id, display_name, quantity, unit_price, total_price
                FROM sale_items 
                WHERE sale_id = ?
            """, (self.selected_sale_id,))
            
            items_data = cursor.fetchall()
            
            # Prepare items list in the format expected by invoice_printer
            items = []
            for item in items_data:
                items.append({
                    'description': item['display_name'],
                    'name': item['display_name'],  # Add name field as well
                    'qty': item['quantity'],
                    'price': item['unit_price'],
                    'total': item['total_price']
                })
            
            # Format date from YYYY-MM-DD to DD/MM/YYYY
            sale_date = self.sale_details['sale_date']
            try:
                date_obj = datetime.strptime(sale_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%Y")
            except:
                formatted_date = sale_date
            
            # Prepare bill data in the exact format expected by invoice_printer
            sale = self.sale_details
            bill_data = {
                'bill_number': sale['bill_number'],
                'customer': sale['customer'],
                'items': items,
                'subtotal': sale['subtotal'],
                'discount': sale['discount'],
                'discount_type': sale.get('discount_type', 'Amount'),
                'tax_rate': sale.get('tax_rate', 0.0),
                'grand_total': sale['grand_total'],
                'date': formatted_date,
                'time': sale['sale_time']
            }
            
            return bill_data
            
        except Exception as e:
            print(f"Error preparing bill data: {e}")
            return None

    def preview_invoice(self):
        """Preview invoice before printing"""
        if not self.selected_sale_id:
            QMessageBox.warning(self, "No Selection", "Please select a sale to preview.")
            return
        
        try:
            # Prepare bill data from sale details
            bill_data = self.prepare_bill_data_from_sale()
            
            if not bill_data:
                QMessageBox.warning(self, "Preview Error", "Could not prepare bill data for preview.")
                return
            
            # Import and use InvoicePreviewDialog
            from invoice_printer import InvoicePreviewDialog
            
            dialog = InvoicePreviewDialog(bill_data, self)
            dialog.exec()
            
        except Exception as e:
            print(f"Error previewing invoice: {e}")
            QMessageBox.critical(self, "Preview Error", f"Could not preview invoice: {str(e)}")
    
    def process_return(self):
        """Process return for selected sale"""
        if not self.selected_sale_id:
            QMessageBox.warning(self, "No Selection", "Please select a sale to process return.")
            return
        
        QMessageBox.information(self, "Feature Coming Soon", 
                              "Sales return functionality will be available in the next update.")
        # TODO: Implement sales return functionality
    
    def email_invoice(self):
        """Email the selected invoice"""
        if not self.selected_sale_id:
            QMessageBox.warning(self, "No Selection", "Please select a sale to email.")
            return
        
        QMessageBox.information(self, "Feature Coming Soon", 
                              "Email functionality will be available in the next update.")
        # TODO: Implement email functionality
    
    def export_to_csv(self):
        """Export sales data to CSV"""
        if 'sales' not in self.db_connections:
            return
        
        try:
            # Get file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Sales to CSV",
                f"sales_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            # Get all filtered sales
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            # Reuse the filter query logic
            # For simplicity, export all sales
            cursor.execute("""
                SELECT DISTINCT
                    s.bill_number, s.sale_date, s.sale_time, s.customer,
                    s.total_items, s.subtotal, s.discount, s.grand_total,
                    s.payment_method, s.payment_status
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                ORDER BY s.sale_date DESC, s.sale_time DESC
            """)
            
            sales = cursor.fetchall()
            
            # Write to CSV
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Bill Number', 'Date', 'Time', 'Customer',
                    'Items', 'Subtotal', 'Discount', 'Grand Total',
                    'Payment Method', 'Payment Status'
                ])
                
                # Write data
                for sale in sales:
                    writer.writerow([
                        sale['bill_number'],
                        sale['sale_date'],
                        sale['sale_time'],
                        sale['customer'],
                        sale['total_items'],
                        sale['subtotal'],
                        sale['discount'],
                        sale['grand_total'],
                        sale['payment_method'],
                        sale['payment_status']
                    ])
            
            self.status_label.setText(f"Exported {len(sales)} sales to {os.path.basename(file_path)}")
            QMessageBox.information(self, "Export Successful", 
                                  f"Successfully exported {len(sales)} sales records to CSV.")
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            QMessageBox.critical(self, "Export Error", f"Could not export to CSV: {str(e)}")
    
    def clear_filters(self):
        """Clear all filters"""
        self.quick_search.clear()
        self.customer_filter.clear()
        self.item_id_filter.clear()
        self.item_desc_filter.clear()
        self.date_filter_combo.setCurrentIndex(0)
        
        # Reload all sales
        self.load_sales()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Refresh shortcut
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.load_sales)
        
        # Print shortcut
        print_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        print_shortcut.activated.connect(self.print_sale)
        
        # Export shortcut
        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self.export_to_csv)
        
        # Clear filters shortcut
        clear_shortcut = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        clear_shortcut.activated.connect(self.clear_filters)
        
        # Toggle cost/profit columns shortcut
        toggle_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        toggle_shortcut.activated.connect(self.toggle_cost_profit_columns)
        
        # Focus quick search shortcut
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(lambda: self.quick_search.setFocus())

        # In setup_shortcuts() method:
        # Print shortcut
        print_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        print_shortcut.activated.connect(self.print_sale)

        # Preview shortcut
        preview_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        preview_shortcut.activated.connect(self.preview_invoice)
            
    def closeEvent(self, event):
        """Close database connections on exit"""
        for db_name, conn in self.db_connections.items():
            if conn:
                try:
                    conn.close()
                    print(f"Closed connection to {db_name}")
                except:
                    pass
        event.accept()


# Widget wrapper for integration with dashboard
class SalesHistoryWidget(QWidget):
    """Sales History Widget for integration into dashboard"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_window = SalesHistoryWindow()
        
        # Get the central widget
        central_widget = self.history_window
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(central_widget)
        
        # Set initial focus
        QTimer.singleShot(100, self.set_initial_focus)
    
    def set_initial_focus(self):
        """Set initial focus to search field"""
        if hasattr(self.history_window, 'quick_search'):
            self.history_window.quick_search.setFocus()
    
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        self.set_initial_focus()
        
        # Refresh data when shown
        if hasattr(self.history_window, 'load_sales'):
            self.history_window.load_sales()


# For standalone testing
if __name__ == "__main__":
    print("Running Sales History standalone...")
    print("Note: This requires sales.db to exist in the same directory.")
    
    app = QApplication(sys.argv)
    
    # Apply some basic styling
    app.setStyleSheet("""
        QWidget {
            font-family: Arial, sans-serif;
        }
        QPushButton {
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
    """)
    
    window = SalesHistoryWindow()
    window.setWindowTitle("Sales History - Standalone Mode")
    window.resize(1400, 800)
    window.show()
    
    sys.exit(app.exec())