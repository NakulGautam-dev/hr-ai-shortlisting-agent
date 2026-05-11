# AI HR Shortlisting System - Frontend

A professional Streamlit dashboard for visualizing and analyzing AI-powered candidate screening results.

## Features

- **📊 Dashboard** - Key metrics and top candidate overview
- **🏅 Rankings** - Interactive candidate rankings with filters and export
- **🔍 Candidate Analysis** - Detailed analysis with score breakdown and skill matching
- **📈 Analytics** - Visual insights and performance analytics
- **ℹ️ System Info** - Backend status and configuration information

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install from Project Root (Optional)

From the project root directory:

```bash
pip install streamlit pandas plotly
```

## Usage

### Run the Dashboard

```bash
streamlit run frontend/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

### Using the Frontend

1. **Sidebar Navigation**
   - Use the sidebar to navigate between different pages
   - Select batch result files from the dropdown

2. **Select Batch File**
   - Choose a results file to load candidate data
   - Click "Refresh" to reload the current file

3. **View Results**
   - Dashboard shows overview and top candidate
   - Rankings page displays all candidates
   - Candidate Analysis shows detailed breakdown
   - Analytics provides visual insights

### Data Source

The frontend loads pre-generated JSON files from:

```
outputs/
├── shortlisting_results_*.json
├── batch_summary_*.json
└── candidates_*.json
```

Run the backend pipeline to generate these files:

```bash
python app.py
```

## File Structure

```
frontend/
├── streamlit_app.py       # Main Streamlit application
├── utils.py               # Utility functions
├── charts.py              # Chart visualization utilities
├── dashboard.py           # Dashboard components (placeholder)
├── candidate_view.py      # Candidate view components (placeholder)
├── requirements.txt       # Python dependencies
├── assets/                # Static assets (images, etc.)
└── README.md             # This file
```

## Configuration

The frontend automatically:

- Detects the output directory from the project structure
- Loads JSON files from the outputs directory
- Works without Gemini API access (uses pre-generated results)

## Troubleshooting

### Issue: "No batch files found"

**Solution:** Run the backend pipeline first:

```bash
python app.py
```

### Issue: "Import error for plotly/pandas"

**Solution:** Install missing dependencies:

```bash
pip install streamlit pandas plotly
```

### Issue: "FileNotFoundError for outputs directory"

**Solution:** The directory is created automatically, or run the backend pipeline.

## Future Enhancements

- Custom dashboard themes
- Advanced filtering options
- Real-time data updates
- Candidate comparison charts
- Export to PDF reports
- Integration with ATS systems

## Performance Notes

- The app caches data in Streamlit's session state
- Initial load may take a few seconds for large datasets
- Charts are interactive with Plotly
- All data operations are client-side (no server backend required)

## Browser Compatibility

Works best with:

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Support

For issues or feature requests, please refer to the main project README.
