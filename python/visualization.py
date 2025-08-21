"""
Customer Segmentation Data Visualization
Author: Sahil Hansa
Email: sahilhansa007@gmail.com
Description: Comprehensive visualization scripts for customer segmentation analysis
Location: Jammu, J&K, India
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Set style for matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class CustomerSegmentationVisualizer:
    """
    Customer Segmentation Visualization Class
    
    Creates comprehensive visualizations for customer segmentation analysis
    
    Author: Sahil Hansa
    Contact: sahilhansa007@gmail.com
    """
    
    def __init__(self, rfm_data=None):
        self.rfm_data = rfm_data
        self.color_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        
    def load_data(self, csv_path):
        """Load RFM data from CSV file"""
        try:
            self.rfm_data = pd.read_csv(csv_path)
            print(f"Data loaded successfully: {len(self.rfm_data)} customers")
            return self.rfm_data
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return None
    
    def create_rfm_distribution_plots(self, save_path='assets/rfm_distribution.png'):
        """Create RFM metrics distribution plots"""
        if self.rfm_data is None:
            print("No data available. Please load data first.")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('RFM Metrics Distribution Analysis', fontsize=16, fontweight='bold')
        
        # Recency Distribution
        axes[0, 0].hist(self.rfm_data['Recency'], bins=30, alpha=0.7, color='#FF6B6B', edgecolor='black')
        axes[0, 0].set_title('Recency Distribution (Days since last purchase)')
        axes[0, 0].set_xlabel('Days')
        axes[0, 0].set_ylabel('Number of Customers')
        axes[0, 0].axvline(self.rfm_data['Recency'].mean(), color='red', linestyle='--', 
                          label=f'Mean: {self.rfm_data["Recency"].mean():.1f}')
        axes[0, 0].legend()
        
        # Frequency Distribution
        axes[0, 1].hist(self.rfm_data['Frequency'], bins=20, alpha=0.7, color='#4ECDC4', edgecolor='black')
        axes[0, 1].set_title('Frequency Distribution (Number of purchases)')
        axes[0, 1].set_xlabel('Number of Purchases')
        axes[0, 1].set_ylabel('Number of Customers')
        axes[0, 1].axvline(self.rfm_data['Frequency'].mean(), color='red', linestyle='--',
                          label=f'Mean: {self.rfm_data["Frequency"].mean():.1f}')
        axes[0, 1].legend()
        
        # Monetary Distribution
        axes[1, 0].hist(self.rfm_data['Monetary'], bins=30, alpha=0.7, color='#45B7D1', edgecolor='black')
        axes[1, 0].set_title('Monetary Distribution (Total spent)')
        axes[1, 0].set_xlabel('Total Amount Spent ($)')
        axes[1, 0].set_ylabel('Number of Customers')
        axes[1, 0].axvline(self.rfm_data['Monetary'].mean(), color='red', linestyle='--',
                          label=f'Mean: ${self.rfm_data["Monetary"].mean():.0f}')
        axes[1, 0].legend()
        
        # RFM Score Distribution
        if 'RFM_Score' in self.rfm_data.columns:
            axes[1, 1].hist(self.rfm_data['RFM_Score'], bins=15, alpha=0.7, color='#96CEB4', edgecolor='black')
            axes[1, 1].set_title('RFM Score Distribution')
            axes[1, 1].set_xlabel('RFM Score')
            axes[1, 1].set_ylabel('Number of Customers')
            axes[1, 1].axvline(self.rfm_data['RFM_Score'].mean(), color='red', linestyle='--',
                              label=f'Mean: {self.rfm_data["RFM_Score"].mean():.2f}')
            axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"RFM distribution plots saved to {save_path}")
    
    def create_customer_segments_pie_chart(self, save_path='assets/segments_pie_chart.png'):
        """Create pie chart showing customer segment distribution"""
        if self.rfm_data is None or 'Segment' not in self.rfm_data.columns:
            print("No segment data available.")
            return
        
        segment_counts = self.rfm_data['Segment'].value_counts()
        
        plt.figure(figsize=(12, 8))
        colors = self.color_palette[:len(segment_counts)]
        
        wedges, texts, autotexts = plt.pie(segment_counts.values, 
                                          labels=segment_counts.index,
                                          autopct='%1.1f%%',
                                          colors=colors,
                                          startangle=90,
                                          explode=[0.05] * len(segment_counts))
        
        plt.title('Customer Segments Distribution', fontsize=16, fontweight='bold', pad=20)
        
        # Enhance text appearance
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # Add legend with customer counts
        legend_labels = [f'{segment}: {count} customers' 
                        for segment, count in segment_counts.items()]
        plt.legend(wedges, legend_labels, title="Segments", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Segment pie chart saved to {save_path}")
    
    def create_rfm_scatter_plot(self, save_path='assets/rfm_scatter.png'):
        """Create interactive scatter plot for RFM analysis"""
        if self.rfm_data is None:
            print("No data available.")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Frequency vs Monetary (colored by Recency)
        scatter1 = axes[0].scatter(self.rfm_data['Frequency'], self.rfm_data['Monetary'], 
                                  c=self.rfm_data['Recency'], cmap='viridis', alpha=0.6, s=60)
        axes[0].set_xlabel('Frequency (Number of Purchases)')
        axes[0].set_ylabel('Monetary (Total Spent $)')
        axes[0].set_title('Frequency vs Monetary (colored by Recency)')
        cbar1 = plt.colorbar(scatter1, ax=axes[0])
        cbar1.set_label('Recency (Days)')
        
        # Recency vs Monetary (colored by Frequency)
        scatter2 = axes[1].scatter(self.rfm_data['Recency'], self.rfm_data['Monetary'], 
                                  c=self.rfm_data['Frequency'], cmap='plasma', alpha=0.6, s=60)
        axes[1].set_xlabel('Recency (Days since last purchase)')
        axes[1].set_ylabel('Monetary (Total Spent $)')
        axes[1].set_title('Recency vs Monetary (colored by Frequency)')
        cbar2 = plt.colorbar(scatter2, ax=axes[1])
        cbar2.set_label('Frequency (Purchases)')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"RFM scatter plots saved to {save_path}")
    
    def create_segment_comparison_chart(self, save_path='assets/segment_comparison.png'):
        """Create bar chart comparing segments by key metrics"""
        if self.rfm_data is None or 'Segment' not in self.rfm_data.columns:
            print("No segment data available.")
            return
        
        # Calculate segment statistics
        segment_stats = self.rfm_data.groupby('Segment').agg({
            'customer_id': 'count',
            'Recency': 'mean',
            'Frequency': 'mean',
            'Monetary': ['mean', 'sum']
        }).round(2)
        
        segment_stats.columns = ['Customer_Count', 'Avg_Recency', 'Avg_Frequency', 'Avg_Monetary', 'Total_Revenue']
        segment_stats = segment_stats.reset_index()
        segment_stats = segment_stats.sort_values('Total_Revenue', ascending=True)
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Customer Segment Comparison Analysis', fontsize=16, fontweight='bold')
        
        # Customer Count by Segment
        axes[0, 0].barh(segment_stats['Segment'], segment_stats['Customer_Count'], 
                       color=self.color_palette[:len(segment_stats)])
        axes[0, 0].set_title('Customer Count by Segment')
        axes[0, 0].set_xlabel('Number of Customers')
        
        # Average Recency by Segment
        axes[0, 1].barh(segment_stats['Segment'], segment_stats['Avg_Recency'], 
                       color=self.color_palette[:len(segment_stats)])
        axes[0, 1].set_title('Average Recency by Segment (Days)')
        axes[0, 1].set_xlabel('Days since Last Purchase')
        
        # Average Frequency by Segment
        axes[1, 0].barh(segment_stats['Segment'], segment_stats['Avg_Frequency'], 
                       color=self.color_palette[:len(segment_stats)])
        axes[1, 0].set_title('Average Frequency by Segment')
        axes[1, 0].set_xlabel('Average Number of Purchases')
        
        # Total Revenue by Segment
        axes[1, 1].barh(segment_stats['Segment'], segment_stats['Total_Revenue'], 
                       color=self.color_palette[:len(segment_stats)])
        axes[1, 1].set_title('Total Revenue by Segment')
        axes[1, 1].set_xlabel('Total Revenue ($)')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Segment comparison chart saved to {save_path}")
        
        return segment_stats
    
    def create_rfm_scores_heatmap(self, save_path='assets/rfm_scores_heatmap.png'):
        """Create heatmap showing RFM score combinations"""
        if self.rfm_data is None:
            print("No data available.")
            return
        
        # Check if score columns exist
        score_cols = ['R_Score', 'F_Score', 'M_Score']
        if not all(col in self.rfm_data.columns for col in score_cols):
            print("RFM score columns not found.")
            return
        
        # Create RFM score combination matrix
        rfm_matrix = self.rfm_data.groupby(['R_Score', 'F_Score']).agg({
            'customer_id': 'count',
            'M_Score': 'mean'
        }).reset_index()
        
        # Pivot for heatmap
        heatmap_data = rfm_matrix.pivot(index='R_Score', columns='F_Score', values='customer_id')
        heatmap_data = heatmap_data.fillna(0)
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlOrRd', 
                    cbar_kws={'label': 'Number of Customers'})
        plt.title('Customer Distribution by RFM Scores\n(Recency vs Frequency)', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Frequency Score')
        plt.ylabel('Recency Score')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"RFM scores heatmap saved to {save_path}")
    
    def create_interactive_plotly_dashboard(self, save_path='assets/interactive_dashboard.html'):
        """Create interactive Plotly dashboard"""
        if self.rfm_data is None:
            print("No data available.")
            return
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Customer Segments', 'RFM Scatter Plot', 
                          'Segment Revenue', 'RFM Score Distribution'),
            specs=[[{"type": "pie"}, {"type": "scatter"}],
                   [{"type": "bar"}, {"type": "histogram"}]]
        )
        
        # 1. Pie chart for segments
        if 'Segment' in self.rfm_data.columns:
            segment_counts = self.rfm_data['Segment'].value_counts()
            fig.add_trace(
                go.Pie(labels=segment_counts.index, values=segment_counts.values,
                       name="Segments", hole=0.3),
                row=1, col=1
            )
        
        # 2. Scatter plot
        fig.add_trace(
            go.Scatter(x=self.rfm_data['Frequency'], y=self.rfm_data['Monetary'],
                      mode='markers', 
                      marker=dict(color=self.rfm_data['Recency'], colorscale='Viridis',
                                showscale=True, colorbar=dict(title="Recency")),
                      text=self.rfm_data.get('Segment', ''),
                      hovertemplate='<b>Frequency:</b> %{x}<br><b>Monetary:</b> %{y}<br><b>Segment:</b> %{text}',
                      name="Customers"),
            row=1, col=2
        )
        
        # 3. Revenue by segment
        if 'Segment' in self.rfm_data.columns:
            segment_revenue = self.rfm_data.groupby('Segment')['Monetary'].sum().sort_values()
            fig.add_trace(
                go.Bar(x=segment_revenue.values, y=segment_revenue.index,
                       orientation='h', name="Revenue"),
                row=2, col=1
            )
        
        # 4. RFM Score distribution
        if 'RFM_Score' in self.rfm_data.columns:
            fig.add_trace(
                go.Histogram(x=self.rfm_data['RFM_Score'], nbinsx=20, name="RFM Score"),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title_text="Customer Segmentation Interactive Dashboard",
            title_x=0.5,
            height=800,
            showlegend=False
        )
        
        # Save as HTML
        fig.write_html(save_path)
        fig.show()
        print(f"Interactive dashboard saved to {save_path}")
    
    def create_comprehensive_report(self, output_dir='visualizations/'):
        """Generate all visualizations and save to directory"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print("=== Creating Comprehensive Visualization Report ===")
        print("Author: Sahil Hansa")
        print("Email: sahilhansa007@gmail.com")
        print("=" * 50)
        
        # Generate all visualizations
        self.create_rfm_distribution_plots(f'{output_dir}rfm_distribution.png')
        self.create_customer_segments_pie_chart(f'{output_dir}segments_pie_chart.png')
        self.create_rfm_scatter_plot(f'{output_dir}rfm_scatter.png')
        segment_stats = self.create_segment_comparison_chart(f'{output_dir}segment_comparison.png')
        self.create_rfm_scores_heatmap(f'{output_dir}rfm_scores_heatmap.png')
        self.create_interactive_plotly_dashboard(f'{output_dir}interactive_dashboard.html')
        
        # Save segment statistics to CSV
        if segment_stats is not None:
            segment_stats.to_csv(f'{output_dir}segment_statistics.csv', index=False)
            print(f"Segment statistics saved to {output_dir}segment_statistics.csv")
        
        print(f"\n=== All visualizations created in {output_dir} ===")
        print("Visualization files:")
        print("1. rfm_distribution.png - RFM metrics distribution")
        print("2. segments_pie_chart.png - Customer segments pie chart")
        print("3. rfm_scatter.png - RFM scatter plots")
        print("4. segment_comparison.png - Segment comparison charts")
        print("5. rfm_scores_heatmap.png - RFM scores heatmap")
        print("6. interactive_dashboard.html - Interactive Plotly dashboard")
        print("7. segment_statistics.csv - Segment performance statistics")

def main():
    """
    Main execution function for visualization
    
    Author: Sahil Hansa
    Contact: sahilhansa007@gmail.com
    """
    print("=== Customer Segmentation Visualization ===")
    print("Author: Sahil Hansa")
    print("Email: sahilhansa007@gmail.com")
    print("GitHub: https://github.com/SAHIL-HANSA")
    print("Location: Jammu, J&K, India")
    print("=" * 45)
    
    # Initialize visualizer
    visualizer = CustomerSegmentationVisualizer()
    
    # Load sample data
    sample_data_path = 'data/sample/customer_segments.csv'
    data = visualizer.load_data(sample_data_path)
    
    if data is not None:
        # Generate comprehensive visualization report
        visualizer.create_comprehensive_report()
        
        print("\n=== Visualization Complete ===")
        print("Check the 'visualizations/' directory for all charts and graphs")
        print("Open 'interactive_dashboard.html' in your browser for interactive analysis")
    else:
        print("Could not load data. Please check the file path.")
        print("Make sure 'customer_segments.csv' exists in data/sample/ directory")

if __name__ == "__main__":
    main()