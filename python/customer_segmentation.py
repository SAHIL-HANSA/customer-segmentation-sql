"""
Customer Segmentation using Machine Learning
Author: Sahil Hansa
Email: sahilhansa007@gmail.com
Description: Python script for customer segmentation using K-means clustering and RFM analysis
Location: Jammu, J&K, India
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Database connection libraries
from sqlalchemy import create_engine
import mysql.connector
import sqlite3
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/segmentation.log'),
        logging.StreamHandler()
    ]
)

class CustomerSegmentation:
    """
    Customer Segmentation Analysis Class
    
    Performs RFM analysis and K-means clustering for customer segmentation
    
    Author: Sahil Hansa
    Contact: sahilhansa007@gmail.com
    """
    
    def __init__(self, connection_string=None):
        self.connection_string = connection_string
        self.engine = None
        self.customer_data = None
        self.rfm_data = None
        self.segmented_data = None
        self.scaler = StandardScaler()
        
    def connect_database(self):
        """Establish database connection"""
        try:
            if self.connection_string:
                self.engine = create_engine(self.connection_string)
                logging.info("Database connection established successfully")
                return True
            else:
                logging.warning("No database connection string provided. Will use sample data.")
                return False
        except Exception as e:
            logging.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def load_data(self, query=None, csv_file=None):
        """
        Load customer transaction data from database or CSV file
        """
        try:
            if query and self.engine:
                # Load from database
                self.customer_data = pd.read_sql(query, self.engine)
                logging.info(f"Loaded {len(self.customer_data)} records from database")
            elif csv_file:
                # Load from CSV file
                self.customer_data = pd.read_csv(csv_file)
                logging.info(f"Loaded {len(self.customer_data)} records from CSV file")
            else:
                # Generate sample data for demonstration
                self.customer_data = self._generate_sample_data()
                logging.info("Generated sample data for demonstration")
                
            return self.customer_data
            
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            return None
    
    def _generate_sample_data(self):
        """Generate sample customer transaction data for demonstration"""
        np.random.seed(42)
        
        # Create sample transaction data
        n_customers = 1000
        n_transactions = 5000
        
        customer_ids = np.random.choice(range(1, n_customers + 1), n_transactions)
        transaction_dates = pd.date_range(
            start='2022-01-01', 
            end='2024-12-31', 
            periods=n_transactions
        )
        transaction_amounts = np.random.lognormal(mean=4, sigma=1, size=n_transactions)
        
        sample_data = pd.DataFrame({
            'customer_id': customer_ids,
            'transaction_date': transaction_dates,
            'transaction_amount': np.round(transaction_amounts, 2)
        })
        
        # Add customer information
        customers = pd.DataFrame({
            'customer_id': range(1, n_customers + 1),
            'customer_name': [f'Customer_{i}' for i in range(1, n_customers + 1)],
            'registration_date': pd.date_range(
                start='2020-01-01', 
                periods=n_customers, 
                freq='D'
            )
        })
        
        # Merge customer and transaction data
        sample_data = sample_data.merge(customers, on='customer_id', how='left')
        
        return sample_data
    
    def calculate_rfm(self, customer_col='customer_id', date_col='transaction_date', 
                     amount_col='transaction_amount', analysis_date=None):
        """
        Calculate RFM (Recency, Frequency, Monetary) metrics
        """
        if analysis_date is None:
            analysis_date = self.customer_data[date_col].max()
        
        # Convert date column to datetime if not already
        self.customer_data[date_col] = pd.to_datetime(self.customer_data[date_col])
        
        # Calculate RFM metrics
        rfm_data = self.customer_data.groupby(customer_col).agg({
            date_col: lambda x: (analysis_date - x.max()).days,  # Recency
            customer_col: 'count',  # Frequency  
            amount_col: 'sum'  # Monetary
        }).round(2)
        
        # Rename columns
        rfm_data.columns = ['Recency', 'Frequency', 'Monetary']
        rfm_data = rfm_data.reset_index()
        
        # Add RFM scores (1-5 scale)
        rfm_data['R_Score'] = pd.cut(rfm_data['Recency'], 
                                   bins=5, labels=[5,4,3,2,1]).astype(int)
        rfm_data['F_Score'] = pd.cut(rfm_data['Frequency'].rank(method='first'), 
                                   bins=5, labels=[1,2,3,4,5]).astype(int)
        rfm_data['M_Score'] = pd.cut(rfm_data['Monetary'].rank(method='first'), 
                                   bins=5, labels=[1,2,3,4,5]).astype(int)
        
        # Create RFM segments
        rfm_data['RFM_Score'] = (rfm_data['R_Score'] + rfm_data['F_Score'] + rfm_data['M_Score']) / 3
        
        # Customer segmentation based on RFM
        def segment_customers(row):
            if row['R_Score'] >= 4 and row['F_Score'] >= 4 and row['M_Score'] >= 4:
                return 'Champions'
            elif row['F_Score'] >= 4 and row['M_Score'] >= 4:
                return 'Loyal Customers'
            elif row['R_Score'] >= 4 and row['F_Score'] >= 3:
                return 'Potential Loyalists'
            elif row['R_Score'] >= 4 and row['F_Score'] <= 2:
                return 'New Customers'
            elif row['R_Score'] >= 3 and row['F_Score'] >= 2 and row['M_Score'] >= 2:
                return 'Promising'
            elif row['R_Score'] >= 3 and row['F_Score'] >= 3:
                return 'Need Attention'
            elif row['R_Score'] == 2 and row['F_Score'] >= 2 and row['M_Score'] >= 2:
                return 'About to Sleep'
            elif row['M_Score'] >= 4 and row['R_Score'] <= 2:
                return 'At Risk'
            elif row['M_Score'] >= 4 and row['R_Score'] == 1:
                return 'Cannot Lose Them'
            elif row['R_Score'] <= 2 and row['F_Score'] >= 2:
                return 'Hibernating'
            else:
                return 'Lost'
        
        rfm_data['Segment'] = rfm_data.apply(segment_customers, axis=1)
        
        self.rfm_data = rfm_data
        logging.info("RFM analysis completed successfully")
        
        return rfm_data
    
    def perform_kmeans_clustering(self, n_clusters=None, features=['Recency', 'Frequency', 'Monetary']):
        """
        Perform K-means clustering on customer data
        """
        if self.rfm_data is None:
            logging.error("RFM data not available. Please run calculate_rfm() first.")
            return None
        
        # Prepare data for clustering
        clustering_data = self.rfm_data[features].copy()
        
        # Scale the features
        scaled_features = self.scaler.fit_transform(clustering_data)
        scaled_df = pd.DataFrame(scaled_features, columns=features)
        
        # Determine optimal number of clusters if not provided
        if n_clusters is None:
            n_clusters = self._find_optimal_clusters(scaled_features)
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(scaled_features)
        
        # Add cluster labels to RFM data
        self.rfm_data['Cluster'] = cluster_labels
        
        # Calculate cluster characteristics
        cluster_summary = self.rfm_data.groupby('Cluster').agg({
            'Recency': ['mean', 'min', 'max'],
            'Frequency': ['mean', 'min', 'max'],
            'Monetary': ['mean', 'min', 'max'],
            'customer_id': 'count'
        }).round(2)
        
        # Flatten column names
        cluster_summary.columns = ['_'.join(col).strip() for col in cluster_summary.columns]
        cluster_summary = cluster_summary.reset_index()
        
        # Calculate silhouette score
        silhouette_avg = silhouette_score(scaled_features, cluster_labels)
        
        logging.info(f"K-means clustering completed with {n_clusters} clusters")
        logging.info(f"Silhouette Score: {silhouette_avg:.3f}")
        
        return cluster_summary, silhouette_avg
    
    def _find_optimal_clusters(self, data, max_clusters=10):
        """Find optimal number of clusters using elbow method and silhouette score"""
        inertias = []
        silhouette_scores = []
        k_range = range(2, min(max_clusters + 1, len(data)))
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(data)
            
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(data, cluster_labels))
        
        # Find optimal k using silhouette score
        optimal_k = k_range[np.argmax(silhouette_scores)]
        
        logging.info(f"Optimal number of clusters: {optimal_k}")
        return optimal_k
    
    def analyze_segments(self):
        """Analyze customer segments and provide business insights"""
        if self.rfm_data is None:
            logging.error("Segmentation not completed. Please run segmentation first.")
            return None
        
        # RFM Segment Analysis
        rfm_segment_summary = self.rfm_data.groupby('Segment').agg({
            'customer_id': 'count',
            'Recency': 'mean',
            'Frequency': 'mean', 
            'Monetary': 'mean',
            'RFM_Score': 'mean'
        }).round(2)
        
        # Calculate percentage of customers in each segment
        rfm_segment_summary['Percentage'] = (
            rfm_segment_summary['customer_id'] / len(self.rfm_data) * 100
        ).round(2)
        
        # Sort by monetary value
        rfm_segment_summary = rfm_segment_summary.sort_values('Monetary', ascending=False)
        
        # K-means cluster analysis (if available)
        cluster_summary = None
        if 'Cluster' in self.rfm_data.columns:
            cluster_summary = self.rfm_data.groupby('Cluster').agg({
                'customer_id': 'count',
                'Recency': 'mean',
                'Frequency': 'mean',
                'Monetary': 'mean'
            }).round(2)
            
            cluster_summary['Percentage'] = (
                cluster_summary['customer_id'] / len(self.rfm_data) * 100
            ).round(2)
        
        self.segmented_data = {
            'rfm_segments': rfm_segment_summary,
            'cluster_segments': cluster_summary
        }
        
        return self.segmented_data
    
    def generate_marketing_recommendations(self):
        """Generate marketing recommendations for each customer segment"""
        if self.rfm_data is None:
            return None
        
        recommendations = {
            'Champions': {
                'description': 'Best customers with high RFM scores',
                'strategy': 'VIP treatment, exclusive offers, loyalty rewards',
                'actions': ['Premium customer service', 'Early access to new products', 
                          'Personalized offers', 'Loyalty program benefits']
            },
            'Loyal Customers': {
                'description': 'High frequency and monetary value customers',
                'strategy': 'Upsell premium products, cross-sell, loyalty program',
                'actions': ['Product recommendations', 'Cross-selling campaigns', 
                          'Loyalty point bonuses', 'Premium upgrades']
            },
            'Potential Loyalists': {
                'description': 'Recent customers with good frequency',
                'strategy': 'Membership offers, engagement campaigns',
                'actions': ['Engagement sequences', 'Product education', 
                          'Membership invitations', 'Social proof']
            },
            'New Customers': {
                'description': 'Recent but low frequency customers',
                'strategy': 'Onboarding sequence, welcome offers',
                'actions': ['Welcome series', 'Onboarding tutorials', 
                          'First purchase incentives', 'Product discovery']
            },
            'At Risk': {
                'description': 'High value but declining engagement',
                'strategy': 'Win-back campaigns, special offers',
                'actions': ['Reactivation campaigns', 'Exclusive discounts', 
                          'Personal outreach', 'Feedback surveys']
            },
            'Cannot Lose Them': {
                'description': 'Highest value customers at risk of churning',
                'strategy': 'Immediate intervention, premium support',
                'actions': ['Personal account manager', 'Exclusive previews', 
                          'Special retention offers', 'Direct communication']
            },
            'Hibernating': {
                'description': 'Previously active, now dormant',
                'strategy': 'Win-back series, incentive offers',
                'actions': ['Re-engagement campaigns', 'Comeback offers', 
                          'Product updates', 'Limited-time promotions']
            },
            'Lost': {
                'description': 'Lowest RFM scores, likely churned',
                'strategy': 'Basic promotional offers, surveys',
                'actions': ['Exit surveys', 'Basic promotional emails', 
                          'Win-back attempts', 'Competitive analysis']
            }
        }
        
        return recommendations
    
    def save_results(self, output_dir='output/'):
        """Save segmentation results to CSV files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        if self.rfm_data is not None:
            # Save detailed RFM data
            self.rfm_data.to_csv(f'{output_dir}customer_rfm_analysis.csv', index=False)
            
            # Save segment summaries
            if self.segmented_data:
                self.segmented_data['rfm_segments'].to_csv(
                    f'{output_dir}rfm_segment_summary.csv'
                )
                
                if self.segmented_data['cluster_segments'] is not None:
                    self.segmented_data['cluster_segments'].to_csv(
                        f'{output_dir}cluster_segment_summary.csv'
                    )
            
            logging.info(f"Results saved to {output_dir}")
            return True
        
        return False
    
    def create_visualizations(self):
        """Create visualizations for customer segmentation analysis"""
        if self.rfm_data is None:
            logging.error("No data available for visualization")
            return None
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Customer Segmentation Analysis', fontsize=16, fontweight='bold')
        
        # 1. RFM Distribution
        axes[0, 0].hist([self.rfm_data['Recency'], self.rfm_data['Frequency'], 
                        self.rfm_data['Monetary']], bins=20, alpha=0.7, 
                       label=['Recency', 'Frequency', 'Monetary'])
        axes[0, 0].set_title('RFM Metrics Distribution')
        axes[0, 0].legend()
        
        # 2. Customer Segments Distribution
        segment_counts = self.rfm_data['Segment'].value_counts()
        axes[0, 1].pie(segment_counts.values, labels=segment_counts.index, autopct='%1.1f%%')
        axes[0, 1].set_title('Customer Segments Distribution')
        
        # 3. RFM Scatter Plot
        scatter = axes[1, 0].scatter(self.rfm_data['Frequency'], self.rfm_data['Monetary'], 
                                   c=self.rfm_data['Recency'], alpha=0.6, cmap='viridis')
        axes[1, 0].set_xlabel('Frequency')
        axes[1, 0].set_ylabel('Monetary')
        axes[1, 0].set_title('Frequency vs Monetary (colored by Recency)')
        plt.colorbar(scatter, ax=axes[1, 0])
        
        # 4. Segment Revenue Contribution
        segment_revenue = self.rfm_data.groupby('Segment')['Monetary'].sum().sort_values()
        axes[1, 1].barh(segment_revenue.index, segment_revenue.values)
        axes[1, 1].set_title('Revenue Contribution by Segment')
        axes[1, 1].set_xlabel('Total Revenue')
        
        plt.tight_layout()
        plt.savefig('assets/customer_segmentation_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Create additional cluster visualization if available
        if 'Cluster' in self.rfm_data.columns:
            self._plot_clusters()
    
    def _plot_clusters(self):
        """Create cluster visualization using PCA"""
        features = ['Recency', 'Frequency', 'Monetary']
        scaled_features = self.scaler.transform(self.rfm_data[features])
        
        # Apply PCA for 2D visualization
        pca = PCA(n_components=2)
        pca_features = pca.fit_transform(scaled_features)
        
        plt.figure(figsize=(10, 8))
        scatter = plt.scatter(pca_features[:, 0], pca_features[:, 1], 
                            c=self.rfm_data['Cluster'], cmap='tab10', alpha=0.7)
        plt.xlabel(f'First Component (Explained Variance: {pca.explained_variance_ratio_[0]:.2%})')
        plt.ylabel(f'Second Component (Explained Variance: {pca.explained_variance_ratio_[1]:.2%})')
        plt.title('Customer Clusters Visualization (PCA)')
        plt.colorbar(scatter)
        plt.savefig('assets/customer_clusters_pca.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    """
    Main execution function for customer segmentation analysis
    
    Author: Sahil Hansa
    Contact: sahilhansa007@gmail.com
    """
    print("=== Customer Segmentation Analysis ===")
    print("Author: Sahil Hansa")
    print("Email: sahilhansa007@gmail.com")
    print("GitHub: https://github.com/SAHIL-HANSA")
    print("Location: Jammu, J&K, India")
    print("=" * 40)
    
    # Initialize segmentation analysis
    segmentation = CustomerSegmentation()
    
    # Load data (using sample data for demonstration)
    print("Loading customer data...")
    data = segmentation.load_data()
    
    if data is not None:
        print(f"Loaded {len(data)} transaction records")
        
        # Perform RFM analysis
        print("Calculating RFM metrics...")
        rfm_results = segmentation.calculate_rfm()
        print(f"RFM analysis completed for {len(rfm_results)} customers")
        
        # Perform K-means clustering
        print("Performing K-means clustering...")
        cluster_summary, silhouette_score = segmentation.perform_kmeans_clustering()
        print(f"Clustering completed with silhouette score: {silhouette_score:.3f}")
        
        # Analyze segments
        print("Analyzing customer segments...")
        segment_analysis = segmentation.analyze_segments()
        
        # Display results
        print("\n=== RFM SEGMENT ANALYSIS ===")
        print(segment_analysis['rfm_segments'])
        
        if segment_analysis['cluster_segments'] is not None:
            print("\n=== CLUSTER ANALYSIS ===")
            print(segment_analysis['cluster_segments'])
        
        # Generate marketing recommendations
        recommendations = segmentation.generate_marketing_recommendations()
        print("\n=== MARKETING RECOMMENDATIONS ===")
        for segment, rec in recommendations.items():
            print(f"\n{segment}:")
            print(f"  Strategy: {rec['strategy']}")
            print(f"  Actions: {', '.join(rec['actions'][:2])}")
        
        # Save results
        print("\nSaving results...")
        segmentation.save_results()
        
        # Create visualizations
        print("Creating visualizations...")
        segmentation.create_visualizations()
        
        print("\n=== Analysis Complete ===")
        print("Check the 'output/' directory for CSV files")
        print("Check the 'assets/' directory for visualizations")
    
    else:
        print("Failed to load data. Please check your data source.")

if __name__ == "__main__":
    main()