import sys
import sqlite3
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLineEdit, QLabel, QMessageBox, QGroupBox, QFormLayout, 
                             QComboBox, QSpinBox, QDoubleSpinBox, QHeaderView,
                             QDialog, QDialogButtonBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QFont, QColor, QDoubleValidator

class BearingsDatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('bearings_inventory.db')
        self.create_tables()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        # Create bearings table with new structure
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bearings (
                bearing_id TEXT PRIMARY KEY NOT NULL,
                inner_diameter REAL NOT NULL,
                outer_diameter REAL NOT NULL,
                width REAL NOT NULL,
                type TEXT NOT NULL,
                brand TEXT,
                quantity INTEGER DEFAULT 0,
                cost REAL DEFAULT 0,
                price REAL DEFAULT 0,
                min_stock INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()
        
    def get_bearings(self, search_text="", filters=None):
        cursor = self.conn.cursor()
        query = "SELECT * FROM bearings WHERE 1=1"
        params = []
        
        # Search functionality
        if search_text:
            query += " AND (bearing_id LIKE ? OR type LIKE ? OR brand LIKE ?)"
            search_term = f"%{search_text}%"
            params.extend([search_term, search_term, search_term])
        
        # Filter functionality - exact matching
        if filters:
            if 'inner_diameter' in filters and filters['inner_diameter']:
                query += " AND inner_diameter = ?"
                params.append(float(filters['inner_diameter']))
            if 'outer_diameter' in filters and filters['outer_diameter']:
                query += " AND outer_diameter = ?"
                params.append(float(filters['outer_diameter']))
            if 'width' in filters and filters['width']:
                query += " AND width = ?"
                params.append(float(filters['width']))
            if 'type' in filters and filters['type']:
                query += " AND type = ?"
                params.append(filters['type'])
                
        query += " ORDER BY bearing_id"
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def get_bearing_by_id(self, bearing_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bearings WHERE bearing_id=?", (bearing_id,))
        return cursor.fetchone()
    
    def add_bearing(self, bearing_id, inner_d, outer_d, width, bearing_type, brand, quantity, cost, price, min_stock):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO bearings (bearing_id, inner_diameter, outer_diameter, width, 
                type, brand, quantity, cost, price, min_stock) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (bearing_id, inner_d, outer_d, width, bearing_type, brand, quantity, cost, price, min_stock)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_bearing(self, old_bearing_id, bearing_id, inner_d, outer_d, width, bearing_type, brand, quantity, cost, price, min_stock):
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE bearings SET bearing_id=?, inner_diameter=?, outer_diameter=?, width=?, 
            type=?, brand=?, quantity=?, cost=?, price=?, min_stock=? 
            WHERE bearing_id=?""",
            (bearing_id, inner_d, outer_d, width, bearing_type, brand, quantity, cost, price, min_stock, old_bearing_id)
        )
        self.conn.commit()
    
    def delete_bearing(self, bearing_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM bearings WHERE bearing_id=?", (bearing_id,))
        self.conn.commit()
    
    def get_bearing_types(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT type FROM bearings ORDER BY type")
        return [row[0] for row in cursor.fetchall()]

class BearingDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Add Bearing" if data is None else "Edit Bearing")
        self.setModal(True)
        self.setGeometry(100, 100, 450, 550)
        
        layout = QFormLayout(self)
        
        # Bearing ID (user-defined)
        self.bearing_id = QLineEdit()
        layout.addRow("Bearing ID*:", self.bearing_id)
        
        # Dimensions - FIXED: Use QLineEdit with validator for completely empty fields
        self.inner_d = QLineEdit()
        self.inner_d.setPlaceholderText("mm")
        self.inner_d.setValidator(QDoubleValidator(0, 1000, 2))
        layout.addRow("Inner Diameter*:", self.inner_d)
        
        self.outer_d = QLineEdit()
        self.outer_d.setPlaceholderText("mm")
        self.outer_d.setValidator(QDoubleValidator(0, 1000, 2))
        layout.addRow("Outer Diameter*:", self.outer_d)
        
        self.width = QLineEdit()
        self.width.setPlaceholderText("mm")
        self.width.setValidator(QDoubleValidator(0, 1000, 2))
        layout.addRow("Width*:", self.width)
        
        # Type and Brand
        self.type = QComboBox()
        self.type.setEditable(True)
        self.type.addItems(["Ball", "Roller", "Tapered", "Needle", "Thrust", "Other"])
        layout.addRow("Type*:", self.type)
        
        self.brand = QLineEdit()
        layout.addRow("Brand:", self.brand)
        
        # Stock and pricing
        self.quantity = QSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setValue(0)
        self.quantity.setSpecialValueText("")  # Show empty when value is 0
        layout.addRow("Quantity:", self.quantity)
        
        self.cost = QLineEdit()
        self.cost.setPlaceholderText("Rs")
        self.cost.setValidator(QDoubleValidator(0, 10000, 2))
        layout.addRow("Cost:", self.cost)
        
        self.price = QLineEdit()
        self.price.setPlaceholderText("Rs")
        self.price.setValidator(QDoubleValidator(0, 10000, 2))
        layout.addRow("Price:", self.price)
        
        self.min_stock = QSpinBox()
        self.min_stock.setRange(0, 10000)
        self.min_stock.setValue(0)
        self.min_stock.setSpecialValueText("")  # Show empty when value is 0
        layout.addRow("Min Stock:", self.min_stock)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        # Populate if editing
        if data:
            self.bearing_id.setText(data[0])
            self.inner_d.setText(str(data[1]) if data[1] else "")
            self.outer_d.setText(str(data[2]) if data[2] else "")
            self.width.setText(str(data[3]) if data[3] else "")
            self.type.setCurrentText(data[4])
            self.brand.setText(data[5])
            self.quantity.setValue(int(data[6]) if data[6] else 0)
            self.cost.setText(str(data[7]) if data[7] else "")
            self.price.setText(str(data[8]) if data[8] else "")
            self.min_stock.setValue(int(data[9]) if data[9] else 0)
            
    def validate_and_accept(self):
        """Validate data before accepting"""
        if not self.bearing_id.text().strip():
            QMessageBox.warning(self, "Validation Error", "Bearing ID is required!")
            return
            
        # Check if dimensions are provided and valid
        try:
            inner_val = float(self.inner_d.text()) if self.inner_d.text() else 0
            outer_val = float(self.outer_d.text()) if self.outer_d.text() else 0
            width_val = float(self.width.text()) if self.width.text() else 0
            
            if inner_val <= 0 or outer_val <= 0 or width_val <= 0:
                QMessageBox.warning(self, "Validation Error", "All dimensions must be greater than 0!")
                return
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter valid numeric values for dimensions!")
            return
            
        if not self.type.currentText().strip():
            QMessageBox.warning(self, "Validation Error", "Type is required!")
            return
            
        self.accept()
            
    def get_data(self):
        # Convert empty strings to 0 for numeric fields
        inner_val = float(self.inner_d.text()) if self.inner_d.text() else 0
        outer_val = float(self.outer_d.text()) if self.outer_d.text() else 0
        width_val = float(self.width.text()) if self.width.text() else 0
        cost_val = float(self.cost.text()) if self.cost.text() else 0
        price_val = float(self.price.text()) if self.price.text() else 0
        
        return (
            self.bearing_id.text().strip(),
            inner_val,
            outer_val,
            width_val,
            self.type.currentText(),
            self.brand.text(),
            self.quantity.value(),
            cost_val,
            price_val,
            self.min_stock.value()
        )

class BearingsApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = BearingsDatabaseManager()
        self.init_ui()
        self.setup_shortcuts()
        self.load_bearings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Apply similar styling to inventory_manager
        self.apply_styles()

        # Search section
        search_group = QGroupBox("Search & Filters")
        search_layout = QGridLayout(search_group)
        
        # Search bar
        search_layout.addWidget(QLabel("Search:"), 0, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID, type, brand...")
        self.search_input.textChanged.connect(self.load_bearings)
        search_layout.addWidget(self.search_input, 0, 1, 1, 3)
        
        # Filter labels and inputs - FIXED: Use QLineEdit for completely empty fields
        search_layout.addWidget(QLabel("Inner Diameter:"), 1, 0)
        self.filter_inner = QLineEdit()
        self.filter_inner.setPlaceholderText("mm")
        self.filter_inner.setValidator(QDoubleValidator(0, 1000, 2))
        self.filter_inner.textChanged.connect(self.load_bearings)
        search_layout.addWidget(self.filter_inner, 1, 1)
        
        search_layout.addWidget(QLabel("Outer Diameter:"), 1, 2)
        self.filter_outer = QLineEdit()
        self.filter_outer.setPlaceholderText("mm")
        self.filter_outer.setValidator(QDoubleValidator(0, 1000, 2))
        self.filter_outer.textChanged.connect(self.load_bearings)
        search_layout.addWidget(self.filter_outer, 1, 3)
        
        search_layout.addWidget(QLabel("Width:"), 2, 0)
        self.filter_width = QLineEdit()
        self.filter_width.setPlaceholderText("mm")
        self.filter_width.setValidator(QDoubleValidator(0, 1000, 2))
        self.filter_width.textChanged.connect(self.load_bearings)
        search_layout.addWidget(self.filter_width, 2, 1)
        
        search_layout.addWidget(QLabel("Type:"), 2, 2)
        self.filter_type = QComboBox()
        self.filter_type.addItem("All Types", "")
        self.filter_type.currentIndexChanged.connect(self.load_bearings)
        search_layout.addWidget(self.filter_type, 2, 3)
        
        # Clear filters button
        self.clear_filters_btn = QPushButton("Clear Filters (Ctrl+C)")
        self.clear_filters_btn.clicked.connect(self.clear_filters)
        search_layout.addWidget(self.clear_filters_btn, 3, 0, 1, 4)
        
        layout.addWidget(search_group)
        
        # Table
        self.bearings_table = QTableWidget()
        self.bearings_table.setColumnCount(10)
        self.bearings_table.setHorizontalHeaderLabels([
            "Bearing ID", "Inner Diameter", "Outer Diameter", "Width", 
            "Type", "Brand", "Quantity", "Cost", "Price", "Min Stock"
        ])
        self.bearings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.bearings_table.setAlternatingRowColors(True)
        self.bearings_table.doubleClicked.connect(self.edit_bearing)
        self.set_table_column_widths()
        layout.addWidget(self.bearings_table)
        
        # Summary panel
        summary_group = QGroupBox("Bearings Summary")
        summary_layout = QGridLayout(summary_group)
        
        self.total_bearings_label = QLabel("Total Bearings: 0")
        self.total_value_label = QLabel("Total Value: Rs0.00")
        self.low_stock_label = QLabel("Low Stock Items: 0")
        self.out_of_stock_label = QLabel("Out of Stock Items: 0")
        
        summary_layout.addWidget(self.total_bearings_label, 0, 0)
        summary_layout.addWidget(self.total_value_label, 0, 1)
        summary_layout.addWidget(self.low_stock_label, 1, 0)
        summary_layout.addWidget(self.out_of_stock_label, 1, 1)
        
        layout.addWidget(summary_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Bearing (Ctrl+N)")
        self.add_btn.clicked.connect(self.add_bearing)
        button_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Edit Bearing (Ctrl+E)")
        self.edit_btn.clicked.connect(self.edit_bearing)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Bearing (Ctrl+D)")
        self.delete_btn.clicked.connect(self.delete_bearing)
        button_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("Refresh (F5)")
        self.refresh_btn.clicked.connect(self.load_bearings)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Load initial data
        self.update_type_filter()
        
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
                color: #333;
            }
            
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F1F3F8;
                gridline-color: #D0D7E5;
                border: 1px solid #D0D7E5;
                selection-background-color: #4A90E2;
            }
            
            QHeaderView::section {
                background-color: #4A90E2;
                color: #FFFFFF;
                padding: 4px;
                border: none;
                font-size: 9pt;
                font-weight: bold;
            }
            
            QPushButton {
                background-color: #4A90E2;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 9pt;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #357ABD;
            }
            
            QPushButton:pressed {
                background-color: #2C5F9E;
            }
            
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CED4DA;
                border-radius: 4px;
                padding: 4px;
            }
            
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CED4DA;
                border-radius: 4px;
                padding: 4px;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CED4DA;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #CED4DA;
                border-radius: 4px;
                padding: 4px;
            }
        """)

    def set_table_column_widths(self):
        """Set appropriate column widths"""
        self.bearings_table.setColumnWidth(0, 195)  # Bearing ID
        self.bearings_table.setColumnWidth(1, 110)  # Inner Diameter
        self.bearings_table.setColumnWidth(2, 110)  # Outer Diameter
        self.bearings_table.setColumnWidth(3, 100)   # Width
        self.bearings_table.setColumnWidth(4, 100)  # Type
        self.bearings_table.setColumnWidth(5, 120)  # Brand
        self.bearings_table.setColumnWidth(6, 80)   # Quantity
        self.bearings_table.setColumnWidth(7, 110)   # Cost
        self.bearings_table.setColumnWidth(8, 110)   # Price
        self.bearings_table.setColumnWidth(9, 80)   # Min Stock

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Add Bearing - Ctrl+N
        self.add_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.add_shortcut.activated.connect(self.add_bearing)
        
        # Edit Bearing - Ctrl+E
        self.edit_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.edit_shortcut.activated.connect(self.edit_bearing)
        
        # Delete Bearing - Ctrl+D
        self.delete_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.delete_shortcut.activated.connect(self.delete_bearing)
        
        # Refresh - F5
        self.refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.refresh_shortcut.activated.connect(self.load_bearings)
        
        # Clear Filters - Ctrl+C - FIXED: Connect to clear_filters directly
        self.clear_filters_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.clear_filters_shortcut.activated.connect(self.clear_filters)
        
        # Focus Search - Ctrl+F
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.focus_search_field)

    def focus_search_field(self):
        """Focus on search field when Ctrl+F is pressed"""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def load_bearings(self):
        """Load bearings with current filters and search"""
        search_text = self.search_input.text().strip()
        
        # Get filter values - empty strings if no input
        filters = {
            'inner_diameter': self.filter_inner.text().strip(),
            'outer_diameter': self.filter_outer.text().strip(),
            'width': self.filter_width.text().strip(),
            'type': self.filter_type.currentData() if self.filter_type.currentData() else ""
        }
        
        bearings = self.db.get_bearings(search_text, filters)
        self.bearings_table.setRowCount(len(bearings))
        
        total_value = 0
        low_stock_count = 0
        out_of_stock_count = 0
        
        for row, bearing in enumerate(bearings):
            quantity = bearing[6]
            min_stock = bearing[9]
            cost = bearing[7]
            
            # Update summary counts
            if quantity == 0:
                out_of_stock_count += 1
            elif quantity <= min_stock:
                low_stock_count += 1
                
            total_value += quantity * cost
            
            for col, value in enumerate(bearing):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Apply coloring based on stock status
                if quantity == 0:
                    item.setBackground(QColor('#ffcccc'))  # Red for out of stock
                elif quantity <= min_stock:
                    item.setBackground(QColor('#ffffcc'))  # Yellow for low stock
                
                # Right align numeric columns
                if col in [1, 2, 3, 6, 7, 8, 9]:  # Numeric columns
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                self.bearings_table.setItem(row, col, item)
        
        # Update summary
        self.total_bearings_label.setText(f"Total Bearings: {len(bearings)}")
        self.total_value_label.setText(f"Total Value: Rs{total_value:,.2f}")
        self.low_stock_label.setText(f"Low Stock Items: {low_stock_count}")
        self.out_of_stock_label.setText(f"Out of Stock Items: {out_of_stock_count}")
        
    def update_type_filter(self):
        """Update the type filter dropdown"""
        types = self.db.get_bearing_types()
        self.filter_type.clear()
        self.filter_type.addItem("All Types", "")
        for t in types:
            self.filter_type.addItem(t, t)
            
    def clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.filter_inner.clear()
        self.filter_outer.clear()
        self.filter_width.clear()
        self.filter_type.setCurrentIndex(0)
        self.load_bearings()
        
    def add_bearing(self):
        """Add new bearing"""
        dialog = BearingDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            success = self.db.add_bearing(*data)
            if success:
                self.load_bearings()
                self.update_type_filter()
                QMessageBox.information(self, "Success", "Bearing added successfully!")
            else:
                QMessageBox.warning(self, "Error", "A bearing with this ID already exists!")
                
    def edit_bearing(self):
        """Edit selected bearing"""
        selected = self.bearings_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Warning", "Please select a bearing to edit")
            return
            
        # Get the bearing ID from the first column
        bearing_id = self.bearings_table.item(selected, 0).text()
        
        # Get the complete bearing data from database
        bearing_data = self.db.get_bearing_by_id(bearing_id)
        
        if not bearing_data:
            QMessageBox.warning(self, "Error", "Bearing not found in database!")
            return
            
        # Convert the database row to a list for the dialog
        data_list = list(bearing_data)
        
        dialog = BearingDialog(self, data_list)
        if dialog.exec():
            new_data = dialog.get_data()
            self.db.update_bearing(bearing_id, *new_data)
            self.load_bearings()
            QMessageBox.information(self, "Success", "Bearing updated successfully!")
            
    def delete_bearing(self):
        """Delete selected bearing"""
        selected = self.bearings_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Warning", "Please select a bearing to delete")
            return
            
        bearing_id = self.bearings_table.item(selected, 0).text()
        
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete bearing '{bearing_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_bearing(bearing_id)
            self.load_bearings()
            self.update_type_filter()
            QMessageBox.information(self, "Success", "Bearing deleted successfully!")