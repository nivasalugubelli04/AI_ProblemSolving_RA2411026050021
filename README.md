📘 1. Student Exam Score Predictor – README.md
# 🎓 Student Exam Score Predictor

A Machine Learning-based desktop application that predicts student exam scores using academic performance data.

---

## 📌 Problem Description

Educational institutions often need a way to estimate student performance based on factors like study time, attendance, and previous scores.

This project solves that problem by:
- Taking key academic inputs
- Training a machine learning model
- Predicting final exam scores with accuracy metrics

---

## 🧠 Algorithms Used

### 🔹 Linear Regression
- A supervised machine learning algorithm
- Used to predict continuous values (exam scores)
- Learns relationship between:
  - Input features (study hours, attendance, etc.)
  - Output (exam score)

### 🔹 Data Preprocessing
- Missing value handling (median filling)
- Feature scaling using **StandardScaler**

### 🔹 Model Evaluation Metrics
- **R² Score** → Accuracy of model
- **MAE** → Average error
- **RMSE** → Standard deviation of prediction errors

---

## ⚙️ Execution Steps

1. Install dependencies:
   ```bash
   pip install scikit-learn pandas numpy

Run the application:

python StudentScorePredictor.py
Load dataset:
Upload CSV file OR
Generate synthetic data OR
Enter data manually
Train the model:
Click Train Model
Predict:
Enter student details
Press Predict (or Enter key)
📊 Sample Input
Feature	Value
Hours Studied	6
Attendance %	85
Previous Score	78
Assignments Done	8
📈 Sample Output
Predicted Score: 82.45
Grade: Good
Confidence Range: ±4.2
🚀 Features
GUI-based application (Tkinter)
Real-time predictions
Data visualization (charts)
Multiple dataset input methods
Prediction confidence range
🛠 Technologies Used
Python
Tkinter
Scikit-learn
Pandas
NumPy
💡 Future Improvements
Add advanced ML models (Random Forest, XGBoost)
Export predictions to CSV
Improve UI with graphs using matplotlib
👨‍💻 Author

Machine Learning Mini Project


# ✈️ 2. Tourist Travel Planner 

# ✈️ Tourist Travel Planner

A GUI-based travel planning application that helps users organize trips, manage budgets, and create itineraries efficiently.

---

## 📌 Problem Description

Planning a trip involves multiple tasks:
- Managing destinations
- Tracking expenses
- Scheduling activities
- Organizing packing items

This project provides an **all-in-one solution** to simplify travel planning.

---

## 🧠 Algorithms / Logic Used

### 🔹 Data Management
- Uses Python data structures (lists, dictionaries)
- Stores data in structured format (JSON)

### 🔹 Budget Calculation
- Sum of expenses
- Remaining budget calculation:

Remaining = Total Budget - Total Expenses


### 🔹 Sorting & Filtering
- Activities sorted by time
- Destinations filtered using search

### 🔹 Progress Tracking
- Packing completion percentage
- Budget usage percentage

---

## ⚙️ Execution Steps

1. Run the application:

 python TouristTravelPlanner.py
Add trip details:
Enter trip name
Add destinations
Plan itinerary:
Select day
Add activities
Track budget:
Set total budget
Add expenses
Manage packing list:
Add items
Mark items as packed
Save or export:
Save trip data
Export summary as TXT
📊 Sample Inputs
Destination
City: Paris
Days: 3
Cost: 1200
Expense
Category: Food
Amount: 50
Packing Item
Item: Passport
Category: Documents
📈 Sample Outputs
Budget Summary
Total Budget: $2000
Spent: $850
Remaining: $1150
Itinerary Example
Day 1:
09:00 - Visit Eiffel Tower
13:00 - Lunch at local cafe
16:00 - River cruise
Packing Progress
Packed: 8 / 12 items
Completion: 66%
🚀 Features
Destination management system
Day-by-day itinerary planner
Expense tracking with visualization
Packing checklist with progress bar
Save/load trip functionality
🛠 Technologies Used
Python
Tkinter
JSON
💡 Future Enhancements
Map integration (Google Maps)
Currency converter
Multi-user collaboration
Mobile app version
