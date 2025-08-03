import os
import tempfile
import logging
from typing import Dict, List
from datetime import datetime
import pandas as pd
from app.backend.db.database import IndexDatabase

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting data to Excel files."""
    
    def __init__(self):
        self.db = IndexDatabase()
        self.export_dir = "exports"
        self._ensure_export_dir()
    
    def _ensure_export_dir(self):
        """Ensure export directory exists."""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
    
    def export_data(self, start_date: str, end_date: str, 
                   include_performance: bool = True,
                   include_compositions: bool = True,
                   include_changes: bool = True) -> Dict:
        """Export data to Excel file."""
        try:
            # Create temporary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"index_data_{start_date}_to_{end_date}_{timestamp}.xlsx"
            filepath = os.path.join(self.export_dir, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # Export performance data
                if include_performance:
                    self._export_performance_data(writer, start_date, end_date)
                
                # Export composition data
                if include_compositions:
                    self._export_composition_data(writer, start_date, end_date)
                
                # Export composition changes
                if include_changes:
                    self._export_composition_changes(writer, start_date, end_date)
                
                # Export summary
                self._export_summary(writer, start_date, end_date)
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            return {
                "success": True,
                "file_url": f"/api/v1/download/{filename}",
                "file_path": filepath,
                "file_size": file_size,
                "export_date": datetime.now().isoformat(),
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _export_performance_data(self, writer, start_date: str, end_date: str):
        """Export performance data to Excel sheet."""
        try:
            performance = self.db.get_index_performance(start_date, end_date)
            
            if performance:
                df = pd.DataFrame(performance)
                
                # Format columns
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                df['daily_return'] = df['daily_return'].round(4)
                df['cumulative_return'] = df['cumulative_return'].round(4)
                df['index_value'] = df['index_value'].round(2)
                
                # Rename columns for better readability
                df = df.rename(columns={
                    'date': 'Date',
                    'daily_return': 'Daily Return (%)',
                    'cumulative_return': 'Cumulative Return (%)',
                    'index_value': 'Index Value'
                })
                
                df.to_excel(writer, sheet_name='Performance', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Performance']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                    
        except Exception as e:
            logger.error(f"Error exporting performance data: {str(e)}")
    
    def _export_composition_data(self, writer, start_date: str, end_date: str):
        """Export composition data to Excel sheet."""
        try:
            conn = self.db._get_connection()
            
            query = """
                SELECT 
                    ic.date,
                    ic.symbol,
                    ic.weight,
                    ic.market_cap,
                    ic.rank,
                    m.name,
                    m.exchange
                FROM index_compositions ic
                LEFT JOIN stock_metadata m ON ic.symbol = m.symbol
                WHERE ic.date BETWEEN ? AND ?
                ORDER BY ic.date, ic.rank
            """
            
            result = conn.execute(query, [start_date, end_date]).fetchall()
            conn.close()
            
            if result:
                df = pd.DataFrame(result, columns=[
                    'date', 'symbol', 'weight', 'market_cap', 'rank', 'name', 'exchange'
                ])
                
                # Format columns
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                df['weight'] = (df['weight'] * 100).round(4)  # Convert to percentage
                df['market_cap'] = df['market_cap'].round(0)
                
                # Rename columns
                df = df.rename(columns={
                    'date': 'Date',
                    'symbol': 'Symbol',
                    'weight': 'Weight (%)',
                    'market_cap': 'Market Cap',
                    'rank': 'Rank',
                    'name': 'Company Name',
                    'exchange': 'Exchange'
                })
                
                df.to_excel(writer, sheet_name='Compositions', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Compositions']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                    
        except Exception as e:
            logger.error(f"Error exporting composition data: {str(e)}")
    
    def _export_composition_changes(self, writer, start_date: str, end_date: str):
        """Export composition changes to Excel sheet."""
        try:
            changes = self.db.get_composition_changes(start_date, end_date)
            
            if changes:
                df = pd.DataFrame(changes)
                
                # Format columns
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                df['market_cap'] = df['market_cap'].round(0)
                
                # Rename columns
                df = df.rename(columns={
                    'date': 'Date',
                    'symbol': 'Symbol',
                    'action': 'Action',
                    'previous_rank': 'Previous Rank',
                    'new_rank': 'New Rank',
                    'market_cap': 'Market Cap'
                })
                
                df.to_excel(writer, sheet_name='Composition Changes', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Composition Changes']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                    
        except Exception as e:
            logger.error(f"Error exporting composition changes: {str(e)}")
    
    def _export_summary(self, writer, start_date: str, end_date: str):
        """Export summary statistics to Excel sheet."""
        try:
            # Get summary data
            conn = self.db._get_connection()
            
            # Performance summary
            perf_query = """
                SELECT 
                    COUNT(*) as total_days,
                    AVG(daily_return) as avg_daily_return,
                    MAX(cumulative_return) as max_cumulative_return,
                    MIN(cumulative_return) as min_cumulative_return
                FROM index_performance
                WHERE date BETWEEN ? AND ?
            """
            
            perf_summary = conn.execute(perf_query, [start_date, end_date]).fetchone()
            
            # Composition summary
            comp_query = """
                SELECT 
                    COUNT(DISTINCT date) as total_composition_days,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    AVG(weight * 100) as avg_weight_percentage
                FROM index_compositions
                WHERE date BETWEEN ? AND ?
            """
            
            comp_summary = conn.execute(comp_query, [start_date, end_date]).fetchone()
            
            # Changes summary
            changes_query = """
                SELECT 
                    COUNT(*) as total_changes,
                    COUNT(CASE WHEN action = 'added' THEN 1 END) as additions,
                    COUNT(CASE WHEN action = 'removed' THEN 1 END) as removals
                FROM composition_changes
                WHERE date BETWEEN ? AND ?
            """
            
            changes_summary = conn.execute(changes_query, [start_date, end_date]).fetchone()
            
            conn.close()
            
            # Create summary DataFrame
            summary_data = {
                'Metric': [
                    'Date Range',
                    'Total Trading Days',
                    'Average Daily Return (%)',
                    'Maximum Cumulative Return (%)',
                    'Minimum Cumulative Return (%)',
                    'Total Composition Days',
                    'Unique Symbols',
                    'Average Weight per Stock (%)',
                    'Total Composition Changes',
                    'Additions',
                    'Removals'
                ],
                'Value': [
                    f"{start_date} to {end_date}",
                    perf_summary[0] if perf_summary[0] else 0,
                    round(perf_summary[1], 4) if perf_summary[1] else 0,
                    round(perf_summary[2], 4) if perf_summary[2] else 0,
                    round(perf_summary[3], 4) if perf_summary[3] else 0,
                    comp_summary[0] if comp_summary[0] else 0,
                    comp_summary[1] if comp_summary[1] else 0,
                    round(comp_summary[2], 4) if comp_summary[2] else 0,
                    changes_summary[0] if changes_summary[0] else 0,
                    changes_summary[1] if changes_summary[1] else 0,
                    changes_summary[2] if changes_summary[2] else 0
                ]
            }
            
            df = pd.DataFrame(summary_data)
            df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Summary']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
                
        except Exception as e:
            logger.error(f"Error exporting summary: {str(e)}") 