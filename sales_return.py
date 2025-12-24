# sales_return.py - Professional Sales Return System
import sys
import os
import sqlite3
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QDialogButtonBox, QLabel, QMessageBox,
    QStatusBar, QSpinBox, QDoubleSpinBox, QGroupBox, QFrame, QHeaderView,
    QFileDialog, QTextEdit, QDateEdit, QSplitter, QScrollArea,
    QCheckBox, QRadioButton, QButtonGroup, QTabWidget, QStackedWidget,
    QToolBar, QToolButton, QMenu
)
from PyQt6.QtGui import (
    QColor, QAction, QIcon, QKeySequence, QFont, QPalette, 
    QBrush, QPainter, QShortcut, QPixmap
)
from PyQt6.QtCore import Qt, QTimer, QDate, pyqtSignal, QSettings, QSize, QPoint

class EnhancedReturnDialog(QDialog):
    """Professional return dialog with validation"""
    
    def __init__(self, sale_data, item_data, parent=None):
        super().__init__(parent)
        self.sale_data = sale_data
        self.item_data = item_data
        self.original_quantity = item_data['quantity']
        self.available_qty = self.calculate_available_quantity()
        self.setup_ui()
        
    def calculate_available_quantity(self):
        """Calculate how many items can still be returned"""
        if 'sales' not in self.parent().db_connections:
            return self.original_quantity
            
        try:
            conn = self.parent().db_connections['sales']
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COALESCE(SUM(ri.quantity), 0) as already_returned
                FROM sale_items si
                LEFT JOIN return_items ri ON ri.sale_id = si.sale_id AND ri.item_id = si.item_id
                WHERE si.sale_id = ? AND si.item_id = ?
                GROUP BY si.id
            """, (self.sale_data['id'], self.item_data['item_id']))
            
            result = cursor.fetchone()
            if result:
                already_returned = result['already_returned'] if hasattr(result, '__getitem__') else result[0]
                return max(0, self.original_quantity - already_returned)
            return self.original_quantity
            
        except Exception as e:
            print(f"Error calculating available quantity: {e}")
            return self.original_quantity
        
    def setup_ui(self):
        """Setup professional return dialog UI"""
        self.setWindowTitle(f"Return Item - Bill #{self.sale_data.get('bill_number', 'N/A')}")
        self.setMinimumSize(600, 600)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_label = QLabel("RETURN PROCESSING")
        header_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 8px 0;
            border-bottom: 2px solid #007bff;
        """)
        main_layout.addWidget(header_label)
        
        # Compact layout using grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        
        # Bill Information
        bill_info_group = QGroupBox("Bill Information")
        bill_info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 5px;
                padding-top: 10px;
            }
        """)
        bill_layout = QFormLayout(bill_info_group)
        bill_layout.setSpacing(5)
        
        bill_layout.addRow("Bill Number:", QLabel(str(self.sale_data.get('bill_number', 'N/A'))))
        bill_layout.addRow("Date:", QLabel(self.sale_data.get('sale_date', 'N/A')))
        bill_layout.addRow("Customer:", QLabel(self.sale_data.get('customer', 'Walk-in')))
        
        grid_layout.addWidget(bill_info_group, 0, 0, 1, 2)
        
        # Item Information
        item_info_group = QGroupBox("Item Details")
        item_info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 5px;
                padding-top: 10px;
            }
        """)
        item_layout = QFormLayout(item_info_group)
        item_layout.setSpacing(5)
        
        item_layout.addRow("Item ID:", QLabel(self.item_data['item_id']))
        item_layout.addRow("Description:", QLabel(self.item_data['display_name']))
        item_layout.addRow("Original Qty:", QLabel(str(self.original_quantity)))
        item_layout.addRow("Available:", QLabel(f"<b>{self.available_qty}</b>"))
        item_layout.addRow("Unit Price:", QLabel(f"Rs {self.item_data['unit_price']:,.2f}"))
        
        grid_layout.addWidget(item_info_group, 1, 0, 1, 2)
        
        # Return Quantity
        qty_group = QGroupBox("Return Quantity")
        qty_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 5px;
                padding-top: 10px;
            }
        """)
        qty_layout = QHBoxLayout(qty_group)
        qty_layout.setSpacing(10)
        
        qty_layout.addWidget(QLabel("Quantity:"))
        self.return_qty = QSpinBox()
        self.return_qty.setRange(1, self.available_qty)
        self.return_qty.setValue(self.available_qty if self.available_qty > 0 else 1)
        self.return_qty.setMaximumWidth(80)
        self.return_qty.valueChanged.connect(self.calculate_refund)
        qty_layout.addWidget(self.return_qty)
        
        qty_layout.addWidget(QLabel("Available:"))
        available_label = QLabel(str(self.available_qty))
        available_label.setStyleSheet("color: #28a745; font-weight: bold;")
        qty_layout.addWidget(available_label)
        qty_layout.addStretch()
        
        grid_layout.addWidget(qty_group, 2, 0, 1, 2)
        
        # Reason and Condition
        self.reason_combo = QComboBox()
        self.reason_combo.addItems([
            "🔴 Defective/Faulty",
            "🟡 Wrong Item Received",
            "🟢 Customer Changed Mind",
            "🔵 Wrong Size/Fit",
            "🟣 Other Reason"
        ])
        grid_layout.addWidget(QLabel("Reason:"), 3, 0)
        grid_layout.addWidget(self.reason_combo, 3, 1)
        
        self.condition_combo = QComboBox()
        self.condition_combo.addItems([
            "🟢 Unopened/New",
            "🟡 Opened - Good",
            "🔴 Damaged/Defective"
        ])
        grid_layout.addWidget(QLabel("Condition:"), 4, 0)
        grid_layout.addWidget(self.condition_combo, 4, 1)
        
        # Restocking Fee
        restocking_layout = QHBoxLayout()
        restocking_layout.addWidget(QLabel("Restocking Fee:"))
        self.restocking_spin = QDoubleSpinBox()
        self.restocking_spin.setRange(0, 50)
        self.restocking_spin.setValue(0.0)
        self.restocking_spin.setSuffix("%")
        self.restocking_spin.setMaximumWidth(80)
        self.restocking_spin.valueChanged.connect(self.calculate_refund)
        restocking_layout.addWidget(self.restocking_spin)
        restocking_layout.addStretch()
        
        grid_layout.addLayout(restocking_layout, 5, 0, 1, 2)
        
        # Refund Calculation
        calc_frame = QFrame()
        calc_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        calc_layout = QGridLayout(calc_frame)
        calc_layout.setVerticalSpacing(5)
        calc_layout.setHorizontalSpacing(15)
        
        calc_layout.addWidget(QLabel("Refund per Unit:"), 0, 0)
        self.refund_per_unit_label = QLabel("Rs 0.00")
        self.refund_per_unit_label.setStyleSheet("font-weight: bold; color: #28a745;")
        calc_layout.addWidget(self.refund_per_unit_label, 0, 1)
        
        calc_layout.addWidget(QLabel("Total Refund:"), 1, 0)
        self.total_refund_label = QLabel("Rs 0.00")
        self.total_refund_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px; 
            color: #28a745;
            background-color: #d4edda;
            padding: 3px;
            border-radius: 3px;
        """)
        calc_layout.addWidget(self.total_refund_label, 1, 1)
        
        grid_layout.addWidget(calc_frame, 6, 0, 1, 2)
        
        # Refund Method
        method_layout = QHBoxLayout()
        self.refund_cash = QRadioButton("Cash")
        self.refund_card = QRadioButton("Card")
        self.refund_credit = QRadioButton("Credit")
        self.refund_cash.setChecked(True)
        
        for rb in [self.refund_cash, self.refund_card, self.refund_credit]:
            rb.setStyleSheet("font-size: 12px; padding: 4px;")
            method_layout.addWidget(rb)
        
        method_layout.addStretch()
        grid_layout.addWidget(QLabel("Refund Method:"), 7, 0)
        grid_layout.addLayout(method_layout, 7, 1)
        
        # Notes
        grid_layout.addWidget(QLabel("Notes:"), 8, 0)
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(60)
        self.notes_text.setPlaceholderText("Additional notes...")
        grid_layout.addWidget(self.notes_text, 8, 1)
        
        main_layout.addLayout(grid_layout)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #6c757d;
                border-radius: 3px;
                color: #6c757d;
                font-weight: bold;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        self.process_btn = QPushButton("Process Return")
        self.process_btn.setMinimumWidth(100)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 6px 15px;
                border-radius: 3px;
                border: none;
            }
        """)
        self.process_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.process_btn)
        
        main_layout.addLayout(button_layout)
        
        # Initial calculation
        self.calculate_refund()
        
    def calculate_refund(self):
        """Calculate refund amount"""
        unit_price = self.item_data['unit_price']
        qty = self.return_qty.value()
        restocking_percent = self.restocking_spin.value() / 100
        
        restocking_fee = unit_price * restocking_percent
        refund_per_unit = unit_price - restocking_fee
        total_refund = refund_per_unit * qty
        
        self.refund_per_unit_label.setText(f"Rs {refund_per_unit:,.2f}")
        self.total_refund_label.setText(f"Rs {total_refund:,.2f}")
        
    def get_return_data(self):
        """Get all return data"""
        refund_method = "Cash"
        if self.refund_card.isChecked():
            refund_method = "Card"
        elif self.refund_credit.isChecked():
            refund_method = "Store Credit"
            
        # Get unit price from item_data
        unit_price = self.item_data['unit_price']
        restocking_percent = self.restocking_spin.value() / 100
        restocking_amount = unit_price * restocking_percent * self.return_qty.value()
            
        return {
            'sale_id': self.sale_data.get('id'),
            'bill_number': self.sale_data.get('bill_number', ''),
            'item_id': self.item_data['item_id'],
            'item_name': self.item_data['display_name'],
            'quantity': self.return_qty.value(),
            'unit_price': unit_price,
            'unit_cost': self.item_data.get('unit_cost', 0),
            'original_quantity': self.original_quantity,
            'available_quantity': self.available_qty,
            'total_refund': float(self.total_refund_label.text().replace('Rs ', '').replace(',', '')),
            'refund_per_unit': float(self.refund_per_unit_label.text().replace('Rs ', '').replace(',', '')),
            'reason': self.reason_combo.currentText(),
            'condition': self.condition_combo.currentText(),
            'refund_method': refund_method,
            'restocking_fee': self.restocking_spin.value(),
            'notes': self.notes_text.toPlainText(),
            'restocking_amount': restocking_amount
        }


class ProfessionalSalesReturnWindow(QWidget):
    """Professional Sales Return System"""
    
    return_processed = pyqtSignal(dict)  # Signal for return completion
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_connections = {}
        self.selected_sale_id = None
        self.sale_details = {}
        self.return_items = []
        self.current_mode = 'return'
        self.setup_ui()
        self.setup_database()
        self.load_recent_sales()
        self.setup_shortcuts()
        
    def setup_ui(self):
        """Setup clean, professional UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Compact Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(5)
        
        # Mode toggle
        self.return_mode_btn = QPushButton("Returns")
        self.return_mode_btn.setCheckable(True)
        self.return_mode_btn.setChecked(True)
        self.return_mode_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                border: 1px solid #007bff;
                border-radius: 3px;
                background-color: #007bff;
                color: white;
            }
            QPushButton:checked {
                background-color: #0056b3;
            }
        """)
        self.return_mode_btn.clicked.connect(lambda: self.switch_mode('return'))
        
        self.exchange_mode_btn = QPushButton("Exchange")
        self.exchange_mode_btn.setCheckable(True)
        self.exchange_mode_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                border: 1px solid #6c757d;
                border-radius: 3px;
                background-color: #6c757d;
                color: white;
            }
        """)
        self.exchange_mode_btn.clicked.connect(lambda: self.switch_mode('exchange'))
        
        toolbar_layout.addWidget(self.return_mode_btn)
        toolbar_layout.addWidget(self.exchange_mode_btn)
        toolbar_layout.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setMaximumWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #ced4da;
                border-radius: 3px;
            }
        """)
        toolbar_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 3px;
            }
        """)
        search_btn.clicked.connect(self.perform_search)
        toolbar_layout.addWidget(search_btn)
        
        # Date filter
        self.date_filter = QComboBox()
        self.date_filter.addItems([
            "Last 7 Days",
            "Last 30 Days",
            "Today",
            "Yesterday",
            "This Month",
            "All Time"
        ])
        self.date_filter.setMaximumWidth(120)
        self.date_filter.currentIndexChanged.connect(self.load_recent_sales)
        toolbar_layout.addWidget(self.date_filter)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
            }
        """)
        refresh_btn.clicked.connect(self.load_recent_sales)
        toolbar_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # Main horizontal splitter (TOP and BOTTOM)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top Panel: Sales List and Bill Info
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)
        
        # Sales List (Left side)
        sales_group = QGroupBox("Sales History")
        sales_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 10px;
            }
        """)
        sales_layout = QVBoxLayout(sales_group)
        sales_layout.setContentsMargins(5, 5, 5, 5)
        sales_layout.setSpacing(5)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(5)
        self.sales_table.setHorizontalHeaderLabels([
            "Bill #", "Date", "Customer", "Items", "Total"
        ])
        
        header = self.sales_table.horizontalHeader()
        self.sales_table.setColumnWidth(0, 70)  # Bill #
        self.sales_table.setColumnWidth(1, 70)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Customer
        self.sales_table.setColumnWidth(3, 50)  # Items
        self.sales_table.setColumnWidth(4, 80)  # Total
        
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sales_table.itemSelectionChanged.connect(self.on_sale_selected)
        
        self.sales_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 3px;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 3px;
                font-size: 11px;
            }
            QHeaderView::section {
                padding: 6px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        sales_layout.addWidget(self.sales_table)
        top_layout.addWidget(sales_group, 2)  # 2 parts width
        
        # Bill Info Panel (Right side)
        info_group = QGroupBox("Bill Details")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 10px;
            }
        """)
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setSpacing(5)
        
        self.bill_info_table = QTableWidget()
        self.bill_info_table.setColumnCount(2)
        self.bill_info_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.bill_info_table.setRowCount(6)
        
        # Set rows
        self.bill_info_table.setItem(0, 0, QTableWidgetItem("Bill Number"))
        self.bill_info_table.setItem(1, 0, QTableWidgetItem("Date"))
        self.bill_info_table.setItem(2, 0, QTableWidgetItem("Customer"))
        self.bill_info_table.setItem(3, 0, QTableWidgetItem("Payment"))
        self.bill_info_table.setItem(4, 0, QTableWidgetItem("Items"))
        self.bill_info_table.setItem(5, 0, QTableWidgetItem("Total"))
        
        self.bill_info_table.horizontalHeader().setStretchLastSection(True)
        self.bill_info_table.verticalHeader().setVisible(False)
        self.bill_info_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.bill_info_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 3px;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 4px;
                font-size: 11px;
            }
            QHeaderView::section {
                padding: 6px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        info_layout.addWidget(self.bill_info_table)
        
        # Quick action buttons
        quick_btn_layout = QHBoxLayout()
        
        self.full_return_btn = QPushButton("Full Invoice Return")
        self.full_return_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                border: none;
                font-size: 11px;
            }
        """)
        self.full_return_btn.setEnabled(False)
        self.full_return_btn.clicked.connect(self.return_full_invoice)
        
        self.clear_returns_btn = QPushButton("Clear Returns")
        self.clear_returns_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                border: none;
                font-size: 11px;
            }
        """)
        self.clear_returns_btn.setEnabled(False)
        self.clear_returns_btn.clicked.connect(self.clear_all_returns)
        
        quick_btn_layout.addWidget(self.full_return_btn)
        quick_btn_layout.addWidget(self.clear_returns_btn)
        
        info_layout.addLayout(quick_btn_layout)
        top_layout.addWidget(info_group, 1)  # 1 part width
        
        main_splitter.addWidget(top_panel)
        
        # Bottom Panel: Return Items and Pending Returns
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(5)
        
        # Sale Items
        items_group = QGroupBox("Sale Items")
        items_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 10px;
            }
        """)
        items_layout = QVBoxLayout(items_group)
        items_layout.setContentsMargins(5, 5, 5, 5)
        items_layout.setSpacing(5)
        
        self.sale_items_table = QTableWidget()
        self.sale_items_table.setColumnCount(7)
        self.sale_items_table.setHorizontalHeaderLabels([
            "Item ID", "Description", "Qty", "Price", "Sold", "Ret'd", "Action"
        ])
        
        header = self.sale_items_table.horizontalHeader()
        self.sale_items_table.setColumnWidth(0, 80)  # Item ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        self.sale_items_table.setColumnWidth(2, 40)  # Qty
        self.sale_items_table.setColumnWidth(3, 60)  # Price
        self.sale_items_table.setColumnWidth(4, 40)  # Sold
        self.sale_items_table.setColumnWidth(5, 40)  # Ret'd
        self.sale_items_table.setColumnWidth(6, 80)  # Action
        
        self.sale_items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sale_items_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 3px;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 3px;
                font-size: 11px;
            }
            QHeaderView::section {
                padding: 6px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        items_layout.addWidget(self.sale_items_table)
        bottom_layout.addWidget(items_group, 1)
        
        # Pending Returns
        pending_group = QGroupBox("Pending Returns")
        pending_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ffc107;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 10px;
            }
        """)
        pending_layout = QVBoxLayout(pending_group)
        pending_layout.setContentsMargins(5, 5, 5, 5)
        pending_layout.setSpacing(5)
        
        self.pending_returns_table = QTableWidget()
        self.pending_returns_table.setColumnCount(8)
        self.pending_returns_table.setHorizontalHeaderLabels([
            "Item ID", "Description", "Qty", "Refund", "Reason", "Method", "Status", "Action"
        ])
        
        header = self.pending_returns_table.horizontalHeader()
        self.pending_returns_table.setColumnWidth(0, 80)  # Item ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        self.pending_returns_table.setColumnWidth(2, 50)  # Qty
        self.pending_returns_table.setColumnWidth(3, 80)  # Refund
        self.pending_returns_table.setColumnWidth(4, 100)  # Reason
        self.pending_returns_table.setColumnWidth(5, 70)  # Method
        self.pending_returns_table.setColumnWidth(6, 70)  # Status
        self.pending_returns_table.setColumnWidth(7, 70)  # Action
        
        self.pending_returns_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 3px;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 3px;
                font-size: 11px;
            }
            QHeaderView::section {
                padding: 6px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        pending_layout.addWidget(self.pending_returns_table)
        
        # Summary and Process button
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 3px;
                padding: 8px;
            }
        """)
        summary_layout = QGridLayout(summary_frame)
        
        self.pending_items_label = QLabel("0")
        self.pending_qty_label = QLabel("0")
        self.pending_refund_label = QLabel("Rs 0.00")
        
        summary_layout.addWidget(QLabel("Items:"), 0, 0)
        summary_layout.addWidget(self.pending_items_label, 0, 1)
        summary_layout.addWidget(QLabel("Quantity:"), 0, 2)
        summary_layout.addWidget(self.pending_qty_label, 0, 3)
        summary_layout.addWidget(QLabel("Total Refund:"), 1, 0)
        summary_layout.addWidget(self.pending_refund_label, 1, 1, 1, 3)
        
        self.process_return_btn = QPushButton("Process Return")
        self.process_return_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: none;
                font-size: 12px;
            }
        """)
        self.process_return_btn.setEnabled(False)
        self.process_return_btn.clicked.connect(self.process_return)
        
        summary_layout.addWidget(self.process_return_btn, 2, 0, 1, 4)
        pending_layout.addWidget(summary_frame)
        
        bottom_layout.addWidget(pending_group, 1)
        
        main_splitter.addWidget(bottom_panel)
        main_splitter.setSizes([300, 400])
        
        main_layout.addWidget(main_splitter, 1)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 3px;
                font-size: 11px;
            }
        """)
        main_layout.addWidget(self.status_bar)
        
        self.setMinimumSize(1200, 700)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
        """)
        
    def load_recent_sales(self):
        """Load recent sales with proper filtering"""
        if 'sales' not in self.db_connections:
            self.status_bar.showMessage("Database not connected")
            return
            
        try:
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            # Get filter from combobox
            filter_text = self.date_filter.currentText()
            date_filter = ""
            
            if "Last 7 Days" in filter_text:
                date_filter = "AND sale_date >= DATE('now', '-7 days')"
            elif "Last 30 Days" in filter_text:
                date_filter = "AND sale_date >= DATE('now', '-30 days')"
            elif "Today" in filter_text:
                date_filter = "AND sale_date = DATE('now')"
            elif "Yesterday" in filter_text:
                date_filter = "AND sale_date = DATE('now', '-1 day')"
            elif "This Month" in filter_text:
                date_filter = "AND strftime('%Y-%m', sale_date) = strftime('%Y-%m', 'now')"
            elif "All Time" in filter_text:
                date_filter = ""
            
            query = f"""
                SELECT 
                    id, bill_number, sale_date, customer, 
                    total_items, grand_total, payment_method, payment_status
                FROM sales 
                WHERE 1=1 {date_filter}
                ORDER BY sale_date DESC, id DESC
                LIMIT 100
            """
            
            cursor.execute(query)
            sales = cursor.fetchall()
            
            self.sales_table.setRowCount(len(sales))
            
            for row, sale in enumerate(sales):
                # Bill number
                bill_item = QTableWidgetItem(str(sale['bill_number']))
                bill_item.setData(Qt.ItemDataRole.UserRole, sale['id'])
                self.sales_table.setItem(row, 0, bill_item)
                
                # Date
                try:
                    date_obj = datetime.strptime(sale['sale_date'], "%Y-%m-%d")
                    display_date = date_obj.strftime("%d/%m/%y")
                except:
                    display_date = sale['sale_date'][:10] if sale['sale_date'] else ''
                self.sales_table.setItem(row, 1, QTableWidgetItem(display_date))
                
                # Customer
                customer_name = sale['customer'] or "Walk-in"
                if len(customer_name) > 20:
                    customer_name = customer_name[:17] + "..."
                self.sales_table.setItem(row, 2, QTableWidgetItem(customer_name))
                
                # Items count
                items_item = QTableWidgetItem(str(sale['total_items']))
                items_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.sales_table.setItem(row, 3, items_item)
                
                # Total
                total_item = QTableWidgetItem(f"Rs {sale['grand_total']:,.2f}")
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.sales_table.setItem(row, 4, total_item)
            
            self.status_bar.showMessage(f"Loaded {len(sales)} sales")
            
        except Exception as e:
            print(f"Error loading sales: {e}")
            self.status_bar.showMessage(f"Error: {str(e)}")
    
    def on_sale_selected(self):
        """Handle sale selection"""
        selected = self.sales_table.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        item = self.sales_table.item(row, 0)
        if not item:
            return
            
        self.selected_sale_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_sale_details(self.selected_sale_id)
        self.full_return_btn.setEnabled(True)
    
    def load_sale_details(self, sale_id):
        """Load detailed sale information"""
        if 'sales' not in self.db_connections:
            return
            
        try:
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            # Get sale header
            cursor.execute("SELECT * FROM sales WHERE id = ?", (sale_id,))
            sale = cursor.fetchone()
            
            if not sale:
                return
                
            self.sale_details = dict(sale)
            
            # Update bill info table
            self.update_bill_info_table(sale)
            
            # Get sale items with return information
            cursor.execute("""
                SELECT 
                    si.*,
                    COALESCE(SUM(ri.quantity), 0) as already_returned
                FROM sale_items si
                LEFT JOIN return_items ri ON ri.sale_id = si.sale_id AND ri.item_id = si.item_id
                WHERE si.sale_id = ?
                GROUP BY si.id
            """, (sale_id,))
            
            items = cursor.fetchall()
            
            self.sale_items_table.setRowCount(len(items))
            
            for row, item in enumerate(items):
                item_dict = dict(item)
                
                # Item ID
                id_item = QTableWidgetItem(item_dict['item_id'])
                self.sale_items_table.setItem(row, 0, id_item)
                
                # Description
                desc_text = item_dict['display_name']
                if len(desc_text) > 25:
                    desc_text = desc_text[:22] + "..."
                desc_item = QTableWidgetItem(desc_text)
                desc_item.setToolTip(item_dict['display_name'])
                self.sale_items_table.setItem(row, 1, desc_item)
                
                # Quantity
                qty_item = QTableWidgetItem(str(item_dict['quantity']))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.sale_items_table.setItem(row, 2, qty_item)
                
                # Price
                price_item = QTableWidgetItem(f"{item_dict['unit_price']:,}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.sale_items_table.setItem(row, 3, price_item)
                
                # Sold Qty
                sold_item = QTableWidgetItem(str(item_dict['quantity']))
                sold_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.sale_items_table.setItem(row, 4, sold_item)
                
                # Already Returned
                returned = item_dict.get('already_returned', 0)
                returned_item = QTableWidgetItem(str(returned))
                returned_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if returned > 0:
                    returned_item.setForeground(QColor('#dc3545'))
                self.sale_items_table.setItem(row, 5, returned_item)
                
                # Return button - FIXED: Capture item_dict in lambda properly
                if item_dict['quantity'] - returned > 0:
                    return_btn = QPushButton("Return")
                    return_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #17a2b8;
                            color: white;
                            border: none;
                            padding: 3px 6px;
                            border-radius: 2px;
                            font-size: 10px;
                        }
                    """)
                    # FIX: Create a copy of item_dict for each button
                    item_data = dict(item_dict)  # Create a copy
                    return_btn.clicked.connect(lambda checked, data=item_data: self.initiate_item_return(data))
                    self.sale_items_table.setCellWidget(row, 6, return_btn)
                else:
                    disabled_btn = QPushButton("Fully Returned")
                    disabled_btn.setEnabled(False)
                    disabled_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #6c757d;
                            color: white;
                            border: none;
                            padding: 3px 6px;
                            border-radius: 2px;
                            font-size: 10px;
                        }
                    """)
                    self.sale_items_table.setCellWidget(row, 6, disabled_btn)
            
            self.status_bar.showMessage(f"Loaded items for Bill #{sale['bill_number']}")
            
        except Exception as e:
            print(f"Error loading sale details: {e}")
            self.status_bar.showMessage(f"Error: {str(e)}")
    
    def update_bill_info_table(self, sale):
        """Update bill information table"""
        # Set values
        self.bill_info_table.setItem(0, 1, QTableWidgetItem(str(sale['bill_number'])))
        self.bill_info_table.setItem(1, 1, QTableWidgetItem(sale['sale_date']))
        self.bill_info_table.setItem(2, 1, QTableWidgetItem(sale['customer'] or "Walk-in"))
        self.bill_info_table.setItem(3, 1, QTableWidgetItem(sale['payment_method']))
        self.bill_info_table.setItem(4, 1, QTableWidgetItem(str(sale['total_items'])))
        self.bill_info_table.setItem(5, 1, QTableWidgetItem(f"Rs {sale['grand_total']:,.2f}"))
    
    def initiate_item_return(self, item_data):
        """Initiate return for a specific item"""
        if not self.selected_sale_id:
            return
            
        dialog = EnhancedReturnDialog(self.sale_details, item_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return_data = dialog.get_return_data()
            self.add_return_item(return_data)
    
    def add_return_item(self, return_data):
        """Add item to pending returns"""
        # Check for duplicates
        for i, item in enumerate(self.return_items):
            if item['item_id'] == return_data['item_id']:
                reply = QMessageBox.question(
                    self,
                    "Item Already in Return",
                    f"This item is already in the return list with {item['quantity']} quantity.\nReplace it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.return_items[i] = return_data
                    self.update_pending_returns()
                return
        
        self.return_items.append(return_data)
        self.update_pending_returns()
        self.clear_returns_btn.setEnabled(True)
        self.process_return_btn.setEnabled(True)
    
    def update_pending_returns(self):
        """Update pending returns table"""
        self.pending_returns_table.setRowCount(len(self.return_items))
        
        total_items = len(self.return_items)
        total_qty = 0
        total_refund = 0
        
        for row, item in enumerate(self.return_items):
            # Item ID
            self.pending_returns_table.setItem(row, 0, QTableWidgetItem(item['item_id']))
            
            # Description
            desc = QTableWidgetItem(item['item_name'])
            if len(item['item_name']) > 25:
                desc.setText(item['item_name'][:22] + "...")
            desc.setToolTip(item['item_name'])
            self.pending_returns_table.setItem(row, 1, desc)
            
            # Quantity
            qty_item = QTableWidgetItem(str(item['quantity']))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pending_returns_table.setItem(row, 2, qty_item)
            total_qty += item['quantity']
            
            # Refund
            refund_item = QTableWidgetItem(f"Rs {item['total_refund']:,.2f}")
            refund_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.pending_returns_table.setItem(row, 3, refund_item)
            total_refund += item['total_refund']
            
            # Reason
            reason_text = item['reason']
            if len(reason_text) > 12:
                reason_text = reason_text[:9] + "..."
            reason_item = QTableWidgetItem(reason_text)
            reason_item.setToolTip(item['reason'])
            self.pending_returns_table.setItem(row, 4, reason_item)
            
            # Method
            method_item = QTableWidgetItem(item['refund_method'])
            self.pending_returns_table.setItem(row, 5, method_item)
            
            # Status
            status_item = QTableWidgetItem("Pending")
            status_item.setForeground(QColor('#ffc107'))
            self.pending_returns_table.setItem(row, 6, status_item)
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 2px 6px;
                    border-radius: 2px;
                    font-size: 10px;
                }
            """)
            remove_btn.clicked.connect(lambda checked, r=row: self.remove_return_item(r))
            self.pending_returns_table.setCellWidget(row, 7, remove_btn)
        
        # Update summary
        self.pending_items_label.setText(str(total_items))
        self.pending_qty_label.setText(str(total_qty))
        self.pending_refund_label.setText(f"Rs {total_refund:,.2f}")
    
    def remove_return_item(self, row):
        """Remove item from pending returns"""
        if 0 <= row < len(self.return_items):
            del self.return_items[row]
            self.update_pending_returns()
            
            if len(self.return_items) == 0:
                self.clear_returns_btn.setEnabled(False)
                self.process_return_btn.setEnabled(False)
    
    def return_full_invoice(self):
        """Return full invoice with all items"""
        if not self.selected_sale_id:
            return
            
        try:
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            # Get all items that can be returned
            cursor.execute("""
                SELECT 
                    si.*,
                    COALESCE(SUM(ri.quantity), 0) as already_returned
                FROM sale_items si
                LEFT JOIN return_items ri ON ri.sale_id = si.sale_id AND ri.item_id = si.item_id
                WHERE si.sale_id = ?
                GROUP BY si.id
                HAVING si.quantity - COALESCE(SUM(ri.quantity), 0) > 0
            """, (self.selected_sale_id,))
            
            items = cursor.fetchall()
            
            if not items:
                QMessageBox.information(self, "No Items", "All items have already been returned.")
                return
            
            # Create simple batch return dialog
            reply = QMessageBox.question(
                self,
                "Return Full Invoice",
                f"Add all {len(items)} available items to returns?\n\n"
                "Note: You can adjust quantities later in the pending returns list.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                for item in items:
                    item_dict = dict(item)
                    available_qty = item_dict['quantity'] - item_dict.get('already_returned', 0)
                    
                    return_data = {
                        'sale_id': self.selected_sale_id,
                        'bill_number': self.sale_details.get('bill_number', ''),
                        'item_id': item_dict['item_id'],
                        'item_name': item_dict['display_name'],
                        'quantity': available_qty,
                        'unit_price': item_dict['unit_price'],
                        'unit_cost': item_dict.get('unit_cost', 0),
                        'total_refund': item_dict['unit_price'] * available_qty,
                        'refund_per_unit': item_dict['unit_price'],
                        'reason': 'Full Invoice Return',
                        'condition': 'Unopened/New',
                        'refund_method': 'Cash',
                        'restocking_fee': 0.0,
                        'restocking_amount': 0.0
                    }
                    
                    # Check if already in return list
                    existing = False
                    for i, ret_item in enumerate(self.return_items):
                        if ret_item['item_id'] == return_data['item_id']:
                            self.return_items[i] = return_data
                            existing = True
                            break
                    
                    if not existing:
                        self.return_items.append(return_data)
                
                self.update_pending_returns()
                self.clear_returns_btn.setEnabled(True)
                self.process_return_btn.setEnabled(True)
                self.status_bar.showMessage(f"Added {len(items)} items to pending returns")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process full return: {str(e)}")
    
    def process_return(self):
        """Process all pending returns"""
        if not self.return_items:
            return
            
        # Confirmation dialog
        total_refund = sum(item['total_refund'] for item in self.return_items)
        reply = QMessageBox.question(
            self,
            "Confirm Return",
            f"Process {len(self.return_items)} return items?\n\n"
            f"Total Refund: Rs {total_refund:,.2f}\n"
            f"Total Items: {sum(item['quantity'] for item in self.return_items)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        try:
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            # Generate return number
            return_number = self.generate_return_number()
            
            # Calculate totals
            total_items = len(self.return_items)
            total_qty = sum(item['quantity'] for item in self.return_items)
            total_restocking = sum(item.get('restocking_amount', 0) for item in self.return_items)
            refund_method = self.return_items[0]['refund_method'] if self.return_items else 'Cash'
            
            # Insert return header
            cursor.execute("""
                INSERT INTO returns (
                    return_number, sale_id, bill_number, customer,
                    return_date, return_time, total_items, total_quantity,
                    total_refund, total_restocking_fee, refund_method,
                    processed_by, status, notes
                ) VALUES (?, ?, ?, ?, DATE('now'), TIME('now'), ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                return_number, self.selected_sale_id,
                self.sale_details.get('bill_number', ''),
                self.sale_details.get('customer', 'Walk-in'),
                total_items, total_qty, total_refund, total_restocking,
                refund_method, "System", "Completed",
                f"Processed {total_items} items"
            ))
            
            return_id = cursor.lastrowid
            
            # Insert return items
            for item in self.return_items:
                cursor.execute("""
                    INSERT INTO return_items (
                        return_id, sale_id, item_id, item_name, quantity,
                        unit_price, unit_cost, refund_per_unit, total_refund,
                        restocking_fee, condition, reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    return_id, self.selected_sale_id,
                    item['item_id'], item['item_name'], item['quantity'],
                    item['unit_price'], item.get('unit_cost', 0),
                    item['refund_per_unit'], item['total_refund'],
                    item.get('restocking_fee', 0),
                    item['condition'], item['reason']
                ))
                
                # Restock inventory
                self.restock_inventory(item['item_id'], item['quantity'])
            
            conn.commit()
            
            # Success message
            QMessageBox.information(
                self,
                "Return Processed",
                f"✅ Return #{return_number} completed successfully!\n\n"
                f"• Items: {total_items}\n"
                f"• Quantity: {total_qty}\n"
                f"• Total Refund: Rs {total_refund:,.2f}\n"
                f"• Refund Method: {refund_method}"
            )
            
            # Clear pending returns
            self.return_items.clear()
            self.update_pending_returns()
            self.clear_returns_btn.setEnabled(False)
            self.process_return_btn.setEnabled(False)
            
            # Refresh sale details to show updated return status
            self.load_sale_details(self.selected_sale_id)
            
            self.status_bar.showMessage(f"Return #{return_number} processed successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process return: {str(e)}")
            print(f"Error processing return: {e}")
    
    def generate_return_number(self):
        """Generate unique return number"""
        try:
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y%m%d')
            cursor.execute("""
                SELECT COUNT(*) as count FROM returns 
                WHERE return_number LIKE ?
            """, (f'RTN-{today}-%',))
            
            result = cursor.fetchone()
            count = result['count'] + 1 if result else 1
            
            return f"RTN-{today}-{count:03d}"
            
        except:
            return f"RTN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    def restock_inventory(self, item_id, quantity):
        """Restock inventory after return"""
        try:
            inventory_db = 'database.db'
            if os.path.exists(inventory_db):
                conn = sqlite3.connect(inventory_db)
                cursor = conn.cursor()
                
                # Update inventory
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = quantity + ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                """, (quantity, item_id))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            print(f"Note: Inventory update failed - {e}")
    
    def switch_mode(self, mode):
        """Switch between return and exchange modes"""
        self.current_mode = mode
        
        if mode == 'return':
            self.return_mode_btn.setChecked(True)
            self.exchange_mode_btn.setChecked(False)
        else:
            self.return_mode_btn.setChecked(False)
            self.exchange_mode_btn.setChecked(True)
    
    def perform_search(self):
        """Perform search across sales"""
        search_text = self.search_input.text().strip()
        if not search_text:
            self.load_recent_sales()
            return
            
        try:
            conn = self.db_connections['sales']
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id, bill_number, sale_date, customer, 
                    total_items, grand_total, payment_method
                FROM sales 
                WHERE bill_number LIKE ? 
                   OR customer LIKE ?
                   OR id IN (
                       SELECT DISTINCT sale_id 
                       FROM sale_items 
                       WHERE item_id LIKE ? OR display_name LIKE ?
                   )
                ORDER BY sale_date DESC
                LIMIT 50
            """
            
            search_pattern = f"%{search_text}%"
            cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            sales = cursor.fetchall()
            
            self.sales_table.setRowCount(len(sales))
            
            for row, sale in enumerate(sales):
                # Bill number
                bill_item = QTableWidgetItem(str(sale['bill_number']))
                bill_item.setData(Qt.ItemDataRole.UserRole, sale['id'])
                self.sales_table.setItem(row, 0, bill_item)
                
                # Date
                try:
                    date_obj = datetime.strptime(sale['sale_date'], "%Y-%m-%d")
                    display_date = date_obj.strftime("%d/%m/%y")
                except:
                    display_date = sale['sale_date'][:10] if sale['sale_date'] else ''
                self.sales_table.setItem(row, 1, QTableWidgetItem(display_date))
                
                # Customer
                customer_name = sale['customer'] or "Walk-in"
                if len(customer_name) > 20:
                    customer_name = customer_name[:17] + "..."
                self.sales_table.setItem(row, 2, QTableWidgetItem(customer_name))
                
                # Items count
                items_item = QTableWidgetItem(str(sale['total_items']))
                items_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.sales_table.setItem(row, 3, items_item)
                
                # Total
                total_item = QTableWidgetItem(f"Rs {sale['grand_total']:,.2f}")
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.sales_table.setItem(row, 4, total_item)
            
            self.status_bar.showMessage(f"Found {len(sales)} results for '{search_text}'")
            
        except Exception as e:
            print(f"Error searching: {e}")
            self.status_bar.showMessage(f"Search error: {str(e)}")
    
    def clear_all_returns(self):
        """Clear all pending returns"""
        if not self.return_items:
            return
            
        reply = QMessageBox.question(
            self,
            "Clear All Returns",
            "Are you sure you want to clear all pending returns?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.return_items.clear()
            self.update_pending_returns()
            self.clear_returns_btn.setEnabled(False)
            self.process_return_btn.setEnabled(False)
            self.status_bar.showMessage("Cleared all pending returns")
    
    def setup_database(self):
        """Setup database connections and tables"""
        try:
            # Connect to sales database
            sales_db = 'sales.db'
            if os.path.exists(sales_db):
                conn = sqlite3.connect(sales_db)
                conn.row_factory = sqlite3.Row
                self.db_connections['sales'] = conn
                
                # Create returns table if not exists
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS returns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        return_number TEXT UNIQUE,
                        sale_id INTEGER,
                        bill_number TEXT,
                        customer TEXT,
                        return_date DATE,
                        return_time TIME,
                        total_items INTEGER,
                        total_quantity INTEGER,
                        total_refund REAL,
                        total_restocking_fee REAL,
                        refund_method TEXT,
                        processed_by TEXT,
                        status TEXT DEFAULT 'Completed',
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS return_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        return_id INTEGER,
                        sale_id INTEGER,
                        item_id TEXT,
                        item_name TEXT,
                        quantity INTEGER,
                        unit_price REAL,
                        unit_cost REAL,
                        refund_per_unit REAL,
                        total_refund REAL,
                        restocking_fee REAL,
                        condition TEXT,
                        reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (return_id) REFERENCES returns(id)
                    )
                """)
                
                conn.commit()
                print("Database setup completed successfully")
                
        except Exception as e:
            print(f"Error setting up database: {e}")
            QMessageBox.warning(self, "Database Error", f"Failed to setup database: {str(e)}")
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        QShortcut(QKeySequence("F5"), self).activated.connect(self.load_recent_sales)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(lambda: self.search_input.setFocus())
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.process_return)
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.clear_all_returns)
    
    def closeEvent(self, event):
        """Close database connections when window closes"""
        for name, conn in self.db_connections.items():
            if conn:
                try:
                    conn.close()
                    print(f"Closed database connection: {name}")
                except:
                    pass
        event.accept()


# Main application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = ProfessionalSalesReturnWindow()
    window.setWindowTitle("Professional Sales Return System")
    window.resize(1200, 700)
    window.show()
    
    sys.exit(app.exec())