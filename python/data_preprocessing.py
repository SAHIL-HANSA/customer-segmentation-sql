"""
Customer Data Preprocessing Pipeline
Author: Sahil Hansa
Email: sahilhansa007@gmail.com
Description: Data cleaning and preparation for customer segmentation analysis
Location: Jammu, J&K, India
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/preprocessing.log'),
        logging.StreamHandler()
    ]
)

class CustomerDataPreprocessor:
    """
    Customer Data Preprocessing Class
    
    Handles data cleaning, validation, and preparation for segmentation analysis
    
    Author: Sahil Hansa
    Contact: sahilhansa007@gmail.com
    """
    
    def __init__(self):
        self.raw_data = None
        self.processed_data = None
        self.data_quality_report = {}
        
    def load_raw_data(self, file_path, file_type='csv'):
        """Load raw customer transaction data"""
        try:
            if file_type.lower() == 'csv':
                self.raw_data = pd.read_csv(file_path)
            elif file_type.lower() == 'excel':
                self.raw_data = pd.read_excel(file_path)
            elif file_type.lower() == 'json':
                self.raw_data = pd.read_json(file_path)
            
            logging.info(f"Raw data loaded successfully: {len(self.raw_data)} records")
            return self.raw_data
            
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            return None
    
    def perform_data_quality_assessment(self):
        """Assess data quality and identify issues"""
        if self.raw_data is None:
            logging.error("No data loaded for quality assessment")
            return None
        
        logging.info("Performing data quality assessment...")
        
        # Basic data info
        self.data_quality_report['total_records'] = len(self.raw_data)
        self.data_quality_report['total_columns'] = len(self.raw_data.columns)
        self.data_quality_report['memory_usage'] = self.raw_data.memory_usage(deep=True).sum()
        
        # Missing values analysis
        missing_analysis = {}
        for column in self.raw_data.columns:
            missing_count = self.raw_data[column].isnull().sum()
            missing_percentage = (missing_count / len(self.raw_data)) * 100
            missing_analysis[column] = {
                'missing_count': missing_count,
                'missing_percentage': round(missing_percentage, 2)
            }
        
        self.data_quality_report['missing_values'] = missing_analysis
        
        # Duplicate records
        duplicates = self.raw_data.duplicated().sum()
        self.data_quality_report['duplicate_records'] = duplicates
        self.data_quality_report['duplicate_percentage'] = round((duplicates / len(self.raw_data)) * 100, 2)
        
        # Data type analysis
        data_types = {}
        for column in self.raw_data.columns:
            data_types[column] = str(self.raw_data[column].dtype)
        
        self.data_quality_report['data_types'] = data_types
        
        # Outlier detection for numeric columns
        numeric_columns = self.raw_data.select_dtypes(include=[np.number]).columns
        outlier_analysis = {}
        
        for column in numeric_columns:
            Q1 = self.raw_data[column].quantile(0.25)
            Q3 = self.raw_data[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = self.raw_data[(self.raw_data[column] < lower_bound) | 
                                   (self.raw_data[column] > upper_bound)]
            
            outlier_analysis[column] = {
                'outlier_count': len(outliers),
                'outlier_percentage': round((len(outliers) / len(self.raw_data)) * 100, 2),
                'lower_bound': lower_bound,
                'upper_bound': upper_bound
            }
        
        self.data_quality_report['outliers'] = outlier_analysis
        
        logging.info("Data quality assessment completed")
        return self.data_quality_report
    
    def clean_customer_data(self):
        """Clean and standardize customer data"""
        if self.raw_data is None:
            logging.error("No data loaded for cleaning")
            return None
        
        logging.info("Starting data cleaning process...")
        
        # Create a copy for processing
        self.processed_data = self.raw_data.copy()
        
        # 1. Handle missing values
        self._handle_missing_values()
        
        # 2. Remove duplicates
        self._remove_duplicates()
        
        # 3. Standardize data types
        self._standardize_data_types()
        
        # 4. Clean and validate dates
        self._clean_date_columns()
        
        # 5. Clean monetary values
        self._clean_monetary_values()
        
        # 6. Standardize text fields
        self._standardize_text_fields()
        
        # 7. Handle outliers
        self._handle_outliers()
        
        # 8. Create derived features
        self._create_derived_features()
        
        logging.info(f"Data cleaning completed. Final dataset: {len(self.processed_data)} records")
        return self.processed_data
    
    def _handle_missing_values(self):
        """Handle missing values based on column type and business logic"""
        logging.info("Handling missing values...")
        
        initial_records = len(self.processed_data)
        
        # Remove records with missing critical fields
        critical_fields = ['customer_id', 'transaction_date', 'transaction_amount']
        
        for field in critical_fields:
            if field in self.processed_data.columns:
                before_count = len(self.processed_data)
                self.processed_data = self.processed_data.dropna(subset=[field])
                after_count = len(self.processed_data)
                if before_count != after_count:
                    logging.info(f"Removed {before_count - after_count} records with missing {field}")
        
        # Fill missing categorical values
        categorical_columns = self.processed_data.select_dtypes(include=['object']).columns
        for column in categorical_columns:
            if column not in critical_fields:
                mode_value = self.processed_data[column].mode()
                if len(mode_value) > 0:
                    self.processed_data[column].fillna(mode_value[0], inplace=True)
                else:
                    self.processed_data[column].fillna('Unknown', inplace=True)
        
        # Fill missing numerical values
        numerical_columns = self.processed_data.select_dtypes(include=[np.number]).columns
        for column in numerical_columns:
            if column not in critical_fields:
                median_value = self.processed_data[column].median()
                self.processed_data[column].fillna(median_value, inplace=True)
        
        final_records = len(self.processed_data)
        logging.info(f"Missing value handling: {initial_records} → {final_records} records")
    
    def _remove_duplicates(self):
        """Remove duplicate records"""
        initial_count = len(self.processed_data)
        
        # Remove exact duplicates
        self.processed_data = self.processed_data.drop_duplicates()
        
        # Remove duplicates based on business logic (same customer, date, amount)
        if all(col in self.processed_data.columns for col in ['customer_id', 'transaction_date', 'transaction_amount']):
            self.processed_data = self.processed_data.drop_duplicates(
                subset=['customer_id', 'transaction_date', 'transaction_amount'],
                keep='first'
            )
        
        final_count = len(self.processed_data)
        duplicates_removed = initial_count - final_count
        
        if duplicates_removed > 0:
            logging.info(f"Removed {duplicates_removed} duplicate records")
    
    def _standardize_data_types(self):
        """Standardize data types for consistency"""
        logging.info("Standardizing data types...")
        
        # Convert customer_id to string
        if 'customer_id' in self.processed_data.columns:
            self.processed_data['customer_id'] = self.processed_data['customer_id'].astype(str)
        
        # Convert transaction_id to string if exists
        if 'transaction_id' in self.processed_data.columns:
            self.processed_data['transaction_id'] = self.processed_data['transaction_id'].astype(str)
        
        # Ensure monetary columns are numeric
        monetary_columns = ['transaction_amount', 'total_amount', 'unit_price', 'monetary']
        for column in monetary_columns:
            if column in self.processed_data.columns:
                self.processed_data[column] = pd.to_numeric(self.processed_data[column], errors='coerce')
    
    def _clean_date_columns(self):
        """Clean and validate date columns"""
        logging.info("Cleaning date columns...")
        
        date_columns = ['transaction_date', 'registration_date', 'last_purchase_date']
        
        for column in date_columns:
            if column in self.processed_data.columns:
                # Convert to datetime
                self.processed_data[column] = pd.to_datetime(self.processed_data[column], errors='coerce')
                
                # Remove future dates (data quality issue)
                if column == 'transaction_date':
                    future_dates = self.processed_data[self.processed_data[column] > datetime.now()]
                    if len(future_dates) > 0:
                        logging.warning(f"Found {len(future_dates)} future transaction dates, removing...")
                        self.processed_data = self.processed_data[self.processed_data[column] <= datetime.now()]
                
                # Remove very old dates (potential data quality issue)
                cutoff_date = datetime.now() - timedelta(days=3650)  # 10 years
                old_dates = self.processed_data[self.processed_data[column] < cutoff_date]
                if len(old_dates) > 0:
                    logging.warning(f"Found {len(old_dates)} very old dates in {column}")
    
    def _clean_monetary_values(self):
        """Clean and validate monetary values"""
        logging.info("Cleaning monetary values...")
        
        monetary_columns = ['transaction_amount', 'total_amount', 'unit_price']
        
        for column in monetary_columns:
            if column in self.processed_data.columns:
                # Remove negative values
                negative_values = self.processed_data[self.processed_data[column] < 0]
                if len(negative_values) > 0:
                    logging.warning(f"Found {len(negative_values)} negative values in {column}, removing...")
                    self.processed_data = self.processed_data[self.processed_data[column] >= 0]
                
                # Remove zero values for transaction amounts
                if column in ['transaction_amount', 'total_amount']:
                    zero_values = self.processed_data[self.processed_data[column] == 0]
                    if len(zero_values) > 0:
                        logging.warning(f"Found {len(zero_values)} zero values in {column}, removing...")
                        self.processed_data = self.processed_data[self.processed_data[column] > 0]
    
    def _standardize_text_fields(self):
        """Standardize text fields for consistency"""
        logging.info("Standardizing text fields...")
        
        text_columns = ['customer_name', 'product_category', 'location', 'region']
        
        for column in text_columns:
            if column in self.processed_data.columns:
                # Remove extra whitespace and standardize case
                self.processed_data[column] = self.processed_data[column].astype(str).str.strip()
                self.processed_data[column] = self.processed_data[column].str.title()
                
                # Replace common variations
                if column == 'product_category':
                    category_mapping = {
                        'Electronic': 'Electronics',
                        'Cloth': 'Clothing',
                        'Clothes': 'Clothing',
                        'Book': 'Books',
                        'Sport': 'Sports',
                        'Home Garden': 'Home & Garden',
                        'Home&Garden': 'Home & Garden'
                    }
                    
                    for old_value, new_value in category_mapping.items():
                        self.processed_data[column] = self.processed_data[column].replace(old_value, new_value)
    
    def _handle_outliers(self):
        """Handle outliers in monetary values"""
        logging.info("Handling outliers...")
        
        monetary_columns = ['transaction_amount', 'total_amount']
        
        for column in monetary_columns:
            if column in self.processed_data.columns:
                # Calculate IQR bounds
                Q1 = self.processed_data[column].quantile(0.25)
                Q3 = self.processed_data[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR  # Using 3*IQR for extreme outliers
                upper_bound = Q3 + 3 * IQR
                
                # Cap outliers instead of removing them
                outliers_count = len(self.processed_data[
                    (self.processed_data[column] < lower_bound) | 
                    (self.processed_data[column] > upper_bound)
                ])
                
                if outliers_count > 0:
                    self.processed_data[column] = np.where(
                        self.processed_data[column] > upper_bound,
                        upper_bound,
                        self.processed_data[column]
                    )
                    
                    self.processed_data[column] = np.where(
                        self.processed_data[column] < lower_bound,
                        lower_bound,
                        self.processed_data[column]
                    )
                    
                    logging.info(f"Capped {outliers_count} outliers in {column}")
    
    def _create_derived_features(self):
        """Create additional features for analysis"""
        logging.info("Creating derived features...")
        
        # Create transaction date features
        if 'transaction_date' in self.processed_data.columns:
            self.processed_data['transaction_year'] = self.processed_data['transaction_date'].dt.year
            self.processed_data['transaction_month'] = self.processed_data['transaction_date'].dt.month
            self.processed_data['transaction_quarter'] = self.processed_data['transaction_date'].dt.quarter
            self.processed_data['transaction_day_of_week'] = self.processed_data['transaction_date'].dt.dayofweek
            self.processed_data['transaction_week_of_year'] = self.processed_data['transaction_date'].dt.isocalendar().week
            
            # Create season feature
            def get_season(month):
                if month in [12, 1, 2]:
                    return 'Winter'
                elif month in [3, 4, 5]:
                    return 'Spring'
                elif month in [6, 7, 8]:
                    return 'Summer'
                else:
                    return 'Fall'
            
            self.processed_data['transaction_season'] = self.processed_data['transaction_month'].apply(get_season)
        
        # Create transaction amount categories
        if 'transaction_amount' in self.processed_data.columns:
            amount_bins = [0, 50, 100, 250, 500, 1000, float('inf')]
            amount_labels = ['Very Low', 'Low', 'Medium', 'High', 'Very High', 'Premium']
            self.processed_data['amount_category'] = pd.cut(
                self.processed_data['transaction_amount'],
                bins=amount_bins,
                labels=amount_labels,
                right=False
            )
    
    def validate_processed_data(self):
        """Validate the processed data quality"""
        if self.processed_data is None:
            logging.error("No processed data available for validation")
            return False
        
        logging.info("Validating processed data...")
        
        validation_results = {
            'total_records': len(self.processed_data),
            'missing_values': self.processed_data.isnull().sum().sum(),
            'duplicate_records': self.processed_data.duplicated().sum(),
            'data_types_consistent': True,
            'date_ranges_valid': True,
            'monetary_values_valid': True
        }
        
        # Check for critical missing values
        critical_fields = ['customer_id', 'transaction_date', 'transaction_amount']
        for field in critical_fields:
            if field in self.processed_data.columns:
                missing_count = self.processed_data[field].isnull().sum()
                if missing_count > 0:
                    logging.error(f"Critical field {field} has {missing_count} missing values")
                    validation_results['data_types_consistent'] = False
        
        # Validate date ranges
        if 'transaction_date' in self.processed_data.columns:
            future_dates = self.processed_data[self.processed_data['transaction_date'] > datetime.now()]
            if len(future_dates) > 0:
                validation_results['date_ranges_valid'] = False
        
        # Validate monetary values
        monetary_columns = ['transaction_amount', 'total_amount']
        for column in monetary_columns:
            if column in self.processed_data.columns:
                negative_values = self.processed_data[self.processed_data[column] < 0]
                if len(negative_values) > 0:
                    validation_results['monetary_values_valid'] = False
        
        # Overall validation status
        validation_results['validation_passed'] = (
            validation_results['data_types_consistent'] and
            validation_results['date_ranges_valid'] and
            validation_results['monetary_values_valid'] and
            validation_results['missing_values'] == 0
        )
        
        if validation_results['validation_passed']:
            logging.info("Data validation passed successfully")
        else:
            logging.warning("Data validation found issues")
        
        return validation_results
    
    def save_processed_data(self, output_path, file_format='csv'):
        """Save processed data to file"""
        if self.processed_data is None:
            logging.error("No processed data to save")
            return False
        
        try:
            if file_format.lower() == 'csv':
                self.processed_data.to_csv(output_path, index=False)
            elif file_format.lower() == 'excel':
                self.processed_data.to_excel(output_path, index=False)
            elif file_format.lower() == 'parquet':
                self.processed_data.to_parquet(output_path, index=False)
            
            logging.info(f"Processed data saved to {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving processed data: {str(e)}")
            return False
    
    def generate_preprocessing_report(self, output_path='reports/preprocessing_report.txt'):
        """Generate comprehensive preprocessing report"""
        if self.data_quality_report is None:
            logging.error("No quality assessment available")
            return
        
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("="*60 + "\n")
            f.write("CUSTOMER DATA PREPROCESSING REPORT\n")
            f.write("="*60 + "\n")
            f.write(f"Author: Sahil Hansa\n")
            f.write(f"Email: sahilhansa007@gmail.com\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            # Data overview
            f.write("DATA OVERVIEW\n")
            f.write("-"*20 + "\n")
            f.write(f"Total Records: {self.data_quality_report['total_records']:,}\n")
            f.write(f"Total Columns: {self.data_quality_report['total_columns']}\n")
            f.write(f"Memory Usage: {self.data_quality_report['memory_usage'] / 1024 / 1024:.2f} MB\n\n")
            
            # Missing values
            f.write("MISSING VALUES ANALYSIS\n")
            f.write("-"*25 + "\n")
            for column, info in self.data_quality_report['missing_values'].items():
                f.write(f"{column}: {info['missing_count']} ({info['missing_percentage']}%)\n")
            f.write("\n")
            
            # Duplicates
            f.write("DUPLICATE RECORDS\n")
            f.write("-"*17 + "\n")
            f.write(f"Duplicate Records: {self.data_quality_report['duplicate_records']} ")
            f.write(f"({self.data_quality_report['duplicate_percentage']}%)\n\n")
            
            # Outliers
            f.write("OUTLIER ANALYSIS\n")
            f.write("-"*16 + "\n")
            for column, info in self.data_quality_report['outliers'].items():
                f.write(f"{column}: {info['outlier_count']} outliers ({info['outlier_percentage']}%)\n")
            
        logging.info(f"Preprocessing report saved to {output_path}")

def main():
    """
    Main execution function for data preprocessing
    
    Author: Sahil Hansa
    Contact: sahilhansa007@gmail.com
    """
    print("=== Customer Data Preprocessing Pipeline ===")
    print("Author: Sahil Hansa")
    print("Email: sahilhansa007@gmail.com")
    print("GitHub: https://github.com/SAHIL-HANSA")
    print("Location: Jammu, J&K, India")
    print("=" * 45)
    
    # Initialize preprocessor
    preprocessor = CustomerDataPreprocessor()
    
    # Load sample data
    sample_data_path = 'data/sample/sample_transactions.csv'
    raw_data = preprocessor.load_raw_data(sample_data_path)
    
    if raw_data is not None:
        print(f"Loaded {len(raw_data)} raw records")
        
        # Perform quality assessment
        quality_report = preprocessor.perform_data_quality_assessment()
        
        # Clean the data
        processed_data = preprocessor.clean_customer_data()
        
        if processed_data is not None:
            print(f"Processed data: {len(processed_data)} records")
            
            # Validate processed data
            validation_results = preprocessor.validate_processed_data()
            
            if validation_results['validation_passed']:
                print("✅ Data validation passed")
            else:
                print("⚠️ Data validation found issues")
            
            # Save processed data
            preprocessor.save_processed_data('data/processed/clean_transactions.csv')
            
            # Generate report
            preprocessor.generate_preprocessing_report()
            
            print("\n=== Preprocessing Complete ===")
            print("Files created:")
            print("- data/processed/clean_transactions.csv")
            print("- reports/preprocessing_report.txt")
            
        else:
            print("❌ Data preprocessing failed")
    else:
        print("❌ Could not load raw data")

if __name__ == "__main__":
    main()