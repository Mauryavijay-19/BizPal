# BizPal — AI-Powered Business Intelligence & Decision Support Platform

A web-based Business Intelligence and Decision Support Platform designed to help small retail businesses turn sales data into actionable insights.

## 🚀 Live Demo

https://bizpal.streamlit.app/

## 💡 What is BizPal?

BizPal takes retail sales data and converts it into business insights through analytics, machine learning, inventory analysis, and recommendations.

## ✨ Features

- 📊 Sales & Revenue Analytics
- 📈 KPI Dashboard
- 🤖 Machine Learning Demand Forecasting
- 📦 Inventory & Reorder Analysis
- 🔮 Forecast-Aware Inventory Recommendations
- 💡 Business Recommendations
- 💬 Rule-Based "Ask BizPal" Chatbot
- 📄 PDF & Excel Report Generation

## 🧠 Machine Learning

BizPal compares multiple forecasting models:

- Random Forest Regressor
- Gradient Boosting Regressor

Evaluation metrics:

- MAE
- RMSE
- MAPE

Gradient Boosting achieved better average performance on the evaluated products.

## 🛠️ Tech Stack

- Python
- Pandas
- NumPy
- Scikit-learn
- Streamlit
- Plotly
- SQLite
- ReportLab
- OpenPyXL
- Git & GitHub

## 🏗️ Project Structure

```text
BizPal/
├── app.py
├── requirements.txt
├── models/
├── src/
│   ├── data_cleaning.py
│   ├── pipeline.py
│   ├── chatbot.py
│   ├── database.py
│   ├── kpi.py
│   ├── report_export.py
│   ├── utils.py
│   ├── forecasting.py
│   ├── inventory.py
│   └── advisor.py
└── README.md

📊 Workflow
CSV Sales Data
      ↓
Data Cleaning & Validation
      ↓
Business Analytics & KPIs
      ↓
Demand Forecasting
      ↓
Inventory Analysis
      ↓
Recommendations
      ↓
Dashboard & Reports
