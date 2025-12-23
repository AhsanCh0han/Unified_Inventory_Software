import os
import sys
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QStatusBar, QLabel,
    QDialogButtonBox, QMessageBox, QProgressDialog, QTextBrowser
)
from PyQt6.QtGui import (
    QFont, QAction, QKeySequence, QTextDocument, QImage,
    QTextCursor, QTextTableFormat, QTextCharFormat, QTextBlockFormat,
    QTextLength, QTextTable, QBrush, QColor, QTextImageFormat,
    QPixmap, QTextFrameFormat, QPageSize, QTextTableCellFormat, QPageLayout,
    QFontMetricsF
)
from PyQt6.QtCore import Qt, QSizeF, QFileInfo, QRectF
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import QMarginsF

# ======= CONFIGURATION =======
class InvoiceConfig:
    """Configuration class for invoice settings"""
    
    # Paper settings
    PAPER_SIZE = QPageSize.PageSizeId.A5
    ORIENTATION = 'portrait'
    
    # FIXED MARGINS - Increased to ensure proper text fitting
    MARGIN_TOP = 2        # Increased from 1.4
    MARGIN_BOTTOM = 2     # Increased from 1.4
    MARGIN_LEFT = 2       # Increased from 1.0
    MARGIN_RIGHT = 2      # Increased from 1.0
    
    # Logo settings
    LOGO_FILE = "TOOLTREKHARDWARE_TRANSPARENT_LOGO.png"
    LOGO_WIDTH = 160  # Slightly reduced
    LOGO_HEIGHT = 50  # Slightly reduced
    
    # Shop information
    SHOP_NAME = "TOOLTREK HARDWARE"
    SHOP_ADDRESS = "NEAR LARI ADDA, MANGA ROAD, RAIWIND"
    SHOP_PHONE = "0324-4651561"
    SHOP_EMAIL = "TOOLTREKHARDWARE@GMAIL.COM"
    
    # FIXED FONT SIZES - Adjusted for better fitting
    LOGO_FONT_SIZE = 16
    SHOP_NAME_FONT_SIZE = 12  # Reduced from 14
    SHOP_ADDRESS_FONT_SIZE = 9  # Reduced from 10
    CONTACT_FONT_SIZE = 8  # Reduced from 9
    BILL_INFO_LABEL_FONT_SIZE = 8  # Reduced from 9
    BILL_INFO_VALUE_FONT_SIZE = 8  # Reduced from 9
    TABLE_HEADER_FONT_SIZE = 8  # Reduced from 9
    TABLE_DATA_FONT_SIZE = 7  # Reduced from 8
    TOTALS_LABEL_FONT_SIZE = 8  # Reduced from 9
    TOTALS_VALUE_FONT_SIZE = 9  # Reduced from 10
    GRAND_TOTAL_FONT_SIZE = 10  # Reduced from 11
    TERMS_TITLE_FONT_SIZE = 9  # Reduced from 10
    TERMS_TEXT_FONT_SIZE = 7  # Reduced from 8
    THANK_YOU_FONT_SIZE = 8  # Reduced from 9
    FOOTER_FONT_SIZE = 7  # Reduced from 8
    
    # FIXED COLUMN WIDTHS - Adjusted to prevent wrapping
    # A5 usable width after margins: ~390 points (420 - 15 - 15 = 390)
    # Adjusted percentages to ensure S.R# and TOTAL fit on one line
    COL_SNO_WIDTH = 12      # Increased from 8% (to fit "S.R#" better)
    COL_DESC_WIDTH = 52     # Reduced from 59% (to balance other columns)
    COL_QTY_WIDTH = 12      # Same
    COL_PRICE_WIDTH = 12    # Same
    COL_TOTAL_WIDTH = 12    # Same (but now more space)
    
    # Table styling
    TABLE_CELL_PADDING = 1  # Reduced from 2
    TABLE_BORDER_WIDTH = 0.4
    TABLE_HEADER_BORDER_WIDTH = 0.8
    TABLE_ROW_BORDER_WIDTH = 0.2
    BORDER_COLOR = QColor(0, 0, 0)
    
    # Colors
    FOOTER_COLOR = QColor(128, 128, 128)
    THANK_YOU_COLOR = QColor(128, 128, 128)
    
    # Terms and conditions
    TERMS_AND_CONDITIONS = [
        "NO RETURN, NO EXCHANGE WITHOUT BILL",
        "NO RETURN, NO EXCHANGE AFTER 3 DAYS",
        "ITEMS LIKE PIPES ARE NOT RETURNABLE OR EXCHANGEABLE",
        "DAMAGED AND USED ITEMS OR ITEMS WITH TORN AND RIPPED PACKING WILL NOT BE ACCEPTED FOR RETURN OR EXCHANGE"
    ]
    
    # Other settings
    CURRENCY_SYMBOL = "Rs"
    DATE_FORMAT = "%d/%m/%Y"
    MAX_CHARS_PER_LINE = 45  # Reduced from 60 to prevent overflow
    
    @classmethod
    def get_margins(cls):
        """Get margins as QMarginsF object"""
        return QMarginsF(cls.MARGIN_LEFT, cls.MARGIN_TOP, 
                        cls.MARGIN_RIGHT, cls.MARGIN_BOTTOM)
    
    @classmethod
    def get_page_size(cls):
        """Get page size based on orientation"""
        if cls.ORIENTATION == 'landscape':
            return QPageSize(QPageSize.PageSizeId.A5Landscape)
        else:
            return QPageSize(QPageSize.PageSizeId.A5)


class SimplePaginationCalculator:
    """Calculates page breaks with continuous table support"""
    
    def __init__(self, config):
        self.config = config
        self.page_size = config.get_page_size()
        self.margins = config.get_margins()
        
        # Get page dimensions in points
        page_size_points = self.page_size.size(QPageSize.Unit.Point)
        self.page_width_pts = page_size_points.width()
        self.page_height_pts = page_size_points.height()
        
        # Calculate usable area (subtract margins) - MORE SPACE NOW
        self.usable_width_pts = self.page_width_pts - self.margins.left() - self.margins.right()
        self.usable_height_pts = self.page_height_pts - self.margins.top() - self.margins.bottom()
        
        print(f"DEBUG: Page dimensions: {self.page_width_pts:.1f} x {self.page_height_pts:.1f} pts")
        print(f"DEBUG: Usable area: {self.usable_width_pts:.1f} x {self.usable_height_pts:.1f} pts")
        print(f"DEBUG: Margins: L={self.margins.left():.1f}, R={self.margins.right():.1f}, T={self.margins.top():.1f}, B={self.margins.bottom():.1f}")
    
    def measure_section_heights(self, builder, bill_data):
        """Measure actual heights of fixed sections"""
        measured_heights = {}
        
        # Create temporary document for measurement
        temp_doc = QTextDocument()
        
        # Set same page size and text width as real document
        page_size = self.page_size.size(QPageSize.Unit.Point)
        temp_doc.setPageSize(page_size)
        
        # Set text width to match usable width
        usable_width = self.page_width_pts - self.config.MARGIN_LEFT - self.config.MARGIN_RIGHT
        temp_doc.setTextWidth(usable_width)
        
        # 1. Measure logo + shop info
        temp_cursor = QTextCursor(temp_doc)
        builder.add_logo(cursor=temp_cursor)
        builder.add_shop_info(cursor=temp_cursor)
        measured_heights['logo_shop'] = temp_doc.documentLayout().documentSize().height()
        
        # Reset and measure bill info
        temp_doc.clear()
        temp_cursor = QTextCursor(temp_doc)
        builder.add_bill_info(bill_data, cursor=temp_cursor)
        measured_heights['bill_info'] = temp_doc.documentLayout().documentSize().height()
        
        # Reset and measure table header
        temp_doc.clear()
        temp_cursor = QTextCursor(temp_doc)
        # builder.add_table_header(cursor=temp_cursor)
        measured_heights['table_header'] = temp_doc.documentLayout().documentSize().height()
        
        # Reset and measure totals
        temp_doc.clear()
        temp_cursor = QTextCursor(temp_doc)
        builder.add_totals_section(bill_data, cursor=temp_cursor)
        measured_heights['totals'] = temp_doc.documentLayout().documentSize().height()
        
        # Reset and measure terms
        temp_doc.clear()
        temp_cursor = QTextCursor(temp_doc)
        builder.add_terms_and_conditions(cursor=temp_cursor)
        measured_heights['terms'] = temp_doc.documentLayout().documentSize().height()
        
        # Reset and measure one item row for reference
        temp_doc.clear()
        temp_cursor = QTextCursor(temp_doc)
        sample_item = {'description': 'Sample Item for Measurement', 'qty': 1, 'price': 100, 'total': 100}
        builder.add_item_row(sample_item, 1, cursor=temp_cursor)
        measured_heights['item_row'] = temp_doc.documentLayout().documentSize().height()
        
        return measured_heights
    
    def calculate_pages(self, items, measured_heights):
        """
        Simple pagination logic: 
        - First page: logo + shop info + bill info + table header + some items
        - Middle pages: items only (NO HEADER)
        - Last page: remaining items + totals + terms
        """
        if not items:
            return [{'page_type': 'first_last', 'items': []}]
        
        pages = []
        
        # Calculate available space for items on each page type
        first_page_space = self.usable_height_pts - (
            measured_heights['logo_shop'] +
            measured_heights['bill_info'] +
            measured_heights['table_header']
        )
        
        middle_page_space = self.usable_height_pts  # Full page for items
        
        last_page_space = self.usable_height_pts - (
            measured_heights['totals'] +
            measured_heights['terms']
        )
        
        print(f"DEBUG: First page space for items: {first_page_space:.1f} pts")
        print(f"DEBUG: Middle page space: {middle_page_space:.1f} pts")
        print(f"DEBUG: Last page space: {last_page_space:.1f} pts")
        
        # Simple algorithm: distribute items based on available space
        remaining_items = items.copy()
        page_number = 0
        
        while remaining_items:
            if page_number == 0:
                # First page
                available_space = first_page_space
                page_type = 'first'
            elif len(remaining_items) == 1:
                # Last item
                available_space = last_page_space
                page_type = 'last'
            else:
                # Check if remaining items can fit on last page
                remaining_height = sum(self.estimate_item_height(item) for item in remaining_items)
                
                if remaining_height <= last_page_space:
                    available_space = last_page_space
                    page_type = 'last'
                else:
                    available_space = middle_page_space
                    page_type = 'middle'
            
            # Add items to this page
            page_items = []
            current_height = 0
            
            while remaining_items and current_height + self.estimate_item_height(remaining_items[0]) <= available_space:
                item = remaining_items.pop(0)
                page_items.append(item)
                current_height += self.estimate_item_height(item)
            
            # If this is the only page, mark it as first_last
            if page_number == 0 and not remaining_items:
                page_type = 'first_last'
            
            # If this is the last page with remaining items
            elif not remaining_items and page_type != 'first_last':
                page_type = 'last'
            
            pages.append({
                'page_type': page_type,
                'items': page_items
            })
            
            page_number += 1
        
        # Debug output
        for i, page in enumerate(pages):
            print(f"Page {i+1}: type={page['page_type']}, items={len(page['items'])}")
        
        return pages
    
    def estimate_item_height(self, item):
        """Estimate height of an item row"""
        description = item.get('description', item.get('name', ''))
        
        if not description:
            return 25  # Minimum row height
        
        # Estimate based on description length
        if len(description) > 100:
            return 45  # Multi-line item (3 lines)
        elif len(description) > 50:
            return 35  # Multi-line item (2 lines)
        else:
            return 25  # Single line item


# ======= PROFESSIONAL INVOICE BUILDER =======
class ProfessionalInvoiceBuilder:
    """Builds invoice with clean pagination and continuous tables"""
    
    def __init__(self, config=None):
        self.config = config or InvoiceConfig()
        self.doc = QTextDocument()
        self.cursor = QTextCursor(self.doc)
        self.calculator = SimplePaginationCalculator(self.config)
        self.current_serial = 0  # Track serial number across pages
        self.item_table = None  # For continuous table
        self.item_table_row = 0  # Current row in continuous table
        
        # Setup document
        self.setup_document()
    
    def setup_document(self):
        """Setup document with proper page size and margins"""
        page_size = self.config.get_page_size().size(QPageSize.Unit.Point)
        self.doc.setPageSize(page_size)
        
        # Root frame: Set margins
        frame_format = QTextFrameFormat()
        frame_format.setMargin(0)
        self.doc.rootFrame().setFrameFormat(frame_format)
        
        # Calculate usable width CORRECTLY
        usable_width = (
            page_size.width()
            - self.config.MARGIN_LEFT
            - self.config.MARGIN_RIGHT
        )
        
        print(f"DEBUG: Page width: {page_size.width()} points")
        print(f"DEBUG: Left margin: {self.config.MARGIN_LEFT}, Right margin: {self.config.MARGIN_RIGHT}")
        print(f"DEBUG: Calculated usable width: {usable_width} points")
        
        # Use 100% of usable width
        self.doc.setTextWidth(usable_width)
        
        # Verify text width was set
        print(f"DEBUG: Actual document text width: {self.doc.textWidth()} points")
    
    # Also update the add_horizontal_line method to use more width:
    def add_horizontal_line(self, cursor=None, thickness=1.0, margin_top=10, margin_bottom=10, line_width=None):
        """Add a horizontal line separator"""
        if cursor is None:
            cursor = self.cursor
        
        # Calculate optimal line width based on usable width
        if line_width is None:
            # Use approximately 90% of usable width
            line_width = int(self.doc.textWidth() * 0.9 / 4.5)
        
        # Create a block format for spacing
        block_format = QTextBlockFormat()
        block_format.setTopMargin(margin_top)
        block_format.setBottomMargin(margin_bottom)
        block_format.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cursor.insertBlock(block_format)
        
        # Insert a simple line of characters
        cursor.insertText("_" * line_width)
        
        # Move cursor to end
        cursor.movePosition(QTextCursor.MoveOperation.End)
    
    # ======= HELPER METHODS =======
    def _create_block_format(self, alignment, top_margin=0, bottom_margin=0, left_margin=0, right_margin=0):
        """Helper to create block format"""
        block_format = QTextBlockFormat()
        block_format.setAlignment(alignment)
        block_format.setTopMargin(top_margin)
        block_format.setBottomMargin(bottom_margin)
        if left_margin > 0:
            block_format.setLeftMargin(left_margin)
        if right_margin > 0:
            block_format.setRightMargin(right_margin)
        return block_format
    
    def _create_char_format(self, font_size, bold=False, italic=False, color=None):
        """Helper to create character format"""
        char_format = QTextCharFormat()
        font = QFont("Arial", font_size)
        if bold:
            font.setWeight(QFont.Weight.Bold)
        if italic:
            font.setItalic(True)
        char_format.setFont(font)
        if color:
            char_format.setForeground(QBrush(color))
        return char_format
    
    def format_currency(self, value, include_symbol=True):
        """Format currency value without decimals"""
        try:
            amount = float(value)
            if include_symbol:
                return f"{self.config.CURRENCY_SYMBOL} {amount:,.0f}"
            else:
                return f"{amount:,.0f}"
        except (ValueError, TypeError):
            if include_symbol:
                return f"{self.config.CURRENCY_SYMBOL} 0"
            else:
                return "0"

    
    # ======= SECTION BUILDERS =======
    def find_logo(self):
        """Find logo file in various locations"""
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), self.config.LOGO_FILE),
            os.path.join(os.getcwd(), self.config.LOGO_FILE),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.config.LOGO_FILE),
            self.config.LOGO_FILE
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def add_logo(self, cursor=None):
        """Add logo to the document"""
        if cursor is None:
            cursor = self.cursor
        
        logo_path = self.find_logo()
        
        if logo_path and os.path.exists(logo_path):
            try:
                image_format = QTextImageFormat()
                image_format.setWidth(self.config.LOGO_WIDTH)
                image_format.setHeight(self.config.LOGO_HEIGHT)
                image_format.setName(logo_path)
                
                block_format = self._create_block_format(
                    Qt.AlignmentFlag.AlignCenter,
                    top_margin=5,
                    bottom_margin=10
                )
                cursor.insertBlock(block_format)
                cursor.insertImage(image_format)
            except Exception as e:
                print(f"Warning: Could not load logo: {e}")
                self.add_text_logo(cursor)
        else:
            self.add_text_logo(cursor)
    
    def add_text_logo(self, cursor=None):
        """Add text-based logo as fallback"""
        if cursor is None:
            cursor = self.cursor
        
        block_format = self._create_block_format(
            Qt.AlignmentFlag.AlignCenter,
            top_margin=10,
            bottom_margin=5
        )
        cursor.insertBlock(block_format)
        
        logo_format = self._create_char_format(self.config.LOGO_FONT_SIZE, bold=True)
        cursor.insertText(f"{self.config.SHOP_NAME}\n", logo_format)
    
    def add_shop_info(self, cursor=None):
        """Add shop information section - FIXED to keep phone/email on one line"""
        if cursor is None:
            cursor = self.cursor
        
        # Shop address - Keep as is
        address_format = self._create_char_format(self.config.SHOP_ADDRESS_FONT_SIZE)
        
        block_format = self._create_block_format(
            Qt.AlignmentFlag.AlignCenter,
            top_margin=5,
            bottom_margin=5  # Reduced from 8
        )
        cursor.insertBlock(block_format)
        cursor.insertText(f"SHOP: {self.config.SHOP_ADDRESS}", address_format)
        
        # Contact information - FIXED: Use non-breaking spaces and smaller font
        contact_format = self._create_char_format(self.config.CONTACT_FONT_SIZE)
        
        block_format = self._create_block_format(
            Qt.AlignmentFlag.AlignCenter,
            top_margin=3,  # Reduced from 5
            bottom_margin=5  # Reduced from 15
        )
        cursor.insertBlock(block_format)
        
        # Use non-breaking spaces between phone and email
        contact_text = f"PHONE: {self.config.SHOP_PHONE} | EMAIL: {self.config.SHOP_EMAIL}"
        cursor.insertText(contact_text, contact_format)
        
        # Add separator line after shop info
        self.add_horizontal_line(cursor, thickness=0.8, margin_top=5, margin_bottom=5, line_width=60)
    
    def add_bill_info(self, bill_data, cursor=None):
        """Add bill information (NAME, BILL #, DATE)"""
        if cursor is None:
            cursor = self.cursor
        
        customer = bill_data.get('customer', 'WALK-IN CUSTOMER')
        bill_no = bill_data.get('bill_number', '00001')
        date_str = bill_data.get('date', datetime.now().strftime(self.config.DATE_FORMAT))
        
        # Create a table for bill info
        table_format = QTextTableFormat()
        table_format.setBorder(0)
        table_format.setCellSpacing(1)  # Reduced from 2
        table_format.setCellPadding(1)   # Reduced from 2
        
        # Optimized widths for more space
        table_format.setColumnWidthConstraints([
            QTextLength(QTextLength.Type.PercentageLength, 12),  # Reduced from 15
            QTextLength(QTextLength.Type.PercentageLength, 40),  # Increased from 35 (for customer name)
            QTextLength(QTextLength.Type.PercentageLength, 22),  # Reduced from 25
            QTextLength(QTextLength.Type.PercentageLength, 26),  # Increased from 25
        ])
        
        label_format = self._create_char_format(self.config.BILL_INFO_LABEL_FONT_SIZE, bold=True)
        value_format = self._create_char_format(self.config.BILL_INFO_VALUE_FONT_SIZE)
        
        table = cursor.insertTable(2, 4, table_format)
        
        # Row 1: NAME and BILL #
        cell = table.cellAt(0, 0).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignLeft))
        cell.insertText("NAME", label_format)
        
        cell = table.cellAt(0, 1).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignLeft))
        # Truncate very long customer names
        if len(customer) > 30:
            customer = customer[:27] + "..."
        cell.insertText(customer, value_format)
        
        cell = table.cellAt(0, 2).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText("BILL #", label_format)
        
        cell = table.cellAt(0, 3).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(bill_no, value_format)
        
        # Row 2: DATE
        cell = table.cellAt(1, 2).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText("DATE:", label_format)
        
        cell = table.cellAt(1, 3).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(date_str, value_format)
        
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add separator line between bill info and invoice table
        self.add_horizontal_line(cursor, thickness=0.6, margin_top=8, margin_bottom=8, line_width=75)  # Reduced margins
    
    def start_items_table(self, cursor=None):
        """Start a continuous table for items - FIXED to prevent header wrapping"""
        if cursor is None:
            cursor = self.cursor
        
        # Create table format
        table_format = QTextTableFormat()
        table_format.setHeaderRowCount(1)
        table_format.setCellPadding(self.config.TABLE_CELL_PADDING)
        table_format.setCellSpacing(0)
        table_format.setBorder(self.config.TABLE_BORDER_WIDTH)
        table_format.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_Solid)
        table_format.setBorderBrush(QBrush(self.config.BORDER_COLOR))
        
        # FIXED: Calculate correct usable width with some buffer for alignment
        # Reduce width slightly to account for cell padding and borders
        usable_width = self.doc.textWidth() * 0.98  # Use 98% of usable width
        
        # Calculate absolute widths based on actual usable width
        col1_width = usable_width * (self.config.COL_SNO_WIDTH / 100)  # S.R#
        col2_width = usable_width * (self.config.COL_DESC_WIDTH / 100)  # DESCRIPTION
        col3_width = usable_width * (self.config.COL_QTY_WIDTH / 100)  # QTY
        col4_width = usable_width * (self.config.COL_PRICE_WIDTH / 100)  # PRICE
        col5_width = usable_width * (self.config.COL_TOTAL_WIDTH / 100)  # TOTAL
        
        # Debug: Print actual widths
        print(f"DEBUG: Table widths - Total usable: {usable_width:.1f}")
        print(f"DEBUG: Column widths: S.R#={col1_width:.1f}, DESC={col2_width:.1f}, QTY={col3_width:.1f}, PRICE={col4_width:.1f}, TOTAL={col5_width:.1f}")
        
        # Set column widths as fixed widths
        table_format.setColumnWidthConstraints([
            QTextLength(QTextLength.Type.FixedLength, col1_width),
            QTextLength(QTextLength.Type.FixedLength, col2_width),
            QTextLength(QTextLength.Type.FixedLength, col3_width),
            QTextLength(QTextLength.Type.FixedLength, col4_width),
            QTextLength(QTextLength.Type.FixedLength, col5_width),
        ])
        
        # Set table alignment to left (this is key!)
        table_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Create table with 1 row for now (header)
        self.item_table = cursor.insertTable(1, 5, table_format)
        self.item_table_row = 0
        
        # Add table header with NO WRAPPING
        header_format = self._create_char_format(self.config.TABLE_HEADER_FONT_SIZE, bold=True)
        # Use non-breaking spaces in headers
        headers = ["S.R#", "DESCRIPTION", "QTY", "PRICE", "TOTAL"]
        
        for col in range(5):
            cell = self.item_table.cellAt(0, col).firstCursorPosition()
            
            if col == 0:  # S.R#
                # Use non-breaking space after S.R to prevent wrapping
                cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignCenter))
                cell_format = QTextCharFormat(header_format)
                cell_format.setFontKerning(False)  # Disable kerning to prevent wrapping
                cell.insertText(headers[col], cell_format)
            elif col == 1:  # DESCRIPTION
                cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignLeft))
                cell.insertText(headers[col], header_format)
            else:  # QTY, PRICE, TOTAL
                cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
                if col == 4:  # TOTAL - ensure it doesn't wrap
                    cell_format = QTextCharFormat(header_format)
                    cell_format.setFontKerning(False)
                    cell.insertText(headers[col], cell_format)
                else:
                    cell.insertText(headers[col], header_format)
            
            # Add thicker bottom border to header
            cell_format_table = QTextTableCellFormat()
            cell_format_table.setBottomBorder(self.config.TABLE_HEADER_BORDER_WIDTH)
            cell_format_table.setBottomBorderBrush(QBrush(self.config.BORDER_COLOR))
            self.item_table.cellAt(0, col).setFormat(cell_format_table)
        
        cursor.movePosition(QTextCursor.MoveOperation.End)
    
    def add_item_row_to_table(self, item, serial_number):
        """Add a single item row to the continuous table"""
        if self.item_table is None:
            return
        
        # Append a new row to the table
        self.item_table.appendRows(1)
        self.item_table_row += 1
        current_row = self.item_table_row  # 0-based, but header is row 0
        
        # Data format
        data_format = self._create_char_format(self.config.TABLE_DATA_FONT_SIZE)
        
        # S.R#
        cell = self.item_table.cellAt(current_row, 0).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignCenter))
        cell.insertText(str(serial_number), data_format)
        
        # DESCRIPTION
        description = item.get('description', item.get('name', ''))
        cell = self.item_table.cellAt(current_row, 1).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignLeft))

        # SMART width-based word wrapping
        font = QFont("Arial", self.config.TABLE_DATA_FONT_SIZE)
        metrics = QFontMetricsF(font)

        # Actual description column width (same logic as header)
        desc_col_width = self.doc.textWidth() * (self.config.COL_DESC_WIDTH / 100)

        words = description.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if metrics.horizontalAdvance(test_line) <= desc_col_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines):
            if i > 0:
                cell.insertText("\n")
            cell.insertText(line, data_format)

        
        # QTY
        quantity = item.get('qty', 1)
        cell = self.item_table.cellAt(current_row, 2).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(str(quantity), data_format)
        
        # PRICE
        price = item.get('price', 0)
        cell = self.item_table.cellAt(current_row, 3).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(self.format_currency(price, include_symbol=False), data_format)
        
        # TOTAL
        total = item.get('total', quantity * price)
        cell = self.item_table.cellAt(current_row, 4).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(self.format_currency(total, include_symbol=False), data_format)
    
    def add_item_row(self, item, serial_number, cursor=None):
        """Add a single item row (fallback method for measurement)"""
        if cursor is None:
            cursor = self.cursor
        
        # Create table for single row
        table_format = QTextTableFormat()
        table_format.setCellPadding(self.config.TABLE_CELL_PADDING)
        table_format.setCellSpacing(0)
        table_format.setBorder(self.config.TABLE_ROW_BORDER_WIDTH)
        table_format.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_Solid)
        table_format.setBorderBrush(QBrush(self.config.BORDER_COLOR))
        
        # FIXED: Use actual usable width with some buffer
        usable_width = self.doc.textWidth() * 0.96  # Use 98% of usable width
        
        # Set column widths (SAME AS HEADER)
        table_format.setColumnWidthConstraints([
            QTextLength(QTextLength.Type.FixedLength, usable_width * (self.config.COL_SNO_WIDTH / 100)),
            QTextLength(QTextLength.Type.FixedLength, usable_width * (self.config.COL_DESC_WIDTH / 100)),
            QTextLength(QTextLength.Type.FixedLength, usable_width * (self.config.COL_QTY_WIDTH / 100)),
            QTextLength(QTextLength.Type.FixedLength, usable_width * (self.config.COL_PRICE_WIDTH / 100)),
            QTextLength(QTextLength.Type.FixedLength, usable_width * (self.config.COL_TOTAL_WIDTH / 100)),
        ])
        
        # Set table alignment to left
        table_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Rest of the method remains the same...
        # Create table (1 row, 5 columns)
        table = cursor.insertTable(1, 5, table_format)
        
        # Data format
        data_format = self._create_char_format(self.config.TABLE_DATA_FONT_SIZE)
        
        # S.R#
        cell = table.cellAt(0, 0).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignCenter))
        cell.insertText(str(serial_number), data_format)
        
        # DESCRIPTION
        description = item.get('description', item.get('name', ''))
        cell = table.cellAt(0, 1).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignLeft))
        
        # Handle long descriptions with word wrap
        if len(description) > 50:
            # Split long description
            words = description.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= 50:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for i, line in enumerate(lines):
                if i > 0:
                    cell.insertText("\n")
                cell.insertText(line, data_format)
        else:
            cell.insertText(description, data_format)
        
        # QTY
        quantity = item.get('qty', 1)
        cell = table.cellAt(0, 2).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(str(quantity), data_format)
        
        # PRICE
        price = item.get('price', 0)
        cell = table.cellAt(0, 3).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(self.format_currency(price, include_symbol=False), data_format)
        
        # TOTAL
        total = item.get('total', quantity * price)
        cell = table.cellAt(0, 4).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(self.format_currency(total, include_symbol=False), data_format)
        
        cursor.movePosition(QTextCursor.MoveOperation.End)
    
    def add_item_rows_batch(self, items, cursor=None):
        """Add multiple item rows in a continuous block"""
        if cursor is None:
            cursor = self.cursor
        
        for item in items:
            self.current_serial += 1
            self.add_item_row_to_table(item, self.current_serial)
    
    def add_totals_section(self, bill_data, cursor=None):
        """Add totals section (SUBTOTAL, DISCOUNT, GRAND TOTAL) - ONLY ON LAST PAGE"""
        if cursor is None:
            cursor = self.cursor
        
        subtotal = bill_data.get('subtotal', 0)
        discount = bill_data.get('discount', 0)
        grand_total = bill_data.get('grand_total', subtotal)
        
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add spacing before totals
        block_format = self._create_block_format(
            Qt.AlignmentFlag.AlignRight,
            top_margin=20
        )
        cursor.insertBlock(block_format)
        
        # Create totals table
        table_format = QTextTableFormat()
        table_format.setBorder(0)
        table_format.setCellSpacing(0)
        table_format.setCellPadding(2)
        
        table_format.setColumnWidthConstraints([
            QTextLength(QTextLength.Type.PercentageLength, 40),
            QTextLength(QTextLength.Type.PercentageLength, 60)
        ])
        
        # Create table with 3 rows
        table = cursor.insertTable(3, 2, table_format)
        
        # Format definitions
        label_format = self._create_char_format(self.config.TOTALS_LABEL_FONT_SIZE, bold=True)
        value_format = self._create_char_format(self.config.TOTALS_VALUE_FONT_SIZE)
        grand_format = self._create_char_format(self.config.GRAND_TOTAL_FONT_SIZE, bold=True)
        
        # SUBTOTAL row
        cell = table.cellAt(0, 0).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignLeft))
        cell.insertText("SUBTOTAL", label_format)
        
        cell = table.cellAt(0, 1).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(self.format_currency(subtotal), value_format)
        
        # DISCOUNT row
        cell = table.cellAt(1, 0).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignLeft))
        cell.insertText("DISCOUNT", label_format)
        
        cell = table.cellAt(1, 1).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight))
        cell.insertText(self.format_currency(discount), value_format)
        
        # GRAND TOTAL row
        cell = table.cellAt(2, 0).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignLeft, top_margin=5, bottom_margin=2))
        cell.insertText("GRAND TOTAL", grand_format)
        
        cell = table.cellAt(2, 1).firstCursorPosition()
        cell.setBlockFormat(self._create_block_format(Qt.AlignmentFlag.AlignRight, top_margin=5, bottom_margin=2))
        cell.insertText(self.format_currency(grand_total), grand_format)
        
        cursor.movePosition(QTextCursor.MoveOperation.End)
                # Add separator line between bill info and invoice table
        self.add_horizontal_line(cursor, line_width=76)
    
    def add_terms_and_conditions(self, cursor=None):
        """Add terms and conditions section - ONLY ON LAST PAGE"""
        if cursor is None:
            cursor = self.cursor
        
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add spacing before terms
        block_format = self._create_block_format(
            Qt.AlignmentFlag.AlignLeft,
            top_margin=5
        )
        cursor.insertBlock(block_format)
        
        # Title
        title_format = self._create_char_format(self.config.TERMS_TITLE_FONT_SIZE, bold=True)
        cursor.insertText("TERMS & CONDITIONS\n", title_format)
        
        # Terms list
        terms_format = self._create_char_format(self.config.TERMS_TEXT_FONT_SIZE)
        
        for term in self.config.TERMS_AND_CONDITIONS:
            cursor.insertText(f"• {term}\n", terms_format)
        
        # Thank you message
        block_format = self._create_block_format(
            Qt.AlignmentFlag.AlignCenter,
            top_margin=15
        )
        cursor.insertBlock(block_format)
        
        thank_format = self._create_char_format(
            self.config.THANK_YOU_FONT_SIZE,
            bold=True,
            italic=True,
            color=self.config.THANK_YOU_COLOR
        )
        cursor.insertText("THANK YOU FOR YOUR BUSINESS WITH US!", thank_format)
        
        # Software note
        block_format = self._create_block_format(
            Qt.AlignmentFlag.AlignCenter,
            top_margin=5
        )
        cursor.insertBlock(block_format)
        
        software_format = self._create_char_format(7, color=self.config.FOOTER_COLOR)
        cursor.insertText("Invoice generated by ToolTrek Sales System", software_format)
    
    # ======= MAIN BUILD LOGIC =======
    def build_document(self, bill_data):
        """Build complete invoice document with correct pagination"""
        # Reset document
        self.doc.clear()
        self.cursor = QTextCursor(self.doc)
        self.setup_document()
        self.current_serial = 0
        self.item_table = None
        self.item_table_row = 0
        
        # Extract items
        all_items = bill_data.get('items', [])
        
        print(f"DEBUG: Total items: {len(all_items)}")
        
        # Measure section heights
        measured_heights = self.calculator.measure_section_heights(self, bill_data)
        
        # Calculate pages
        pages = self.calculator.calculate_pages(all_items, measured_heights)
        
        print(f"DEBUG: Calculated {len(pages)} pages")
        
        # Render each page
        for page_index, page in enumerate(pages):
            page_type = page['page_type']
            page_items = page['items']
            
            # Add page break (except for first page)
            if page_index > 0:
                self.cursor.insertText("\f")  # Form feed for page break
            
            print(f"DEBUG: Rendering page {page_index+1}, type={page_type}, items={len(page_items)}")
            
            # ========== FIRST PAGE CONTENT ==========
            if page_type in ('first', 'first_last'):
                self.add_logo()
                self.add_shop_info()
                self.add_bill_info(bill_data)
                # Start continuous table for items
                self.start_items_table()  # TABLE HEADER ONLY ON FIRST PAGE
            
            # ========== ITEM ROWS ==========
            if page_items:
                # For middle/last pages without header, just add items to existing table
                if self.item_table is None and page_index > 0:
                    # If we're on a middle page without a table, create one without header
                    # But actually, items should continue in the same table across pages
                    pass
                self.add_item_rows_batch(page_items)
            
            # ========== LAST PAGE SECTIONS ==========
            if page_type in ('last', 'first_last'):
                # Add separator line before totals
                self.add_horizontal_line(self.cursor, thickness=0.8, margin_top=15, margin_bottom=10, line_width=76)
                self.add_totals_section(bill_data)
                self.add_terms_and_conditions()
        
        return self.doc


# ======= INVOICE GENERATOR =======
class InvoiceGenerator:
    """Main class for generating and printing invoices"""
    
    def __init__(self, config=None):
        self.config = config or InvoiceConfig()
    
    def generate_invoice_document(self, bill_data):
        """Generate QTextDocument for the invoice"""
        try:
            if not bill_data:
                raise ValueError("No bill data provided")
            
            if 'items' not in bill_data:
                raise ValueError("Bill data must contain 'items' list")
            
            builder = ProfessionalInvoiceBuilder(self.config)
            return builder.build_document(bill_data)
            
        except Exception as e:
            print(f"Error generating invoice document: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def generate_invoice_pdf(self, bill_data, filename=None):
        """Generate PDF file from invoice"""
        try:
            if not bill_data:
                raise ValueError("No bill data provided")
            
            doc = self.generate_invoice_document(bill_data)
            
            # Generate filename if not provided
            if not filename:
                temp_dir = tempfile.gettempdir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                bill_no = bill_data.get('bill_number', '00001').replace('/', '_')
                filename = os.path.join(temp_dir, f"TOOLTREK_Invoice_{bill_no}_{timestamp}.pdf")
            
            # Setup printer for PDF
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(self.config.get_page_size())
            
            page_layout = printer.pageLayout()
            if self.config.ORIENTATION == 'landscape':
                page_layout.setOrientation(QPageLayout.Orientation.Landscape)
            else:
                page_layout.setOrientation(QPageLayout.Orientation.Portrait)
            
            printer.setPageLayout(page_layout)
            printer.setPageMargins(self.config.get_margins())
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageOrder(QPrinter.PageOrder.FirstPageFirst)
            
            # Print to PDF
            doc.print(printer)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename
            else:
                raise Exception("PDF file was not created or is empty")
                
        except Exception as e:
            print(f"Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def print_invoice(self, bill_data, parent=None):
        """Print invoice directly to printer"""
        try:
            if not bill_data:
                if parent:
                    QMessageBox.critical(parent, "Print Error", "No bill data to print")
                return False
            
            doc = self.generate_invoice_document(bill_data)
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(self.config.get_page_size())
            
            page_layout = printer.pageLayout()
            if self.config.ORIENTATION == 'landscape':
                page_layout.setOrientation(QPageLayout.Orientation.Landscape)
            else:
                page_layout.setOrientation(QPageLayout.Orientation.Portrait)
            
            printer.setPageLayout(page_layout)
            printer.setPageMargins(self.config.get_margins())
            
            dialog = QPrintDialog(printer, parent)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                doc.print(printer)
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"Print error: {str(e)}"
            print(error_msg)
            
            if parent:
                QMessageBox.critical(parent, "Print Error", error_msg)
            
            return False


# ======= COMPATIBILITY FUNCTIONS =======
class InvoiceFactory:
    """Factory class for creating invoice generators"""
    
    @staticmethod
    def create_invoice(config=None):
        return InvoiceGenerator(config)
    
    @staticmethod
    def preview_invoice(bill_data, parent=None):
        dialog = InvoicePreviewDialog(bill_data, parent)
        return dialog.exec()


def prepare_bill_data_from_sale(sale_items, customer="", bill_number=""):
    """Prepare bill data from sale items"""
    items = []
    for item in sale_items:
        items.append({
            'name': item.get('display_name', '') or item.get('name', ''),
            'description': item.get('display_name', '') or item.get('name', ''),
            'qty': item.get('quantity', 1),
            'price': item.get('price', 0),
            'total': item.get('total_price', item.get('price', 0) * item.get('quantity', 1))
        })
    
    subtotal = sum(it['total'] for it in items)
    
    return {
        'bill_number': bill_number or "00001",
        'customer': customer or "WALK-IN CUSTOMER",
        'items': items,
        'subtotal': subtotal,
        'discount': 0,
        'discount_type': 'Amount',
        'tax_rate': 0,
        'grand_total': subtotal,
        'date': datetime.now().strftime(InvoiceConfig.DATE_FORMAT),
        'time': datetime.now().strftime("%I:%M %p")
    }


# ======= PREVIEW DIALOG =======
class InvoicePreviewDialog(QDialog):
    """Dialog for previewing invoices before printing"""
    
    def __init__(self, bill_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Invoice Preview - F9 to Print | Esc to Close")
        self.setGeometry(100, 50, 620, 820)
        self.bill_data = bill_data
        self.generator = InvoiceGenerator()
        self.setup_ui()
        self.load_preview()
        self.setup_shortcuts()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Preview area
        self.preview = QTextBrowser()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)
        
        # Status bar
        self.status = QStatusBar()
        layout.addWidget(self.status)
        
        self.page_info = QLabel("")
        self.status.addPermanentWidget(self.page_info)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText("Print (F9)")
        buttons.accepted.connect(self.on_print)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
    
    def load_preview(self):
        """Load invoice preview"""
        try:
            doc = self.generator.generate_invoice_document(self.bill_data)
            self.preview.setDocument(doc)
            
            # Update status info
            item_count = len(self.bill_data.get('items', []))
            pages = doc.pageCount()
            self.page_info.setText(f"Items: {item_count} | Pages: {pages} | A5 Portrait")
            
        except Exception as e:
            error_msg = f"Error loading preview: {str(e)}"
            self.preview.setPlainText(error_msg)
            print(error_msg)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        print_action = QAction("Print", self)
        print_action.setShortcut(QKeySequence("F9"))
        print_action.triggered.connect(self.on_print)
        self.addAction(print_action)
        
        close_action = QAction("Close", self)
        close_action.setShortcut(QKeySequence("Escape"))
        close_action.triggered.connect(self.reject)
        self.addAction(close_action)
    
    def on_print(self):
        """Handle print button click"""
        try:
            reply = QMessageBox.question(
                self, "Print Invoice",
                f"Print invoice #{self.bill_data.get('bill_number', '')}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success = self.generator.print_invoice(self.bill_data, self)
                
                if success:
                    QMessageBox.information(
                        self, "Print Successful",
                        "Invoice sent to printer successfully."
                    )
                    self.accept()
                else:
                    QMessageBox.warning(
                        self, "Print Failed",
                        "Printing was cancelled or failed."
                    )
                    
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Error while printing: {str(e)}")


# ======= MAIN TEST FUNCTION =======
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create EXACT test data matching BILL31.pdf with 20 items
    test_items = [
        # Page 1 items (from BILL31.pdf)
        {'name': 'STEEL WIRE PIPE CHINA BLUE 3"', 'description': 'STEEL WIRE PIPE CHINA BLUE 3"', 'qty': 1, 'price': 400, 'total': 400},
        {'name': 'WHITE STEEL POLISH DISC 4"', 'description': 'WHITE STEEL POLISH DISC 4"', 'qty': 1, 'price': 100, 'total': 100},
        {'name': 'WHITE STEEL POLISH DISC 5"', 'description': 'WHITE STEEL POLISH DISC 5"', 'qty': 1, 'price': 150, 'total': 150},
        {'name': 'RED STEEL POLISH DISC 4"', 'description': 'RED STEEL POLISH DISC 4"', 'qty': 1, 'price': 100, 'total': 100},
        {'name': 'RED STEEL POLISH DISC 5"', 'description': 'RED STEEL POLISH DISC 5"', 'qty': 1, 'price': 150, 'total': 150},
        {'name': 'CUTTING DISC 4" X 1MM HORSE', 'description': 'CUTTING DISC 4" X 1MM HORSE', 'qty': 1, 'price': 50, 'total': 50},
        {'name': 'CUTTING DISC 5"X1MM HORSE', 'description': 'CUTTING DISC 5"X1MM HORSE', 'qty': 1, 'price': 60, 'total': 60},
        {'name': 'PRESSURE GAUGE STEEL 3500PSI LIQUID 2" X 1/4" BSP', 'description': 'PRESSURE GAUGE STEEL 3500PSI LIQUID 2" X 1/4" BSP', 'qty': 1, 'price': 5000, 'total': 5000},
        {'name': 'Test Item 1', 'description': 'IT IS A VERY LONG NAME ITEM TO TEST THE PRINTING LOGIC OF THE SOFTWARE HOW IT WILL WRAP THE TEXT SO IT WILL NOT COLLIED WITH THE BORDER OF THE NEXT UPCOMING COLUMN 000000000001', 'qty': 1, 'price': 1, 'total': 1},
        {'name': 'Test Item 2', 'description': 'IT IS A VERY LONG NAME ITEM TO TEST THE PRINTING LOGIC OF THE SOFTWARE HOW IT WILL WRAP THE TEXT SO IT WILL NOT COLLIED WITH THE BORDER OF THE NEXT UPCOMING COLUMN 000000000002', 'qty': 1, 'price': 1, 'total': 1},
        
        # Page 2 items (from BILL31.pdf)
        {'name': 'PRESSURE GAUGE STEEL 3500PSI LIQUID 2" X 1/4" BSP', 'description': 'PRESSURE GAUGE STEEL 3500PSI LIQUID 2" X 1/4" BSP', 'qty': 1, 'price': 5000, 'total': 5000},
        {'name': '12 STEP DRILL 3 PIECES SET', 'description': '12 STEP DRILL 3 PIECES SET', 'qty': 1, 'price': 1200, 'total': 1200},
        {'name': 'STEEL FLEXIBLE GRINDING DISC 4"', 'description': 'STEEL FLEXIBLE GRINDING DISC 4"', 'qty': 1, 'price': 150, 'total': 150},
        {'name': 'GOODDO ANT-RUST 450ML', 'description': 'GOODDO ANT-RUST 450ML', 'qty': 1, 'price': 680, 'total': 680},
        {'name': 'GUARD GREASE NLGI GRADE 2 180G', 'description': 'GUARD GREASE NLGI GRADE 2 180G', 'qty': 1, 'price': 200, 'total': 200},
        {'name': 'GUARD GREASEE NLGI GRADE 2 500G', 'description': 'GUARD GREASEE NLGI GRADE 2 500G', 'qty': 1, 'price': 850, 'total': 850},
        {'name': 'VEGA-DX GREASE NLGI GRADE 2 500G', 'description': 'VEGA-DX GREASE NLGI GRADE 2 500G', 'qty': 1, 'price': 550, 'total': 550},
        {'name': 'COMBINATION SPANNER 6MM', 'description': 'COMBINATION SPANNER 6MM', 'qty': 1, 'price': 120, 'total': 120},
        
        # Page 3 items (from BILL31.pdf)
        {'name': 'EUROPEAN TYPE CLAMP STEEL 22 - 32MM 1-1/4"', 'description': 'EUROPEAN TYPE CLAMP STEEL 22 - 32MM 1-1/4"', 'qty': 1, 'price': 80, 'total': 80},
        {'name': 'MALE FEMALE COUPLER PLASTIC QUICK RELEASE 8MM PIPE', 'description': 'MALE FEMALE COUPLER PLASTIC QUICK RELEASE 8MM PIPE', 'qty': 1, 'price': 400, 'total': 400},
    ]
    
    test_data = {
        'bill_number': '00048',
        'customer': 'WALK-IN CUSTOMER',
        'items': test_items,
        'subtotal': 15242,
        'discount': 242,
        'discount_type': 'Amount',
        'tax_rate': 0,
        'grand_total': 15000,
        'date': '16/12/2025',
        'time': '12:00 PM'
    }
    
    print(f"Testing with {len(test_items)} items")
    print(f"Subtotal: {test_data['subtotal']}")
    print(f"Grand total: {test_data['grand_total']}")
    
    try:
        generator = InvoiceGenerator()
        
        print("\n1. Testing PDF generation...")
        pdf_path = generator.generate_invoice_pdf(test_data, "TOOLTREK_BILL_00048_PROFESSIONAL.pdf")
        
        if pdf_path:
            print(f"✓ PDF generated: {pdf_path}")
            print(f"✓ File size: {os.path.getsize(pdf_path):,} bytes")
        else:
            print("✗ PDF generation failed")
        
        print("\n2. Testing preview dialog...")
        dialog = InvoicePreviewDialog(test_data)
        
        doc = generator.generate_invoice_document(test_data)
        print(f"✓ Document pages: {doc.pageCount()}")
        
        dialog.exec()
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(app.exec())